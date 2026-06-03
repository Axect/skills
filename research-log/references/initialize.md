# Workflow: Initialize a Research Project

Use when the user asks to register a new project in the research log.

## Trigger examples

- "Register this repo in research-log"
- "Initialize research log for this project"
- "Add this project to my research log"
- "Set up research tracking for this repo"

## Interaction flow

Ask one question at a time, in this order:

1. Project name (human-readable)
2. Slug (kebab-case identifier)
3. Repo / working directory path (absolute)
4. Main goal (1–2 sentences)
5. Initial sub-goals with rough percentages
6. Why This Approach (optional — press Enter to skip)
7. Biggest Risk (optional — press Enter to skip)

## Actions

1. Ensure these directories exist; create if missing:
   - `~/.research/`
   - `~/.research/projects/`
   - `~/.research/lessons/`
   - `~/.research/.locks/`
   - `~/.research/wiki/`

2. If `~/.research/dashboard.md` does not exist, create it using the format in `conventions.md`.

3. If `~/.research/rules.md` does not exist, create it as an empty file with the header from
   `conventions.md` (zero rules initially).

4. If the slug already appears in the Project Registry of `dashboard.md`, ask whether to update
   the existing project rather than overwriting it.

5. Create the project directory `~/.research/projects/{slug}/` and write three files per the
   schemas in `conventions.md`:
   - `compass.md` — Main Goal, Sub-goals with percentages, Why This Approach, Biggest Risk,
     `← current focus` on the first active sub-goal; also append an empty Core Documents
     section after Biggest Risk (see template below).
   - `state.md` — initial state (see template below).
   - `journal.md` — header only; no entries yet.

6. Create `~/.research/.locks/{slug}.lock` (empty file; used for flock serialization).

7. Update `dashboard.md`: add the slug → path entry to Project Registry; add an Active Projects
   entry with Current stage, Status, Next milestone, and Last session.

8. Offer to pre-populate context from available sources:
   - `README.md` in the repo
   - project notes or design docs
   - local agent instruction files (e.g. `CLAUDE.md`, `.cursorrules`)
   - recent `git log --oneline`

## Initial compass.md Core Documents block

Append the following after the Biggest Risk section in every new `compass.md`:

```markdown
## Core Documents
> Pointers to current research-frontier artifacts. Read by recall, record, and review
> for forward-looking recommendations. Updated via skill prompts on user approval.
> Cap: ≤15 entries; demote stale items to ★★ before removal.

### ★★★ Core (current frontier)

(No entries yet — added as the project produces canonical artifacts.)

### ★★ Foundational (architecture / training-data / paper-substrate references)

(No entries yet.)
```

## Initial state.md template

```markdown
# {PROJECT NAME} — State
- **Session**: —
- **Last session**: —
- **Location**: G1.1
- **Working on**: —
- **Current status**: Project initialized
- **Blocker**: None
- **Next step**: {first leaf sub-goal from compass.md}
- **Compass link**: Starts work on G1
```

Follow the exact field names from the State schema in `conventions.md`.

## Reporting

When complete, report:
- Project registered (slug, path)
- Files created: `projects/{slug}/compass.md`, `state.md`, `journal.md`
- Suggested next step (first sub-goal)
