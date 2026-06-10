"""HTTP access for the InspireHEP author and literature REST APIs."""

from __future__ import annotations

import re

import requests

from . import USER_AGENT

REQUEST_DELAY_S: float = 0.4

_API_BASE = "https://inspirehep.net/api"


def make_session() -> requests.Session:
    """Return a session with polite headers."""
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return s


# ---------------------------------------------------------------------------
# Author profile
# ---------------------------------------------------------------------------

def fetch_author(session: requests.Session, recid: int) -> dict:
    """Fetch an author profile by InspireHEP recid.

    Returns a dict with keys: recid, bai, orcid, display_name, phd_year,
    current_inst, current_rank, arxiv_cats, advisors.
    """
    resp = session.get(f"{_API_BASE}/authors/{recid}", timeout=30)
    resp.raise_for_status()
    meta = resp.json().get("metadata", {})

    # --- identifiers ---
    bai = None
    orcid = None
    for id_entry in meta.get("ids", []):
        schema = id_entry.get("schema", "")
        val = id_entry.get("value")
        if schema == "INSPIRE BAI":
            bai = val
        elif schema == "ORCID":
            orcid = val

    display_name = (meta.get("name") or {}).get("value")

    # --- positions ---
    positions = meta.get("positions") or []
    phd_year = None
    for pos in positions:
        if (pos.get("rank") or "").upper() == "PHD":
            raw_date = pos.get("start_date") or ""
            m = re.match(r"(\d{4})", raw_date)
            if m:
                phd_year = int(m.group(1))
            break

    current_inst = None
    current_rank = None
    current_pos = None
    # prefer explicit current flag
    for pos in positions:
        if pos.get("current"):
            current_pos = pos
            break
    # fall back to latest start_date
    if current_pos is None and positions:
        def _sort_key(p: dict) -> str:
            return p.get("start_date") or ""
        current_pos = max(positions, key=_sort_key)
    if current_pos is not None:
        inst = current_pos.get("institution")
        current_inst = inst if isinstance(inst, str) else (inst or {}).get("value") if inst else None
        current_rank = current_pos.get("rank") or None

    # --- arxiv categories ---
    cats = meta.get("arxiv_categories") or []
    arxiv_cats = ",".join(cats) if cats else None

    # --- advisors ---
    advisors = [
        {"name": a.get("name"), "degree_type": a.get("degree_type")}
        for a in (meta.get("advisors") or [])
    ]

    return {
        "recid": recid,
        "bai": bai,
        "orcid": orcid,
        "display_name": display_name,
        "phd_year": phd_year,
        "current_inst": current_inst,
        "current_rank": current_rank,
        "arxiv_cats": arxiv_cats,
        "advisors": advisors,
    }


# ---------------------------------------------------------------------------
# Literature
# ---------------------------------------------------------------------------

_LITERATURE_FIELDS = (
    "titles,publication_info,citation_count,citation_count_without_self_citations,"
    "earliest_date,authors,arxiv_eprints,document_type"
)


def fetch_papers(
    session: requests.Session,
    bai: str,
    *,
    limit: int = 500,
    recid: int | None = None,
) -> list[dict]:
    """Fetch literature for an author identified by BAI.

    recid is optional; when given it is used to determine the author's 1-based
    position in each paper's author list.
    """
    params = {
        "q": f"a {bai}",
        "sort": "mostrecent",
        "size": str(limit),
        "fields": _LITERATURE_FIELDS,
    }
    resp = session.get(f"{_API_BASE}/literature", params=params, timeout=60)
    resp.raise_for_status()
    hits = resp.json().get("hits", {}).get("hits", [])

    results = []
    ref_suffix = f"/{recid}" if recid is not None else None

    for hit in hits:
        meta = hit.get("metadata", {})
        paper_id = str(meta.get("control_number") or hit.get("id") or "")

        # year
        earliest = meta.get("earliest_date") or ""
        m = re.match(r"(\d{4})", earliest)
        year = int(m.group(1)) if m else None

        # venue: first publication_info entry with a journal_title
        venue = None
        for pub in (meta.get("publication_info") or []):
            jt = pub.get("journal_title")
            if jt:
                venue = jt
                break

        citations = meta.get("citation_count")
        if citations is not None:
            citations = int(citations)

        authors = meta.get("authors") or []
        n_authors = len(authors) if authors else None

        # author position (1-based)
        author_pos = None
        if ref_suffix is not None:
            for idx, auth in enumerate(authors, start=1):
                ref_url = (auth.get("record") or {}).get("$ref") or ""
                if ref_url.endswith(ref_suffix):
                    author_pos = idx
                    break

        doctype = None
        doctypes = meta.get("document_type") or []
        if doctypes:
            doctype = doctypes[0]

        field = None
        eprints = meta.get("arxiv_eprints") or []
        if eprints:
            cats = eprints[0].get("categories") or []
            if cats:
                field = cats[0]

        title = None
        titles = meta.get("titles") or []
        if titles:
            title = titles[0].get("title")

        results.append({
            "paper_id": paper_id,
            "year": year,
            "venue": venue,
            "citations": citations,
            "n_authors": n_authors,
            "author_pos": author_pos,
            "doctype": doctype,
            "field": field,
            "title": title,
        })

    return results
