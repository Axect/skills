# Skills Collection

A curated collection of reusable skills for common automation, research, and infrastructure workflows.

## Overview

This repository groups a small set of focused skills into one place with consistent naming and structure.
Each skill lives in its own directory, includes a `SKILL.md` entrypoint, and may also bundle `scripts/` or `references/` depending on the workflow.

## Included skills

| Skill | Primary use | Entry point |
|---|---|---|
| `dropbox` | Upload, download, and share files through the Dropbox API | `dropbox/SKILL.md` |
| `paperbanana` | Generate academic diagrams and statistical plots with the PaperBanana CLI | `paperbanana/SKILL.md` |
| `research-log` | Manage research-log workflows such as initialization, querying, review, and state capture | `research-log/SKILL.md` |
| `research-report` | Create or revise structured research and experiment reports with plots, manifests, and validation helpers | `research-report/SKILL.md` |
| `vastai` | Search, create, and manage Vast.ai GPU cloud instances | `vastai/SKILL.md` |

## Quick start

1. Pick the skill that matches the user's task.
2. Open that skill's `SKILL.md` first.
3. Follow any prerequisite checks before running scripts or commands.
4. Use bundled `scripts/` for executable helpers and `references/` for deeper guidance.
5. For client-specific installation and linking, see `CLIENT_SETUP.md`.

## Which skill to use?

- Choose `dropbox` for file upload, download, or shared-link workflows in Dropbox.
- Choose `paperbanana` for figures, diagrams, plots, or visual refinement tasks.
- Choose `research-log` for project registration, experiment logs, status queries, and review workflows.
- Choose `research-report` for generating or revising structured report artifacts from research or experiment outputs.
- Choose `vastai` for renting GPUs, searching offers, or managing remote compute instances.

## Structure

```text
skills/
├── dropbox/
├── paperbanana/
├── research-log/
├── research-report/
└── vastai/
```
