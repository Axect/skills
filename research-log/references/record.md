# Forge Workflow: Record a Decision Log Entry

Use this workflow after an experiment, debugging session, design choice, or failed attempt.

## Trigger examples
- "방금 작업 decision log로 남겨줘"
- "Record this experiment"
- "실패 원인 분석까지 포함해서 기록해줘"

## Steps

1. Identify the project from `~/.research-log/dashboard.md` using the current working directory.
2. If no project matches, ask the user which project the entry belongs to.
3. Read the target project's Compass section to determine the relevant sub-goal.
4. Gather context from available sources:
   - recent git history
   - recent diffs
   - changed config files
   - logs, metrics, experiment outputs
   - current conversation context
   - optional topic hint from the user
5. Draft a Decision Log entry using the exact project-file format from `conventions.md`.
6. Present the full draft and ask for approval.
7. After approval, acquire the project lock and insert the new entry at the top of the `## Decision Log` section.
8. If needed, propose Compass percentage updates or focus changes and apply them only after approval.

## Why analysis rules

- Point 1 is mandatory: trace the causal chain.
- Point 2 is mandatory: explain the domain-specific reason.
- Point 3 is encouraged: include literature, precedent, or prior experiment evidence.
- If the cause is unknown, say so explicitly.

## Lesson rules

- Phrase the lesson as a general principle.
- Mention other registered projects if the lesson transfers.
