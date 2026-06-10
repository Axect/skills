# Rumor Mill Sheet

## Source page

The rumor mill lives at `https://sites.google.com/site/postdocrumor/{year}-rumors`. Each
year's page embeds a public Google Sheet. The sheet is exported as CSV via:

```
https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv
```

No login is required.

## Known sheet IDs

The `SHEETS` dict in `prm/sheet.py` maps years to sheet IDs. Only one year ships today:

| Year | Sheet ID |
| ---- | -------- |
| 2026 | `1Bp74ujR94aNXMns3o1FepCIDyx5IlMFs0yQHuZf1_uc` |

## Columns

The parser reads the first six columns only. Trailing blank columns are ignored.

| Index | Column | Notes |
| ----- | ------ | ----- |
| 0 | Name | Display name as entered by the submitter |
| 1 | Inspire link | Full URL, e.g. `https://inspirehep.net/authors/1804701` |
| 2 | Institution | Free text; used verbatim and for country inference |
| 3 | Status | `Offered`, `Accepted`, or `Declined` (verbatim from sheet) |
| 4 | Remarks | Named fellowship, extra context, etc. |
| 5 | Timestamp | Verbatim sheet timestamp string |

The InspireHEP author record ID (recid) is parsed from the Inspire link with the regex
`/authors/(\d+)`. Rows without a valid Inspire link are stored with `recid = NULL` and
cannot be enriched.

`fetch` reads only the default (first) tab of the sheet. Multi-tab sheets for a single
year are not supported.

## Adding a past year

1. Open `https://sites.google.com/site/postdocrumor/{year}-rumors` in a browser.
2. View page source and grep for `spreadsheets/d/` to find the embedded sheet ID.
3. Add the entry to `SHEETS` in `prm/sheet.py`:
   ```python
   SHEETS: dict[int, str] = {
       2025: "...",
       2026: "1Bp74ujR94aNXMns3o1FepCIDyx5IlMFs0yQHuZf1_uc",
   }
   ```
4. For a one-off fetch without editing the source, pass the id directly:
   ```bash
   uv run prm fetch --year 2025 --sheet-id <ID>
   ```
