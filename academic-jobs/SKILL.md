---
name: academic-jobs
description: >
  Fetch valid (still-open, deadline-not-passed) job postings from Academic Jobs Online
  (academicjobsonline.org, AJO). Use when the user wants current academic openings:
  postdoc / faculty / PhD positions in physics, cosmology, ML, astrophysics or any field,
  filtered to postings whose application deadline has not passed. Manage field presets
  (keywords + position types), fetch and store valid postings, see what is new since last
  check, and inspect a posting's details. Triggers on: Academic Jobs Online, AJO, academic
  job postings, postdoc openings, faculty positions, job listings, valid 공고, 학술 잡,
  교수 공고, 포닥 공고, 채용 공고, 잡 마켓.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill
user-invocable: true
---

# Academic Jobs (AJO) Skill

Conversational interface over the `ajo` CLI, which fetches **valid** postings from
Academic Jobs Online and tracks them in a local SQLite store.

## Quick Reference

| Intent | Command | Reference |
|--------|---------|-----------|
| Show / edit field presets | `ajo config [...]` | `references/presets.md` |
| Fetch current open postings | `ajo fetch [--preset N \| --keyword K]` | `references/fetch.md` |
| Show stored postings | `ajo list [--valid] [--new]` | `references/schema.md` |
| Inspect one posting | `ajo show {id}` | `references/fetch.md` |
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

**Validity is judged from the detail page, not the list.** The AJO list page only shows a
deadline for *some* postings, and a missing list deadline does NOT mean "no deadline". So
`ajo fetch` fetches each candidate's detail page by default and judges validity from the
**effective deadline** = firm `Appl Deadline` if present, else the `listed until` date.

- valid  → effective deadline is in the future
- expired → effective deadline has passed (excluded)
- rolling → no deadline and no listed-until date (excluded unless `--include-rolling`)

`--fast` skips detail pages (faster but deadlines are approximate and many valid postings
will be missed). Prefer the default detail mode for correctness.

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
- Sort by deadline ascending; show deadline, position type, title, institution, and the
  AJO URL (`https://academicjobsonline.org/ajo/jobs/{id}`).
- When emitting a structured data table back to the user, prefer **TOON** over JSON
  (per the user's global preference): declare fields once, stream rows.
- `--fast` runs and any detail-fetch cap truncation are reported in the CLI `stats` (stderr
  / JSON). Never present a truncated run as complete; mention how many candidates were judged.

### Presets
A preset bundles `keywords` (each runs a separate AJO search, results deduped) plus optional
`position_types` and `countries` substring filters applied against the detail page. Edit with
`ajo config --set-preset NAME --keywords a,b --types postdoc --countries ...`. See
`references/presets.md`.

### Etiquette
The CLI uses one polite session with a real User-Agent and a small delay between detail
fetches, and caps detail fetches per run (logged when hit). Do not parallelise or hammer AJO.
