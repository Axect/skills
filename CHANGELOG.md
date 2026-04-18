# Changelog

All notable changes to this repository are documented in this file.

## 2026-04-18

### Added
- Added the `commit-triage` skill for classifying uncommitted changes into commit / `failure/`-archive / ambiguous buckets, with a no-`Co-Authored-By` rule, a named-paths-only staging rule, and a no-auto-push rule. Includes `references/classification.md` for per-path heuristics and `references/failure-layout.md` for the `failure/<YYYY-MM-DD-slug>/` archive convention and `NOTES.md` template.
- Added the `adversarial-review` skill that spawns a parallel persona swarm (Hostile Theorist, Experimentalist, Statistician, Journal Editor, Citation Auditor, Figure Critic) against a draft and synthesizes their findings into a ranked fix list. Outputs land under `outputs/review/<YYYY-MM-DD-HHMM>/` next to the draft. Includes `references/personas.md` (per-persona briefs and output contract), `references/meta-editor.md` (dedup, severity ranking, defense authoring), and `references/integration.md` (wiring with `reference-search`, `research-report`, Korean translation, and `commit-triage`).

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
