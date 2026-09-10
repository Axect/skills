# academic-jobs

The `academic-jobs` skill curates opportunities from **Academic Jobs Online,
InspireHEP, and official institution/research-group recruitment**. Broad postdoc
requests include both board and direct discovery automatically; explicit board-only
requests, named-lab searches and maintenance commands retain their narrower scope.

The bundled `ajo` CLI is the **board backend**, not an autonomous web-research agent.
It searches both boards by keyword presets, stores eligible board postings in SQLite,
and tracks newly discovered records. Each posting carries a `source` (`ajo` or
`inspire`); overlapping integer IDs are keyed by `(source, id)`. CLI source options
and the database schema are unchanged.

The assistant follows [SKILL.md](SKILL.md) and
[references/direct-discovery.md](references/direct-discovery.md) for official-source
research, then returns one deduplicated result separating current vacancies,
standing application routes, research-fit leads, and conflicting/closed findings.
All required instructions and tools ship inside this directory; no separate or
managed companion skill is needed.

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

## Direct-source snapshots

Official calls and application routes remain separate from the board DB. Dated
snapshots and source extracts default to `~/.local/share/academic-direct-opportunities/`;
the existing `AJO_DATA_DIR` override continues to apply only to the board backend.
The schema and evidence rules are in
[references/direct-discovery.md](references/direct-discovery.md).

```bash
python3 scripts/direct_ledger.py validate /path/to/snapshot.json
python3 scripts/direct_ledger.py diff /path/to/before.json /path/to/after.json
```

The helper uses only Python's standard library and does not fetch websites.
It rejects malformed records and inconsistent open-job classifications. Diff ignores
retrieval metadata and reports added, changed, and not-observed records; omission
does not automatically close a job. Different search scopes require the explicit
`--allow-scope-change` option.

`ajo report` emits only a board skeleton. Integrated curation must add verified
direct records, preserve source/status distinctions, and avoid counting prospects
or standing routes as funded vacancies.

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
