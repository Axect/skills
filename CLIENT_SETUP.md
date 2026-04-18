# Client Setup Guide

This document explains how to use the skills in this repository from different clients, with a focus on Claude Code, Codex, and Forge-style local setups.

## What this repository provides

Each skill in this repository lives in its own directory and uses `SKILL.md` as the entrypoint.
Some skills also include helper assets such as:

- `scripts/` for executable helpers
- `references/` for supporting documentation
- `assets/` for templates or bundled resources

Current skill directories in this repository:

- `adversarial-review`
- `commit-triage`
- `dropbox`
- `paperbanana`
- `reference-search`
- `research-log`
- `research-report`
- `vastai`

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
for skill in adversarial-review commit-triage dropbox paperbanana reference-search research-log research-report vastai; do
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

Codex uses Agent Skills and scans several locations for installed skills.

### Common locations

- User scope: `$HOME/.agents/skills`
- Project scope: `$CWD/.agents/skills`
- Parent scope when launched inside a repository: `$CWD/../.agents/skills`
- Repository-root scope: `$REPO_ROOT/.agents/skills`
- Admin scope: `/etc/codex/skills`

Codex also supports symlinked skill folders.

### Install one skill for your user account

```bash
mkdir -p ~/.agents/skills
ln -s "$REPO/research-log" ~/.agents/skills/research-log
```

### Install one skill only for the current repository

Run this from the target project root:

```bash
mkdir -p .agents/skills
ln -s "$REPO/paperbanana" .agents/skills/paperbanana
```

### Install the whole collection for your user account

```bash
mkdir -p ~/.agents/skills
for skill in adversarial-review commit-triage dropbox paperbanana reference-search research-log research-report vastai; do
  ln -s "$REPO/$skill" "$HOME/.agents/skills/$skill"
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
├── adversarial-review/
├── commit-triage/
├── dropbox/
├── paperbanana/
├── reference-search/
├── research-log/
├── research-report/
└── vastai/
```

### Behavior notes

- Forge behavior still depends on the launcher or wrapper that starts it.
- If Forge caches the available skills at session start, open a new session after changing `~/forge/skills`.
- If this repository is already mirrored or copied into `~/forge/skills`, you only need to keep the installed directories up to date.

## Per-skill prerequisites

Installing a skill into your client's skill directory only makes it **discoverable** — some skills also need an external CLI, API key, or credentials file on your machine before they can actually run. Do this once per machine, regardless of which client you are using.

### adversarial-review — no setup required

Spawns persona subagents through the host client's Agent tool and reuses `reference-search` for citation and prior-art checks. No additional CLIs or keys.

### commit-triage — no setup required

Uses only `git` inside the target repository. Install it in the same scope as the other skills and invoke it from any git working tree.

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

### reference-search — no setup required

Runs entirely on the Python standard library against the public OpenAlex API.

- Optional: pass `--email you@example.com` to `reference-search/scripts/openalex_search.py` to use OpenAlex's polite pool.

### research-log — workspace auto-created

The skill manages `~/.research-log/` automatically on first use. Nothing to install.

- Register a new project via `/log-init` (or the skill's `initialize` workflow).
- Storage layout: `research-log/references/conventions.md`.

### research-report — no setup required

Uses only the Python standard library. Helper scripts live in `research-report/scripts/` and are invoked from inside a project's output directory.

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

7. Re-check the "Per-skill prerequisites" section above — missing CLI binaries (`paperbanana`, `vastai`), missing credentials (`~/.config/dropbox-skill/credentials.json`, `~/.vast_api_key`), or a missing env file (`~/.config/paperbanana/env`) are the most common cause.

## Repository maintenance tip

If you are actively developing skills in this repository, keep one canonical checkout. For Claude Code and Codex, symlinking from the client into that checkout can keep updates simple. For Forge, copy the real skill directories into `~/forge/skills` instead of symlinking, because symlinked skills may not be detected.
