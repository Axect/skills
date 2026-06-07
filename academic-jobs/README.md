# academic-jobs

Fetch **valid** (still-open, deadline-not-passed) job postings from
[Academic Jobs Online](https://academicjobsonline.org) (AJO).

This is the backend for the `academic-jobs` Claude Code skill. It searches AJO by keyword
presets, keeps only postings whose application deadline has not passed, stores them in a local
SQLite database, and tracks which postings are new since the last fetch.

## Install

```bash
uv sync          # creates .venv with requests + beautifulsoup4
```

## Usage

```bash
uv run ajo config                       # show field presets (seeds physics-ml on first run)
uv run ajo fetch                        # search default preset, store valid postings
uv run ajo fetch --keyword cosmology    # ad-hoc keyword search
uv run ajo fetch --details              # also fetch detail pages (type/subject/institution)
uv run ajo list --valid                 # show stored postings still open now
uv run ajo show 32059                   # parse one posting's detail page
uv run ajo mark-seen --all              # clear the "new" flag
uv run ajo prune                        # delete expired postings
```

Add `--json` to any command for machine-readable output.

## Data

- DB:     `~/.local/share/academic-jobs/jobs.db`
- Config: `~/.local/share/academic-jobs/config.toml`

Override the data dir with `AJO_DATA_DIR`.

## Validity

A posting is **valid** when its AJO deadline is in the future. Postings with no deadline
(rolling / open until filled) are excluded by default; pass `--include-rolling` to keep them.
Deadlines are poster-local wall-clock times, compared against the local clock.
