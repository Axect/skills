# `ajo fetch` and `ajo show`

## fetch

```bash
uv run ajo fetch [--preset NAME | --keyword K] [--source ajo|inspire|both] [--limit N]
                 [--include-rolling] [--fast] [--types t1,t2] [--countries c1,c2] [--json]
```

`fetch` runs against **every board in scope** (the preset's `sources`, or `--source`). For each
board, in order:

1. **Search** for each keyword (from the preset, or the single `--keyword`). Matching postings
   are collected and deduped within the board.
   - *AJO*: HTML full-text search.
   - *InspireHEP*: JSON API with `status=open` (closed postings filtered server-side).
2. **Enrich** (AJO only, default): fetch each candidate's detail page to read the authoritative
   deadline, position type, subject areas, and institution. `--fast` skips this (approximate,
   not recommended). InspireHEP needs no detail pass: the list response already carries the
   structured deadline, ranks, categories, institution, and region.
3. **Classify** by effective deadline:
   - deadline in the future → **valid** (AJO firm `Appl Deadline` or `listed until` date;
     InspireHEP `deadline_date`)
   - deadline in the past → expired, dropped
   - no deadline → **rolling**, dropped unless `--include-rolling`
4. **Filter** by `position_types` / `countries` (substring match on AJO Position Type /
   InspireHEP ranks, and institution / InspireHEP region), if the preset or flags set them.
5. **Store** into SQLite keyed by `(source, id)`; postings not seen before are flagged
   `is_new = 1`.
6. **Output** the merged valid set, deadline-sorted (table, or `--json`). `stats.per_source`
   reports each board's candidate count, details fetched, truncation, and filtered-out count.

### Flags
- `--preset NAME` — use a saved preset (default: the config's `default_preset`).
- `--keyword K` — one-off search, ignores presets. With no `--types`/`--countries`, no detail
  filtering is applied (so faculty/PhD postings show too). Searches both boards unless
  `--source` narrows it.
- `--source ajo|inspire|both` — override the preset's `sources` for this run.
- `--limit N` — page size per keyword (AJO default 500; InspireHEP default 250).
- `--include-rolling` — also keep postings with no deadline at all (both boards).
- `--fast` — AJO list-only; skips detail pages. Faster but misses valid AJO postings whose
  deadline is only on the detail page. No effect on InspireHEP.
- `--json` — machine-readable; each job has a flat view (incl. `source`) plus `raw` (full DB row).

### Notes
- AJO detail fetches are capped per run (default 80) with a small delay between them; if the cap
  is hit it is logged and the remainder are judged by list deadline only. Narrow the preset
  keywords if you routinely exceed it.
- Deadlines are compared to the local clock. AJO deadlines are poster-local wall-clock;
  InspireHEP `deadline_date` is a date, taken as end-of-day. No timezone conversion.

## show

```bash
uv run ajo show {id} [--source ajo|inspire] [--json]
```

Fetches and parses a single posting. `--source ajo` (default) parses the AJO detail page;
`--source inspire` hits the InspireHEP API record and additionally returns the cleaned
`description`, `contact` email, and `regions`. Useful to confirm a posting before applying.

## mark-seen

```bash
uv run ajo mark-seen --all                       # clear new flag on everything
uv run ajo mark-seen 32058 30572 --source ajo    # clear specific ids on one board
```

Run after the user has reviewed a batch so the next `fetch` only flags genuinely new postings.
With explicit ids you must pass `--source` (ids are not unique across boards); `--all` may be
scoped with `--source` or left unscoped to clear both.
