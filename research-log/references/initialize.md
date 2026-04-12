# Forge Workflow: Initialize a Research Project

Use this workflow when the user asks to register a new research project.

## Trigger examples
- "연구 프로젝트 등록해줘"
- "Initialize research log for this repo"
- "새 프로젝트를 research-log에 추가해줘"

## Interaction flow

Ask for the following one question at a time:
1. Project name
2. Slug
3. Repo path
4. Main goal
5. Initial sub-goals and rough percentages
6. Optional Why This Approach
7. Optional Biggest Risk

## Actions

1. Ensure these paths exist:
   - `~/.research-log/`
   - `~/.research-log/.locks/`
2. If `~/.research-log/dashboard.md` does not exist, create it using the format in `conventions.md`.
3. If the slug already exists in Project Registry, ask whether to update the project instead of overwriting blindly.
4. Create or update `~/.research-log/{slug}.md` with Compass, State, and Decision Log sections.
5. Create `~/.research-log/.locks/{slug}.lock`.
6. Update `dashboard.md` Project Registry and Active Projects.
7. Offer to pre-populate context from repository sources such as:
   - `README.md`
   - project notes
   - local agent instruction files
   - recent git history

## Initial State template

```markdown
## State
- **Session**: —
- **Last session**: —
- **Location**: —
- **Working on**: —
- **Current status**: Project initialized
- **Blocker**: None
- **Next step**: {first sub-goal from Compass}
- **Compass link**: {first sub-goal ID}
```

## Reporting

When complete, report:
- project registered
- files created or updated
- suggested next step
