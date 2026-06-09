"""HTTP access for the InspireHEP jobs REST API.

InspireHEP serves a clean public JSON API, no auth:

* List/search:  GET /api/jobs?q={kw}&status=open&sort=deadline&size={n}&fields=...
  Each hit:
    metadata.control_number   -> int id (also `id` at the top level)
    metadata.position         -> job title
    metadata.institutions[].value
    metadata.ranks[]          -> POSTDOC / JUNIOR / SENIOR / PHD / STAFF / VISITOR
    metadata.regions[]        -> Europe / North America / ...
    metadata.arxiv_categories[] -> hep-ph, astro-ph, ...
    metadata.deadline_date    -> "YYYY-MM-DD" (date only; may be junk like "1111" or absent)
    metadata.status           -> "open" / "closed"  (we request status=open server-side)
* Detail:  GET /api/jobs/{id}   -> same metadata block, plus description/contact_details.

Public web URL for a posting: https://inspirehep.net/jobs/{control_number}.

Validity mirrors the AJO module: effective deadline = parsed deadline_date (end of that day)
if it is a real date, else None (rolling). classify() then keeps future deadlines as 'valid',
drops past ones, and treats no-deadline postings as 'rolling' (excluded unless include_rolling).
The status=open server filter already removes closed postings.
"""

from __future__ import annotations

import html
import re
import time
from datetime import datetime

import requests

from .fetch import USER_AGENT, classify, _match_any

API_URL = "https://inspirehep.net/api/jobs"
WEB_URL = "https://inspirehep.net/jobs"
DEFAULT_LIMIT = 250          # status=open keeps result sets small; this is plenty per keyword
REQUEST_DELAY_S = 0.4        # politeness pause between per-keyword API calls
FIELDS = (
    "position,institutions,regions,ranks,deadline_date,status,"
    "arxiv_categories,external_job_identifier"
)

_DEADLINE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
    return s


def parse_deadline(text: str | None) -> datetime | None:
    """Parse an InspireHEP 'YYYY-MM-DD' deadline -> end-of-day datetime (naive).

    Returns None for missing or malformed values (e.g. the placeholder "1111").
    """
    if not text:
        return None
    m = _DEADLINE_RE.match(text.strip())
    if not m:
        return None
    try:
        d = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return d.replace(hour=23, minute=59, second=59)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# list / search
# --------------------------------------------------------------------------- #
def fetch_list(
    session: requests.Session, keyword: str, *, limit: int = DEFAULT_LIMIT
) -> list[dict]:
    """Fetch open postings matching `keyword`. Returns raw normalized row dicts."""
    params = {
        "q": keyword,
        "status": "open",
        "sort": "deadline",
        "size": str(limit),
        "fields": FIELDS,
    }
    resp = session.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    return [_row_from_hit(h) for h in payload.get("hits", {}).get("hits", [])]


def _row_from_hit(hit: dict) -> dict:
    m = hit.get("metadata", {})
    cid = m.get("control_number") or hit.get("id")
    try:
        jid = int(cid) if cid is not None else cid
    except (TypeError, ValueError):
        jid = cid

    institutions = [
        i.get("value") for i in m.get("institutions", []) if i.get("value")
    ]
    ranks = m.get("ranks", []) or []
    cats = m.get("arxiv_categories", []) or []
    regions = m.get("regions", []) or []
    deadline_raw = m.get("deadline_date")
    deadline_dt = parse_deadline(deadline_raw)

    return {
        "id": jid,
        "source": "inspire",
        "code": m.get("external_job_identifier") or None,
        "title": m.get("position") or "",
        "institution": "; ".join(institutions) or None,
        "position_type": ", ".join(ranks) or None,
        "subject_areas": ", ".join(cats) or None,
        "regions": ", ".join(regions) or None,
        "deadline_raw": deadline_raw if _DEADLINE_RE.match((deadline_raw or "").strip()) else None,
        "deadline_dt": deadline_dt,
        "url": f"{WEB_URL}/{jid}",
    }


# --------------------------------------------------------------------------- #
# detail
# --------------------------------------------------------------------------- #
def fetch_detail(session: requests.Session, job_id: int) -> dict:
    """Fetch one posting's detail record."""
    resp = session.get(f"{API_URL}/{job_id}", params={"format": "json"}, timeout=30)
    resp.raise_for_status()
    m = resp.json().get("metadata", {})
    row = _row_from_hit({"metadata": m, "id": job_id})
    # detail-only extras
    desc = m.get("description")
    if desc:
        text = html.unescape(re.sub(r"<[^>]+>", " ", desc))  # strip tags + entities
        row["description"] = re.sub(r"\s+", " ", text).strip()
    contacts = m.get("contact_details", []) or []
    emails = [c.get("email") for c in contacts if c.get("email")]
    if emails:
        row["contact"] = ", ".join(emails)
    return row


# --------------------------------------------------------------------------- #
# validity + enrichment orchestration (mirrors fetch.search_valid)
# --------------------------------------------------------------------------- #
def search_valid(
    session: requests.Session,
    keywords: list[str],
    *,
    now: datetime | None = None,
    limit: int = DEFAULT_LIMIT,
    include_rolling: bool = False,
    position_types: list[str] | None = None,
    countries: list[str] | None = None,
    log=lambda _msg: None,
) -> tuple[list[dict], dict]:
    """Search each keyword on InspireHEP, keep valid postings, dedup, classify.

    Returns (jobs, stats) with jobs ready for db.upsert_job. The API already returns
    structured deadlines, so there is no separate detail-fetch pass: validity is judged
    from the deadline_date carried in the list response. position_types is matched against
    the joined ranks string, countries against institution + regions (substring, parity
    with the AJO module).
    """
    now = now or datetime.now()

    merged: dict[object, dict] = {}
    for kw in keywords:
        log(f"inspire search: {kw!r}")
        try:
            rows = fetch_list(session, kw, limit=limit)
        except requests.RequestException as e:
            log(f"  inspire search failed for {kw!r}: {e}")
            continue
        for r in rows:
            jid = r["id"]
            if jid in merged:
                kws = merged[jid]["_kw"]
                if kw not in kws:
                    kws.append(kw)
            else:
                r = dict(r)
                r["_kw"] = [kw]
                r["effective_dt"] = r.get("deadline_dt")
                merged[jid] = r
        log(f"  {len(rows)} open postings ({len(merged)} unique so far)")
        time.sleep(REQUEST_DELAY_S)

    candidates = list(merged.values())
    stats = {
        "source": "inspire",
        "keywords": keywords,
        "candidates": len(candidates),
        "filtered_out": 0,
        "mode": "api",
    }

    kept = []
    for r in candidates:
        status = classify(r.get("effective_dt"), now, include_rolling)
        if status is None:
            continue
        if position_types and r.get("position_type") is not None:
            if not _match_any(r.get("position_type"), position_types):
                stats["filtered_out"] += 1
                continue
        if countries:
            hay = " ".join(
                str(r.get(f) or "") for f in ("institution", "regions")
            )
            if not _match_any(hay, countries):
                stats["filtered_out"] += 1
                continue
        r["status"] = status
        kept.append(r)
    candidates = kept

    jobs = []
    for r in candidates:
        eff = r.get("effective_dt")
        deadline_raw = r.get("deadline_raw")
        if not deadline_raw and isinstance(eff, datetime):
            deadline_raw = f"listed until {eff.strftime('%Y/%m/%d')}"
        jobs.append({
            "id": r["id"],
            "source": "inspire",
            "code": r.get("code"),
            "title": r.get("title"),
            "institution": r.get("institution"),
            "position_type": r.get("position_type"),
            "subject_areas": r.get("subject_areas"),
            "deadline_raw": deadline_raw,
            "deadline_dt": eff.isoformat() if isinstance(eff, datetime) else eff,
            "status": r.get("status"),
            "url": r.get("url"),
            "matched_keywords": ",".join(r.get("_kw", [])),
        })
    jobs.sort(key=lambda j: (j["deadline_dt"] is None, j["deadline_dt"] or ""))
    return jobs, stats
