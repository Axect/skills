---
name: research-log
description: Manage a research log workspace with project registration, state saves, decision logging, timeline/status queries, and weekly review workflows. Use when the user asks to initialize a research-log project, query past research activity, record an experiment or decision, save current session state, review all projects, or generally maintain a research-log workspace.
---

# Research Log

This skill organizes Forge-oriented research-log workflows around a shared storage model in `~/.research-log/`.

## Core references

Read `references/conventions.md` first when you need the storage layout, project file structure, dashboard rules, archive policy, or locking expectations.

Then load the matching workflow reference for the user request:

- Project registration or onboarding → `references/initialize.md`
- History/status/lesson queries → `references/query.md`
- Recording an experiment, debugging result, or design choice → `references/record.md`
- Weekly review, dashboard refresh, or archive scan → `references/review.md`
- Saving current session context → `references/save-state.md`

## Working rules

- Match the current working directory against the Project Registry in `~/.research-log/dashboard.md` before acting on an existing project.
- Follow the project file format defined in `references/conventions.md`.
- Acquire the per-project lock before writing project state.
- Treat dashboard updates as review-time derived data unless the workflow explicitly says otherwise.
- When a workflow requires user approval before writing, draft first and wait for approval.
