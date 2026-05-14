"""Semantic Scholar Graph API source module for reference-search.

Supplements OpenAlex for non-HEP domains or when OpenAlex results are sparse.
The `tldr` field (SS-generated 1–2 line summary) is the key differentiator.
"""

from __future__ import annotations

import math
import os
import sys
import urllib.error
import urllib.parse
from typing import Any

from _common import WorkSummary, extract_arxiv_id, http_get_json

_BASE = "https://api.semanticscholar.org/graph/v1/paper/search"
_FIELDS = (
    "paperId,externalIds,url,title,abstract,venue,year,authors,"
    "citationCount,influentialCitationCount,tldr,fieldsOfStudy,publicationVenue"
)

# Mode → default year_from. "baseline" has no year cap → omit from dict.
_MODE_YEAR_DEFAULTS: dict[str, int] = {
    "background": 2021,
    "claim-support": 2021,
    "survey": 2019,
    "method": 2020,
    "evaluation": 2020,
}


def search(
    query: str,
    *,
    mode: str = "background",
    limit: int = 10,
    email: str | None = None,
    year_from: int | None = None,
    api_key: str | None = None,
    min_score: float = 0.0,
) -> list[WorkSummary]:
    """Search Semantic Scholar /paper/search and return WorkSummary records.

    API key is read from the S2_API_KEY env var if not passed. Unauthenticated
    requests work but are rate-limited; the caller should be tolerant of 429.
    """
    api_key = api_key or os.environ.get("S2_API_KEY")

    resolved_year = year_from if year_from is not None else _MODE_YEAR_DEFAULTS.get(mode)
    fetch_n = min(100, max(limit, 20))

    params: dict[str, str] = {
        "query": query,
        "limit": str(fetch_n),
        "offset": "0",
        "fields": _FIELDS,
    }
    if resolved_year is not None:
        params["year"] = f"{resolved_year}-"

    url = _BASE + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)

    headers: dict[str, str] = {}
    if api_key:
        headers["x-api-key"] = api_key
    if email:
        headers["User-Agent"] = f"mailto:{email}"

    try:
        data = http_get_json(url, headers=headers)
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            print(
                "[semscholar] rate-limited (no API key or burst); returning []",
                file=sys.stderr,
            )
        else:
            print(f"[semscholar] HTTP {exc.code}: {exc.reason}", file=sys.stderr)
        return []
    except urllib.error.URLError as exc:
        print(f"[semscholar] URL error: {exc.reason}", file=sys.stderr)
        return []
    except Exception as exc:  # noqa: BLE001
        print(f"[semscholar] unexpected error: {exc}", file=sys.stderr)
        return []

    papers: list[dict[str, Any]] = data.get("data") or []
    summaries = [_parse_paper(p) for p in papers]
    summaries = [s for s in summaries if s.source_score >= min_score]
    return summaries[:limit]


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_paper(paper: dict[str, Any]) -> WorkSummary:
    title: str = paper.get("title") or "Untitled"
    year: int | None = paper.get("year")
    cited_by_count: int = paper.get("citationCount") or 0
    influential: int = paper.get("influentialCitationCount") or 0

    authors = _format_authors(paper.get("authors"))
    identifier = _identifier_for(paper)
    abstract = _extract_abstract(paper)
    concepts: list[str] = paper.get("fieldsOfStudy") or []
    venue = _venue(paper)

    external_ids: dict[str, Any] = paper.get("externalIds") or {}
    arxiv_id: str | None = external_ids.get("ArXiv") or extract_arxiv_id(identifier)

    source_score = _compute_score(influential, cited_by_count)

    return WorkSummary(
        title=title,
        year=year,
        cited_by_count=cited_by_count,
        authors=authors,
        identifier=identifier,
        abstract=abstract,
        concepts=concepts,
        source="semscholar",
        source_score=source_score,
        venue=venue,
        arxiv_id=arxiv_id,
    )


def _format_authors(authors: list[dict[str, Any]] | None) -> str:
    if not authors:
        return "Unknown"
    names = [a.get("name", "").strip() for a in authors if a.get("name")]
    if not names:
        return "Unknown"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{names[0]} et al."


def _identifier_for(paper: dict[str, Any]) -> str:
    external_ids: dict[str, Any] = paper.get("externalIds") or {}
    doi: str | None = external_ids.get("DOI")
    if doi:
        return f"https://doi.org/{doi}"
    arxiv: str | None = external_ids.get("ArXiv")
    if arxiv:
        return f"https://arxiv.org/abs/{arxiv}"
    return paper.get("url") or ""


def _extract_abstract(paper: dict[str, Any]) -> str:
    """Prefer SS-generated tldr over raw abstract; truncate to ~2 sentences."""
    tldr: dict[str, Any] | None = paper.get("tldr")
    if tldr and tldr.get("text"):
        return _truncate_sentences(tldr["text"], 2)
    abstract: str | None = paper.get("abstract")
    if abstract:
        return _truncate_sentences(abstract, 2)
    return "N/A"


def _truncate_sentences(text: str, n: int) -> str:
    """Return at most n sentences from text."""
    import re
    # Split on sentence-ending punctuation followed by whitespace or end-of-string.
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(parts[:n])


def _venue(paper: dict[str, Any]) -> str | None:
    pub_venue: dict[str, Any] | None = paper.get("publicationVenue")
    if pub_venue and pub_venue.get("name"):
        return pub_venue["name"]
    return paper.get("venue") or None


def _compute_score(influential: int, total: int) -> float:
    """Synthesize a [0,1] quality score from SS citation signals.

    influentialCitationCount is SS's own quality signal (citations that
    meaningfully engage the paper), so it is weighted higher than raw total.
    Dividing by 6 maps typical high-impact counts (~log1p(400)) near 1.0.
    """
    raw = 0.7 * math.log1p(influential) + 0.3 * math.log1p(total)
    return min(1.0, raw / 6.0)


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    results = search("diffusion model image generation", mode="background", limit=5)
    print(f"# fetched {len(results)} results")
    for r in results[:3]:
        print(f"- [{r.source_score:.2f}] {r.title[:80]}  ({r.year}, cited: {r.cited_by_count})")
        print(f"  tldr: {r.abstract[:100]}")
        print(f"  {r.identifier}")
