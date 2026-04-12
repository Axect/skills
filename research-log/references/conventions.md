# Research Log Conventions for Forge

## Storage Location

`~/.research-log/`

## File Structure

```text
~/.research-log/
├── dashboard.md                       # All projects at a glance (derived data)
├── .locks/                            # flock files for concurrency safety
│   └── {slug}.lock                    # One lock per project
├── {slug}.md                          # Compass + State + Decision Log (one per project)
└── {slug}-decisions-{year}.md         # Archived Decision Log entries (when main file grows)
```

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
> Only naturally emerging connections. Forge proposes them during review; add only after user approval.
```

Dashboard is derived data and should be regenerated from project files during review.
Routine state saves should not write to dashboard directly.

## Project File ({slug}.md) Format

Three sections: Compass, State, Decision Log.

### Compass Section

```markdown
## Compass

### Main Goal
{1-2 sentence research objective}

### Sub-goals

- **G1. {title}** [{percentage}%]
  - G1.1 {task} [{percentage}%] — {brief status}
  - G1.2 {task} [{percentage}%]

- **G2. {title}** [{percentage}%] ← current focus
  - G2.1 {task} [{percentage}%]

### Why This Approach
{Fundamental reasoning for current approach}

### Biggest Risk
{Key risk requiring direction change if realized}
```

### Percentage Rules

- Leaf-level percentages are proposed by Forge and approved by the user.
- Parent-level percentages are computed from child goals.
- The `← current focus` marker must appear on exactly one active focus item.

### State Section

```markdown
## State
- **Session**: {YYYY-MM-DDTHH:MM}
- **Last session**: {YYYY-MM-DDTHH:MM}
- **Location**: {G?.? reference to Compass}
- **Working on**: {what was being worked on}
- **Current status**: {current status}
- **Blocker**: {blocker or "None"}
- **Next step**: {next concrete action}
- **Compass link**: {how this connects to sub-goal}
```

State is overwritten on each save, not appended.

### Decision Log Section

```markdown
## Decision Log

### YYYY-MM-DD | {title}

**Context**: {Which Compass goal this falls under}

**Tried**: {What was attempted}
**Expected**: {What was expected}
**Got**: {What actually happened}

**Why analysis**:
1. {Root cause chain}
2. {Domain-specific explanation}
3. {Literature/empirical evidence}

**Conclusion**: {Next action}
**Lesson**: {Generalizable principle — cross-project connection point}
```

Newest entries come first. Forge drafts the analysis; the user approves before any write.

## Archive Rules

- Trigger: Decision Log > 30 entries OR main file > 500 lines
- Review proposes archiving; the user approves before changes
- Entries older than 6 months move to `{slug}-decisions-{year}.md`
- Entries are preserved verbatim
- Queries should search both main and archive files

## Concurrency

- Before any write to `{slug}.md`, acquire `flock ~/.research-log/.locks/{slug}.lock`
- Different projects can be updated in parallel
- The same project must be serialized
- Locks are released automatically if the process exits
- Dashboard writes should happen during review, not ad hoc state saves

## Project Identification

Forge identifies the current project by matching the current working directory against the Project Registry in `dashboard.md`. Each registry entry maps a slug to an absolute path, and CWD is checked as a prefix match.
