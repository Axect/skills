#!/usr/bin/env python3
"""Scaffold a local MkDocs Material research portal over a folder of markdown notes.

Creates a self-contained portal project (default ~/research-portal) whose
`docs_dir` points straight at the notes folder, so the original `.md` files,
their `<stem>.assets/` image folders, and any PDFs are served in place and never
modified. Writes a MathJax config into `<notes>/javascripts/mathjax.js` for full
LaTeX rendering, auto-excludes subtrees that contain broken symlinks (mkdocs
aborts on those), then builds the home page + sidebar nav and sets up uv deps.

Usage:
  scaffold.py --notes-dir ~/notes \
              --portal-dir ~/research-portal --name "Research Portal" --lang ko
  scaffold.py --notes-dir <dir> --no-install     # generate files only
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS = SKILL_DIR / "assets"


def broken_symlink_excludes(notes: Path) -> list[str]:
    """First-level subtrees under `notes` that contain dangling symlinks."""
    excl: set[str] = set()
    for root, _, files in os.walk(notes):
        for entry in files:
            p = Path(root) / entry
            if p.is_symlink() and not p.exists():
                rel = p.relative_to(notes)
                excl.add(rel.parts[0] + ("/" if len(rel.parts) > 1 else ""))
    return sorted(excl)


def render_mkdocs(notes: Path, portal: Path, name: str, lang: str, excludes: list[str]) -> str:
    tmpl = (ASSETS / "mkdocs.yml.tmpl").read_text(encoding="utf-8")
    if excludes:
        block = "\n# subtrees with broken symlinks (mkdocs aborts on these)\nexclude_docs: |\n"
        block += "".join(f"  {e}\n" for e in excludes)
    else:
        block = ""
    return (tmpl
            .replace("__SITE_NAME__", name)
            .replace("__DOCS_DIR__", str(notes))
            .replace("__SITE_DIR__", str(portal / "site"))
            .replace("__LANG__", lang)
            .replace("__EXCLUDE_BLOCK__", block))


def run(cmd: list[str], cwd: Path) -> None:
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--notes-dir", required=True)
    ap.add_argument("--portal-dir", default="~/research-portal")
    ap.add_argument("--name", default="Research Portal")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--port", default="8123")
    ap.add_argument("--no-install", action="store_true", help="generate files but skip uv venv/install/gen")
    args = ap.parse_args()

    notes = Path(args.notes_dir).expanduser().resolve()
    portal = Path(args.portal_dir).expanduser().resolve()
    if not notes.is_dir():
        sys.exit(f"notes dir not found: {notes}")
    portal.mkdir(parents=True, exist_ok=True)

    excludes = broken_symlink_excludes(notes)
    if excludes:
        print(f"excluding broken-symlink subtrees: {', '.join(excludes)}")

    (portal / "mkdocs.yml").write_text(render_mkdocs(notes, portal, args.name, args.lang, excludes), encoding="utf-8")
    (portal / "gen_index.py").write_text((SKILL_DIR / "scripts" / "gen_index.py").read_text(encoding="utf-8"), encoding="utf-8")
    (portal / "tag_note.py").write_text((SKILL_DIR / "scripts" / "tag_note.py").read_text(encoding="utf-8"), encoding="utf-8")

    jsdir = notes / "javascripts"
    jsdir.mkdir(exist_ok=True)
    (jsdir / "mathjax.js").write_text((ASSETS / "mathjax.js").read_text(encoding="utf-8"), encoding="utf-8")

    print(f"portal files written to {portal}")
    print(f"  mkdocs.yml  gen_index.py  tag_note.py")
    print(f"  {jsdir/'mathjax.js'}")

    if args.no_install:
        print("\n--no-install: run these yourself:")
        print(f"  cd {portal} && uv venv && uv pip install mkdocs-material mkdocs-literate-nav")
        print(f"  uv run python gen_index.py --title '{args.name}'")
        print(f"  uv run mkdocs serve -a 127.0.0.1:{args.port}")
        return

    print("\nsetting up uv environment:")
    run(["uv", "venv"], portal)
    run(["uv", "pip", "install", "mkdocs-material", "mkdocs-literate-nav"], portal)
    run(["uv", "run", "python", "gen_index.py", "--title", args.name], portal)
    print(f"\ndone. serve with:\n  cd {portal} && uv run mkdocs serve -a 127.0.0.1:{args.port}")


if __name__ == "__main__":
    main()
