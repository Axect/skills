"""OpenAlex /works source module with precision filters for reference-search."""

from __future__ import annotations

import math
import urllib.error
import urllib.parse
from typing import Any

from _common import WorkSummary, extract_arxiv_id, http_get_json

_BASE = "https://api.openalex.org/works"
_SELECT = (
    "id,display_name,title,publication_year,cited_by_count,doi,primary_location,"
    "authorships,abstract_inverted_index,topics,concepts,relevance_score,language"
)

_MODE_DEFAULTS: dict[str, dict[str, Any]] = {
    "background":    {"year_from": 2021, "types": ["article", "review"]},
    "survey":        {"year_from": 2019, "types": ["review", "article"]},
    "method":        {"year_from": 2020, "types": ["article", "review", "preprint"]},
    "baseline":      {"types": ["article", "review", "preprint"]},
    "evaluation":    {"year_from": 2020, "types": ["article", "review", "dataset"]},
    "claim-support": {"year_from": 2021, "types": ["article", "review", "report"]},
}


def search(
    query: str,
    *,
    mode: str = "background",
    limit: int = 10,
    email: str | None = None,
    min_score: float = 0.0,
    topic_ids: list[str] | None = None,
    year_from: int | None = None,
    types: list[str] | None = None,
    sort: str | None = None,
    use_precise_filter: bool = True,
) -> list[WorkSummary]:
    """Search OpenAlex /works with precision filters; return normalized
    WorkSummary records, score-filtered."""
    defaults = _MODE_DEFAULTS.get(mode, {})
    resolved_year = year_from if year_from is not None else defaults.get("year_from")
    resolved_types = types if types is not None else defaults.get("types")

    if sort is None:
        sort = "cited_by_count:desc" if mode in ("survey", "baseline") else "relevance_score:desc"

    fetch_n = min(50, max(limit * 3, 25))
    filter_parts = ["has_abstract:true", "language:en", "is_paratext:false"]

    if resolved_year:
        filter_parts.append(f"from_publication_date:{resolved_year}-01-01")
    if resolved_types:
        filter_parts.append("type:" + "|".join(resolved_types))
    if topic_ids:
        filter_parts.append("topics.id:" + "|".join(topic_ids))

    if use_precise_filter:
        # Restrict to title+abstract match — avoids full-text noise hits.
        # OpenAlex does not accept quoted values inside filter strings; unquoted works.
        filter_parts.append(f"title_and_abstract.search:{query}")
        filter_str = ",".join(filter_parts)
        params: dict[str, str] = {
            "filter": filter_str,
            "sort": sort,
            "select": _SELECT,
            "per-page": str(fetch_n),
        }
    else:
        filter_str = ",".join(filter_parts)
        params = {
            "search": query,
            "filter": filter_str,
            "sort": sort,
            "select": _SELECT,
            "per-page": str(fetch_n),
        }

    url = _BASE + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)

    try:
        data = http_get_json(url, email=email)
    except (urllib.error.HTTPError, urllib.error.URLError):
        return []

    raw_results: list[dict[str, Any]] = data.get("results") or []
    summaries = [_parse_work(w) for w in raw_results]
    summaries = _normalize_scores(summaries)
    summaries = [s for s in summaries if s.source_score >= min_score]
    return summaries[:limit]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_work(work: dict[str, Any]) -> WorkSummary:
    title = work.get("display_name") or work.get("title") or "Untitled"
    year: int | None = work.get("publication_year")
    cited_by_count: int = work.get("cited_by_count") or 0
    authors = _format_authors(work.get("authorships"))
    identifier = _identifier_for(work)
    abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))
    concepts = _top_concepts(work)
    venue = _venue(work)
    arxiv_id = extract_arxiv_id(identifier) or extract_arxiv_id(
        ((work.get("primary_location") or {}).get("landing_page_url"))
    )
    raw_score: float | None = work.get("relevance_score")
    # Store raw for batch normalization; final source_score set in _normalize_scores
    return WorkSummary(
        title=title,
        year=year,
        cited_by_count=cited_by_count,
        authors=authors,
        identifier=identifier,
        abstract=abstract,
        concepts=concepts,
        source="openalex",
        source_score=raw_score if raw_score is not None else float(cited_by_count),
        venue=venue,
        arxiv_id=arxiv_id,
    )


def _normalize_scores(summaries: list[WorkSummary]) -> list[WorkSummary]:
    """Normalize source_score to [0,1] across the batch."""
    if not summaries:
        return summaries

    # Check whether all had real relevance scores (distinguishable from cited_by fallback
    # by checking if any score looks like a citation count — we stored raw floats above).
    # Strategy: if sort was by relevance, scores are large unbounded floats; otherwise
    # they were replaced by cited_by_count ints. We can't tell after the fact, so we
    # always normalize the batch by max.
    max_score = max(s.source_score for s in summaries)

    for s in summaries:
        if max_score > 0:
            s.source_score = s.source_score / max_score
        else:
            # All zeros — fall back to citation-derived score
            s.source_score = min(math.log1p(s.cited_by_count) / 10.0, 1.0)

    return summaries


def _reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    if not inverted_index:
        return "N/A"
    size = max(pos for positions in inverted_index.values() for pos in positions) + 1
    tokens: list[str] = [""] * size
    for word, positions in inverted_index.items():
        for pos in positions:
            tokens[pos] = word
    full_text = " ".join(t for t in tokens if t)
    sentences = [p.strip() for p in full_text.split(". ") if p.strip()]
    return ". ".join(sentences[:2]) or full_text[:400] or "N/A"


def _format_authors(authorships: list[dict[str, Any]] | None) -> str:
    if not authorships:
        return "Unknown"
    names = [
        ((entry.get("author") or {}).get("display_name") or "Unknown")
        for entry in authorships[:3]
    ]
    if len(authorships) == 1:
        return names[0]
    if len(authorships) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{names[0]} et al."


def _identifier_for(work: dict[str, Any]) -> str:
    doi = work.get("doi")
    if doi:
        return doi
    primary = work.get("primary_location") or {}
    landing = primary.get("landing_page_url")
    if landing:
        return landing
    pdf = primary.get("pdf_url")
    if pdf:
        return pdf
    return work.get("id") or "N/A"


def _top_concepts(work: dict[str, Any]) -> list[str]:
    topics = work.get("topics") or []
    if topics:
        ranked = sorted(
            (t for t in topics if t.get("display_name")),
            key=lambda t: t.get("score", 0),
            reverse=True,
        )
        return [t["display_name"] for t in ranked[:5]]
    # Fall back to deprecated concepts field
    concepts = work.get("concepts") or []
    ranked_c = sorted(
        (c for c in concepts if c.get("display_name")),
        key=lambda c: c.get("score", 0),
        reverse=True,
    )
    return [c["display_name"] for c in ranked_c[:5]]


def _venue(work: dict[str, Any]) -> str | None:
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}
    return source.get("display_name") or None


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    results = search("halo mass function N-body simulation", mode="background", limit=5)
    print(f"# fetched {len(results)} results")
    for r in results[:3]:
        print(f"- [{r.source_score:.2f}] {r.title[:80]}  ({r.year})")
        print(f"  {r.identifier}")
