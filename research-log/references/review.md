# Workflow: Weekly Review

Use for a scheduled review across all projects — compasses alignment, lesson promotion,
dashboard regeneration, QMD reindex, and archive management.

## Trigger examples

- "Weekly research review"
- "Run research-log review"
- "Refresh dashboard"
- "Promote any new lessons"

## Phases

### 1. Load all projects

- Read `~/.research/dashboard.md`; parse the Project Registry (slug → path entries).
- For each project: read `compass.md`, `state.md`, and the last 2 weeks of `journal.md`
  entries (newest-first; stop at the first entry older than 14 days).

### 2. Compass alignment

- Map each recent journal entry to its stated Compass sub-goal (**Context** field).
- Compute the fraction of entries that fall outside the `← current focus` sub-goal.
- If drift > 40%, flag that project: "X% of recent work is off-focus from {sub-goal}."
- Propose percentage updates for sub-goals (leaf-level only; parents computed from children).
- Apply changes only after user approval; see conventions.md for compass format rules.

#### Core Documents staleness check

For each project, if `~/.research/projects/{slug}/compass.md` contains a `## Core Documents`
section:

- Parse the ★★★ Core entries and extract the trailing `last YYYY-MM-DD` date from each.
- If the touch date is **30+ days** older than today, propose demotion to ★★ Foundational:
  > "Core Documents staleness ({slug}):
  > - `outputs/<dir-a>/` (★★★, last YYYY-MM-DD) — N days untouched. Demote to ★★?
  > Apply these changes?"
- Also flag: any ★★★ entry whose status is `superseded` (should already be ★★ or removed)
  and any breach of the ≤ 15 entry cap.
- Apply only after user approval. Use `flock ~/.research/.locks/{slug}.lock` for the write.

### 3. Cross-project pattern scan

- Collect recent journal entries across all projects.
- Identify shared failure modes, transferable techniques, or contradictory approaches.
- Present each proposed observation with supporting evidence citations `({project}, {date})`.
- Add observations to the **Cross-Project Observations** section of `dashboard.md` only after
  user approval.

### 4. Lesson promotion

- Read all files in `~/.research/lessons/`.
- Identify any lesson with `status: lesson` and `len(projects) >= 2`.
- For each candidate: propose promoting `status` to `rule`.
- After user approval: update the lesson file (`status: rule`) and regenerate `rules.md`
  as the compact projection of all `status: rule` lessons per the schema in conventions.md.
- Lessons are **never archived** — they are the long-term cross-project asset.

### 5. Dashboard regeneration

Rebuild `~/.research/dashboard.md` from source files:
- **Active Projects** block: from each project's `compass.md` (current stage, focus) +
  `state.md` (status, blocker, next step, last session).
- **Timeline**: headers from the last 2 weeks of each `journal.md`.
- **Project Registry**: preserve verbatim (do not re-derive paths).
- **Cross-Project Observations**: preserve previously approved observations; append any
  newly approved ones from Phase 3.
- **Core Documents** (`## Core Documents` in each `compass.md`): preserve intact — it is
  **user-curated**, not derived from State or Journal. Phase 2 staleness check handles its
  updates separately; do not overwrite or regenerate it here.

### 6. Reindex QMD

Refresh the QMD index over `~/.research/` so recall and lesson matching reflect the latest
lesson promotions and journal entries. A config change or new/edited files are **not** picked
up automatically — run both commands:

```bash
qmd update    # re-scan ~/.research, add/update/remove changed docs (BM25 index)
qmd embed     # refresh vector embeddings for any new/changed chunks
```

`qmd update` reports `Indexed: N new, M updated, ... K removed`; `qmd embed` reports embedded
chunk/document counts. Verify with `qmd status` (Documents Total should match the store) and a
sanity query (e.g. `qmd query` via the MCP tool for a known lesson). If stale entries from a
removed/renamed collection linger (Total exceeds the actual file count), run `qmd cleanup` to
vacuum them. Note any QMD errors; do not treat a reindex failure as fatal to the rest of the
review.

### 7. Archive management

For each project:
- Count journal entries and total line count in `journal.md`.
- If entries > 30 OR lines > 500: propose moving entries older than 6 months to a clearly
  marked archive region at the bottom of `journal.md` or to a sibling `journal-{year}.md`,
  preserved verbatim.
- Apply only after user approval. Lessons and `rules.md` are never archived.
- After archiving, recall and QMD search must cover both active and archived regions.

## Reporting

After all phases, summarize:
- Alignment status per project (on-focus / drifted; proposed % updates if any)
- Cross-project patterns found and whether any were approved for dashboard
- Lessons promoted (id, from how many projects) and whether `rules.md` was regenerated
- Dashboard regeneration result
- QMD reindex status
- Archive actions taken (or "none needed")
- Recommended next review date (default: 7 days)
