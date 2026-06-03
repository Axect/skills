# Research Log Conventions

This document defines the storage model, file schemas, and shared rules for the research-log
skill. Read this first; every workflow reference builds on it.

The skill turns a research log from a passive diary into an **advisor** that acts at three
moments: a decision-time guardrail (M1), cross-project recall when stuck (M3), and real-time
goal-drift detection (M4). The data model below exists to make those three moments cheap.

## Storage Location

`~/.research/`

A single unified store. It replaces older split stores. If a legacy `~/.research-log/` exists,
treat it as read-only backup until migration is confirmed; do not write to it.

## File Structure

```text
~/.research/
├── dashboard.md                 # All projects at a glance (derived data, regenerated at review)
├── rules.md                     # Promoted Rules — small, ALWAYS-LOADED decision checklist (M1)
├── projects/
│   └── {slug}/
│       ├── compass.md           # Main Goal / Sub-goals + % / Why / Biggest Risk / current focus
│       ├── state.md             # Session pointer (overwritten on each save)
│       └── journal.md           # Decision Log, append-only, newest-first, kept VERBATIM
├── lessons/
│   └── {lesson-id}.md           # First-class Lesson object (one principle per file)
├── wiki/                        # Thesis narratives, concept definitions, method descriptions
└── .locks/
    └── {slug}.lock              # One flock file per project
```

Design principle — **separate layers by how they are read**:

| Layer    | Size       | Lifetime        | How it is read                 |
|----------|------------|-----------------|--------------------------------|
| Compass  | small      | always current  | always loaded (steering)       |
| State    | tiny       | overwritten     | session restore                |
| Journal  | large      | append, verbatim| searched, not read whole       |
| Lessons  | small/file | accumulating    | searched + matched (M1/M3)     |
| Rules    | tiny       | accumulating    | always loaded (M1 checklist)   |

## dashboard.md Format

```markdown
# Research Dashboard
> Last updated: YYYY-MM-DD

## Project Registry
<!-- Format: "- {slug}: {absolute_path}" — parsed to map CWD to project -->
- slug1: ~/path/to/project1
- slug2: ~/path/to/project2

## Active Projects

### {PROJECT NAME} — {one-line description}
- **Current stage**: {current sub-goal ID and name}
- **Status**: {active | blocked | stalled} — {one-line detail}
- **Next milestone**: {next milestone}
- **Last session**: {YYYY-MM-DD}

## Timeline (last 2 weeks)
| Date | Project | Decision/Event |
|------|---------|----------------|
| MM-DD | {project} | {one-line summary} |

## Cross-Project Observations
> Only naturally emerging connections. Proposed during review; added only after user approval.
```

Dashboard is derived data, regenerated from project files during review. Routine state saves do
not write to the dashboard.

## Project Files (`projects/{slug}/`)

### compass.md

```markdown
# {PROJECT NAME} — Compass

## Main Goal
{1-2 sentence research objective}

## Sub-goals

- **G1. {title}** [{percentage}%]
  - G1.1 {task} [{percentage}%] — {brief status}
  - G1.2 {task} [{percentage}%]

- **G2. {title}** [{percentage}%] ← current focus
  - G2.1 {task} [{percentage}%]

## Why This Approach
{Fundamental reasoning for the current approach}

## Biggest Risk
{Key risk that would force a direction change if realized}
```

Percentage rules:
- Leaf-level percentages are proposed by the skill and approved by the user.
- Parent-level percentages are computed from child goals.
- The `← current focus` marker must appear on exactly one active focus item. It is the anchor
  for drift detection (M4).

#### Core Documents (optional)

`compass.md` may include a `## Core Documents` section appended **after the Biggest Risk
section**. When present, it is a user-curated pointer layer to the project's research-frontier
artifacts. Skills read it during recall and record; it is never auto-edited.

```markdown
## Core Documents
> Pointers to current research-frontier artifacts. Read by recall, record, and review
> for forward-looking recommendations. Updated via skill prompts on user approval.
> Cap: ≤15 entries; demote stale items to ★★ before removal.

### ★★★ Core (current frontier)

- `<path>` — **<role>** (<artifact inventory>) · <status> · <last YYYY-MM-DD>

### ★★ Foundational (architecture / training-data / paper-substrate references)

- `<path>` — <role> · <status> · <last YYYY-MM-DD>
```

**Tier semantics:**
- **★★★ Core** — actively cited by paper substrate or the current canonical artifact.
- **★★ Foundational** — architecture / training-data / methodology references kept for
  context.

**Status enum** (extend only when necessary):
- `active canonical` — current source of truth
- `component → <other-path-stem>` — preserved; cross-reference header points at a different
  active canonical
- `preserved + header` — predates current methodology; kept as historical artifact
- `foundational` — used as reference; not actively maintained
- `reference §X` — paper section it supports
- `superseded` — kept only as predecessor evidence (rare; usually demote to ★★ instead)

**Field separator** is the middle-dot ` · ` (U+00B7) so that paths and roles containing
hyphens or em-dashes remain unambiguous. Paths are wrapped in backticks for regex extraction.

**Cap and maintenance:**
- ≤ 15 entries total. When the list grows, demote ★★★ → ★★ before removing entries.
- ★★★ entries with no `last YYYY-MM-DD` touch in 30+ days are flagged by review for
  demotion to ★★.
- The section is **user-curated** (not derived). Review preserves it intact during dashboard
  regeneration; skills propose updates via prompt and never auto-edit without user approval.

### state.md

```markdown
# {PROJECT NAME} — State
- **Session**: {YYYY-MM-DDTHH:MM}
- **Last session**: {YYYY-MM-DDTHH:MM}
- **Location**: {G?.? reference to Compass}
- **Working on**: {what was being worked on}
- **Current status**: {current status}
- **Blocker**: {blocker or "None"}
- **Next step**: {next concrete action}
- **Compass link**: {how this connects to the focused sub-goal}
```

State is overwritten on each save, never appended.

### journal.md

```markdown
# {PROJECT NAME} — Journal (Decision Log)

### YYYY-MM-DD | {title}

**Context**: {Which Compass goal this falls under}

**Tried**: {What was attempted}
**Expected**: {What was expected}
**Got**: {What actually happened}

**Why analysis**:
1. {Root cause chain}
2. {Domain-specific explanation}
3. {Literature / empirical evidence}

**Conclusion**: {Next action}
**Lesson**: {Generalizable principle — points to a lessons/{id}.md file}
```

Newest entries first. Entries are kept **verbatim** — the journal is the long-form "why we did
things" record and is consumed by search, not by reading the whole file. The skill drafts
entries; the user approves before any write.

## Lesson Objects (`lessons/{id}.md`)

A Lesson is the first-class, reusable unit extracted from journal entries. One principle per
file. Lessons are the corpus that powers the decision guardrail (M1) and recall (M3).

```markdown
---
id: {kebab-case-stable-id}
title: {short human title}
kind: {anti-pattern | principle | technique | convention}
trigger:                          # phrases matched against a proposed action (M1) and queries (M3)
  - {phrase, e.g. "architecture choice"}
  - {phrase, e.g. "before data sanity check"}
projects: [{slug}, ...]           # every project where this recurred; len >= 2 => promote to rule
status: {lesson | rule}           # promoted to "rule" once it recurs across >= 2 projects
confidence: {low | medium | high}
created: YYYY-MM-DD
---

**Pattern:** {what the situation looks like}

**Why it bites:** {root-cause / domain reasoning}

**Check (for M1):** {a one-line question to ask before committing to the matching action}

**Evidence:** {project + date/section pointers, e.g. project-a 2026-01-12 / project-b phase-2 / project-c run-7}

**Related:** [[other-lesson-id]]
```

Rules for Lessons:
- `id` is stable; never reuse for a different lesson.
- `trigger` phrases are how a proposed action is matched at decision time — write them as the
  kinds of phrases a user would say when about to make the relevant choice.
- `projects` is the recurrence ledger. When its length reaches 2, the lesson is eligible for
  promotion to `status: rule`.
- Lessons are **never archived** — they are the long-term cross-project asset.

## rules.md (the M1 engine)

`rules.md` is the compact projection of every Lesson with `status: rule`. It is small by
construction (only promoted lessons) and is meant to be **loaded on every relevant turn** so
the decision guardrail can fire without reading the full lessons corpus.

```markdown
# Research Rules
> Promoted lessons (recurred across >= 2 projects). Consult before agreeing to any approach
> choice. Regenerated at review from lessons/ where status: rule.

- **{lesson-id}** — {one-line Check}. ({comma-separated projects})
- **{lesson-id}** — {one-line Check}. ({comma-separated projects})
```

Regenerated whenever a lesson is promoted (during record or review).

## Archive Rules

- Trigger: a project's `journal.md` exceeds 30 entries OR 500 lines.
- Review proposes archiving; the user approves before changes.
- Entries older than 6 months move to a clearly marked archive region at the bottom of
  `journal.md` (or a sibling `journal-{year}.md`), preserved verbatim.
- Queries and recall search both the active and archived regions.
- Lessons and rules are never archived.

## Concurrency

- Before any write under `projects/{slug}/`, acquire `flock ~/.research/.locks/{slug}.lock`.
- Different projects can be updated in parallel; the same project is serialized.
- Locks release automatically when the process exits.
- Dashboard and rules regeneration happen during review (or, for rules, immediately on
  promotion), not on routine state saves.

## Project Identification

The current project is identified by matching the current working directory against the Project
Registry in `dashboard.md`. Each registry entry maps a slug to an absolute path; the CWD is
checked as a prefix of the registered path.

## Search Backbone (QMD)

Semantic recall (M3) and lesson dedup (during record) rely on QMD indexing `~/.research/`.
The QMD collection should point at `~/.research/` with pattern `**/*.md`. Recall queries combine
lexical, vector, and HyDE sub-queries; results are merged with direct reads of matched
`lessons/*.md` and `journal.md` regions. If QMD is unavailable, fall back to file-based
search (grep over lessons/ and journals/).
