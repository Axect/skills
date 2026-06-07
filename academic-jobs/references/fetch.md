# `ajo fetch` and `ajo show`

## fetch

```bash
uv run ajo fetch [--preset NAME | --keyword K] [--limit N] [--include-rolling] [--fast]
                 [--types t1,t2] [--countries c1,c2] [--json]
```

What it does, in order:

1. **Search** AJO for each keyword (from the preset, or the single `--keyword`). All matching
   posting ids/titles are collected and deduped across keywords.
2. **Enrich** (default): fetch each candidate's detail page to read the authoritative deadline,
   position type, subject areas, and institution. `--fast` skips this (approximate, not
   recommended for validity).
3. **Classify** by effective deadline:
   - firm `Appl Deadline` in the future → **valid**
   - no firm deadline but `listed until <date>` in the future → **valid** (shown as
     `listed until YYYY/MM/DD`)
   - deadline/listed-until in the past → expired, dropped
   - neither present → **rolling**, dropped unless `--include-rolling`
4. **Filter** by `position_types` / `countries` (substring match on Position Type /
   institution), if the preset or flags set them.
5. **Store** into SQLite; postings not seen before are flagged `is_new = 1`.
6. **Output** the valid set (table, or `--json`). `stats` (stderr / JSON) reports candidate
   count, details fetched, truncation, and how many were filtered out.

### Flags
- `--preset NAME` — use a saved preset (default: the config's `default_preset`).
- `--keyword K` — one-off search, ignores presets. With no `--types`/`--countries`, no detail
  filtering is applied (so faculty/PhD postings show too).
- `--limit N` — AJO page size (default 500; one request returns all matches for a keyword).
- `--include-rolling` — also keep postings with no deadline at all.
- `--fast` — list-only; skips detail pages. Faster but misses valid postings whose deadline is
  only on the detail page. Avoid unless you only need a rough scan.
- `--json` — machine-readable; each job has a flat view plus `raw` (full DB row).

### Notes
- Detail fetches are capped per run (default 80) with a small delay between them; if the cap is
  hit it is logged and the remainder are judged by list deadline only. Narrow the preset
  keywords if you routinely exceed it.
- Deadlines are poster-local wall-clock, compared to the local clock. No timezone conversion.

## show

```bash
uv run ajo show {id} [--json]
```

Fetches and parses a single detail page: institution, position type, subject areas, clean
deadline, and URL. Useful to confirm a posting before applying.

## mark-seen

```bash
uv run ajo mark-seen --all          # clear new flag on everything
uv run ajo mark-seen 32058 30572    # clear specific ids
```

Run after the user has reviewed a batch so the next `fetch` only flags genuinely new postings.
