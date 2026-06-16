# Client Setup Guide

This document explains how to use the skills in this repository from different clients, with a focus on Claude Code, Codex, and Forge-style local setups.

## What this repository provides

Each skill in this repository lives in its own directory and uses `SKILL.md` as the entrypoint.
Some skills also include helper assets such as:

- `scripts/` for executable helpers
- `references/` for supporting documentation
- `assets/` for templates or bundled resources

Current skill directories in this repository:

- `academic-jobs`
- `academic-slides`
- `adversarial-review`
- `bibtex-gen`
- `commit-triage`
- `concept-explainer`
- `dropbox`
- `hep-rumor-mill`
- `journal-club-review`
- `md2pdf-typora`
- `morgen`
- `overleap`
- `overleaf-section-workflow`
- `paperbanana`
- `proton-mail`
- `reference-search`
- `research-backup`
- `research-log`
- `research-portal`
- `research-report`
- `scienceplot-py`
- `vastai`
- `wide-slide-illustrator`
- `workshop-paper-review`
- `xkcd-py`

> Several skills also need a one-time **external setup** (CLIs, API keys, credentials files) that is independent of the client. See the "Per-skill prerequisites" section near the end of this guide — do that before your first invocation.

## Recommended installation style

In most cases, **symlinking** a skill directory is the best choice while you are actively editing this repository.

Use a **symlink** when:
- you want changes in this repo to show up immediately in the client
- you maintain the skill in one canonical place

Use a **copy** when:
- you want a pinned snapshot
- the target environment does not follow symlinks cleanly
- you are packaging a release artifact

In the examples below, assume this repository is checked out at:

```bash
REPO=/absolute/path/to/skills
```

## Claude Code

Claude Code supports personal, project, and plugin skill locations.

### Supported locations

- Personal: `~/.claude/skills/<skill-name>/SKILL.md`
- Project: `.claude/skills/<skill-name>/SKILL.md`
- Plugin: `<plugin>/skills/<skill-name>/SKILL.md`

### Install one skill for all projects

```bash
mkdir -p ~/.claude/skills
ln -s "$REPO/research-report" ~/.claude/skills/research-report
```

### Install one skill only for the current repository

Run this from the target project root:

```bash
mkdir -p .claude/skills
ln -s "$REPO/vastai" .claude/skills/vastai
```

### Install the whole collection into your personal Claude Code skills

```bash
mkdir -p ~/.claude/skills
for skill in academic-jobs academic-slides adversarial-review bibtex-gen commit-triage concept-explainer dropbox hep-rumor-mill journal-club-review md2pdf-typora morgen overleap overleaf-section-workflow paperbanana proton-mail reference-search research-backup research-log research-portal research-report scienceplot-py vastai wide-slide-illustrator workshop-paper-review xkcd-py; do
  ln -s "$REPO/$skill" "$HOME/.claude/skills/$skill"
done
```

### Behavior notes

- Claude Code watches skill directories for changes.
- Adding, editing, or removing an existing skill under `~/.claude/skills/` or `.claude/skills/` is picked up in the current session.
- If the top-level skills directory did not exist when the session started, restart Claude Code after creating it.
- Skills inside a `.claude/skills/` directory from an `--add-dir` path are also loaded.

### Quick verification

After installation, confirm one of the following works:

- invoke the skill directly, for example `/research-report`
- ask Claude for a task that should naturally trigger the skill

## Codex

Codex uses Agent Skills from `$CODEX_HOME/skills`, which defaults to
`~/.codex/skills`.

### Common locations

- User scope: `$CODEX_HOME/skills` (default: `~/.codex/skills`)

Codex also supports symlinked skill folders.

### Install one skill for your user account

```bash
mkdir -p ~/.codex/skills
ln -s "$REPO/research-log" ~/.codex/skills/research-log
```

### Install another single skill

```bash
mkdir -p ~/.codex/skills
ln -s "$REPO/paperbanana" ~/.codex/skills/paperbanana
```

### Install the whole collection for your user account

```bash
mkdir -p ~/.codex/skills
for skill in academic-jobs academic-slides adversarial-review bibtex-gen commit-triage concept-explainer dropbox hep-rumor-mill journal-club-review md2pdf-typora morgen overleap overleaf-section-workflow paperbanana proton-mail reference-search research-backup research-log research-portal research-report scienceplot-py vastai wide-slide-illustrator workshop-paper-review xkcd-py; do
  ln -s "$REPO/$skill" "$HOME/.codex/skills/$skill"
done
```

### Behavior notes

- Codex discovers skills from its configured scan locations.
- If a skill does not appear immediately, start a new Codex session.
- If a skill was intentionally disabled, check `~/.codex/config.toml` for `[[skills.config]]` entries.
- If you are building a richer Codex integration later, you can add optional metadata in `agents/openai.yaml` next to the skill.

### Quick verification

After installation:

- start Codex in a directory where the installed scope applies
- ask for a workflow that matches the skill, or invoke the skill if your interface exposes it directly

## Forge

In this environment, Forge uses `~/forge` as its main working directory, and the active skill collection lives under `~/forge/skills`.

### Recommended approach for this repository

Treat this repository as the canonical source, then expose it to Forge by copying real skill directories into `~/forge/skills`.

Do **not** use symlinks for Forge skills in this environment. Forge may fail to detect symlinked skill directories, so the installed skill under `~/forge/skills` must be a real directory.

### Practical patterns

#### Option 1: copy selected skills into `~/forge/skills`

Use this setup when you want Forge to load specific skills from this repository.

```bash
mkdir -p ~/forge/skills
cp -R "$REPO/research-report" ~/forge/skills/research-report
cp -R "$REPO/vastai" ~/forge/skills/vastai
```

#### Option 2: make this repository the active Forge skills collection

Use this when your local Forge setup allows the skill root itself to be configured.

```text
/absolute/path/to/skills/
├── academic-jobs/
├── academic-slides/
├── adversarial-review/
├── bibtex-gen/
├── commit-triage/
├── concept-explainer/
├── dropbox/
├── hep-rumor-mill/
├── journal-club-review/
├── md2pdf-typora/
├── morgen/
├── overleap/
├── overleaf-section-workflow/
├── paperbanana/
├── proton-mail/
├── reference-search/
├── research-backup/
├── research-log/
├── research-portal/
├── research-report/
├── scienceplot-py/
├── vastai/
├── wide-slide-illustrator/
├── workshop-paper-review/
└── xkcd-py/
```

### Behavior notes

- Forge behavior still depends on the launcher or wrapper that starts it.
- If Forge caches the available skills at session start, open a new session after changing `~/forge/skills`.
- If this repository is already mirrored or copied into `~/forge/skills`, you only need to keep the installed directories up to date.

## Per-skill prerequisites

Installing a skill into your client's skill directory only makes it **discoverable** — some skills also need an external CLI, API key, or credentials file on your machine before they can actually run. Do this once per machine, regardless of which client you are using.

### academic-jobs: uv (deps auto-installed)

Requires `uv` on `PATH`; no API keys or credentials. The skill bundles a uv project (`ajo`) whose dependencies (`requests`, `beautifulsoup4`) are auto-installed into an isolated environment on first `uv run`.

- Smoke-test the CLI (creates the data dir, DB, and default `physics-ml` preset on first run):
  ```bash
  uv run --project "$REPO/academic-jobs" ajo config
  ```
  Expected: the default preset's keywords and position-type / country filters printed as a table.
- State lives under `~/.local/share/academic-jobs/` (`jobs.db` + `config.toml`); override with `AJO_DATA_DIR`.
- Validity is judged from each posting's detail page (effective deadline = firm `Appl Deadline`, else `listed until`). `--fast` skips detail pages but misses many valid postings; prefer the default.
- The CLI is polite by design (single session, real User-Agent, inter-request delay, per-run detail-fetch cap). Do not parallelise.

### academic-slides: Node + pnpm (Slidev) + matplotlib/scienceplots/TeX

Two toolchains. Slidev (Node) builds and exports the deck; the scienceplots pipeline (Python) renders the figures. No API keys.

- Install Node.js and `pnpm`. From a deck folder, `pnpm install`, then `pnpm exec playwright install chromium` (Chromium is used only by `slidev export` for the PDF).
- Figures need `matplotlib` + `scienceplots` and a system TeX distribution on `PATH`:
  ```bash
  uv add matplotlib scienceplots numpy
  pdflatex --version
  ```
- If `pnpm install` leaves `esbuild` / `vue-demi` unbuilt, run `pnpm rebuild esbuild vue-demi`; if `slidev export` prompts for a theme, `pnpm add @slidev/theme-default`.

### adversarial-review — no setup required

Spawns persona subagents through the host client's Agent tool and reuses `reference-search` for citation and prior-art checks. No additional CLIs or keys.

### bibtex-gen — no setup required

No keys, no installs. The orchestrator `scripts/bibtex_gen.py` carries a **PEP 723 inline script metadata** header that declares `scholarly` as a dependency, so `uv run` automatically provisions an ephemeral environment with `scholarly` on first invocation and reuses the cached env after that.

Smoke-test with a HEP arXiv ID (uses the stdlib-only InspireHEP path; should return immediately even on a fresh machine):

```bash
uv run "$REPO/bibtex-gen/scripts/bibtex_gen.py" arxiv:1207.7214
```

Expected: an `@article{ATLAS:2012yve, ...}` bibtex entry on stdout.

Smoke-test the non-HEP path (Scholar → CrossRef fallback). On first run `uv` resolves `scholarly` and caches it:

```bash
uv run "$REPO/bibtex-gen/scripts/bibtex_gen.py" --no-hep "Attention is all you need"
```

If the orchestrator is invoked with bare `python3` (no `uv`) instead, `scholarly` may be missing and non-HEP queries fall through directly to CrossRef — still correct publisher-grade bibtex, but you lose Scholar's preferred key style.

### commit-triage — no setup required

Uses only `git` inside the target repository. Install it in the same scope as the other skills and invoke it from any git working tree.

### concept-explainer: matplotlib + scienceplots + TeX

Requires `matplotlib` and `scienceplots` in the runtime that executes the generated plot scripts, plus a working system TeX install (LaTeX rendering is mandatory; the `no-latex` style is forbidden by this skill). The `md2pdf-typora` skill handles the PDF assembly step.

- Install runtime deps:
  ```bash
  uv add matplotlib scienceplots numpy
  ```
- A system TeX distribution must be on `PATH` (e.g. TeX Live). Verify with `pdflatex --version` or `xelatex --version`.
- Unlike `scienceplot-py`, this skill executes the plot scripts it generates (via `uv run`), because the PDF step depends on the PNGs existing.
- Optionally install `wide-slide-illustrator` for Friendly Whiteboard schematic prompt generation, and `codex-image` if you want the prompts rendered automatically.

### dropbox — OAuth credentials

1. Install `curl` and `jq` if missing.
2. Create (or open) a Dropbox app at https://www.dropbox.com/developers/apps with:
   - Permission type: **Scoped access**
   - Access type: **Full Dropbox**
   - Permissions: `files.content.write`, `files.content.read`, `sharing.write`, `sharing.read`
3. Run the interactive setup:
   ```bash
   bash "$REPO/dropbox/scripts/setup.sh"
   ```
   It prompts for the app key, app secret, and authorization code, then writes `~/.config/dropbox-skill/credentials.json` (mode 600).
4. Verify:
   ```bash
   test -f ~/.config/dropbox-skill/credentials.json && echo "dropbox: ready"
   ```

### hep-rumor-mill: uv (deps auto-installed)

Requires `uv` on `PATH`; no API keys or credentials. The skill bundles a uv project (`prm`) whose single dependency (`requests`) is auto-installed into an isolated environment on first `uv run`.

- Smoke-test the CLI:
  ```bash
  uv run --project "$REPO/hep-rumor-mill" prm --help
  ```
- State lives under `~/.local/share/hep-rumor-mill/rumor.db`; override with `PRM_DATA_DIR`.
- Optional: set `S2_API_KEY` (same env var `reference-search` uses) to raise the Semantic Scholar rate limit and make citation backfill reliable.
- The CLI paces InspireHEP and OpenAlex requests by design. Do not parallelise.

### journal-club-review: uv (+ optional codex for figures)

Requires `uv`. The extractor `scripts/extract_text.py` carries a **PEP 723 inline script metadata** header declaring `pdfplumber`, `httpx`, and `feedparser`, so `uv run` provisions an ephemeral environment on first invocation and reuses the cache after that. No `uv add` step needed.

- Smoke-test the extractor on an arXiv ID (downloads the PDF, prints a JSON summary):
  ```bash
  uv run "$REPO/journal-club-review/scripts/extract_text.py" 1706.03762
  ```
  Expected: a JSON object with `title`, `authors`, `out_dir`, `source_md`, and `n_chars`, plus a `reviews/1706.03762/source.md` file.
- Figures are optional and need a logged-in bundled `codex` runtime (ChatGPT OAuth). Verify with `codex login status` ("Logged in using ChatGPT"). Without it the review still renders text-only.
- For arXiv inputs with messy extracted math, pass an `arxiv-doc-builder` markdown path instead of the raw ID for cleaner structure.

### md2pdf-typora — pandoc + Chromium

1. Install pandoc:
   ```bash
   # Arch
   sudo pacman -S pandoc
   # Debian / Ubuntu
   sudo apt install pandoc
   # macOS
   brew install pandoc
   ```
   Verify with `pandoc --version`.
2. Install a Chromium-family browser if not already present (`google-chrome-stable`, `google-chrome`, or `chromium`). The skill renders the patched HTML to PDF via `--headless=new --print-to-pdf` and needs the binary on `PATH`. Verify with `command -v google-chrome-stable` or equivalent.
3. Network access: math is rendered with MathJax SVG (`tex-svg-full.js`) loaded from the `cdn.jsdelivr.net` CDN, and body fonts (IBM Plex Serif, MaruBuri, Roboto Slab, JetBrains Mono) come from Google Fonts. Chrome must reach these CDNs during the conversion.
4. No credentials, no API keys.
5. Smoke-test:
   ```bash
   echo -e "# Hello\n\nInline math: $a^2 + b^2 = c^2$." > /tmp/_md2pdf_test.md
   bash -c 'cd /tmp && pandoc _md2pdf_test.md -o _md2pdf_test.html --standalone --mathjax'
   ```
   If pandoc completes without error, the skill itself drives the rest of the pipeline (HTML patch + Chrome print).

### morgen — API key

1. Install `curl` and `jq` if missing.
2. Get a Morgen API key at https://platform.morgen.so under *Developers API*.
3. Run the interactive setup:
   ```bash
   bash "$REPO/morgen/scripts/setup.sh"
   ```
   It prompts for the API key, verifies it against `/v3/calendars/list`, and writes `~/.config/morgen-skill/credentials.json` (mode 600).
4. Verify:
   ```bash
   test -f ~/.config/morgen-skill/credentials.json && echo "morgen: ready"
   ```

All requests go to `https://api.morgen.so/v3` with `Authorization: ApiKey <KEY>`. Rate limit is 100 points per 15 minutes — list endpoints cost 10 points each.

### overleap — Node.js CLI + Overleaf session cookie

1. Install Node.js >= 18 and `git`. Verify:
   ```bash
   node --version    # must be >= 18
   git --version
   ```
2. Install the CLI globally:
   ```bash
   npm install -g overleap
   ```
   (The `socket.io-client` dependency is fetched from a GitHub fork, which is why `git` is required.)
3. Verify the binary is on `PATH`:
   ```bash
   command -v overleap && overleap --help | head -5
   ```
4. For each Overleaf project you want to sync, save the cookie into a per-project `.env` file using the bundled helper:
   ```bash
   bash "$REPO/overleap/scripts/init_env.sh" <project-dir> <<< 'overleaf_session2=...'
   ```
   The script writes `<project-dir>/.env` with mode `0600` and ensures `.env` is in `<project-dir>/.gitignore`. Get the cookie from browser DevTools → Application → Cookies → `overleaf.com` → copy the full cookie string (or just the `overleaf_session2` value).
5. Smoke-test:
   ```bash
   cd <project-dir> && overleap projects
   ```
   On success you'll see a numbered project list; that's also the connectivity / auth check.

`overleap sync` is a long-running daemon. Run it from a dedicated terminal pane, under `pueue`, or via `run_in_background` — never as a foreground Bash call from Claude. See `overleap/references/long-running-patterns.md` for concrete recipes.

### overleaf-section-workflow — TeX + companion skills

The skill is a workflow orchestrator. It needs a working TeX distribution on `PATH` plus the companion skills it invokes; nothing else.

1. Install TeX Live (or another TeX distribution that provides `pdflatex` and `bibtex`):
   ```bash
   # Arch
   sudo pacman -S texlive-most
   # Debian / Ubuntu
   sudo apt install texlive-full
   # macOS
   brew install --cask mactex
   ```
   Verify:
   ```bash
   command -v pdflatex && command -v bibtex && pdflatex --version | head -1
   ```
2. Make sure the companion skills are installed and configured according to their own per-skill prerequisites in this file:
   - `overleap` (Overleaf sync — needs the `overleap` CLI and a per-project session cookie)
   - `scienceplot-py` (plot scripts — needs `matplotlib` + `scienceplots` in the runtime env)
   - `reference-search` (literature discovery — no setup)
   - `bibtex-gen` (citation generation — no setup; `scholarly` auto-installed via PEP 723 when `uv run`)
   - `commit-triage` (session-end commits — no setup)
3. Three-directory contract. The workflow assumes the user maintains three sibling directories per paper project — typically under `~/zbin/OverLeaf/`:
   - `<PROJECT>/` — the Overleaf sync folder (mirrored via `overleap`). `.tex`, `ref.bib`, `figs/` live here. **Never run pdflatex/bibtex here** — build artefacts would sync back to Overleaf.
   - `<PROJECT>_draft/` — Korean section drafts as `section<N>_ko.md`.
   - `<PROJECT>_build/` — out-of-tree build scripts and artefacts. Use the bundled `templates/build_template.sh` (set `JOBNAME`).
4. The skill does not install any libraries itself and does not write to your system other than via the companion-skill scripts.

### paperbanana — CLI + env file

1. Install the `paperbanana` CLI per its upstream instructions; confirm with `paperbanana --help`.
2. Create the env file:
   ```bash
   mkdir -p ~/.config/paperbanana
   cat > ~/.config/paperbanana/env << 'EOF'
   export GOOGLE_API_KEY="your-google-api-key"
   export VLM_MODEL="gemini-3-flash-preview"
   EOF
   chmod 600 ~/.config/paperbanana/env
   ```
   Alternatively, run `paperbanana setup` for the interactive wizard.
3. The skill always runs commands as `source ~/.config/paperbanana/env && paperbanana ...`, so never hardcode keys in invocations.

### proton-mail: Proton Bridge + ~/.proton-imap

Requires a locally running Proton Bridge instance and a credentials file.

1. Install and configure Proton Bridge from https://proton.me/mail/bridge. Start it and let it finish syncing before invoking the skill.
2. Create `~/.proton-imap` (chmod 600) with KEY=VALUE lines. Use the bridge-specific password shown in the Bridge app under "Mailbox details" (not your main Proton account password):
   ```bash
   cat > ~/.proton-imap << 'EOF'
   PROTON_IMAP_USER=you@proton.me
   PROTON_IMAP_PASS=<bridge-generated password>
   PROTON_IMAP_HOST=127.0.0.1
   PROTON_IMAP_PORT=1143
   EOF
   chmod 600 ~/.proton-imap
   ```
3. Verify Proton Bridge is running and accepting IMAP connections on 127.0.0.1:1143 (confirm the port in the Bridge app).
4. The skill is read-only: it does not send, delete, or move messages.

### reference-search — no setup required

Runs entirely on the Python standard library against the public OpenAlex API.

- Optional: pass `--email you@example.com` to `reference-search/scripts/openalex_search.py` to use OpenAlex's polite pool.

### research-backup: rsync + locally synced Dropbox folder

Requires `rsync` on `PATH` and the official Dropbox client syncing a local folder on this machine. No API keys or credentials: the skill only writes files under the synced folder (default `~/Dropbox/ResearchBackup/`) and the daemon uploads them.

- Verify the prerequisites:
  ```bash
  command -v rsync && test -d ~/Dropbox && echo "research-backup: ready"
  ```
- Config and registry are auto-created under `~/.config/research-backup/` on first run; override the directory with `RESEARCH_BACKUP_CONFIG_DIR`. Defaults: `SCAN_ROOT="$HOME/Documents/Project"`, `BACKUP_ROOT="$HOME/Dropbox/ResearchBackup"`.
- Smoke-test (read-only scan, prints a `STATE GIT PATH` table):
  ```bash
  bash "$REPO/research-backup/scripts/discover.sh"
  ```
- Backups are additive (`rsync` without `--delete`); local deletions never propagate to Dropbox.

### research-log — workspace auto-created

The skill manages `~/.research/` automatically on first use. Nothing to install. The redesigned advisor mode adds a `check` step (surfaces relevant past lessons and rules before a decision) and a `recall` step (surfaces cross-project findings when stuck); both work from the same workspace with no extra config.

- Register a new project via `/log-init` (or the skill's `initialize` workflow).
- Storage layout: `research-log/references/conventions.md`.

### research-portal: uv (mkdocs auto-installed)

Requires `uv` on `PATH`. No other manual installs are needed.

- The scaffold script auto-installs `mkdocs-material` and `mkdocs-literate-nav` into an isolated environment on first run.
- `docs_dir` points at your notes folder; originals are never modified.
- Verify `uv` is available: `uv --version`.

### research-report — no setup required

Uses only the Python standard library. Helper scripts live in `research-report/scripts/` and are invoked from inside a project's output directory.

### scienceplot-py — Python deps in your runtime

The skill writes a `.py` file but does not run it; the user runs the script (typically `uv run <path>`). Make sure the *runtime environment* has the libraries the generated script imports:

```bash
uv add matplotlib scienceplots pandas pyarrow numpy
```

`pyarrow` is needed only for parquet input — drop it if your data is CSV-only or NumPy-only. The `scienceplots` package is required even though linters flag the import as unused; it registers the `science` and `nature` styles by import side-effect.

### vastai — CLI + API key

1. Install the CLI:
   ```bash
   uv pip install vastai     # preferred
   # or: pip install vastai
   ```
2. Register your API key (get it at https://cloud.vast.ai/cli/):
   ```bash
   vastai set api-key YOUR_API_KEY
   ```
   The key is stored at `~/.vast_api_key` — treat it as secret.
3. Verify:
   ```bash
   vastai show user
   ```

### workshop-paper-review: no setup required

No external CLIs, API keys, or credentials needed. The skill reads the source PDF locally for fact-checking and uses only Python standard library.

- Make sure the paper PDF is accessible at a local path before invoking the skill.
- The skill targets 4-8 page workshop submissions for ICML, NeurIPS, and ICLR; the review format follows OpenReview conventions.

### xkcd-py — Python deps in your runtime

The skill writes a `.py` file but does not run it; the user runs the script. Make sure the *runtime environment* has:

```bash
uv add matplotlib pandas pyarrow numpy
```

No `scienceplots` is needed — `plt.xkcd()` is built into matplotlib. For best visual results, install an xkcd-style font (Humor Sans / xkcd Script / Comic Neue). Without one, matplotlib falls back to Bitstream Vera Sans and emits a `findfont: Font family ['xkcd Script', ...] not found` warning at render time; the plot still renders correctly.

## Choosing a scope

Use this rule of thumb:

- **Personal/global scope**: use when you want the same skill in many projects
- **Project scope**: use when the skill is tightly coupled to one repository
- **Whole collection install**: use when you want this repo to act as your main reusable skill library
- **Selective install**: use when you want tighter control over what each client can see

## Troubleshooting checklist

If a skill does not show up:

1. Confirm the final path contains `SKILL.md` directly inside the skill directory.
2. For Forge, confirm the installed skill directory is a real directory copied into the client root, not a symlink.
3. Confirm you installed into the correct client-specific root.
4. Start a new client session.
5. For Codex, also check whether the skill was disabled in `~/.codex/config.toml`.
6. For Claude Code, if you created the top-level skills directory after launch, restart the session.

If a skill loads but fails at runtime:

7. Re-check the "Per-skill prerequisites" section above — missing CLI binaries (`paperbanana`, `vastai`), missing credentials (`~/.config/dropbox-skill/credentials.json`, `~/.config/morgen-skill/credentials.json`, `~/.vast_api_key`), or a missing env file (`~/.config/paperbanana/env`) are the most common cause.

## Repository maintenance tip

If you are actively developing skills in this repository, keep one canonical checkout. For Claude Code and Codex, symlinking from the client into that checkout can keep updates simple. For Forge, copy the real skill directories into `~/forge/skills` instead of symlinking, because symlinked skills may not be detected.
