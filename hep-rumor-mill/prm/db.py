"""SQLite storage for rumor-mill entries, resolved author records, papers, and metrics.

Four tables plus meta:

* rumors  - one row per rumor-mill entry (a person at an institution with a status). The same
            person appears multiple times (different institutions / Offered->Accepted), so the
            key is (year, name, institution, status, timestamp).
* authors - one row per resolved person, keyed by InspireHEP recid. Holds the cross-source ids
            (BAI, ORCID, OpenAlex id, Semantic Scholar id) and InspireHEP profile facts.
* papers  - one row per (recid, source, paper_id). `source` is 'inspire' | 'openalex' | 'ss'.
* metrics - one cached aggregate row per recid (computed by metrics.py).

Enrichment is incremental and resumable: `authors.enriched` flips to 1 once a person's record
and papers are captured, so re-running `prm enrich` only touches the unfinished people.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from . import DB_PATH

SCHEMA_VERSION = "1"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS rumors (
    year         INTEGER NOT NULL,
    name         TEXT NOT NULL,
    recid        INTEGER,            -- InspireHEP author id parsed from the profile link
    inspire_url  TEXT,
    institution  TEXT NOT NULL,
    status       TEXT NOT NULL,      -- 'Offered' | 'Accepted' | 'Declined' | other (verbatim)
    remarks      TEXT,
    timestamp    TEXT,               -- verbatim sheet timestamp string
    country      TEXT,               -- inferred ISO2 of the institution
    region       TEXT,               -- inferred region
    first_seen   TEXT,
    last_fetched TEXT,
    PRIMARY KEY (year, name, institution, status, timestamp)
);
CREATE TABLE IF NOT EXISTS authors (
    recid         INTEGER PRIMARY KEY,
    bai           TEXT,              -- INSPIRE BAI, e.g. 'Mudit.Rai.1'
    orcid         TEXT,
    openalex_id   TEXT,
    ss_id         TEXT,              -- Semantic Scholar authorId
    display_name  TEXT,
    phd_year      INTEGER,
    current_inst  TEXT,
    current_rank  TEXT,
    arxiv_cats    TEXT,              -- comma-separated, e.g. 'hep-th,hep-ph,gr-qc'
    advisors      TEXT,              -- JSON list of {name, degree_type}
    enriched      INTEGER DEFAULT 0, -- 1 once author record + papers captured
    fetched_at    TEXT
);
CREATE TABLE IF NOT EXISTS papers (
    recid       INTEGER NOT NULL,
    source      TEXT NOT NULL,       -- 'inspire' | 'openalex' | 'ss'
    paper_id    TEXT NOT NULL,
    year        INTEGER,
    venue       TEXT,
    venue_tier  TEXT,                -- 'A' | 'B' | 'C' | 'preprint' | '' (filled by metrics)
    citations   INTEGER,
    n_authors   INTEGER,
    author_pos  INTEGER,             -- 1-based position of this person, NULL if unknown
    doctype     TEXT,
    field       TEXT,                -- primary subject / field of study
    title       TEXT,
    PRIMARY KEY (recid, source, paper_id)
);
CREATE TABLE IF NOT EXISTS metrics (
    recid            INTEGER PRIMARY KEY,
    n_papers         INTEGER,
    n_first_author   INTEGER,
    n_large_collab   INTEGER,         -- InspireHEP papers with > 50 authors (collaboration inflation)
    total_citations  INTEGER,
    h_index          INTEGER,
    top_venues       TEXT,           -- JSON: [[venue, count], ...]
    field_mix        TEXT,           -- JSON: {field: count}
    years_since_phd  INTEGER,
    interdisciplinary INTEGER DEFAULT 0,  -- 1 if non-HEP venues/topics are material
    cross_disc       TEXT,           -- JSON: {source: {n_papers, total_citations, h_index, top_venues}}
    computed_at      TEXT
);
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def connect(path: Path | None = None) -> sqlite3.Connection:
    db_path = Path(path) if path else DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    conn.execute(
        "INSERT OR IGNORE INTO meta(key, value) VALUES ('schema_version', ?)",
        (SCHEMA_VERSION,),
    )
    conn.commit()
    return conn


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


# --------------------------------------------------------------------------- #
# rumors
# --------------------------------------------------------------------------- #
def upsert_rumor(conn: sqlite3.Connection, r: dict) -> bool:
    """Insert or refresh one rumor-mill entry. Returns True on a new insert.

    Expected keys: year, name, recid, inspire_url, institution, status, remarks,
    timestamp, country, region. Missing keys default to None.
    """
    now = _now_iso()
    key = (r["year"], r["name"], r["institution"], r["status"], r.get("timestamp") or "")
    existing = conn.execute(
        "SELECT first_seen FROM rumors WHERE year=? AND name=? AND institution=? "
        "AND status=? AND timestamp=?",
        key,
    ).fetchone()
    first_seen = existing["first_seen"] if existing else now
    conn.execute(
        """INSERT INTO rumors
               (year, name, recid, inspire_url, institution, status, remarks, timestamp,
                country, region, first_seen, last_fetched)
           VALUES (:year, :name, :recid, :inspire_url, :institution, :status, :remarks,
                   :timestamp, :country, :region, :first_seen, :last_fetched)
           ON CONFLICT(year, name, institution, status, timestamp) DO UPDATE SET
               recid=excluded.recid, inspire_url=excluded.inspire_url,
               remarks=excluded.remarks, country=excluded.country, region=excluded.region,
               last_fetched=excluded.last_fetched""",
        {
            "year": r["year"],
            "name": r["name"],
            "recid": r.get("recid"),
            "inspire_url": r.get("inspire_url"),
            "institution": r["institution"],
            "status": r["status"],
            "remarks": r.get("remarks"),
            "timestamp": r.get("timestamp") or "",
            "country": r.get("country"),
            "region": r.get("region"),
            "first_seen": first_seen,
            "last_fetched": now,
        },
    )
    conn.commit()
    return existing is None


def query_rumors(
    conn: sqlite3.Connection,
    *,
    year: int | None = None,
    status: str | None = None,
    institution_like: str | None = None,
) -> list[dict]:
    clauses, params = [], []
    if year is not None:
        clauses.append("year = ?")
        params.append(year)
    if status:
        clauses.append("status = ?")
        params.append(status)
    if institution_like:
        clauses.append("LOWER(institution) LIKE ?")
        params.append(f"%{institution_like.lower()}%")
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = conn.execute(f"SELECT * FROM rumors{where}", params).fetchall()
    return [dict(r) for r in rows]


def distinct_recids(conn: sqlite3.Connection, *, year: int | None = None,
                    status: str | None = None) -> list[int]:
    """Recids that appear in rumors (optionally filtered), for enrichment."""
    clauses, params = ["recid IS NOT NULL"], []
    if year is not None:
        clauses.append("year = ?")
        params.append(year)
    if status:
        clauses.append("status = ?")
        params.append(status)
    rows = conn.execute(
        f"SELECT DISTINCT recid FROM rumors WHERE {' AND '.join(clauses)}", params
    ).fetchall()
    return [r["recid"] for r in rows]


# --------------------------------------------------------------------------- #
# authors
# --------------------------------------------------------------------------- #
def upsert_author(conn: sqlite3.Connection, a: dict) -> None:
    """Insert or update an author record keyed by recid. advisors may be a list or JSON str."""
    advisors = a.get("advisors")
    if isinstance(advisors, (list, dict)):
        advisors = json.dumps(advisors, ensure_ascii=False)
    conn.execute(
        """INSERT INTO authors
               (recid, bai, orcid, openalex_id, ss_id, display_name, phd_year,
                current_inst, current_rank, arxiv_cats, advisors, enriched, fetched_at)
           VALUES (:recid, :bai, :orcid, :openalex_id, :ss_id, :display_name, :phd_year,
                   :current_inst, :current_rank, :arxiv_cats, :advisors, :enriched, :fetched_at)
           ON CONFLICT(recid) DO UPDATE SET
               bai=COALESCE(excluded.bai, bai),
               orcid=COALESCE(excluded.orcid, orcid),
               openalex_id=COALESCE(excluded.openalex_id, openalex_id),
               ss_id=COALESCE(excluded.ss_id, ss_id),
               display_name=COALESCE(excluded.display_name, display_name),
               phd_year=COALESCE(excluded.phd_year, phd_year),
               current_inst=COALESCE(excluded.current_inst, current_inst),
               current_rank=COALESCE(excluded.current_rank, current_rank),
               arxiv_cats=COALESCE(excluded.arxiv_cats, arxiv_cats),
               advisors=COALESCE(excluded.advisors, advisors),
               enriched=excluded.enriched,
               fetched_at=excluded.fetched_at""",
        {
            "recid": a["recid"],
            "bai": a.get("bai"),
            "orcid": a.get("orcid"),
            "openalex_id": a.get("openalex_id"),
            "ss_id": a.get("ss_id"),
            "display_name": a.get("display_name"),
            "phd_year": a.get("phd_year"),
            "current_inst": a.get("current_inst"),
            "current_rank": a.get("current_rank"),
            "arxiv_cats": a.get("arxiv_cats"),
            "advisors": advisors,
            "enriched": int(a.get("enriched", 0) or 0),
            "fetched_at": _now_iso(),
        },
    )
    conn.commit()


def get_author(conn: sqlite3.Connection, recid: int) -> dict | None:
    row = conn.execute("SELECT * FROM authors WHERE recid = ?", (recid,)).fetchone()
    return dict(row) if row else None


def unenriched_recids(conn: sqlite3.Connection, recids: list[int]) -> list[int]:
    """Subset of `recids` whose author row is missing or not yet enriched."""
    out = []
    for rid in recids:
        row = conn.execute(
            "SELECT enriched FROM authors WHERE recid = ?", (rid,)
        ).fetchone()
        if row is None or not row["enriched"]:
            out.append(rid)
    return out


# --------------------------------------------------------------------------- #
# papers
# --------------------------------------------------------------------------- #
def replace_papers(conn: sqlite3.Connection, recid: int, source: str,
                   papers: list[dict]) -> int:
    """Replace all stored papers for (recid, source) with the given list. Returns count."""
    conn.execute("DELETE FROM papers WHERE recid = ? AND source = ?", (recid, source))
    for p in papers:
        conn.execute(
            """INSERT OR REPLACE INTO papers
                   (recid, source, paper_id, year, venue, venue_tier, citations,
                    n_authors, author_pos, doctype, field, title)
               VALUES (:recid, :source, :paper_id, :year, :venue, :venue_tier, :citations,
                       :n_authors, :author_pos, :doctype, :field, :title)""",
            {
                "recid": recid,
                "source": source,
                "paper_id": str(p.get("paper_id")),
                "year": p.get("year"),
                "venue": p.get("venue"),
                "venue_tier": p.get("venue_tier"),
                "citations": p.get("citations"),
                "n_authors": p.get("n_authors"),
                "author_pos": p.get("author_pos"),
                "doctype": p.get("doctype"),
                "field": p.get("field"),
                "title": p.get("title"),
            },
        )
    conn.commit()
    return len(papers)


def get_papers(conn: sqlite3.Connection, recid: int,
               source: str | None = None) -> list[dict]:
    if source:
        rows = conn.execute(
            "SELECT * FROM papers WHERE recid = ? AND source = ?", (recid, source)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM papers WHERE recid = ?", (recid,)).fetchall()
    return [dict(r) for r in rows]


def update_paper_tier(conn: sqlite3.Connection, recid: int, source: str,
                      paper_id: str, tier: str) -> None:
    conn.execute(
        "UPDATE papers SET venue_tier = ? WHERE recid = ? AND source = ? AND paper_id = ?",
        (tier, recid, source, str(paper_id)),
    )


# --------------------------------------------------------------------------- #
# metrics
# --------------------------------------------------------------------------- #
def upsert_metrics(conn: sqlite3.Connection, m: dict) -> None:
    # Encode the JSON columns into a local copy; never mutate the caller's dict.
    m = dict(m)
    for k in ("top_venues", "field_mix", "cross_disc"):
        if isinstance(m.get(k), (list, dict)):
            m[k] = json.dumps(m[k], ensure_ascii=False)
    conn.execute(
        """INSERT INTO metrics
               (recid, n_papers, n_first_author, n_large_collab, total_citations, h_index,
                top_venues, field_mix, years_since_phd, interdisciplinary, cross_disc, computed_at)
           VALUES (:recid, :n_papers, :n_first_author, :n_large_collab, :total_citations, :h_index,
                   :top_venues, :field_mix, :years_since_phd, :interdisciplinary, :cross_disc, :computed_at)
           ON CONFLICT(recid) DO UPDATE SET
               n_papers=excluded.n_papers, n_first_author=excluded.n_first_author,
               n_large_collab=excluded.n_large_collab,
               total_citations=excluded.total_citations, h_index=excluded.h_index,
               top_venues=excluded.top_venues, field_mix=excluded.field_mix,
               years_since_phd=excluded.years_since_phd,
               interdisciplinary=excluded.interdisciplinary,
               cross_disc=excluded.cross_disc, computed_at=excluded.computed_at""",
        {
            "recid": m["recid"],
            "n_papers": m.get("n_papers"),
            "n_first_author": m.get("n_first_author"),
            "n_large_collab": m.get("n_large_collab"),
            "total_citations": m.get("total_citations"),
            "h_index": m.get("h_index"),
            "top_venues": m.get("top_venues"),
            "field_mix": m.get("field_mix"),
            "years_since_phd": m.get("years_since_phd"),
            "interdisciplinary": int(m.get("interdisciplinary", 0) or 0),
            "cross_disc": m.get("cross_disc"),
            "computed_at": _now_iso(),
        },
    )
    conn.commit()


def get_metrics(conn: sqlite3.Connection, recid: int) -> dict | None:
    row = conn.execute("SELECT * FROM metrics WHERE recid = ?", (recid,)).fetchone()
    if not row:
        return None
    d = dict(row)
    for k in ("top_venues", "field_mix", "cross_disc"):
        if d.get(k):
            try:
                d[k] = json.loads(d[k])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()


def get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None
