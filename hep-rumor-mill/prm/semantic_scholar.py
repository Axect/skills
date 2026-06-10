"""Semantic Scholar Graph API access.

Used as a cross-disciplinary fallback when a person has no ORCID (so
OpenAlex-by-ORCID is unavailable) and to cross-check an h-index.

No API key required for low-volume public access. The API rate-limits hard
(HTTP 429) so every call is surrounded by time.sleep() and 429 responses are
caught and returned as None / [] rather than raised.

Endpoints used:
  Author search:
    GET https://api.semanticscholar.org/graph/v1/author/search
        ?query={name}&fields=name,affiliations,paperCount,citationCount,hIndex
    Response: {"data": [{authorId, name, affiliations:[...], paperCount,
                         citationCount, hIndex}, ...]}

  Author papers:
    GET https://api.semanticscholar.org/graph/v1/author/{authorId}/papers
        ?fields=title,year,venue,citationCount,fieldsOfStudy&limit={limit}
    Response: {"data": [{paperId, title, year, venue, citationCount,
                         fieldsOfStudy:[...]|None}, ...]}

Note: ORCID direct lookup via author/ORCID:{orcid} is unreliable (often
returns 404 even for valid ORCIDs). Name search is used exclusively.
"""

from __future__ import annotations

import os
import time

import requests

from . import USER_AGENT

_BASE = "https://api.semanticscholar.org/graph/v1"
# Unauthenticated SS shares a strict ~1 req/s pool, so back-to-back lookups get 429s. Setting
# S2_API_KEY (same env var the reference-search skill uses) raises the limit and makes the
# citation backfill reliable; without it the pipeline still works but backfill is best-effort.
_API_KEY = os.environ.get("S2_API_KEY") or os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
_SLEEP = 0.3 if _API_KEY else 1.0


def _make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    if _API_KEY:
        s.headers.update({"x-api-key": _API_KEY})
    return s


def find_author(name: str, *, affiliation_hint: str | None = None) -> dict | None:
    """Search for an author by name and return their profile.

    Disambiguation: if affiliation_hint is given, prefer the candidate whose
    affiliations string contains the hint (case-insensitive substring match in
    either direction). If no hint is given or no candidate matches, fall back to
    the candidate with the largest paperCount and set match_confidence='low'.
    A hint match yields match_confidence='high'.

    Returns a dict:
        {
            "ss_id": str,
            "name": str,
            "paperCount": int | None,
            "citationCount": int | None,
            "hIndex": int | None,
            "match_confidence": "high" | "low",
        }
    Returns None if no candidates were found or the request failed.
    """
    time.sleep(_SLEEP)
    session = _make_session()
    params = {
        "query": name,
        "fields": "name,affiliations,paperCount,citationCount,hIndex",
    }
    try:
        resp = session.get(f"{_BASE}/author/search", params=params, timeout=30)
    except requests.RequestException:
        return None

    time.sleep(_SLEEP)

    if resp.status_code == 429:
        return None
    if not resp.ok:
        return None

    data = resp.json().get("data") or []
    if not data:
        return None

    hint_lc = affiliation_hint.lower() if affiliation_hint else None

    def affil_str(candidate: dict) -> str:
        parts = candidate.get("affiliations") or []
        return " ".join(a.get("name", "") if isinstance(a, dict) else str(a) for a in parts).lower()

    matched = None
    if hint_lc:
        for c in data:
            aff = affil_str(c)
            # substring match in either direction
            if hint_lc in aff or aff in hint_lc:
                matched = c
                break

    if matched is not None:
        confidence = "high"
    else:
        # pick the one with the most papers
        matched = max(data, key=lambda c: c.get("paperCount") or 0)
        confidence = "low"

    return {
        "ss_id": matched.get("authorId") or matched.get("author_id") or "",
        "name": matched.get("name") or "",
        "paperCount": matched.get("paperCount"),
        "citationCount": matched.get("citationCount"),
        "hIndex": matched.get("hIndex"),
        "match_confidence": confidence,
    }


def fetch_papers(ss_id: str, *, limit: int = 500) -> list[dict]:
    """Fetch the paper list for an author identified by their Semantic Scholar ID.

    Returns a list of dicts:
        {
            "paper_id": str,
            "year": int | None,
            "venue": str | None,
            "citations": int | None,
            "n_authors": None,
            "author_pos": None,
            "doctype": None,
            "field": str | None,   # first entry of fieldsOfStudy
            "title": str | None,
        }
    Returns [] on error or HTTP 429.

    Callers are expected to add source='ss' themselves.
    """
    time.sleep(_SLEEP)
    session = _make_session()
    params = {
        "fields": "title,year,venue,citationCount,fieldsOfStudy",
        "limit": str(limit),
    }
    try:
        resp = session.get(f"{_BASE}/author/{ss_id}/papers", params=params, timeout=30)
    except requests.RequestException:
        return []

    time.sleep(_SLEEP)

    if resp.status_code == 429:
        return []
    if not resp.ok:
        return []

    data = resp.json().get("data") or []
    papers = []
    for p in data:
        fos = p.get("fieldsOfStudy") or []
        first_field = fos[0] if fos else None
        papers.append({
            "paper_id": p.get("paperId") or "",
            "year": p.get("year"),
            "venue": p.get("venue") or None,
            "citations": p.get("citationCount"),
            "n_authors": None,
            "author_pos": None,
            "doctype": None,
            "field": first_field,
            "title": p.get("title") or None,
        })
    return papers


def match_paper(title: str) -> dict | None:
    """Best-match a single paper by title and return its citation/venue/field.

    Used to backfill citations on arXiv-only works (no DOI) that get no OpenAlex/InspireHEP
    citation count. Returns {citations, venue, field, arxiv_id} or None on no-match/error/429.
    Semantic Scholar citation counts are conservative (lower than Google Scholar), so this is a
    floor, not a ceiling.
    """
    if not title or not title.strip():
        return None
    session = _make_session()
    params = {
        "query": title.strip(),
        "fields": "title,citationCount,venue,fieldsOfStudy,externalIds",
    }
    # SS rate-limits hard (429). Retry the request a few times with growing backoff so a busy
    # window does not silently drop a real citation count.
    resp = None
    for attempt in range(4):
        time.sleep(_SLEEP * (attempt + 1))
        try:
            resp = session.get(f"{_BASE}/paper/search/match", params=params, timeout=30)
        except requests.RequestException:
            continue
        if resp.status_code == 429:
            continue
        break
    if resp is None or resp.status_code == 404 or not resp.ok:
        return None
    try:
        data = resp.json().get("data") or []
    except ValueError:
        return None
    if not data:
        return None
    m = data[0]
    fos = m.get("fieldsOfStudy") or []
    return {
        "citations": m.get("citationCount"),
        "venue": m.get("venue") or None,
        "field": fos[0] if fos else None,
        "arxiv_id": (m.get("externalIds") or {}).get("ArXiv"),
    }
