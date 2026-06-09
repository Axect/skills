---
name: academic-jobs
description: >
  Fetch valid (still-open, deadline-not-passed) job postings from Academic Jobs Online
  (academicjobsonline.org, AJO) and the InspireHEP jobs board (inspirehep.net/jobs). Use
  when the user wants current academic openings: postdoc / faculty / PhD positions in
  physics, cosmology, HEP, ML, astrophysics or any field, filtered to postings whose
  application deadline has not passed. Searches both boards by default and merges the
  results. Manage field presets (keywords + position types + which boards), fetch and store
  valid postings, see what is new since last check, and inspect a posting's details. Triggers
  on: Academic Jobs Online, AJO, InspireHEP jobs, Inspire HEP 공고, academic job postings,
  postdoc openings, faculty positions, job listings, valid 공고, 학술 잡, 교수 공고,
  포닥 공고, 채용 공고, 잡 마켓.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill
user-invocable: true
---

# Academic Jobs Skill

Conversational interface over the `ajo` CLI, which fetches **valid** postings from two
academic job boards and tracks them in a local SQLite store:

- **AJO** — Academic Jobs Online (`academicjobsonline.org`), HTML scraping, all fields.
- **InspireHEP** — the HEP/astro jobs board (`inspirehep.net/jobs`), via its public JSON API.

By default `ajo fetch` searches **both** boards with the same keywords and merges the
results, deadline-sorted. Each posting carries a `source` (`ajo` or `inspire`); the two
boards use overlapping integer ids, so everything is keyed by `(source, id)`.

## Quick Reference

| Intent | Command | Reference |
|--------|---------|-----------|
| Show / edit field presets | `ajo config [...]` | `references/presets.md` |
| Fetch current open postings | `ajo fetch [--preset N \| --keyword K] [--source ajo\|inspire\|both] [--preferred TIERS] [--excluded LIST] [--detail-cap N]` | `references/fetch.md` |
| Show stored postings | `ajo list [--valid] [--new] [--source S]` | `references/schema.md` |
| Inspect one posting (stored-first) | `ajo show {id} [--source ajo\|inspire] [--refresh]` | `references/fetch.md` |
| Fetch missing detail bodies | `ajo enrich [--source ajo\|inspire] [--detail-cap N] [--include-expired]` | `references/fetch.md` |
| Emit curation skeleton | `ajo report [--source S] [--preferred TIERS] [--excluded LIST] [--out PATH]` | `references/curation.md` |
| Mark postings as seen | `ajo mark-seen --all` | `references/fetch.md` |
| Drop expired postings | `ajo prune` | `references/schema.md` |

## Running the CLI

The CLI lives in this skill directory. Always invoke it through `uv`:

```bash
uv run --project <skill-dir> ajo <command> [...]
```

where `<skill-dir>` is the directory containing this file. Add `--json` to any command
when you (Claude) need to post-process the output; the default is a human table.

First run auto-creates the data dir, the SQLite DB, and a default `physics-ml` preset.

## Curation rule (read before writing a report)

Before writing any postings report, you must deep-read every posting via `ajo show {id}`. After
`ajo fetch` or `ajo enrich`, full description bodies are stored in the DB, so `ajo show` reads
locally (no extra network calls). Never judge a posting from its title or keyword match alone.

Every posting in a report must fill the mandatory 10-field schema:

1. 직급/seniority
2. 기관, 그룹, 국가
3. 연구주제, PI
4. 자격/eligibility
5. 기간, 급여, 시작일
6. 마감 체계 (hard/rolling/etc.)
7. 지원 서류
8. fit 근거 + 등급
9. 신빙성/주의 플래그
10. 출처 URL

Use `ajo report` to generate a skeleton with data-backed fields pre-filled and blank placeholders
for judgment fields. The full procedure is in `references/curation.md`. Reports are saved to
`~/Dropbox/AJO/AJO_YYYY-MM-DD.md` in Korean.

## Core behaviour you must understand

### Two sources, one merged view
- `ajo fetch` runs the preset's keywords against **every board in the preset's `sources`**
  (default `["ajo", "inspire"]`), merges, dedups within each board, and stores everything
  keyed by `(source, id)`.
- Override per run with `--source ajo` (AJO only), `--source inspire` (InspireHEP only), or
  `--source both`. With an ad-hoc `--keyword`, both boards are searched unless `--source` says
  otherwise.
- The same preset filters apply to both boards: `position_types` is matched against the AJO
  "Position Type" and against the InspireHEP `ranks` (e.g. `postdoc` matches `POSTDOC`);
  `countries` is matched against the institution string (plus InspireHEP `regions`).

### AJO validity (HTML)
**Validity is judged from the detail page, not the list.** The AJO list page only shows a
deadline for *some* postings, and a missing list deadline does NOT mean "no deadline". So
`ajo fetch` fetches each AJO candidate's detail page by default and judges validity from the
**effective deadline** = firm `Appl Deadline` if present, else the `listed until` date.
`--fast` skips AJO detail pages (faster but deadlines are approximate and many valid postings
will be missed). Prefer the default detail mode for correctness. `--fast` does not affect
InspireHEP.

### InspireHEP validity (API)
The InspireHEP API is queried with `status=open` (server-side), so closed postings never
arrive. The structured `deadline_date` is used directly, no detail fetch needed.

In both cases:
- valid  → effective deadline is in the future
- expired → effective deadline has passed (excluded)
- rolling → no deadline (excluded unless `--include-rolling`)

## Common Rules

### Base directory
All state lives under `~/.local/share/academic-jobs/` (override with `AJO_DATA_DIR`):
- `jobs.db` — SQLite store of postings
- `config.toml` — field presets

### Typical flow for "show me current openings"
1. `ajo fetch --json [--preferred "KR,DE; JP,HK,GB,US"] [--excluded "IN,IL"] [--detail-cap 80]`
   (uses the default preset; fetches details up to `--detail-cap`; stores + flags new).
   Pass `--preferred`/`--excluded` to override the preset for this run without saving.
   If AJO has more candidates than `--detail-cap`, the run is truncated; run `ajo enrich` in
   a follow-up pass to capture the remaining detail bodies politely.
2. Render the returned `jobs` as a table sorted by `pref_tier` then deadline. Surface postings
   with `"new": true` first or in a separate "New since last check" group.
3. After presenting, if the user has reviewed them, run `ajo mark-seen --all` so the next
   fetch only flags genuinely new postings.
4. To inspect one posting: `ajo show {id} [--source ajo|inspire]`. It reads the stored row
   (including the cached description body) first; it only hits the network when the row is
   missing, has no stored body, or `--refresh` is given. A live fetch is written back to the DB.

### Output formatting
- Sort by deadline ascending; show source, deadline, position type, title, institution, and
  the posting URL (AJO `https://academicjobsonline.org/ajo/jobs/{id}`, InspireHEP
  `https://inspirehep.net/jobs/{id}`).
- When the user wants to know "where is this from", surface the `source` column. When merging,
  it is fine to interleave both boards by deadline; flag the source on each row.
- When emitting a structured data table back to the user, prefer **TOON** over JSON
  (per the user's global preference): declare fields once, stream rows.
- Each output row now carries `country` (ISO 2-letter code), `region`, `flags`, and
  `pref_tier` (integer; 0 = top tier, higher = lower preference, null = not in any tier).
  Results are sorted first by `pref_tier` ascending, then by deadline ascending within each
  tier. Surface `pref_tier` and `country` when presenting results so the user can see the
  preference grouping at a glance.
- Per-board stats live under `stats.per_source` in the JSON. `--fast` runs and any AJO
  detail-fetch cap truncation are reported there. Each board entry also includes an `excluded`
  count (postings dropped by `excluded_countries`). The AJO entry additionally reports
  `detail_cap` (the cap used for that run). Never present a truncated run as complete; mention
  how many candidates were judged per board and whether the detail cap was hit.

### Presets
A preset bundles `keywords` (each runs a separate search per board, results deduped) plus
optional `position_types`, `countries`, `sources`, `preferred_countries`, and
`excluded_countries` fields. Edit with
`ajo config --set-preset NAME --keywords a,b --types postdoc --sources ajo,inspire`. See
`references/presets.md`.

- `countries` (unchanged): hard INCLUDE substring filter matched against the institution string.
  Only postings whose institution matches are kept.
- `preferred_countries`: ordered list of tiers; each tier is a list of selectors. Tier 0 is
  most preferred. This is a soft filter: it only reorders results (never drops). TOML example:
  `preferred_countries = [["KR", "DE"], ["JP", "HK", "GB", "US"]]`. Set via CLI:
  `ajo config --set-preset NAME --preferred "KR,DE; JP,HK,GB,US"` (`;` separates tiers,
  `,` separates entries within a tier). Displayed in `ajo config` as
  `[KR, DE] > [JP, HK, GB, US]`.
- `excluded_countries`: flat list of selectors. Hard filter: matching postings are dropped at
  fetch time. TOML example: `excluded_countries = ["IN", "IL", "Middle East"]`. Set via
  `ajo config --set-preset NAME --excluded "IN,IL,Middle East"`.
- Selectors for both `preferred_countries` and `excluded_countries` accept: an ISO 2-letter
  code (`"KR"`), a country name (`"Korea"`), or a region alias (`"Europe"`, `"Asia"`,
  `"North America"`, `"Middle East"`, `"EU"`, `"APAC"`, `"MENA"`).
- `position_types` and `sources` work as before.

### Etiquette
The CLI uses one polite session per board with a real User-Agent and small delays between
requests, and caps AJO detail fetches per run (logged when hit). Do not parallelise or hammer
either board.
