# Forge Workflow: Query Research Logs

Use this workflow when the user asks a question about project state, prior decisions, lessons learned, or patterns across projects.

## Trigger examples
- "왜 approach X를 버렸지?"
- "지난달에 뭐 했는지 찾아줘"
- "inverse problems 관련 교훈 모아줘"

## Steps

1. Parse the question type:
   - project-specific
   - cross-project
   - timeline
   - why/decision
   - status
2. Read `~/.research-log/dashboard.md` to identify relevant projects.
3. Read the relevant main project files and any archive files.
4. If a semantic search layer exists, merge those results with file-based findings.
5. Synthesize an answer according to the question type.

## Recommended answer formats

- Why/decision question: quote or summarize the relevant Decision Log entry
- Status question: show the State section and Compass progress
- Timeline question: provide a chronological table
- Cross-project pattern: compare evidence across projects
- How-to or lesson question: collect Lesson fields

## Citation style

Use `({project}, {date})` inside the answer.

## Follow-up

If you discover a cross-project pattern that is not yet recorded, suggest adding it during the next review.
