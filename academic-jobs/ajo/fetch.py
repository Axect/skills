"""HTTP access and HTML parsing for Academic Jobs Online.

AJO serves plain HTML, no auth. Two surfaces are used:

* List/search:  GET /ajo?action=joblist&args=0-0-0-0--{offset}-{limit}---&id={kw}&send=Search
  Each posting is one <li>:
    [<a href="/ajo/jobs/{id}" id="k{id}">{CODE}</a>]
    <span id="j{id}" aria-hidden="true">{full title}</span>
    <span class="purplesml">(deadline YYYY/MM/DD HH:MMPM)</span>   # absent if rolling
* Detail:  GET /ajo/jobs/{id}  -> label/value table (Position ID, Position Type,
  Subject Areas, Appl Deadline: "YYYY/MM/DD HH:MM:SS (posted ...)"), <title> = institution.

Deadlines are poster-local wall-clock; parsed as naive datetimes and compared to local now.
"""

from __future__ import annotations

import re
import time
from datetime import datetime
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from . import BASE_URL
from . import classify as classifymod

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) academic-jobs-skill/0.1 "
    "(+https://academicjobsonline.org)"
)
DEFAULT_LIMIT = 500
DETAIL_FETCH_CAP = 80  # max detail pages per run; truncation is logged, never silent
DETAIL_DELAY_S = 0.4   # politeness pause between detail fetches

_DEADLINE_LIST_RE = re.compile(
    r"deadline\s+(\d{4}/\d{2}/\d{2}\s+\d{1,2}:\d{2}\s*[AP]M)", re.IGNORECASE
)
_DEADLINE_DETAIL_RE = re.compile(r"(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})")
_LISTED_UNTIL_RE = re.compile(r"listed until\s+(\d{4}/\d{2}/\d{2})", re.IGNORECASE)


class AjoError(RuntimeError):
    pass


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


# --------------------------------------------------------------------------- #
# deadline parsing
# --------------------------------------------------------------------------- #
def parse_list_deadline(text: str) -> datetime | None:
    """Parse a list-row deadline like '2026/05/12 11:59PM' -> datetime (naive)."""
    text = text.strip().replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    for fmt in ("%Y/%m/%d %I:%M%p", "%Y/%m/%d %I:%M %p"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_detail_deadline(text: str) -> datetime | None:
    """Parse a firm detail-page deadline like '2026/06/17 23:59:59' -> datetime (naive)."""
    m = _DEADLINE_DETAIL_RE.search(text)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1), "%Y/%m/%d %H:%M:%S")
    except ValueError:
        return None


def parse_listed_until(text: str) -> datetime | None:
    """Parse 'listed until 2027/04/01' -> end-of-that-day datetime (naive)."""
    m = _LISTED_UNTIL_RE.search(text)
    if not m:
        return None
    try:
        d = datetime.strptime(m.group(1), "%Y/%m/%d")
        return d.replace(hour=23, minute=59, second=59)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# list / search
# --------------------------------------------------------------------------- #
def list_url(keyword: str = "", *, offset: int = 0, limit: int = DEFAULT_LIMIT) -> str:
    args = f"0-0-0-0--{offset}-{limit}---"
    return (
        f"{BASE_URL}/ajo?action=joblist&args={args}"
        f"&id={quote(keyword)}&send=Search"
    )


def fetch_list(
    session: requests.Session, keyword: str = "", *, limit: int = DEFAULT_LIMIT
) -> list[dict]:
    """Fetch and parse the list/search page for `keyword`. Returns raw row dicts."""
    url = list_url(keyword, limit=limit)
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return parse_list_html(resp.text)


def parse_list_html(html: str) -> list[dict]:
    """Parse list rows. Each row: id, code, title, deadline_raw, deadline_dt."""
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict] = []
    seen: set[int] = set()

    for a in soup.select('a[href^="/ajo/jobs/"]'):
        m = re.fullmatch(r"/ajo/jobs/(\d+)", str(a.get("href") or ""))
        if not m:
            continue  # skip /apply and other sub-links
        jid = int(m.group(1))
        if jid in seen:
            continue
        seen.add(jid)

        code = a.get_text(strip=True)
        li = a.find_parent("li")
        title, deadline_raw, deadline_dt = "", None, None
        if li is not None:
            tspan = li.find("span", id=f"j{jid}")
            if tspan is not None:
                title = tspan.get_text(" ", strip=True)
            dspan = li.find("span", class_="purplesml")
            text = dspan.get_text(" ", strip=True) if dspan is not None else li.get_text(" ", strip=True)
            dm = _DEADLINE_LIST_RE.search(text)
            if dm:
                deadline_raw = dm.group(1).replace("\xa0", " ")
                deadline_dt = parse_list_deadline(deadline_raw)

        rows.append({
            "id": jid,
            "code": code,
            "title": title,
            "deadline_raw": deadline_raw,
            "deadline_dt": deadline_dt,
            "url": f"{BASE_URL}/ajo/jobs/{jid}",
        })
    return rows


# --------------------------------------------------------------------------- #
# detail
# --------------------------------------------------------------------------- #
def fetch_detail(session: requests.Session, job_id: int) -> dict:
    url = f"{BASE_URL}/ajo/jobs/{job_id}"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    d = parse_detail_html(resp.text)
    d["id"] = job_id
    d["url"] = url
    return d


def _labelled_value(soup: BeautifulSoup, label: str) -> str | None:
    """Find a 'Label:' cell and return the adjacent value text."""
    needle = label.lower().rstrip(":")
    for el in soup.find_all(string=re.compile(re.escape(label), re.IGNORECASE)):
        txt = el.strip().lower().rstrip(":")
        if needle not in txt:
            continue
        # value usually sits in the next sibling cell / element
        parent = el.parent
        sib = parent.find_next_sibling() if parent else None
        for cand in (sib, parent.find_next() if parent else None):
            if cand is None:
                continue
            val = cand.get_text(" ", strip=True).replace("\xa0", " ").strip()
            if val and val.lower().rstrip(":") != needle:
                return val
    return None


def parse_detail_html(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    institution = None
    if soup.title:
        institution = soup.title.get_text(" ", strip=True).replace("\xa0", " ").strip() or None

    position_type = _labelled_value(soup, "Position Type")
    subject_areas = _labelled_value(soup, "Subject Area")
    position_id = _labelled_value(soup, "Position ID")

    deadline_raw, deadline_dt, listed_until = None, None, None
    dl_val = _labelled_value(soup, "Deadline")
    if dl_val:
        deadline_dt = parse_detail_deadline(dl_val)
        listed_until = parse_listed_until(dl_val)
        if deadline_dt is not None:
            # clean firm deadline: drop the trailing "(posted ... listed until ...)" note
            deadline_raw = re.split(r"\s*\(", dl_val, maxsplit=1)[0].strip() or dl_val
        # when there is no firm deadline, leave deadline_raw=None so the caller can
        # render "listed until <date>" from listed_until (avoids the noisy raw text)

    # effective deadline: firm deadline if present, else the listed-until date
    effective = deadline_dt or listed_until

    description, contact = _extract_description(soup)

    return {
        "institution": institution,
        "position_type": position_type,
        "subject_areas": _clean(subject_areas),
        "position_code": position_id,
        "deadline_raw": deadline_raw,
        "deadline_dt": deadline_dt,
        "listed_until": listed_until,
        "effective_deadline_dt": effective,
        "description": description,
        "contact": contact,
    }


_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def _extract_description(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """Capture the free-text posting body and a contact email from an AJO detail page.

    The body lives in <section class="bld"> (the "Position Description" block). Returns
    (description, contact). Either may be None.
    """
    sec = soup.find("section", class_="bld")
    if sec is None:
        return None, None
    text = sec.get_text(" ", strip=True).replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    # drop the boilerplate label that precedes the actual body, if present
    text = re.sub(r"^Position Description\s+", "", text, flags=re.IGNORECASE).strip()
    if not text:
        return None, None
    # contact email: prefer a mailto link, else the last email mentioned in the body
    contact = None
    mailto = soup.select_one('a[href^="mailto:"]')
    if mailto is not None:
        href = str(mailto.get("href") or "")
        m = _EMAIL_RE.search(href)
        if m:
            contact = m.group(0)
    if contact is None:
        emails = _EMAIL_RE.findall(text)
        if emails:
            contact = emails[-1]
    return text, contact


def _clean(v: str | None) -> str | None:
    if not v:
        return None
    v = v.replace("\xa0", " ").strip()
    return v or None


# --------------------------------------------------------------------------- #
# validity + enrichment orchestration
# --------------------------------------------------------------------------- #
def classify(dt: datetime | None, now: datetime, include_rolling: bool) -> str | None:
    """Classify by effective deadline. 'valid' / 'rolling' / None (excluded)."""
    if dt is None:
        return "rolling" if include_rolling else None
    return "valid" if dt >= now else None


def search_valid(
    session: requests.Session,
    keywords: list[str],
    *,
    now: datetime | None = None,
    limit: int = DEFAULT_LIMIT,
    include_rolling: bool = False,
    fetch_details: bool = True,
    position_types: list[str] | None = None,
    countries: list[str] | None = None,
    excluded_countries: list[str] | None = None,
    preferred_tiers: list | None = None,
    detail_cap: int = DETAIL_FETCH_CAP,
    log=lambda _msg: None,
) -> tuple[list[dict], dict]:
    """Search each keyword, keep only valid (or rolling) postings, dedup, enrich, classify.

    The AJO list page shows deadlines for only some postings, and a missing list deadline
    does NOT mean "no deadline" (the firm/effective deadline lives on the detail page). So by
    default this fetches each candidate's detail page and judges validity from the effective
    deadline (firm `Appl Deadline`, else `listed until` date). Pass fetch_details=False for a
    fast but approximate list-only pass.

    Returns (jobs, stats). Each job dict is ready for db.upsert_job.
    """
    now = now or datetime.now()

    # 1) gather candidate ids/titles from the list for each keyword (dedup across keywords)
    merged: dict[int, dict] = {}
    for kw in keywords:
        log(f"search: {kw!r}")
        rows = fetch_list(session, kw, limit=limit)
        for r in rows:
            jid = r["id"]
            if jid in merged:
                kws = merged[jid]["_kw"]
                if kw not in kws:
                    kws.append(kw)
            else:
                r = dict(r)
                r["_kw"] = [kw]
                r["effective_dt"] = r.get("deadline_dt")  # provisional (list hint)
                merged[jid] = r
        log(f"  {len(rows)} rows ({len(merged)} unique so far)")

    candidates = list(merged.values())
    cap = detail_cap if detail_cap and detail_cap > 0 else DETAIL_FETCH_CAP
    stats = {
        "keywords": keywords,
        "candidates": len(candidates),
        "details_fetched": 0,
        "details_truncated": False,
        "detail_cap": cap,
        "filtered_out": 0,
        "excluded": 0,
        "mode": "detail" if fetch_details else "list-only (approximate)",
    }

    # 2) enrich with detail pages (authoritative deadline + type/subject/institution/body)
    if fetch_details:
        to_fetch = candidates[:cap]
        if len(candidates) > cap:
            stats["details_truncated"] = True
            log(
                f"detail cap: fetching first {cap} of {len(candidates)} "
                f"candidates; remainder judged by list deadline only"
            )
        for i, r in enumerate(to_fetch):
            try:
                det = fetch_detail(session, r["id"])
            except requests.RequestException as e:
                log(f"  detail #{r['id']} failed: {e}")
                continue
            stats["details_fetched"] += 1
            r["institution"] = det.get("institution")
            r["position_type"] = det.get("position_type")
            r["subject_areas"] = det.get("subject_areas")
            r["effective_dt"] = det.get("effective_deadline_dt")
            if det.get("deadline_raw"):
                r["deadline_raw"] = det["deadline_raw"]
            r["deadline_dt"] = det.get("deadline_dt")
            r["description"] = det.get("description")
            r["contact"] = det.get("contact")
            if i < len(to_fetch) - 1:
                time.sleep(DETAIL_DELAY_S)

    # 3) classify by effective deadline + apply type/country filters + exclusion
    kept = []
    for r in candidates:
        status = classify(r.get("effective_dt"), now, include_rolling)
        if status is None:
            continue
        code, region = classifymod.infer_country(r.get("institution"))
        r["country"], r["region"] = code, region
        if excluded_countries and classifymod.country_matches(code, region, excluded_countries):
            stats["excluded"] += 1
            continue
        if position_types and r.get("position_type") is not None:
            if not _match_any(r.get("position_type"), position_types):
                stats["filtered_out"] += 1
                continue
        if countries and r.get("institution") is not None:
            if not _match_any(r.get("institution"), countries):
                stats["filtered_out"] += 1
                continue
        r["status"] = status
        r["pref_tier"] = classifymod.preference_tier(code, region, preferred_tiers)
        r["flags"] = classifymod.detect_flags(
            r.get("title"), r.get("position_type"), r.get("description"), r.get("effective_dt")
        )
        kept.append(r)
    candidates = kept

    jobs = []
    for r in candidates:
        eff = r.get("effective_dt")
        deadline_raw = r.get("deadline_raw")
        # if validity comes from a listed-until date (no firm deadline), show that
        if not deadline_raw and isinstance(eff, datetime):
            deadline_raw = f"listed until {eff.strftime('%Y/%m/%d')}"
        jobs.append({
            "id": r["id"],
            "source": "ajo",
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
            "description": r.get("description"),
            "contact": r.get("contact"),
            "country": r.get("country"),
            "region": r.get("region"),
            "flags": ",".join(r.get("flags") or []) or None,
            "pref_tier": r.get("pref_tier"),
        })
    jobs.sort(key=lambda j: (
        j.get("pref_tier", 99), j["deadline_dt"] is None, j["deadline_dt"] or ""
    ))
    return jobs, stats


def _match_any(value: str | None, needles: list[str]) -> bool:
    if not value:
        return False
    v = value.lower()
    return any(n.strip().lower() in v for n in needles if n.strip())
