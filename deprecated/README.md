# Deprecated skills

Skills that are no longer in use, kept here for history and the occasional lookup. Nothing in this directory is a live skill.

## Why they stay in the repo

Deleting a skill outright throws away the accumulated notes (style blocks, CLI flags, hard-won gotchas) that are often worth more than the workflow itself. Keeping it here preserves that without letting any harness load it.

## How deprecation is enforced

1. The skill directory moves under `deprecated/`.
2. Its entrypoint is renamed `SKILL.md` to `SKILL.md.deprecated`. This is the load-bearing step: Pi is configured with this repository root in the `skills` array of `~/.pi/agent/settings.json` and scans it **recursively** for files named exactly `SKILL.md`, so moving the directory alone would not hide it. Claude Code and Codex only look one level below their own skills directory, so for them the move is enough.
3. Every install is removed: symlinks under `~/.claude/skills/` and `~/.codex/skills/`, and the real directory copy under `~/forge/skills/` (Forge does not follow symlinks, so it holds copies).
4. All references in `README.md` and `CLIENT_SETUP.md` are dropped, including the whole-collection install loops, so a fresh install never recreates the link.

Step 4 matters more than it looks: a skill name left in an install loop after its directory is gone produces a dangling symlink on the next run.

## Current contents

| Skill | Deprecated | Reason | Use instead |
|---|---|---|---|
| `paperbanana` | 2026-07-28 | ChatGPT Images 2.0 produces better figures than the paperbanana pipeline, so the multi-agent retrieval/planning/critic loop no longer earns its cost | `wide-slide-illustrator` or `handdrawn-schematic` for methodology and architecture diagrams (both target ChatGPT Images 2.0 / gpt-image); `scienceplot-py` or `xkcd-py` for data plots |

## Restoring one

```bash
REPO=/home/axect/Documents/Project/AI_Project/skills
SKILL=<skill-name>
git mv "$REPO/deprecated/$SKILL/SKILL.md.deprecated" "$REPO/deprecated/$SKILL/SKILL.md"
git mv "$REPO/deprecated/$SKILL" "$REPO/$SKILL"
ln -s "$REPO/$SKILL" "$HOME/.claude/skills/$SKILL"
ln -s "$REPO/$SKILL" "$HOME/.codex/skills/$SKILL"
```

Then put the skill back into the `README.md` touchpoints (skill table, requirements section, "Which skill to use?" picker, directory tree) and the `CLIENT_SETUP.md` touchpoints (skill list, install loops, Forge tree, per-skill prerequisites).
