# Skills Collection

A curated collection of reusable skills for common automation, research, and infrastructure workflows.

## Overview

This repository groups a small set of focused skills into one place with consistent naming and structure.
Each skill lives in its own directory, includes a `SKILL.md` entrypoint, and may also bundle `scripts/` or `references/` depending on the workflow.

## Included skills

| Skill | Primary use | Entry point | External setup |
|---|---|---|---|
| `adversarial-review` | Stress-test a paper draft or report with a parallel persona swarm (hostile theorist, statistician, editor, citation auditor, figure critic) and produce a ranked fix list | `adversarial-review/SKILL.md` | None |
| `commit-triage` | Classify uncommitted changes into commit / failure-archive / ambiguous buckets and produce clean grouped commits with no co-author attribution | `commit-triage/SKILL.md` | None |
| `dropbox` | Upload, download, and share files through the Dropbox API | `dropbox/SKILL.md` | OAuth credentials (interactive) |
| `friendly-slide-illustrator` | Compose detailed image-generation prompts (ChatGPT Image 2.0, DALL-E, Sora, Midjourney) for friendly whiteboard-style infographic slides for lab meetings and informal talks | `friendly-slide-illustrator/SKILL.md` | None |
| `morgen` | Manage calendars, events, tasks, and tags across Google/Microsoft/iCloud/CalDAV accounts via the Morgen API | `morgen/SKILL.md` | Morgen API key |
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

### adversarial-review

No external setup required. Spawns persona subagents through the host client's Agent tool and uses `reference-search` (stdlib Python + OpenAlex) for citation and prior-art audits.

### commit-triage

No external setup required. Uses only `git` in the current repository.

### dropbox

Requires a Dropbox app and OAuth credentials stored at `~/.config/dropbox-skill/credentials.json`.

- Dependencies: `curl`, `jq`.
- Run the interactive setup flow:
  ```bash
  bash dropbox/scripts/setup.sh
  ```
  The script prompts for your app key, app secret, and an authorization code from the Dropbox OAuth URL.
  Required app permissions: `files.content.write`, `files.content.read`, `sharing.write`, `sharing.read`.

### friendly-slide-illustrator

No external setup required. The skill is purely a **prompt composer** — it produces a copy-pasteable text prompt for an image-generation model (ChatGPT Image 2.0 / gpt-image-1, DALL-E 3, Sora image, Midjourney). You bring your own image generator.

- Style block lives in `friendly-slide-illustrator/references/friendly-whiteboard-style.md` and is treated as load-bearing — drop it into prompts verbatim, do not paraphrase.
- The OSPREY v0.21 data-pipeline prompt is preserved as a worked example in `friendly-slide-illustrator/references/example-osprey-v021.md`; reuse its structure 1-for-1 for new multi-stage pipeline figures.
- Defaults: 18:9 cinematic-wide canvas, English-only on-canvas text, numbered circular badges per panel, off-white background. See the SKILL.md for tone dials (calmer / more playful / black-and-white / Korean-caption hybrid).

### morgen

Requires a Morgen API key stored at `~/.config/morgen-skill/credentials.json`.

- Dependencies: `curl`, `jq`.
- Get an API key at https://platform.morgen.so under *Developers API*.
- Run the interactive setup:
  ```bash
  bash morgen/scripts/setup.sh
  ```
  The script prompts for the API key, verifies it against `/v3/calendars/list`, and writes the credentials file with mode 600.
- All requests go to `https://api.morgen.so/v3` with the header `Authorization: ApiKey <KEY>`.
- Rate limit: 100 points per 15 minutes (list endpoints cost 10 points each).

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

- Choose `adversarial-review` to stress-test a paper draft or report before submission, simulate hostile referees, or audit citations and figures.
- Choose `commit-triage` to tidy a noisy working tree, archive failed experiments to `failure/`, and produce clean grouped commits.
- Choose `dropbox` for file upload, download, or shared-link workflows in Dropbox.
- Choose `friendly-slide-illustrator` to compose image-generation prompts for friendly whiteboard-style slides — pipeline diagrams, "how it works" figures, lab-meeting infographics — when you want the result to feel warm and casual rather than stiff and academic.
- Choose `morgen` for calendar and task management across accounts connected to Morgen (Google, Microsoft 365, iCloud, Fastmail, CalDAV) and native Morgen tasks/tags.
- Choose `paperbanana` for figures, diagrams, plots, or visual refinement tasks.
- Choose `reference-search` for literature search, citation curation, and section-level reference support when drafting reports.
- Choose `research-log` for project registration, experiment logs, status queries, and review workflows.
- Choose `research-report` for generating or revising structured report artifacts from research or experiment outputs.
- Choose `vastai` for renting GPUs, searching offers, or managing remote compute instances.

## Structure

```text
skills/
├── adversarial-review/
├── commit-triage/
├── dropbox/
├── friendly-slide-illustrator/
├── morgen/
├── paperbanana/
├── reference-search/
├── research-log/
├── research-report/
└── vastai/
```

## License

Released under the [MIT License](LICENSE) © 2026 Tae-Geun Kim.
