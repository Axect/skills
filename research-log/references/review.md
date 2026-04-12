# Forge Workflow: Weekly Review

Use this workflow for a weekly project review across all registered research efforts.

## Trigger examples
- "주간 research review 해줘"
- "Run research-log review"
- "dashboard 새로 정리해줘"

## Phases

### 1. Load all projects
- Read `~/.research-log/dashboard.md`
- Parse Project Registry
- Read each `{slug}.md`

### 2. Compass alignment
For each project:
- Read Decision Log entries from the last 2 weeks
- Map entries to Compass sub-goals
- Detect drift if more than 40% of recent entries fall outside the current focus
- Propose progress percentage updates
- Apply only after approval

### 3. Cross-project pattern scan
- Collect recent Decision Log entries across projects
- Look for shared failure modes, transferable lessons, or contradictory approaches
- Present proposed observations with evidence
- Add them to dashboard only after approval

### 4. Dashboard regeneration
Rebuild `dashboard.md` from project data:
- Active Projects from State + Compass
- Timeline from recent Decision Log headers
- Preserve Project Registry
- Preserve approved Cross-Project Observations

### 5. Archive management
For each project:
- Count Decision Log entries and total file lines
- If entries exceed 30 or lines exceed 500, propose archiving entries older than 6 months
- Move approved entries to `{slug}-decisions-{year}.md`

## Reporting

Summarize:
- alignment status per project
- cross-project patterns found
- dashboard regeneration result
- archive actions taken
- next recommended review date
