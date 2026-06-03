#!/usr/bin/env python3
"""Generate the home page (index.md) and sidebar nav (SUMMARY.md) for a research portal.

Scans a notes folder of `YYYYMMDD[_PROJECT[_extra]].md` files, groups them by
project (newest first), and writes two helper files INTO the notes folder:

  index.md     - landing page, notes grouped by project
  SUMMARY.md   - sidebar nav consumed by mkdocs-literate-nav

Original notes are never modified. Both helper files are regenerated every run,
so deleting them is safe.

Notes directory resolution order:
  1. --notes-dir / first positional arg
  2. `docs_dir:` parsed from ./mkdocs.yml (run from the portal dir)
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

DATED = re.compile(r"^(\d{4})(\d{2})(\d{2})(?:_(.+))?\.md$")
# H1 titles too generic to add to a sidebar/date label (date is more useful).
GENERIC_H1 = {"progress report", "research progress"}


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


def split_suffix(suffix: str | None) -> tuple[str, str]:
    """'ProjA_Draft' -> ('ProjA', 'Draft'); None -> ('Daily', '')."""
    if not suffix:
        return "Daily", ""
    head, _, tail = suffix.partition("_")
    return head, tail.replace("_", " ")


def first_h1(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    except OSError:
        pass
    return ""


def scan(notes: Path):
    dated: dict[str, list[tuple[date, Path, str, str]]] = {}
    reference: list[tuple[Path, str]] = []
    for p in sorted(notes.glob("*.md")):
        if p.name in {"index.md", "SUMMARY.md"}:
            continue
        m = DATED.match(p.name)
        if m:
            y, mo, d, suffix = m.groups()
            try:
                dt = date(int(y), int(mo), int(d))
            except ValueError:
                reference.append((p, first_h1(p)))
                continue
            proj, extra = split_suffix(suffix)
            dated.setdefault(proj, []).append((dt, p, extra, first_h1(p)))
        else:
            reference.append((p, first_h1(p)))
    return dated, reference


def proj_order(dated: dict) -> list[str]:
    # most notes first; 'Daily' (untagged) always last among dated projects
    return sorted(dated, key=lambda n: (1 if n == "Daily" else 0, -len(dated[n]), n))


def date_label(dt: date, extra: str) -> str:
    return dt.isoformat() + (f" · {extra}" if extra else "")


def write_index(notes: Path, dated: dict, reference: list, title: str) -> int:
    total = sum(len(v) for v in dated.values()) + len(reference)
    lines = [f"# {title}", "", f"{total} notes, grouped by project, newest first.", ""]
    for proj in proj_order(dated):
        items = sorted(dated[proj], key=lambda t: t[0], reverse=True)
        lines += [f"## {proj}  ({len(items)})", ""]
        for dt, p, extra, h1 in items:
            label = date_label(dt, extra)
            if h1 and h1.lower() not in GENERIC_H1:
                label += f" — {h1}"
            lines.append(f"- [{label}]({p.name})")
        lines.append("")
    if reference:
        lines += ["## Reference / Overview", ""]
        for p, h1 in sorted(reference, key=lambda t: t[0].name):
            lines.append(f"- [{h1 or p.stem}]({p.name})")
        lines.append("")
    (notes / "index.md").write_text("\n".join(lines), encoding="utf-8")
    return total


def write_summary(notes: Path, dated: dict, reference: list) -> None:
    lines = ["- [Home](index.md)"]
    for proj in proj_order(dated):
        items = sorted(dated[proj], key=lambda t: t[0], reverse=True)
        lines.append(f"- {proj}")
        for dt, p, extra, _ in items:
            lines.append(f"    - [{date_label(dt, extra)}]({p.name})")
    if reference:
        lines.append("- Reference")
        for p, h1 in sorted(reference, key=lambda t: t[0].name):
            lines.append(f"    - [{h1 or p.stem}]({p.name})")
    (notes / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("notes_dir", nargs="?", help="notes folder (default: docs_dir from ./mkdocs.yml)")
    ap.add_argument("--notes-dir", dest="notes_dir_opt")
    ap.add_argument("--title", default="Research Portal")
    args = ap.parse_args()

    notes = resolve_notes_dir(args.notes_dir_opt or args.notes_dir)
    if not notes.is_dir():
        sys.exit(f"notes dir not found: {notes}")
    dated, reference = scan(notes)
    total = write_index(notes, dated, reference, args.title)
    write_summary(notes, dated, reference)
    print(f"wrote index.md + SUMMARY.md ({total} notes, {len(dated)} projects) in {notes}")


if __name__ == "__main__":
    main()
