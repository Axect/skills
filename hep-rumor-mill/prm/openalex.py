"""OpenAlex public API access for author publication records.

Cross-disciplinary augmentation: catches ML/stats/CS venues (ICML, NeurIPS, journals)
that InspireHEP misses. No authentication required. Uses polite mailto param as
requested by the OpenAlex API guidelines.

Public interface
----------------
fetch_works_by_orcid(orcid, *, mailto) -> list[dict]
fetch_author_summary_by_orcid(orcid, *, mailto) -> dict | None
"""

from __future__ import annotations

import os
import time

import requests

from . import USER_AGENT

# OpenAlex offers a faster "polite pool" when a contact mailto is supplied. It is optional and
# personal, so it is never hardcoded: set OPENALEX_MAILTO to opt in. Default is no mailto.
_MAILTO = os.environ.get("OPENALEX_MAILTO")

_BASE = "https://api.openalex.org"
_SELECT_FIELDS = "id,title,publication_year,cited_by_count,primary_location,authorships,type,topics"
_PAGE_CAP = 5       # at most 5 pages (1000 results)
_PER_PAGE = 200
_DELAY_S = 0.2


def _make_session(mailto: str | None) -> requests.Session:
    s = requests.Session()
    ua = USER_AGENT
    if mailto:
        ua = f"{ua}; mailto:{mailto}"
    s.headers.update({"User-Agent": ua, "Accept": "application/json"})
    return s


def _extract_paper(result: dict) -> dict:
    raw_id: str = result.get("id") or ""
    # id is like "https://openalex.org/W123456789"; take trailing segment
    paper_id = raw_id.rsplit("/", 1)[-1] if raw_id else None

    year = result.get("publication_year")
    citations = result.get("cited_by_count")
    doctype = result.get("type")
    title = result.get("title")

    # venue: primary_location -> source -> display_name
    venue: str | None = None
    pl = result.get("primary_location") or {}
    src = pl.get("source") or {}
    venue = src.get("display_name") or None

    # n_authors
    authorships = result.get("authorships") or []
    n_authors = len(authorships) if authorships else None

    # field: first topic's field.display_name, fallback to topic display_name
    field: str | None = None
    topics = result.get("topics") or []
    if topics:
        first = topics[0]
        nested_field = first.get("field") or {}
        field = nested_field.get("display_name") or first.get("display_name") or None

    return {
        "paper_id": paper_id,
        "year": year,
        "venue": venue,
        "citations": citations,
        "n_authors": n_authors,
        "author_pos": None,
        "doctype": doctype,
        "field": field,
        "title": title,
    }


def fetch_works_by_orcid(
    orcid: str, *, mailto: str | None = None
) -> list[dict]:
    """Fetch all works for an author identified by ORCID.

    Returns a list of paper dicts. The caller is responsible for adding
    source='openalex'. Returns [] on any HTTP error or empty result.
    """
    mailto = mailto or _MAILTO
    session = _make_session(mailto)
    params: dict[str, str] = {
        "filter": f"author.orcid:{orcid}",
        "per-page": str(_PER_PAGE),
        "select": _SELECT_FIELDS,
        "cursor": "*",
    }
    if mailto:
        params["mailto"] = mailto

    papers: list[dict] = []
    pages_fetched = 0

    while True:
        try:
            resp = session.get(f"{_BASE}/works", params=params, timeout=30)
            resp.raise_for_status()
        except requests.RequestException:
            return []

        payload = resp.json()
        results = payload.get("results") or []
        for r in results:
            papers.append(_extract_paper(r))

        pages_fetched += 1
        meta = payload.get("meta") or {}
        next_cursor = meta.get("next_cursor")

        if not next_cursor or pages_fetched >= _PAGE_CAP:
            break

        params["cursor"] = next_cursor
        time.sleep(_DELAY_S)

    return papers


def fetch_author_summary_by_orcid(
    orcid: str, *, mailto: str | None = None
) -> dict | None:
    """Fetch author-level summary from OpenAlex by ORCID.

    Returns a dict with openalex_id, works_count, cited_by_count, h_index,
    or None if the author is not found or the request fails.
    """
    mailto = mailto or _MAILTO
    session = _make_session(mailto)
    params: dict[str, str] = {}
    if mailto:
        params["mailto"] = mailto

    url = f"{_BASE}/authors/https://orcid.org/{orcid}"
    try:
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
    except requests.RequestException:
        return None

    data = resp.json()
    raw_id: str = data.get("id") or ""
    openalex_id = raw_id.rsplit("/", 1)[-1] if raw_id else None

    summary_stats = data.get("summary_stats") or {}
    h_index = summary_stats.get("h_index")

    return {
        "openalex_id": openalex_id,
        "works_count": data.get("works_count"),
        "cited_by_count": data.get("cited_by_count"),
        "h_index": h_index,
    }


def fetch_work_by_doi(doi: str, *, mailto: str | None = None) -> dict | None:
    """Look up a single work by DOI. Exact one-work lookup, no author clustering, so it is safe
    to use for backfilling citation / venue / field on an ORCID-claimed work. Returns the same
    paper dict shape as the by-orcid works (author_pos None), or None on miss/error."""
    if not doi:
        return None
    mailto = mailto or _MAILTO
    doi = doi.strip()
    # accept a bare DOI or a full URL
    doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
    session = _make_session(mailto)
    params: dict[str, str] = {}
    if mailto:
        params["mailto"] = mailto
    url = f"{_BASE}/works/https://doi.org/{doi}"
    try:
        resp = session.get(url, params=params, timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
    except requests.RequestException:
        return None
    try:
        return _extract_paper(resp.json())
    except ValueError:
        return None
