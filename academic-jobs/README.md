# academic-jobs

Fetch **valid** (still-open, deadline-not-passed) job postings from two academic job boards:
[Academic Jobs Online](https://academicjobsonline.org) (AJO) and the
[InspireHEP jobs board](https://inspirehep.net/jobs).

This is the backend for the `academic-jobs` Claude Code skill. It searches both boards by the
same keyword presets, keeps only postings whose application deadline has not passed, stores them
in a local SQLite database, and tracks which postings are new since the last fetch. Each posting
carries a `source` (`ajo` or `inspire`); the two boards use overlapping integer ids, so the
store is keyed by `(source, id)`.

## Install

```bash
uv sync          # creates .venv with requests + beautifulsoup4
```

## Usage

```bash
uv run ajo config                       # show field presets (seeds physics-ml on first run)
uv run ajo fetch                        # search default preset on both boards, store valid postings
uv run ajo fetch --keyword cosmology    # ad-hoc keyword search (both boards)
uv run ajo fetch --source inspire       # only the InspireHEP board
uv run ajo list --valid                 # show stored postings still open now
uv run ajo list --source inspire        # only InspireHEP postings
uv run ajo show 32059                    # parse one AJO posting's detail page
uv run ajo show 3158275 --source inspire # one InspireHEP record (incl. description + contact)
uv run ajo mark-seen --all              # clear the "new" flag
uv run ajo prune                        # delete expired postings
```

Add `--json` to any command for machine-readable output.

## Sources

- **AJO** — HTML scraping. Validity is judged from each posting's detail page (firm
  `Appl Deadline`, else `listed until` date). `--fast` skips detail pages (approximate).
- **InspireHEP** — public JSON API, queried with `status=open`. The structured `deadline_date`
  is used directly; no detail fetch needed. HEP / astro focused.

Pick boards per preset with `--sources ajo,inspire`, or per run with `--source ajo|inspire|both`
(default: both).

## Data

- DB:     `~/.local/share/academic-jobs/jobs.db`
- Config: `~/.local/share/academic-jobs/config.toml`

Override the data dir with `AJO_DATA_DIR`. A v1 database (AJO-only, no `source` column) is
migrated in place on first open, tagging existing rows as `source='ajo'`.

## Validity

A posting is **valid** when its deadline is in the future. Postings with no deadline
(rolling / open until filled) are excluded by default; pass `--include-rolling` to keep them.
AJO deadlines are poster-local wall-clock times; InspireHEP `deadline_date` is taken as
end-of-day. Both are compared against the local clock.
