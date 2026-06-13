# Changelog

All notable changes to this repository are documented in this file.

## 2026-06-13

### Added
- Added the `research-backup` skill for backing up the report directories research projects keep outside git (`outputs/`, `results/`, `report/`, `reports/`) into the locally synced Dropbox folder. The skill writes under `BACKUP_ROOT` (default `~/Dropbox/ResearchBackup/`) with `rsync` and lets the Dropbox daemon handle the upload, so no API credentials are involved; sources are mirrored relative to `SCAN_ROOT` (default `~/Documents/Project`), preserving the `<category>/<project>/<dir>` layout so same-named projects in different categories never collide. `scripts/discover.sh` scans for candidate directories and classifies each against git (`ignored` / `untracked` / `no-git` are candidates; directories with git-tracked files are reported as `TRACKED` and never registered), comparing the result with a registry at `~/.config/research-backup/registry`; `--register` appends the new candidates. `scripts/backup.sh` syncs registry entries (all of them via `--all`, or a case-insensitive path-substring filter), with `--dry-run` as the status/preview mode. Backups are deliberately additive: `--delete` is never passed, so files removed locally stay in Dropbox, and the SKILL.md forbids adding it without explicit user confirmation. Config (`SCAN_ROOT`, `BACKUP_ROOT`, `DIR_NAMES`, `RSYNC_EXCLUDES`) and registry are auto-created on first run; `RESEARCH_BACKUP_CONFIG_DIR` overrides the location for testing. Entry point: `research-backup/SKILL.md`. Requires `rsync` plus the official Dropbox client syncing this machine. Distinct from the `dropbox` skill, which does one-off file upload/download/share through the HTTP API.

### Changed
- Updated `README.md` across the four standard touchpoints (skill table, "Skill requirements & setup" section, "Which skill to use?" picker, directory tree) and `CLIENT_SETUP.md` across its five touchpoints (skill directory list, Claude Code and Codex install loops, Forge Option 2 tree, per-skill prerequisites section) to cover `research-backup`. Also backfilled `hep-rumor-mill` into all five `CLIENT_SETUP.md` touchpoints, where it had been missing since the skill was added.

## 2026-06-09

### Changed
- Extended the `academic-jobs` skill to search the **InspireHEP jobs board** (`inspirehep.net/jobs`) alongside Academic Jobs Online. `ajo fetch` now hits both boards with the same keyword presets by default and merges the results deadline-sorted. InspireHEP is fetched through its public JSON API (`/api/jobs`) with a server-side `status=open` filter and the structured `deadline_date` used directly, so no per-posting detail scrape is needed (the AJO `--fast` flag does not apply to it). The existing preset filters are reused: `position_types` is matched against the InspireHEP `ranks` (e.g. `postdoc` → `POSTDOC`) as well as the AJO Position Type, and `countries` is matched against the institution string plus the InspireHEP `regions`. New `--source ajo|inspire|both` flag on `fetch`/`list`/`show`/`mark-seen` and a new per-preset `sources` field (`ajo config --set-preset NAME --sources ajo,inspire`, default both) select which boards to use. `ajo show {id} --source inspire` additionally returns the cleaned job description and contact email from the API record.
- Migrated the local SQLite store to key postings by the composite `(source, id)` because AJO and InspireHEP use overlapping integer ids. Bumped `schema_version` to `2`; a pre-existing v1 database (AJO-only, no `source` column) is migrated in place on first open, tagging all existing rows as `source='ajo'`. Added `ajo/inspire.py` (the InspireHEP fetch module, mirroring `fetch.search_valid`'s shape so the DB and rendering layers are reused unchanged). `fetch` stats are now reported per board under `stats.per_source`, and the table/JSON output carries a `source` column.
- Updated `academic-jobs/SKILL.md`, its three reference docs (`fetch.md`, `presets.md`, `schema.md`), and `academic-jobs/README.md` to document the two-board model; updated the repository `README.md` across the four standard touchpoints (skill table, requirements section, "Which skill to use?" picker, directory tree) to note the InspireHEP integration.

## 2026-06-08

### Added
- Added the `academic-jobs` skill for fetching **valid** (still-open, application-deadline-not-passed) academic job postings from Academic Jobs Online (academicjobsonline.org, AJO). The skill wraps a bundled `ajo` CLI that manages field presets (each preset bundles `keywords`, plus optional `position_types` and `countries` substring filters), fetches candidate postings, and judges validity from each posting's **detail page** rather than the list page: the effective deadline is the firm `Appl Deadline` if present, else the `listed until` date, so postings with no list-page deadline are not silently treated as open. Postings are stored in a local SQLite DB and flagged new since the last `mark-seen`. Commands: `ajo config` (presets), `ajo fetch` (with `--preset`/`--keyword`, `--fast` to skip detail pages, `--include-rolling` for no-deadline postings), `ajo list [--valid] [--new]`, `ajo show {id}`, `ajo mark-seen --all`, `ajo prune`. The CLI is a uv project (`pyproject.toml` + `uv.lock`, deps `requests` + `beautifulsoup4`); `uv run --project <skill-dir> ajo …` auto-provisions its environment on first run. State lives under `~/.local/share/academic-jobs/` (`jobs.db` + `config.toml`, override via `AJO_DATA_DIR`); first run seeds a default `physics-ml` preset. Etiquette is built in: one polite session with a real User-Agent, an inter-request delay, and a per-run detail-fetch cap reported in `stats`. Bundles `ajo/` (cli, config, db, fetch) and three reference docs (`fetch.md`, `presets.md`, `schema.md`). Entry point: `academic-jobs/SKILL.md`. Requires `uv`; no API keys.

### Changed
- Extended `.gitignore` to ignore per-skill uv virtualenvs (`**/.venv/`), since `academic-jobs` ships a uv project that materializes a local `.venv/` on use.
- Updated `README.md` across the four standard touchpoints (skill table, "Skill requirements & setup" section, "Which skill to use?" picker, directory tree) and `CLIENT_SETUP.md` across its five touchpoints (skill directory list, Claude Code and Codex install loops, Forge Option 2 tree, per-skill prerequisites section) to cover `academic-jobs`, including its uv-project auto-install behavior, the detail-page validity model, and AJO request etiquette.

## 2026-06-04

### Added
- Added the `journal-club-review` skill for turning an arXiv id/URL, a PDF, or raw text/markdown into a journal-club-style paper presentation. The output is nine ordered sections (TL;DR, The Problem, Key Idea, How It Works, Key Results, Why It Matters, Strengths/Limitations/Open Questions, Discussion Questions, Takeaways) designed to help a reading group understand and discuss a paper, deliberately not a referee report (no scores, no accept/reject, no severity tags). Every claim is grounded in the source with section/equation/figure citations, all math is rendered as LaTeX (`$...$` / `$$...$$`), and the output language auto-matches the source paper unless the user requests otherwise. Two optional friendly-whiteboard infographics (a `method` figure and a `results` figure) are generated in parallel via the bundled `codex` `image_generation` tool, reusing the visual style from `wide-slide-illustrator`. The skill is self-contained and does not require the arXiv Explorer app: it ports that project's journal-club section design and figure briefs into prompt form, and Claude does the analysis. Ingestion is handled by `scripts/extract_text.py`, which carries a PEP 723 inline-dependency header (`pdfplumber`, `httpx`, `feedparser`) so `uv run` auto-provisions its environment, writes `reviews/<slug>/source.md`, and prints a JSON metadata summary. Bundles three reference docs (`section-pipeline.md`, `figure-generation.md`, `style-and-math.md`). Entry point: `journal-club-review/SKILL.md`. Requires `uv`; figures additionally need a logged-in bundled `codex` runtime (ChatGPT OAuth), without which the review still renders text-only. Distinct from `workshop-paper-review` (OpenReview referee report) and `adversarial-review` (hostile pre-submission audit); the description cross-links all three to avoid trigger overlap.

### Changed
- Updated `README.md` across the four standard touchpoints (skill table, "Skill requirements & setup" section, "Which skill to use?" picker, directory tree) and `CLIENT_SETUP.md` across its five touchpoints (skill directory list, Claude Code and Codex install loops, Forge Option 2 tree, per-skill prerequisites section) to cover `journal-club-review`, including its PEP 723 auto-install behavior and the optional codex-runtime requirement for figures.

## 2026-06-03

### Added
- Added the `research-portal` skill for building and serving a local MkDocs Material site over an existing folder of Typora/markdown notes. `docs_dir` points at the notes folder so original files are never modified. The skill scaffolds a `mkdocs.yml` with a project-grouped sidebar (mkdocs-literate-nav), full LaTeX rendering via pymdownx.arithmatex + MathJax 3, and safe project tagging and renaming operations that repair image links after a rename. `uv` is the only prerequisite; mkdocs-material and mkdocs-literate-nav are auto-installed by the scaffold script into an isolated environment on first run. Entry point: `research-portal/SKILL.md`.
- Added the `proton-mail` skill for reading and searching Proton Mail through a locally running Proton Bridge. The skill connects read-only over STARTTLS IMAP on 127.0.0.1; it does not send, delete, or move messages. Bridge credentials (bridge username and bridge-specific IMAP password, not the main account password) are stored in `~/.proton-imap` (chmod 600). Entry point: `proton-mail/SKILL.md`. Requires Proton Bridge running locally before invocation.
- Added the `workshop-paper-review` skill for producing OpenReview-ready peer reviews of ICML/NeurIPS/ICLR workshop submissions (4-8 page papers). The workflow covers PDF intake, evidence-grounded drafting with direct PDF citations, anti-anchoring score calibration (scores are assigned after drafting, not before), a parallel fact-check pass against the source PDF, AI-writing-pattern removal, and a Korean-draft to English-submission path for bilingual workflows. No external setup: PDF reading uses the local file, no API keys or CLIs required. Entry point: `workshop-paper-review/SKILL.md`.

### Changed
- Redesigned `research-log` from a write-heavy project diary into a decision-time advisor. The `query` workflow is now split into two focused operations: `check` (surfaces the lesson/rule corpus before a decision, warning against known anti-patterns from past projects) and `recall` (surfaces cross-project findings when stuck on a problem). Lessons and rules are now first-class objects in the workspace rather than free-form log entries. Project registration and session state-capture workflows are unchanged. The `~/.research-log/` workspace is auto-created as before.
- Refined the `vastai` skill with GPU selection guidance by workload type (training, inference, experimentation), a preference for plain ubuntu+uv base images over pre-built ML images for reproducibility, and provisioning-safety notes (health-check before queuing long jobs). SSH connection guidance now documents both direct connection and proxy fallback for instances behind NAT.
- Updated documentation across four touchpoints in `README.md` (skill table, requirements section, "Which skill to use?" picker, directory tree) and four touchpoints in `CLIENT_SETUP.md` (skill directory list, Claude Code and Codex install loops, Forge Option 2 tree, per-skill prerequisites section) to cover `research-portal`, `proton-mail`, and `workshop-paper-review`. Also backfilled `concept-explainer` into the `CLIENT_SETUP.md` directory list, install loops, Forge tree, and per-skill prerequisites, where it had been missing despite being listed in `README.md`.

## 2026-05-13

### Added
- Added the `overleaf-section-workflow` skill — a disciplined, section-by-section workflow for drafting physics papers on Overleaf. Codifies the **Korean intermediate draft → user iteration → Opus-direct English LaTeX → out-of-tree build** loop, with non-negotiables learned from real JCAP-style drafting sessions: no em/en-dashes in any draft or final LaTeX (`grep -cP "[\x{2013}\x{2014}]"` must return 0), no forward references in background sections, no "본 연구" preview outside design statements, citation content (not just metadata) must match the claim, `pdflatex`/`bibtex` **must never run inside the Overleaf sync folder** (use the `_build/` sibling instead), and **translation is Opus-only** — the skill explicitly forbids delegating section translation to a Sonnet subagent, contrary to the general lab convention. Assumes a three-directory contract (`<PROJECT>/`, `<PROJECT>_draft/`, `<PROJECT>_build/`) and orchestrates `overleap` (sync), `scienceplot-py` (plots), `reference-search` (lit), `bibtex-gen` (citations), and `commit-triage` (session-end commits) — optionally `deep-research` for novelty verification. Bundles eight reference docs (`00_workflow_overview.md` through `07_lessons_log.md`) and a `templates/build_template.sh`.
- Added the `bibtex-gen` skill — generate bibtex entries by routing each reference to its most authoritative source. HEP papers go to **InspireHEP** (`/api/literature?format=bibtex`, returning canonical `Author:YYYYabc`-style entries), non-HEP papers go to **Google Scholar** via the `scholarly` library (`firstauthorYYYYword`-style), and **CrossRef** DOI bibtex (`/works/{DOI}/transform/application/x-bibtex`) is the publisher fallback when Scholar is unavailable. HEP / non-HEP classification is automatic: a query is HEP iff InspireHEP returns a match, with arXiv `hep-*` / `nucl-*` category tags as an extra short-circuit signal for arXiv-ID inputs. `--hep` / `--no-hep` flags allow explicit overrides. Source-native bibtex keys are preserved verbatim — the skill does not rewrite keys or fields. Accepts arXiv IDs, DOIs, paper titles, and URLs; supports single-shot and batch (`--batch refs.txt`) input; streams to stdout or appends to a `.bib` file with `--output`. The orchestrator carries a **PEP 723 inline script metadata header** declaring `scholarly` as a dependency, so `uv run scripts/bibtex_gen.py …` auto-provisions an ephemeral environment on first invocation — no `uv add` / `uv pip install` step needed. Bibtex-only fallback path (HEP + CrossRef) is stdlib-only and works under bare `python3` if uv is unavailable. Bundles `scripts/bibtex_gen.py` plus three reference docs (`sources.md`, `hep_classification.md`, `examples.md`).

### Changed
- Updated `README.md` (four touchpoints: skill table, requirements section, "Which skill to use?" picker, and the directory tree) to list `bibtex-gen` and `overleaf-section-workflow`.
- Updated `CLIENT_SETUP.md` (four touchpoints: skill directory list near the top, both install loops for Claude Code and Codex, the Forge tree, and the per-skill prerequisites section) to cover both new skills — including the PEP 723 auto-install behavior for `bibtex-gen` and the TeX-distribution / companion-skill / three-directory-contract notes for `overleaf-section-workflow`.
- Wired `bibtex-gen` to `reference-search` via a new `--from-search <file>.json` flag on the orchestrator. The flag reads `reference-search`'s existing JSON output (`openalex_search.py --format json`), extracts each candidate's DOI (or title fallback when no DOI is present), and feeds the queue through the normal HEP / Scholar / CrossRef routing pipeline — so discovery via OpenAlex yields a `.bib` whose HEP entries still carry InspireHEP `Author:YYYYabc` keys and whose non-HEP entries route through Scholar / CrossRef. Composable with `--batch` and positional args (processed in order: positional → batch → from-search). `reference-search/SKILL.md` gained a new "Downstream: producing bibtex from results" section and a `bibtex-gen` entry in its Resources list, completing the cross-link in both directions.

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
