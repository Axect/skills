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
| `wide-slide-illustrator` | Compose detailed image-generation prompts (ChatGPT Image 2.0, DALL-E, Sora, Midjourney) for wide cinematic 18:9 multi-panel infographic slides — six style variants: Friendly Whiteboard, Editorial Magazine, Engineering Blueprint, Swiss Minimalist, Dark Tech / Neon, Scientific Poster | `wide-slide-illustrator/SKILL.md` | None |
| `md2pdf-typora` | Convert Markdown to PDF that mimics Typora's Whitey-theme export (pandoc + Chrome headless, MathJax SVG, Korean serif fallback) | `md2pdf-typora/SKILL.md` | `pandoc` + Chrome/Chromium |
| `morgen` | Manage calendars, events, tasks, and tags across Google/Microsoft/iCloud/CalDAV accounts via the Morgen API | `morgen/SKILL.md` | Morgen API key |
| `overleap` | Bidirectional real-time sync between an Overleaf project and a local directory via the `overleap` Node.js CLI | `overleap/SKILL.md` | `overleap` CLI + Overleaf session cookie |
| `paperbanana` | Generate academic diagrams and statistical plots with the PaperBanana CLI | `paperbanana/SKILL.md` | `paperbanana` CLI + API keys |
| `reference-search` | Search and curate academic references via OpenAlex for reports, claims, and section-level citation support | `reference-search/SKILL.md` | None (stdlib Python) |
| `research-log` | Manage research-log workflows such as initialization, querying, review, and state capture | `research-log/SKILL.md` | `~/.research-log/` workspace (auto) |
| `research-report` | Create or revise structured research and experiment reports with plots, manifests, and validation helpers | `research-report/SKILL.md` | None (stdlib Python) |
| `scienceplot-py` | Generate a Python matplotlib plot script following the user's mandatory `scienceplots` (`science`+`nature`) lab template, with parquet / CSV / NumPy data sources and four plot variants (single line, multi-line, scatter/errorbar, subplots). Writes the `.py` only — does not execute it. | `scienceplot-py/SKILL.md` | `matplotlib`, `scienceplots`, plus `pandas` / `numpy` as needed (in the user's runtime env) |
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

### wide-slide-illustrator

No external setup required. The skill is purely a **prompt composer** — it produces a copy-pasteable text prompt for an image-generation model (ChatGPT Image 2.0 / gpt-image-1, DALL-E 3, Sora image, Midjourney). You bring your own image generator.

- Six reusable style variants — all share the same 5-panel 18:9 composition and English-only-on-canvas guard rail; they differ only in surface treatment.
  - **Friendly Whiteboard** (warm sketch, lab-meeting feel): `wide-slide-illustrator/references/friendly-whiteboard-style.md`; example `example-osprey-v021.md`.
  - **Editorial Magazine** (Quanta / NYT feature spread): `wide-slide-illustrator/references/editorial-magazine-style.md`; example `example-osprey-editorial.md`. Sub-patterns: STATUS-BADGE / PULL-QUOTE / CONNECTION-LINE.
  - **Engineering Blueprint** (NASA / SpaceX schematic, monospace + cyan-on-navy): `wide-slide-illustrator/references/engineering-blueprint-style.md`. Sub-patterns: DIMENSION-LINE / TERMINAL-NODE / STAGE-BOX.
  - **Swiss Minimalist** (Müller-Brockmann typography over methodology content; orthodox title-poster mode opt-in via tone dial): `wide-slide-illustrator/references/swiss-minimalist-style.md`. Sub-patterns: PROMINENT-NUMBER / PRIMARY-PLOT / GRID-CARD.
  - **Dark Tech / Neon** (Linear / Anthropic / Cursor keynote, charcoal + neon glow): `wide-slide-illustrator/references/dark-tech-neon-style.md`. Sub-patterns: NEON-CHIP / GLOW-PATH / MONOSPACE-LABEL.
  - **Scientific Poster** (Phys Rev / Nature published figure, panel labels (a)–(e), running FIG. N. caption): `wide-slide-illustrator/references/scientific-poster-style.md`. Sub-patterns: PANEL-LETTER / FIG-CAPTION / AXIS-LABEL.
- Style blocks are load-bearing — drop them into prompts verbatim, do not paraphrase. Always include the variant's "hard negatives" bullet so cues from sibling variants don't leak through (lesson learned from the editorial v1 → v2 hardening pass).
- Defaults: 18:9 cinematic-wide canvas, English-only on-canvas text, numbered marker per panel. See SKILL.md for tone dials per variant (calmer / more playful / Bauhaus-clean / orthodox-Swiss-poster / Korean-caption hybrid, etc.).

### md2pdf-typora

Requires `pandoc` and a Chromium-family browser (`google-chrome-stable`, `google-chrome`, or `chromium`) on `PATH`. The Whitey theme CSS bundled at `md2pdf-typora/typora-whitey.css` is used inline; no separate install.

- Install pandoc with your package manager:
  ```bash
  # Arch
  sudo pacman -S pandoc
  # Debian / Ubuntu
  sudo apt install pandoc
  # macOS
  brew install pandoc
  ```
- A working Chromium build is required because the pipeline renders the patched HTML to PDF via `--headless=new --print-to-pdf`.
- Math is rendered via MathJax SVG (`tex-svg-full.js`) loaded from CDN — Chrome needs network access during the conversion. The skill rewrites pandoc's default CHTML reference to SVG to avoid silent missing-glyph fallbacks (e.g. `\phi` rendering as `□`).
- Body fonts (IBM Plex Serif Latin, MaruBuri Korean, Roboto Slab headings, JetBrains Mono code) are also fetched from Google Fonts CDN.
- Optional flags: `--dropbox [subfolder]` mirrors the produced PDF to `~/Dropbox/Magi/[subfolder]/`; `--send-telegram` posts it via the Telegram skill if configured.

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

### overleap

Requires the [`overleap`](https://github.com/Axect/overleap) Node.js CLI and a valid Overleaf session cookie.

- Install:
  ```bash
  npm install -g overleap
  ```
  Requires Node.js >= 18 and `git` (the dependency `socket.io-client` is fetched from a GitHub fork).
- Verify the binary is on `PATH`:
  ```bash
  command -v overleap && overleap --help | head -5
  ```
- Save your Overleaf session cookie into a per-project `.env` file with the bundled helper:
  ```bash
  bash overleap/scripts/init_env.sh <dir> <<< 'overleaf_session2=...'
  ```
  The script writes `<dir>/.env` with mode `0600` and ensures `.env` is in `<dir>/.gitignore`. Get the cookie from browser DevTools → Application → Cookies → `overleaf.com` → copy the full cookie string (or just the `overleaf_session2` value). See `overleap/references/cookie-setup.md` for full instructions and refresh procedure.
- Smoke-test:
  ```bash
  cd <dir> && overleap projects
  ```
- `overleap sync` is a long-running daemon — never invoke it as a foreground Bash call from Claude. Use a separate terminal, `pueue`, or `run_in_background` (`overleap/references/long-running-patterns.md` covers all three).

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
- Choose `wide-slide-illustrator` to compose image-generation prompts for wide cinematic 18:9 multi-panel infographic slides — pipeline diagrams, "how it works" figures, hero figures, paper figures, keynote backdrops. Six style variants by audience and target medium: Friendly Whiteboard (lab meeting), Editorial Magazine (Quanta / NYT paper hero), Engineering Blueprint (technical schematic), Swiss Minimalist (typographic poster on methodology content), Dark Tech / Neon (AI-lab keynote backdrop), Scientific Poster (Phys Rev / Nature journal figure).
- Choose `md2pdf-typora` to convert a Markdown report or note (especially one with LaTeX math, Korean text, and embedded plots) into a print-ready PDF that visually matches Typora's Whitey-theme export.
- Choose `morgen` for calendar and task management across accounts connected to Morgen (Google, Microsoft 365, iCloud, Fastmail, CalDAV) and native Morgen tasks/tags.
- Choose `overleap` to edit Overleaf projects locally with real-time bidirectional sync — local edits propagate to Overleaf and vice versa, so Claude can edit `.tex` files and collaborators see them on Overleaf instantly.
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
├── wide-slide-illustrator/
├── md2pdf-typora/
├── morgen/
├── overleap/
├── paperbanana/
├── reference-search/
├── research-log/
├── research-report/
└── vastai/
```

## License

Released under the [MIT License](LICENSE) © 2026 Tae-Geun Kim.
