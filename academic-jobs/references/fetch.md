# `ajo fetch`, `ajo show`, `ajo enrich`, and `ajo report`

## fetch

```bash
uv run ajo fetch [--preset NAME | --keyword K] [--source ajo|inspire|both] [--limit N]
                 [--include-rolling] [--fast] [--types t1,t2] [--countries c1,c2] [--json]
                 [--preferred TIERS] [--excluded LIST] [--detail-cap N]
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
5. **Country/region tagging**: each row is enriched with `country` (inferred ISO2), `region`,
   `flags` (comma-separated eligibility/caution flags), and `pref_tier` (integer; 0 = top
   preferred tier). Postings matching `--excluded` are dropped here (hard filter). Postings
   matching `--preferred` tiers are tagged and kept; the rest land in the lowest tier.
6. **Store** into SQLite keyed by `(source, id)`; postings not seen before are flagged
   `is_new = 1`.
7. **Output** the merged valid set, sorted by (pref_tier ascending, then deadline ascending)
   (table, or `--json`). `stats.per_source` reports each board's candidate count, details
   fetched, truncation, filtered-out count, and `excluded` count (postings dropped by the
   excluded-countries filter). The AJO board additionally reports `detail_cap`.

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
- `--preferred TIERS` — override the preset's preferred-country tiers for this run. Use `;`
  to separate tiers and `,` to separate entries within a tier (e.g. `"KR,DE; JP,HK,GB,US"`).
  Tier 0 (first) is most preferred. Soft filter: only reorders results, does not drop anything.
  Selectors accept ISO2 codes (`KR`), country names (`Korea`), or region aliases (`Europe`,
  `Asia`, `North America`, `Middle East`, etc.).
- `--excluded LIST` — override the preset's excluded countries for this run. Comma-separated.
  Hard filter: matching postings are dropped at fetch and counted in `stats.per_source.<board>.excluded`.
  Accepts the same selector forms as `--preferred`.
- `--detail-cap N` — max AJO detail pages fetched this run (default 80). Raise it to avoid
  truncation on a broad search, or lower it for a quick pass. No effect on InspireHEP.

### Notes
- The AJO detail cap (default 80, configurable via `--detail-cap`) applies per run. If the cap
  is hit it is logged and remaining postings are judged by list deadline only. Narrow the preset
  keywords or use `ajo enrich` for follow-up passes if you routinely exceed it.
- Deadlines are compared to the local clock. AJO deadlines are poster-local wall-clock;
  InspireHEP `deadline_date` is a date, taken as end-of-day. No timezone conversion.
- The AJO detail pass also captures the posting body (description) and a contact email, stored
  in the DB for use by `ajo show` and `ajo report`.

## show

```bash
uv run ajo show {id} [--source ajo|inspire] [--refresh] [--json]
```

Displays a single posting. The command reads the stored DB row first, including any captured
description and contact. A network request is only made when the row is missing from the DB,
has no stored body, or `--refresh` is passed. Any network fetch is written back to the DB.

AJO postings now return a real description (captured during the detail pass or on first show).
InspireHEP postings return the cleaned `description`, `contact` email, and `regions` from the
API. Fields shown include `country`, `region`, `flags`, `contact`, and `description`.

Use `--refresh` to force a re-fetch (e.g. if the posting was updated upstream). Useful to
confirm a posting before applying.

## enrich

```bash
uv run ajo enrich [--source ajo|inspire] [--detail-cap N] [--include-expired]
```

Fetches detail bodies for stored postings whose body has not been captured yet (internal
`detail_fetched=0`). Use it to complete a truncated `ajo fetch` run in polite follow-up passes:
it is capped and rate-limited the same way as the fetch detail pass.

By default operates only on still-valid postings. Pass `--include-expired` to also enrich
expired postings. `--source` limits the run to one board. Prints a summary of how many postings
were enriched and how many failed.

## report

```bash
uv run ajo report [--source S] [--preferred "TIERS"] [--excluded "LIST"] [--out PATH]
```

Emits a markdown skeleton of valid stored postings, grouped by preference tier. Data-backed
fields are pre-filled: institution, country/region, type, deadline, subject areas, contact,
url, auto-detected flags, and a description excerpt. Judgment fields (research topic/PI,
eligibility, term/salary/start, application documents, fit reasoning and grade) are left as
blank placeholders. The command never invents fit judgments.

`--preferred` and `--excluded` override the preset's country tiers/exclusions for grouping
and filtering, using the same selector syntax as `ajo fetch`. `--out PATH` writes to a file;
without it the output goes to stdout.

Pair with `references/curation.md` for the mandatory curation workflow (filling in the
judgment fields, scoring, and deciding which postings to apply to).

## mark-seen

```bash
uv run ajo mark-seen --all                       # clear new flag on everything
uv run ajo mark-seen 32058 30572 --source ajo    # clear specific ids on one board
```

Run after the user has reviewed a batch so the next `fetch` only flags genuinely new postings.
With explicit ids you must pass `--source` (ids are not unique across boards); `--all` may be
scoped with `--source` or left unscoped to clear both.
