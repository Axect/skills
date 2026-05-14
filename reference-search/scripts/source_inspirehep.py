"""InspireHEP literature API source for reference-search.

Higher precision than OpenAlex for HEP / nuclear / GR-QC queries.
Used by the router when domain inference flags the query as HEP-family.
"""

from __future__ import annotations

import sys
import urllib.error
import urllib.parse
from math import log1p
from typing import Any

from _common import WorkSummary, http_get_json, normalize_doi, extract_arxiv_id

_BASE_URL = "https://inspirehep.net/api/literature"
_FIELDS = (
    "titles,authors,publication_info,abstracts,arxiv_eprints,"
    "dois,citation_count,earliest_date,document_type,"
    "references,publication_type,inspire_categories"
)
_CURRENT_YEAR = 2026

_CITED_MODES = {"survey", "baseline"}


def _resolve_sort(mode: str, sort: str | None) -> str:
    if sort is not None:
        return sort
    return "mostcited" if mode in _CITED_MODES else "mostrecent"


def _parse_year(metadata: dict[str, Any]) -> int | None:
    date_str: str | None = metadata.get("earliest_date")
    if date_str:
        try:
            return int(date_str.split("-")[0])
        except (ValueError, AttributeError):
            pass
    pub_info = metadata.get("publication_info")
    if pub_info:
        year = pub_info[0].get("year")
        if year is not None:
            try:
                return int(year)
            except (ValueError, TypeError):
                pass
    return None


def _parse_authors(metadata: dict[str, Any]) -> str:
    authors: list[dict[str, Any]] = metadata.get("authors", [])
    if not authors:
        return "Unknown"
    names = [a.get("full_name", "") for a in authors if a.get("full_name")]
    if not names:
        return "Unknown"
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{names[0]} et al."


def _parse_abstract(metadata: dict[str, Any]) -> str:
    abstracts: list[dict[str, Any]] = metadata.get("abstracts", [])
    if not abstracts:
        return ""
    full: str = abstracts[0].get("value", "")
    # Two sentences is enough context for ranking without ballooning tokens.
    parts = full.split(". ")
    if len(parts) <= 2:
        return full
    return ". ".join(parts[:2]) + "."


def _parse_identifier(
    metadata: dict[str, Any],
    recid: str | int,
    arxiv_id: str | None,
) -> str:
    dois: list[dict[str, Any]] = metadata.get("dois", [])
    if dois:
        doi_value = dois[0].get("value")
        doi_url = normalize_doi(doi_value)
        if doi_url:
            return doi_url
    if arxiv_id:
        return f"https://arxiv.org/abs/{arxiv_id}"
    return f"https://inspirehep.net/literature/{recid}"


def _parse_venue(metadata: dict[str, Any], arxiv_id: str | None) -> str:
    pub_info: list[dict[str, Any]] = metadata.get("publication_info", [])
    if pub_info:
        journal = pub_info[0].get("journal_title")
        if journal:
            return journal
    if arxiv_id:
        return "arXiv"
    return "InspireHEP"


def _parse_concepts(metadata: dict[str, Any]) -> list[str]:
    cats: list[dict[str, Any]] = metadata.get("inspire_categories", [])
    return [c["term"] for c in cats if c.get("term")][:5]


def _source_score(
    sort_key: str,
    citation_count: int,
    year: int | None,
) -> float:
    if sort_key == "mostcited":
        return min(1.0, log1p(citation_count) / 10.0)
    # mostrecent: penalize older papers linearly, floor at 0.3.
    if year is None:
        return 0.3
    return max(0.3, 1.0 - (_CURRENT_YEAR - year) / 20.0)


def _parse_hit(hit: dict[str, Any], sort_key: str) -> WorkSummary | None:
    metadata: dict[str, Any] = hit.get("metadata", {})
    recid = hit.get("id", "")

    titles: list[dict[str, Any]] = metadata.get("titles", [])
    title = titles[0].get("title", "") if titles else ""
    if not title:
        return None

    year = _parse_year(metadata)
    authors = _parse_authors(metadata)

    citation_count: int = metadata.get("citation_count") or metadata.get(
        "citation_count_without_self_citations", 0
    ) or 0

    eprints: list[dict[str, Any]] = metadata.get("arxiv_eprints", [])
    arxiv_id: str | None = eprints[0].get("value") if eprints else None
    # Fallback: try to extract from DOI text just in case.
    if arxiv_id is None:
        dois = metadata.get("dois", [])
        if dois:
            arxiv_id = extract_arxiv_id(dois[0].get("value"))

    identifier = _parse_identifier(metadata, recid, arxiv_id)
    abstract = _parse_abstract(metadata)
    venue = _parse_venue(metadata, arxiv_id)
    concepts = _parse_concepts(metadata)
    score = _source_score(sort_key, citation_count, year)

    return WorkSummary(
        title=title,
        year=year,
        cited_by_count=citation_count,
        authors=authors,
        identifier=identifier,
        abstract=abstract,
        concepts=concepts,
        source="inspire",
        source_score=score,
        venue=venue,
        arxiv_id=arxiv_id,
    )


def search(
    query: str,
    *,
    mode: str = "background",
    limit: int = 10,
    email: str | None = None,
    sort: str | None = None,
) -> list[WorkSummary]:
    """Search InspireHEP /api/literature and return normalized WorkSummary records."""
    sort_key = _resolve_sort(mode, sort)
    fetch_size = min(50, max(limit * 2, 20))

    params = urllib.parse.urlencode(
        {
            "q": query,
            "size": fetch_size,
            "page": 1,
            "sort": sort_key,
            "fields": _FIELDS,
        }
    )
    url = f"{_BASE_URL}?{params}"

    headers: dict[str, str] = {}
    if email:
        headers["User-Agent"] = f"mailto:{email}"

    try:
        data = http_get_json(url, headers=headers)
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        print(f"[inspirehep] search failed: {exc}", file=sys.stderr)
        return []
    except Exception as exc:  # JSON decode or unexpected
        print(f"[inspirehep] search failed: {exc}", file=sys.stderr)
        return []

    hits: list[dict[str, Any]] = data.get("hits", {}).get("hits", [])
    results: list[WorkSummary] = []
    for hit in hits:
        record = _parse_hit(hit, sort_key)
        if record is not None:
            results.append(record)
        if len(results) >= limit:
            break

    return results


if __name__ == "__main__":
    results = search("SMEFT dimension-six operators", mode="background", limit=5)
    print(f"# fetched {len(results)} results")
    for r in results[:3]:
        print(f"- [{r.source_score:.2f}] {r.title[:80]}  ({r.year}, cited: {r.cited_by_count})")
        print(f"  {r.identifier}")
        print(f"  venue: {r.venue}")
