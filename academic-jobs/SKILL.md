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
| Fetch current open postings | `ajo fetch [--preset N \| --keyword K] [--source ajo\|inspire\|both]` | `references/fetch.md` |
| Show stored postings | `ajo list [--valid] [--new] [--source S]` | `references/schema.md` |
| Inspect one posting | `ajo show {id} [--source ajo\|inspire]` | `references/fetch.md` |
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
1. `ajo fetch --json` (uses the default preset; fetches details; stores + flags new).
2. Render the returned `jobs` as a table sorted by deadline ascending. Surface postings with
   `"new": true` first or in a separate "New since last check" group.
3. After presenting, if the user has reviewed them, run `ajo mark-seen --all` so the next
   fetch only flags genuinely new postings.

### Output formatting
- Sort by deadline ascending; show source, deadline, position type, title, institution, and
  the posting URL (AJO `https://academicjobsonline.org/ajo/jobs/{id}`, InspireHEP
  `https://inspirehep.net/jobs/{id}`).
- When the user wants to know "where is this from", surface the `source` column. When merging,
  it is fine to interleave both boards by deadline; flag the source on each row.
- When emitting a structured data table back to the user, prefer **TOON** over JSON
  (per the user's global preference): declare fields once, stream rows.
- Per-board stats live under `stats.per_source` in the JSON. `--fast` runs and any AJO
  detail-fetch cap truncation are reported there. Never present a truncated run as complete;
  mention how many candidates were judged per board.

### Presets
A preset bundles `keywords` (each runs a separate search per board, results deduped) plus
optional `position_types` and `countries` substring filters, and a `sources` list selecting
which boards to search (default both). Edit with
`ajo config --set-preset NAME --keywords a,b --types postdoc --sources ajo,inspire`. See
`references/presets.md`.

### Etiquette
The CLI uses one polite session per board with a real User-Agent and small delays between
requests, and caps AJO detail fetches per run (logged when hit). Do not parallelise or hammer
either board.
