# Storage schema and `list` / `prune`

## SQLite store

`~/.local/share/academic-jobs/jobs.db`, table `jobs`:

| column | meaning |
|--------|---------|
| `id` | AJO position id (primary key); URL is `/ajo/jobs/{id}` |
| `code` | short code shown in the list (e.g. `PD_COSMO`) |
| `title` | full descriptive title |
| `institution` | from detail page (NULL until details fetched) |
| `position_type` | from detail page (e.g. `Postdoctoral`) |
| `subject_areas` | from detail page (e.g. `Physics / Cosmology`) |
| `deadline_raw` | display string: firm deadline, or `listed until YYYY/MM/DD` |
| `deadline_dt` | **effective** deadline, ISO 8601; NULL only for true rolling postings |
| `status` | `valid` or `rolling` at fetch time |
| `url` | full posting URL |
| `matched_keywords` | comma-separated keywords/presets that surfaced it |
| `first_seen` | when first stored (ISO) |
| `last_fetched` | last time a fetch touched it (ISO) |
| `is_new` | 1 until `mark-seen` clears it |

A `meta` table holds `schema_version` and `last_fetch_at`.

`deadline_dt` stores the **effective** deadline (firm deadline if present, otherwise the
`listed until` date at end-of-day), so validity can be recomputed later without re-fetching.

## list

```bash
uv run ajo list [--valid] [--new] [--keyword-like TEXT] [--json]
```

- `--valid` — only postings whose `deadline_dt` is still in the future (recomputed against the
  current clock; rolling postings count as valid).
- `--new` — only postings still flagged `is_new`.
- `--keyword-like TEXT` — substring filter over title / code / institution / subject areas.
- Output is sorted by deadline ascending (rolling/unknown last).

`list` reads only the local DB; it does not hit the network. Run `fetch` first to populate or
refresh it.

## prune

```bash
uv run ajo prune
```

Deletes postings whose `deadline_dt` has passed. Rolling postings (NULL `deadline_dt`) are
kept. Safe housekeeping to keep the store to currently-relevant openings.

## JSON output shape

`--json` returns:

```json
{
  "count": 13,
  "jobs": [
    {
      "id": 30572, "new": true, "deadline": "2026/10/07 23:59:59",
      "type": "Postdoctoral", "title": "...", "institution": "University of Michigan, ...",
      "url": "https://academicjobsonline.org/ajo/jobs/30572",
      "matched": "cosmology",
      "raw": { ...full DB row... }
    }
  ],
  "stats": { "candidates": 50, "details_fetched": 50, "new": 13, "mode": "detail", ... }
}
```
