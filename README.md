# Skills Collection

A curated collection of reusable skills for common automation, research, and infrastructure workflows.

## Overview

This repository groups a small set of focused skills into one place with consistent naming and structure.
Each skill lives in its own directory, includes a `SKILL.md` entrypoint, and may also bundle `scripts/` or `references/` depending on the workflow.

## Included skills

| Skill | Primary use | Entry point | External setup |
|---|---|---|---|
| `dropbox` | Upload, download, and share files through the Dropbox API | `dropbox/SKILL.md` | OAuth credentials (interactive) |
| `paperbanana` | Generate academic diagrams and statistical plots with the PaperBanana CLI | `paperbanana/SKILL.md` | `paperbanana` CLI + API keys |
| `reference-search` | Search and curate academic references via OpenAlex for reports, claims, and section-level citation support | `reference-search/SKILL.md` | None (stdlib Python) |
| `research-log` | Manage research-log workflows such as initialization, querying, review, and state capture | `research-log/SKILL.md` | `~/.research-log/` workspace (auto) |
| `research-report` | Create or revise structured research and experiment reports with plots, manifests, and validation helpers | `research-report/SKILL.md` | None (stdlib Python) |
| `vastai` | Search, create, and manage Vast.ai GPU cloud instances | `vastai/SKILL.md` | `vastai` CLI + API key |

## Quick start

1. Install the skills you want with your preferred client — see `CLIENT_SETUP.md` for Claude Code, Codex, and Forge instructions.
2. Complete any **external setup** required by the skill (see the next section) before using it.
3. Open that skill's `SKILL.md` first for workflow details.
4. Use bundled `scripts/` for executable helpers and `references/` for deeper guidance.

## Skill requirements & setup

Several skills depend on external CLIs, API keys, or credential files. Install and configure them **once per machine** before invoking the skill.

### dropbox

Requires a Dropbox app and OAuth credentials stored at `~/.config/dropbox-skill/credentials.json`.

- Dependencies: `curl`, `jq`.
- Run the interactive setup flow:
  ```bash
  bash dropbox/scripts/setup.sh
  ```
  The script prompts for your app key, app secret, and an authorization code from the Dropbox OAuth URL.
  Required app permissions: `files.content.write`, `files.content.read`, `sharing.write`, `sharing.read`.

### paperbanana

Requires the `paperbanana` CLI and an env file at `~/.config/paperbanana/env`.

- Install the `paperbanana` CLI per its upstream instructions, then verify with `paperbanana --help`.
- Create the env file with your API key and default VLM model:
  ```bash
  mkdir -p ~/.config/paperbanana
  cat > ~/.config/paperbanana/env << 'EOF'
  export GOOGLE_API_KEY="your-google-api-key"
  export VLM_MODEL="gemini-3-flash-preview"
  EOF
  ```
- Or run `paperbanana setup` for the interactive wizard.
- The skill always sources this env file before running commands, so do **not** hardcode keys elsewhere.

### reference-search

No external setup required. Uses Python standard library only and calls the public OpenAlex API.

- Optional: pass `--email` to the helper for OpenAlex's polite pool.
- Helper script: `reference-search/scripts/openalex_search.py`.

### research-log

No external setup required. The skill creates and manages `~/.research-log/` on first use.

- The workspace holds per-project logs, decision entries, and the dashboard.
- See `research-log/references/conventions.md` for the storage layout.

### research-report

No external setup required. Uses Python standard library only.

- Helper scripts live in `research-report/scripts/` (`build_plot_manifest.py`, `record_report_version.py`, `validate_artifacts.py`).
- Designed to be used from inside a project directory that already contains experiment outputs.

### vastai

Requires the `vastai` CLI and a Vast.ai API key.

- Install the CLI:
  ```bash
  uv pip install vastai   # or: pip install vastai
  ```
- Get your API key from https://cloud.vast.ai/cli/ and register it:
  ```bash
  vastai set api-key YOUR_API_KEY
  ```
  The key is stored at `~/.vast_api_key`. Never commit or share it.
- Verify access: `vastai show user`.

## Which skill to use?

- Choose `dropbox` for file upload, download, or shared-link workflows in Dropbox.
- Choose `paperbanana` for figures, diagrams, plots, or visual refinement tasks.
- Choose `reference-search` for literature search, citation curation, and section-level reference support when drafting reports.
- Choose `research-log` for project registration, experiment logs, status queries, and review workflows.
- Choose `research-report` for generating or revising structured report artifacts from research or experiment outputs.
- Choose `vastai` for renting GPUs, searching offers, or managing remote compute instances.

## Structure

```text
skills/
├── dropbox/
├── paperbanana/
├── reference-search/
├── research-log/
├── research-report/
└── vastai/
```
