# Forge Workflow: Save Current State

Use this workflow when the user asks to save working context, or before ending a work session.

## Trigger examples
- "현재 상태 저장해줘"
- "Update research-log state"
- "세션 상태 남겨줘"

## Steps

1. Read `~/.research-log/dashboard.md`.
2. Match the current working directory against Project Registry.
3. If no project matches, explain briefly that the current directory is not registered.
4. Acquire the project lock and read the current project file.
5. Read the current `## State` section and preserve the old `Session` as the new `Last session`.
6. Generate a concise new State section from the recent work:
   - Session
   - Last session
   - Location
   - Working on
   - Current status
   - Blocker
   - Next step
   - Compass link
7. Replace only the `## State` section.
8. Confirm the update.

## Notes

- Keep each field to one or two sentences.
- Do not append multiple state snapshots.
- State is a quick context-recovery summary.
