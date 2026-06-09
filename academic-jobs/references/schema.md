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
| `description` | full posting body text, captured when the detail page is fetched (AJO detail HTML or InspireHEP detail API); NULL until captured |
| `contact` | contact email(s) parsed from the posting |
| `country` | inferred ISO 3166-1 alpha-2 country code (e.g. `KR`, `DE`, `JP`), derived from the institution string via `ajo/classify.py` |
| `region` | inferred region string: `Europe`, `Asia`, `North America`, `South America`, `Oceania`, `Africa`, or `Middle East` |
| `flags` | comma-separated eligibility/caution flags detected in the body or title: `female-only`, `fresh-phd-limit`, `nationality-restricted`, `military-service-clause`, `funding-pending`, `senior:professor`, `date-mismatch(stale?)` |
| `detail_fetched` | `0` by default; set to `1` once the body has been captured; drives `ajo enrich`, which targets rows still at `0` |

A `meta` table holds `schema_version` (currently `3`) and `last_fetch_at`. The v1-to-v2 migration
(adding the `source` column and rebuilding the composite primary key) runs first when the database
is still on v1, tagging existing rows as `source='ajo'`. The v2-to-v3 migration is purely additive:
six `ALTER TABLE ADD COLUMN` statements append `description`, `contact`, `country`, `region`,
`flags`, and `detail_fetched` to the `jobs` table without touching existing rows. `upsert_job` uses
`COALESCE` for these fields so a cheap list-only pass never overwrites a previously captured
description, contact block, or flags.

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
      "country": "US", "region": "North America", "pref_tier": 0, "flags": "",
      "raw": { ...full DB row, including description, contact, country, region, flags, detail_fetched... }
    }
  ],
  "stats": {
    "sources": ["ajo", "inspire"],
    "per_source": {
      "ajo":     { "candidates": 50, "details_fetched": 50, "mode": "detail", "filtered_out": 4, "excluded": 3, "detail_cap": 100 },
      "inspire": { "candidates": 45, "mode": "api", "filtered_out": 5, "excluded": 2 }
    },
    "new": 13, "stored": 91
  }
}
```

`fetch` reports per-board stats under `stats.per_source`; `list` omits `stats`.
