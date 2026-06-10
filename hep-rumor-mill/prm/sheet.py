"""Fetch and parse the public HEP-theory postdoc rumor-mill Google Sheet.

The sheet is maintained by the community at:
  https://sites.google.com/view/hep-postdoc-rumor-mill

It is exported as CSV via the standard Google Sheets public-export URL:
  https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv

Column layout (first 6 columns only; trailing blank columns are ignored):
  Name, Inspire link, Institution, Status, Remarks, Timestamp
"""

from __future__ import annotations

import csv
import io
import re

import requests

from . import USER_AGENT

# ---------------------------------------------------------------------------
# Known sheet IDs keyed by rumor-mill year
# ---------------------------------------------------------------------------
SHEETS: dict[int, str] = {
    2026: "1Bp74ujR94aNXMns3o1FepCIDyx5IlMFs0yQHuZf1_uc",
    2025: "1qXeVPgwioll9gZNXgcwnX6C45iClAsWZFqwBKligC8w",
}

_EXPORT_URL = "https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

_RECID_RE = re.compile(r"/authors/(\d+)")


def parse_recid(url: str | None) -> int | None:
    """Extract the InspireHEP author record-id from a profile URL.

    Handles both plain URLs and those with query strings, e.g.:
      https://inspirehep.net/authors/1814743
      https://inspirehep.net/authors/2099888?ui-citation-summary=true

    Returns None when the URL is None or contains no /authors/<int> segment.
    """
    if not url:
        return None
    m = _RECID_RE.search(url)
    if not m:
        return None
    return int(m.group(1))


def fetch_rows(year: int, *, sheet_id: str | None = None) -> list[dict]:
    """Download and parse rumor-mill rows for the given year.

    Parameters
    ----------
    year:
        The rumor-mill year (e.g. 2026).
    sheet_id:
        Override the sheet ID from SHEETS. Required when year is not in SHEETS.

    Returns
    -------
    list of dicts with keys:
        year, name, recid, inspire_url, institution, status, remarks, timestamp

    Raises
    ------
    ValueError
        When no sheet ID is available for the requested year.
    """
    sid = sheet_id or SHEETS.get(year)
    if not sid:
        known = ", ".join(str(y) for y in sorted(SHEETS))
        raise ValueError(
            f"No sheet ID for year {year}. Known years: {known}. "
            "Pass sheet_id= explicitly to override."
        )

    url = _EXPORT_URL.format(sheet_id=sid)
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    resp.raise_for_status()

    text = resp.content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))

    rows: list[dict] = []
    header_skipped = False

    for raw in reader:
        # Skip the header row
        if not header_skipped:
            header_skipped = True
            continue

        # Pad to at least 6 columns so index access is safe
        while len(raw) < 6:
            raw.append("")

        name = raw[0].strip()
        if not name:
            continue

        inspire_url = raw[1].strip() or None
        institution = raw[2].strip()
        status = raw[3].strip()
        remarks = raw[4].strip() or None
        timestamp = raw[5].strip() or None

        rows.append(
            {
                "year": year,
                "name": name,
                "recid": parse_recid(inspire_url),
                "inspire_url": inspire_url,
                "institution": institution,
                "status": status,
                "remarks": remarks,
                "timestamp": timestamp,
            }
        )

    return rows
