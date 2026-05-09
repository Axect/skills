# Changelog

All notable changes to this repository are documented in this file.

## 2026-05-09

### Added
- Added the `scienceplot-py` skill that writes a Python matplotlib plot script following the user's `scienceplots` (`science`+`nature`) lab template (canonical source: `~/Socialst/Templates/PyPlot_Template/pq_plot.py`). Style invariants are load-bearing and explicitly enumerated in `SKILL.md`: `import scienceplots` (kept even though linters flag it as unused — the styles register by import side-effect), `with plt.style.context(["science", "nature"]):`, `pparam = dict(...)` + `ax.set(**pparam)`, `ax.autoscale(tight=True)`, raw-string LaTeX, and `dpi=300, bbox_inches='tight'` savefig. Note that the savefig DPI was lowered from the upstream template's 600 to 300 by user request — the skill's invariant has intentionally diverged from `pq_plot.py`. Bundles four reference templates (single line, multi-line + legend, scatter / errorbar, multi-panel subplots) and a parquet / CSV / NumPy `.npy` / `.npz` data-loader cheat sheet at `references/data_loaders.md`. The skill writes the `.py` only and never executes it; the user runs it themselves (typically `uv run`).
- Added the `xkcd-py` skill — the same structural shape as `scienceplot-py` but with `with plt.xkcd():` style context, wider canvas (`figsize=(10, 6)`), and no `scienceplots` import (since `plt.xkcd()` is built into matplotlib). Mirrors `~/Socialst/Templates/PyPlot_Template/xkcd_plot.py`. Same four reference templates and the same `references/data_loaders.md`. `SKILL.md` notes that the Humor Sans / xkcd Script / Comic Neue font fallback warning emitted by matplotlib is informational; the plot still renders, and the skill does not try to install fonts.

### Changed
- Updated `README.md` to list `scienceplot-py` and `xkcd-py` in the skill table.
- Updated `CLIENT_SETUP.md` to include both new skills in the current-skill-directories list, both install loops (Claude Code and Codex), and the per-skill prerequisites section. The Forge "Option 2" tree example was also caught up to skills it had been silently missing (`md2pdf-typora`, `overleap`, `wide-slide-illustrator`) and is now alphabetically complete.

## 2026-05-04

### Added
- Added the `md2pdf-typora` skill for converting Markdown to PDF that visually matches Typora's Whitey-theme export. Pipeline: pandoc (MD → standalone HTML) → patched HTML (inline Whitey CSS, MathJax SVG forced via `sed` rewrite of pandoc's default CHTML reference, print-layout overrides for A4, inline-math `nowrap`, TOC repositioned after the first body `<h1>`) → Chrome headless `--print-to-pdf`. Bundles the Whitey CSS at `md2pdf-typora/typora-whitey.css`. Hardened against a few load-bearing pandoc quirks: HR-then-`##` heading pairs are normalized so they are not fused into a stray table, and the markdown reader is invoked with `-f markdown-yaml_metadata_block+tex_math_dollars` so a Korean blockquote like `> **도메인**: 물리학` does not raise a YAML parse error.
- Added `## Pre-flight Dependency Smoke Test` section to `vastai/SKILL.md` and a matching detailed workflow + troubleshooting row to `vastai/references/python-setup.md`. Documents the late-bound import trap (a script that imports `scipy.optimize.curve_fit` inside a function body passes `python -c "import script"` but fails when the codepath fires mid-batch, cascade-failing every pueue dependent). Recommends one full smoke invocation per distinct script type before queuing the batch.

### Changed
- Updated `README.md` to include `md2pdf-typora` in the skill table, the "Skill requirements & setup" section (pandoc + Chromium prerequisites, MathJax SVG and Google Fonts CDN access notes), the "Which skill to use?" guidance, and the directory tree.
- Updated `CLIENT_SETUP.md` to list `md2pdf-typora` in the skill directories and the Claude Code / Codex install loops, and added a `Per-skill prerequisites` entry covering pandoc install commands per OS, Chromium discovery, network requirements for MathJax + Google Fonts, and a pandoc smoke-test.

## 2026-04-21

### Added
- Added the `morgen` skill wrapping the Morgen API v3 (docs.morgen.so). Covers calendars (`list`, `update`), events (`list`, `create`, `update`, `delete` with `seriesUpdateMode`), Morgen tasks (`list`, `get`, `create`, `update`, `move`, `close`, `reopen`, `delete`), integrations (`accounts`, `providers`), and tags (`list`, `get`, `create`, `update`, `delete`). Uses `ApiKey` header auth with credentials stored at `~/.config/morgen-skill/credentials.json` (mode 600), a sourceable `auth.sh` with unified error handling (exit codes 2/3/4/5/6 for missing creds / auth / 404 / other / 429), and references in `references/api-reference.md` and `references/examples.md`.
- Added `morgen/scripts/todos.sh`, a local-cached TODO wrapper over the Morgen Tasks API. Manual `sync` hits `/tasks/list` once; reads (`list`, `today`, `overdue`, `show`) serve from the local cache at `~/.cache/morgen-skill/todos.json` at 0 rate-limit cost; writes (`add`, `done`, `reopen`, `delete`) hit the API at 1 point each and patch the cache in place. Supports short-ID prefix resolution, stale-cache warnings via `MORGEN_STALE_SECONDS`, and filtering by `--tag` / `--priority` / `--all`. No automatic sync and no conflict resolution — next `sync` wins.

### Changed
- Extended `morgen/scripts/setup.sh` with non-interactive modes (`--stdin`, `--key`, `--help`) so a skill orchestrator (e.g. Claude Code) can run setup without a TTY after the user pastes their API key into chat. Original interactive mode (no args) is unchanged. `SKILL.md` now documents the full skill-orchestrated setup flow, including the security caveat around argv exposure and the rule that Claude must never echo the key back or run setup unprompted.

## 2026-04-18

### Added
- Added the `commit-triage` skill for classifying uncommitted changes into commit / `failure/`-archive / ambiguous buckets, with a no-`Co-Authored-By` rule, a named-paths-only staging rule, and a no-auto-push rule. Includes `references/classification.md` for per-path heuristics and `references/failure-layout.md` for the `failure/<YYYY-MM-DD-slug>/` archive convention and `NOTES.md` template.
- Added the `adversarial-review` skill that spawns a parallel persona swarm (Hostile Theorist, Experimentalist, Statistician, Journal Editor, Citation Auditor, Figure Critic) against a draft and synthesizes their findings into a ranked fix list. Outputs land under `outputs/review/<YYYY-MM-DD-HHMM>/` next to the draft. Includes `references/personas.md` (per-persona briefs and output contract), `references/meta-editor.md` (dedup, severity ranking, defense authoring), and `references/integration.md` (wiring with `reference-search`, `research-report`, Korean translation, and `commit-triage`).
- Extended `.gitignore` to exclude `outputs/` (skill run artifacts) while explicitly preserving `failure/` in history to match the `commit-triage` skill's archive convention.

### Changed
- Updated `README.md` to include the `reference-search` skill in the skill table, directory structure, and "Which skill to use?" guidance.
- Added a `Skill requirements & setup` section to `README.md` summarizing the external CLIs, API keys, and credential files each skill needs before first use (dropbox, paperbanana, vastai, plus "no setup" notes for the rest).
- Updated `CLIENT_SETUP.md` to list `adversarial-review`, `commit-triage`, and `reference-search` in the skill directories, install loops, and repository structure tree.
- Added a `Per-skill prerequisites` section to `CLIENT_SETUP.md` with step-by-step one-time setup instructions for `dropbox`, `paperbanana`, and `vastai`, and explicit "no setup required" confirmation for `adversarial-review`, `commit-triage`, `reference-search`, `research-log`, and `research-report`.
- Extended the `CLIENT_SETUP.md` troubleshooting checklist with a runtime-failure entry pointing back to the prerequisites section.

## 2026-04-15

### Added
- Added the `reference-search` skill with OpenAlex-based literature search guidance, query pattern references, and a helper script for markdown or JSON reference curation.

### Changed
- Updated the `research-report` skill to support optional literature and citation workflows through the new `reference-search` companion skill.
- Updated Forge setup guidance in `CLIENT_SETUP.md` to require copying real skill directories into `~/forge/skills` instead of using symlinks, because Forge may not detect symlinked skills reliably.

## 2026-04-14

### Added
- Added `vastai/references/python-setup.md` with guidance for setting up remote Python environments on Vast.ai instances using `uv`, including CUDA-aware PyTorch installation, verification steps, and common pitfalls.
- Added the `research-report` skill with report templates, plot manifest tooling, report version tracking, artifact validation helpers, and reusable plot templates for research and experiment reporting.
- Added `CLIENT_SETUP.md` with client-specific installation and linking guidance for Claude Code, Codex, and Forge, including the local `~/forge/skills` setup pattern.

### Changed
- Expanded the Vast.ai skill guide with a dedicated Python setup section and linked the new remote setup reference from the main skill document.
- Updated the Vast.ai skill title and introduction to match the upstream skill source.
- Updated the repository README to include the new `research-report` skill in the index, usage guidance, and directory structure.
- Updated the repository README quick start section to link to `CLIENT_SETUP.md` for client-specific setup.

## 2026-04-13

### Added
- Added the initial skills collection repository structure and normalized skill layout across included skills.
- Added `.gitignore` entries to reduce the risk of committing local secrets and generated artifacts.
- Added a repository-level `README.md` describing the collection and its included skills.
- Added a skill index table to the README for faster skill discovery.

### Changed
- Restricted the Dropbox skill credential path handling.
- Polished and refined the repository README for clearer usage guidance and structure.
