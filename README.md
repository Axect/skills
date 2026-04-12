# Skills Collection

A curated collection of reusable skills for common automation, research, and infrastructure workflows.

## Overview

This repository groups a small set of focused skills into one place with consistent naming and structure.
Each skill lives in its own directory, includes a `SKILL.md` entrypoint, and may also bundle `scripts/` or `references/` depending on the workflow.

## Included skills

- `dropbox` — upload, download, and share files through the Dropbox API
- `paperbanana` — generate academic diagrams and statistical plots with the PaperBanana CLI
- `research-log` — manage research-log workflows such as initialization, querying, review, and state capture
- `vastai` — search, create, and manage Vast.ai GPU cloud instances

## Quick start

1. Pick the skill that matches the user's task.
2. Open that skill's `SKILL.md` first.
3. Follow any prerequisite checks before running scripts or commands.
4. Use bundled `scripts/` for executable helpers and `references/` for deeper guidance.

## Which skill to use?

- Choose `dropbox` for file upload, download, or shared-link workflows in Dropbox.
- Choose `paperbanana` for figures, diagrams, plots, or visual refinement tasks.
- Choose `research-log` for project registration, experiment logs, status queries, and review workflows.
- Choose `vastai` for renting GPUs, searching offers, or managing remote compute instances.

## Structure

```text
skills/
├── dropbox/
├── paperbanana/
├── research-log/
└── vastai/
```
