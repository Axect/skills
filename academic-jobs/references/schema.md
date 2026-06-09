# Storage schema and `list` / `prune`

## SQLite store

`~/.local/share/academic-jobs/jobs.db`, table `jobs`. Primary key is the composite
`(source, id)` because AJO and InspireHEP use overlapping integer ids:

| column | meaning |
|--------|---------|
| `source` | `ajo` or `inspire` (part of the primary key) |
| `id` | board-local posting id; URL is `/ajo/jobs/{id}` (AJO) or `/jobs/{id}` (InspireHEP) |
| `code` | AJO short code, or InspireHEP external id (may be NULL) |
| `title` | full descriptive title (InspireHEP `position`) |
| `institution` | AJO detail page / InspireHEP `institutions[].value` (joined with `;`) |
| `position_type` | AJO `Position Type` (e.g. `Postdoctoral`) / InspireHEP `ranks` (e.g. `POSTDOC`) |
| `subject_areas` | AJO subject areas / InspireHEP `arxiv_categories` (e.g. `hep-ph, astro-ph`) |
| `deadline_raw` | display string: firm deadline, `listed until YYYY/MM/DD`, or InspireHEP date |
| `deadline_dt` | **effective** deadline, ISO 8601; NULL only for true rolling postings |
| `status` | `valid` or `rolling` at fetch time |
| `url` | full posting URL |
| `matched_keywords` | comma-separated keywords/presets that surfaced it |
| `first_seen` | when first stored (ISO) |
| `last_fetched` | last time a fetch touched it (ISO) |
| `is_new` | 1 until `mark-seen` clears it |

A `meta` table holds `schema_version` (currently `2`) and `last_fetch_at`. Databases created by
the pre-InspireHEP schema (v1, no `source` column) are migrated in place on first open: existing
rows are tagged `source='ajo'` and the primary key is rebuilt as `(source, id)`.

`deadline_dt` stores the **effective** deadline (AJO firm deadline if present, otherwise the
`listed until` date at end-of-day; InspireHEP `deadline_date` at end-of-day), so validity can be
recomputed later without re-fetching.

## list

```bash
uv run ajo list [--valid] [--new] [--keyword-like TEXT] [--source ajo|inspire] [--json]
```

- `--valid` — only postings whose `deadline_dt` is still in the future (recomputed against the
  current clock; rolling postings count as valid).
- `--new` — only postings still flagged `is_new`.
- `--keyword-like TEXT` — substring filter over title / code / institution / subject areas.
- `--source ajo|inspire` — restrict to one board.
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
      "id": 30572, "source": "ajo", "new": true, "deadline": "2026/10/07 23:59:59",
      "type": "Postdoctoral", "title": "...", "institution": "University of Michigan, ...",
      "url": "https://academicjobsonline.org/ajo/jobs/30572",
      "matched": "cosmology",
      "raw": { ...full DB row... }
    }
  ],
  "stats": {
    "sources": ["ajo", "inspire"],
    "per_source": {
      "ajo":     { "candidates": 50, "details_fetched": 50, "mode": "detail", "filtered_out": 4 },
      "inspire": { "candidates": 45, "mode": "api", "filtered_out": 5 }
    },
    "new": 13, "stored": 91
  }
}
```

`fetch` reports per-board stats under `stats.per_source`; `list` omits `stats`.
