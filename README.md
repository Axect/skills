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

## How to navigate

- Start with each skill's `SKILL.md` file for the main workflow and trigger guidance.
- Use bundled `scripts/` directories for executable helpers.
- Use bundled `references/` directories for deeper task-specific guidance.

## Structure

```text
skills/
├── dropbox/
├── paperbanana/
├── research-log/
└── vastai/
```
