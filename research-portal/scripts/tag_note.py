#!/usr/bin/env python3
"""Safely tag (rename) research notes by project, keeping image links intact.

Renaming `20240115.md` -> `20240115_ProjectA.md` is not just a file rename: Typora
stores images in a sibling `<stem>.assets/` folder and references them by path
(`./20240115.assets/foo.png`). Those references can also be cross-file (one note
embedding another note's assets). A matching exported `<stem>.pdf` may exist too.

This script handles all of that atomically per note:
  1. rename `<old>.assets/` -> `<new>.assets/`
  2. rewrite every `<old>.assets` reference -> `<new>.assets` across ALL notes
  3. rename `<old>.pdf` -> `<new>.pdf` if present
  4. rename `<old>.md` -> `<new>.md`
Then it verifies every `*.assets` reference in every note resolves to a real dir.

The reference rewrite is idempotent (it matches `<old>.assets` literally, never
the already-renamed `<old>_PROJECT.assets`), so re-running is safe.

Usage:
  tag_note.py --project ProjectA 20240115 20240116      # append _ProjectA to each
  tag_note.py --rename 20240115_DraftA 20240115_ProjectA  # explicit single rename
  tag_note.py --project ProjectA 20240115 --dry-run     # preview only
Notes dir: --notes-dir, else docs_dir from ./mkdocs.yml.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def resolve_notes_dir(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    cfg = Path("mkdocs.yml")
    if cfg.exists():
        for line in cfg.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*docs_dir:\s*(.+?)\s*$", line)
            if m:
                return Path(m.group(1).strip().strip('"').strip("'")).expanduser()
    sys.exit("notes dir not given and no docs_dir found in ./mkdocs.yml")


def rewrite_refs(notes: Path, old_stem: str, new_stem: str, dry: bool) -> int:
    """Replace `<old_stem>.assets` -> `<new_stem>.assets` in every .md. Returns files changed."""
    pat = re.compile(re.escape(old_stem) + r"\.assets")
    repl = new_stem + ".assets"
    changed = 0
    for md in notes.glob("*.md"):
        text = md.read_text(encoding="utf-8", errors="ignore")
        new = pat.sub(repl, text)
        if new != text:
            changed += 1
            if not dry:
                md.write_text(new, encoding="utf-8")
    return changed


def rename_note(notes: Path, old_stem: str, new_stem: str, dry: bool) -> bool:
    old_md = notes / f"{old_stem}.md"
    new_md = notes / f"{new_stem}.md"
    if not old_md.exists():
        print(f"  skip: {old_md.name} not found")
        return False
    if new_md.exists():
        print(f"  skip: {new_md.name} already exists")
        return False

    old_assets, new_assets = notes / f"{old_stem}.assets", notes / f"{new_stem}.assets"
    old_pdf, new_pdf = notes / f"{old_stem}.pdf", notes / f"{new_stem}.pdf"

    actions = []
    if old_assets.is_dir():
        actions.append(f"mv {old_assets.name}/ -> {new_assets.name}/")
    n_refs = rewrite_refs(notes, old_stem, new_stem, dry=True)
    if n_refs:
        actions.append(f"rewrite {old_stem}.assets refs in {n_refs} note(s)")
    if old_pdf.exists():
        actions.append(f"mv {old_pdf.name} -> {new_pdf.name}")
    actions.append(f"mv {old_md.name} -> {new_md.name}")

    print(f"{old_stem} -> {new_stem}")
    for a in actions:
        print(f"  {'[dry] ' if dry else ''}{a}")
    if dry:
        return True

    if old_assets.is_dir():
        old_assets.rename(new_assets)
    rewrite_refs(notes, old_stem, new_stem, dry=False)
    if old_pdf.exists():
        old_pdf.rename(new_pdf)
    old_md.rename(new_md)
    return True


REF = re.compile(r"[\w.-]+?\.assets")


def verify(notes: Path) -> int:
    bad = 0
    for md in notes.glob("*.md"):
        text = md.read_text(encoding="utf-8", errors="ignore")
        for ref in sorted(set(REF.findall(text))):
            if not (notes / ref).is_dir():
                print(f"  BROKEN: {ref} referenced in {md.name}")
                bad += 1
    print("all asset refs resolve OK" if not bad else f"{bad} broken reference(s)")
    return bad


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stems", nargs="*", help="note stems (without .md) to tag with --project")
    ap.add_argument("--project", help="project suffix to append, e.g. ProjectA")
    ap.add_argument("--rename", nargs=2, metavar=("OLD", "NEW"), help="explicit old_stem new_stem")
    ap.add_argument("--notes-dir")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    notes = resolve_notes_dir(args.notes_dir)
    if not notes.is_dir():
        sys.exit(f"notes dir not found: {notes}")

    pairs: list[tuple[str, str]] = []
    if args.rename:
        pairs.append((args.rename[0], args.rename[1]))
    if args.project:
        pairs += [(s, f"{s}_{args.project}") for s in args.stems]
    if not pairs:
        sys.exit("nothing to do: pass --project with stems, or --rename OLD NEW")

    done = 0
    for old, new in pairs:
        if rename_note(notes, old, new, args.dry_run):
            done += 1
    print(f"\n{'[dry-run] would rename' if args.dry_run else 'renamed'} {done} note(s)")
    if not args.dry_run and done:
        print("verifying links:")
        verify(notes)


if __name__ == "__main__":
    main()
