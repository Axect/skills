"""ORCID public API access: the author's own self-claimed work list.

Why this exists: OpenAlex clusters works by author and sometimes merges several same-named
people (and a shared ORCID) into one entity, so `works?filter=author.orcid:X` can return a
different person's papers (chemistry, optics, ...). The ORCID public API instead returns the
works the researcher curated on their own ORCID record, so there is no author-conflation. It is
used as a clean fallback when the OpenAlex-by-ORCID cluster is discarded as contaminated.

ORCID works lack citation counts (ORCID does not store them); the caller backfills citations
per work via a DOI lookup (see openalex.fetch_work_by_doi).
"""

from __future__ import annotations

import requests

from . import USER_AGENT

PUB_URL = "https://pub.orcid.org/v3.0/{orcid}/works"


def _make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return s


def fetch_claimed_works(orcid: str) -> list[dict]:
    """Return the works the person claimed on their ORCID record.

    Each dict: {paper_id, title, year, venue, doi, doctype}. paper_id is the DOI when present,
    else a 'orcid:{put-code}' string. Returns [] on any error.
    """
    if not orcid:
        return []
    session = _make_session()
    try:
        resp = session.get(PUB_URL.format(orcid=orcid), timeout=30)
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError):
        return []

    out: list[dict] = []
    for group in payload.get("group", []):
        summaries = group.get("work-summary") or []
        if not summaries:
            continue
        s = summaries[0]
        title = (((s.get("title") or {}).get("title")) or {}).get("value")
        year = (((s.get("publication-date") or {}).get("year")) or {}).get("value")
        venue = (s.get("journal-title") or {}).get("value")
        doctype = s.get("type")
        put_code = s.get("put-code")

        doi = None
        ext = (s.get("external-ids") or {}).get("external-id") or []
        for e in ext:
            if (e.get("external-id-type") or "").lower() == "doi":
                doi = (e.get("external-id-value") or "").strip() or None
                break

        try:
            year_i = int(year) if year else None
        except (TypeError, ValueError):
            year_i = None

        out.append({
            "paper_id": doi or f"orcid:{put_code}",
            "title": title,
            "year": year_i,
            "venue": venue,
            "doi": doi,
            "doctype": doctype,
        })
    return out
