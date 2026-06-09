"""SQLite storage for AJO postings with seen-tracking and dedup."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from . import DB_PATH

SCHEMA_VERSION = "2"

DEFAULT_SOURCE = "ajo"

# Postings are keyed by (source, id): both AJO and InspireHEP use integer ids that can
# collide numerically, so the source namespaces them.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    source           TEXT NOT NULL DEFAULT 'ajo',   -- 'ajo' | 'inspire'
    id               INTEGER NOT NULL,
    code             TEXT,
    title            TEXT,
    institution      TEXT,
    position_type    TEXT,
    subject_areas    TEXT,
    deadline_raw     TEXT,
    deadline_dt      TEXT,          -- ISO 8601, NULL if rolling / unknown
    status           TEXT,          -- 'valid' | 'rolling'
    url              TEXT,
    matched_keywords TEXT,          -- comma-separated keywords/presets that matched
    first_seen       TEXT,
    last_fetched     TEXT,
    is_new           INTEGER DEFAULT 1,
    PRIMARY KEY (source, id)
);
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""

COLUMNS = [
    "source", "id", "code", "title", "institution", "position_type", "subject_areas",
    "deadline_raw", "deadline_dt", "status", "url", "matched_keywords",
    "first_seen", "last_fetched", "is_new",
]


def connect(path: Path | None = None) -> sqlite3.Connection:
    """Open the DB (creating dir + schema on first use, migrating older schemas)."""
    db_path = Path(path) if path else DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _migrate(conn)
    conn.executescript(_SCHEMA)
    conn.execute(
        "INSERT OR IGNORE INTO meta(key, value) VALUES ('schema_version', ?)",
        (SCHEMA_VERSION,),
    )
    conn.execute(
        "UPDATE meta SET value = ? WHERE key = 'schema_version'", (SCHEMA_VERSION,)
    )
    conn.commit()
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    """v1 -> v2: add the `source` column + composite PK, tagging existing rows as 'ajo'.

    A pre-source `jobs` table has `id` as its sole primary key and no `source` column.
    SQLite cannot alter a primary key in place, so rebuild: rename, recreate, copy with
    source='ajo', drop. New databases (no `jobs` table yet) skip this untouched.
    """
    has_jobs = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'"
    ).fetchone()
    if not has_jobs:
        return
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(jobs)").fetchall()]
    if "source" in cols:
        return  # already migrated

    old_cols = [c for c in cols]  # everything the old table carried
    conn.execute("ALTER TABLE jobs RENAME TO jobs_v1")
    conn.executescript(_SCHEMA)
    shared = [c for c in old_cols if c in COLUMNS]
    collist = ", ".join(shared)
    conn.execute(
        f"INSERT INTO jobs (source, {collist}) "
        f"SELECT 'ajo', {collist} FROM jobs_v1"
    )
    conn.execute("DROP TABLE jobs_v1")
    conn.commit()


def _now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def upsert_job(conn: sqlite3.Connection, job: dict) -> bool:
    """Insert or update a posting keyed by (source, id).

    Returns True if this was a genuinely new insert (is_new flagged), False on update.
    On update: refresh volatile fields, keep first_seen, and merge matched_keywords.
    Detail fields (institution/position_type/subject_areas) are only overwritten when
    the incoming job actually carries them (so a cheap list fetch never wipes detail data).
    """
    now = _now_iso()
    source = job.get("source", DEFAULT_SOURCE)
    row = conn.execute(
        "SELECT * FROM jobs WHERE source = ? AND id = ?", (source, job["id"])
    ).fetchone()

    if row is None:
        conn.execute(
            """INSERT INTO jobs
               (source, id, code, title, institution, position_type, subject_areas,
                deadline_raw, deadline_dt, status, url, matched_keywords,
                first_seen, last_fetched, is_new)
               VALUES (:source, :id, :code, :title, :institution, :position_type, :subject_areas,
                       :deadline_raw, :deadline_dt, :status, :url, :matched_keywords,
                       :first_seen, :last_fetched, 1)""",
            {
                "source": source,
                "id": job["id"],
                "code": job.get("code"),
                "title": job.get("title"),
                "institution": job.get("institution"),
                "position_type": job.get("position_type"),
                "subject_areas": job.get("subject_areas"),
                "deadline_raw": job.get("deadline_raw"),
                "deadline_dt": job.get("deadline_dt"),
                "status": job.get("status"),
                "url": job.get("url"),
                "matched_keywords": job.get("matched_keywords", ""),
                "first_seen": now,
                "last_fetched": now,
            },
        )
        conn.commit()
        return True

    # Merge matched keywords (union, order-stable).
    existing_kw = [k for k in (row["matched_keywords"] or "").split(",") if k]
    incoming_kw = [k for k in (job.get("matched_keywords", "") or "").split(",") if k]
    merged_kw = existing_kw + [k for k in incoming_kw if k not in existing_kw]

    conn.execute(
        """UPDATE jobs SET
               code = :code,
               title = :title,
               institution = COALESCE(:institution, institution),
               position_type = COALESCE(:position_type, position_type),
               subject_areas = COALESCE(:subject_areas, subject_areas),
               deadline_raw = :deadline_raw,
               deadline_dt = :deadline_dt,
               status = :status,
               url = :url,
               matched_keywords = :matched_keywords,
               last_fetched = :last_fetched
           WHERE source = :source AND id = :id""",
        {
            "source": source,
            "id": job["id"],
            "code": job.get("code") or row["code"],
            "title": job.get("title") or row["title"],
            "institution": job.get("institution"),
            "position_type": job.get("position_type"),
            "subject_areas": job.get("subject_areas"),
            "deadline_raw": job.get("deadline_raw"),
            "deadline_dt": job.get("deadline_dt"),
            "status": job.get("status"),
            "url": job.get("url") or row["url"],
            "matched_keywords": ",".join(merged_kw),
            "last_fetched": now,
        },
    )
    conn.commit()
    return False


def query_jobs(
    conn: sqlite3.Connection,
    *,
    valid_only: bool = False,
    new_only: bool = False,
    keyword_like: str | None = None,
    source: str | None = None,
    now: datetime | None = None,
) -> list[dict]:
    """Return stored postings. Validity is recomputed against `now` (default: real now)."""
    now = now or datetime.now()
    if source:
        rows = conn.execute("SELECT * FROM jobs WHERE source = ?", (source,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM jobs").fetchall()
    out: list[dict] = []
    for r in rows:
        d = dict(r)
        d["is_valid_now"] = _is_valid_now(d, now)
        if valid_only and not d["is_valid_now"]:
            continue
        if new_only and not d["is_new"]:
            continue
        if keyword_like:
            hay = " ".join(
                str(d.get(f) or "") for f in ("title", "code", "institution", "subject_areas")
            ).lower()
            if keyword_like.lower() not in hay:
                continue
        out.append(d)
    out.sort(key=lambda j: (j["deadline_dt"] is None, j["deadline_dt"] or ""))
    return out


def _is_valid_now(d: dict, now: datetime) -> bool:
    if not d.get("deadline_dt"):
        return True  # rolling / no deadline is treated as open
    try:
        return datetime.fromisoformat(d["deadline_dt"]) >= now
    except ValueError:
        return True


def mark_seen(
    conn: sqlite3.Connection,
    ids: list[int] | None = None,
    *,
    source: str | None = None,
) -> int:
    """Clear is_new for the given ids (or all when ids is None), optionally scoped to a
    single source. Returns rows affected. With ids set, `source` disambiguates the
    composite key (ids alone are not unique across sources)."""
    clauses, params = [], []
    if ids is not None:
        clauses.append(f"id IN ({','.join('?' * len(ids))})")
        params.extend(ids)
    else:
        clauses.append("is_new = 1")
    if source:
        clauses.append("source = ?")
        params.append(source)
    cur = conn.execute(
        f"UPDATE jobs SET is_new = 0 WHERE {' AND '.join(clauses)}", params
    )
    conn.commit()
    return cur.rowcount


def prune_expired(conn: sqlite3.Connection, now: datetime | None = None) -> int:
    """Delete postings whose deadline has passed. Rolling postings are kept."""
    now = now or datetime.now()
    rows = conn.execute(
        "SELECT source, id, deadline_dt FROM jobs WHERE deadline_dt IS NOT NULL"
    ).fetchall()
    expired = []
    for r in rows:
        try:
            if datetime.fromisoformat(r["deadline_dt"]) < now:
                expired.append((r["source"], r["id"]))
        except ValueError:
            continue
    for source, jid in expired:
        conn.execute("DELETE FROM jobs WHERE source = ? AND id = ?", (source, jid))
    if expired:
        conn.commit()
    return len(expired)


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
