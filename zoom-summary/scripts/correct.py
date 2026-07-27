#!/usr/bin/env python3
"""Repair mangled domain terms in a Zoom AI Companion summary.

Zoom's summariser reliably mishears domain jargon, turning acronyms into
similar-sounding words and reversing names. This applies only the substitutions
marked high confidence in the glossary, reports everything it touched, and lists
the low-confidence hits for a human to resolve. It never rewrites a
low-confidence term.

Usage:
    correct.py <file.md|-> [--glossary PATH]... [--in-place] [--report-only]
               [--no-appendix]

Exit codes: 0 ok, 1 bad input, 64 usage.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_GLOSSARIES = [
    SKILL_DIR / "references" / "glossary.tsv",
    Path(os.environ.get("ZOOM_SKILL_GLOSSARY", Path.home() / ".config" / "zoom-skill" / "glossary.tsv")),
]
APPENDIX_HEADING = "## 용어 보정"


class Entry:
    def __init__(self, pattern: str, replacement: str, tier: str, note: str, source: Path):
        self.pattern = pattern
        self.replacement = replacement
        self.tier = tier
        self.note = note
        self.source = source
        # An ASCII acronym must not match inside a longer ASCII word, but must
        # still match when a Korean particle is glued to it ("ABC를"). Python's
        # \b treats Hangul as a word character, so it cannot be used here.
        if pattern.isascii():
            self.regex = re.compile(
                r"(?<![A-Za-z0-9])" + re.escape(pattern) + r"(?![A-Za-z0-9])"
            )
        else:
            self.regex = re.compile(re.escape(pattern))

    def count(self, text: str) -> int:
        return len(self.regex.findall(text))


def load_glossaries(paths: list[Path]) -> list[Entry]:
    entries: list[Entry] = []
    seen: dict[str, Entry] = {}
    for path in paths:
        if not path.is_file():
            continue
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = raw.split("\t")
            if len(parts) < 3:
                print(f"zoom-correct: {path}:{lineno}: need at least 3 tab-separated "
                      f"columns, skipping", file=sys.stderr)
                continue
            pattern = parts[0].strip()
            replacement = parts[1].strip()
            tier = parts[2].strip().lower()
            note = parts[3].strip() if len(parts) > 3 else ""
            if tier not in ("high", "low"):
                print(f"zoom-correct: {path}:{lineno}: unknown tier {tier!r}, skipping",
                      file=sys.stderr)
                continue
            if tier == "high" and (not replacement or replacement == "?"):
                print(f"zoom-correct: {path}:{lineno}: tier 'high' needs a real "
                      f"replacement, demoting to 'low'", file=sys.stderr)
                tier = "low"
            entry = Entry(pattern, replacement, tier, note, path)
            # A later glossary (the user's) overrides an earlier one.
            seen[pattern] = entry
    entries = list(seen.values())
    # Longer patterns first, so a compound term wins over its fragments.
    entries.sort(key=lambda e: len(e.pattern), reverse=True)
    return entries


def split_existing_appendix(text: str) -> str:
    """Drop a previous appendix so repeated runs do not stack them."""
    marker = "\n---\n\n" + APPENDIX_HEADING
    idx = text.find(marker)
    if idx == -1:
        idx = text.find("\n" + APPENDIX_HEADING)
    return text[:idx].rstrip() + "\n" if idx != -1 else text


def build_appendix(applied: list[tuple[Entry, int]], flagged: list[tuple[Entry, int]],
                   raw_path: str | None) -> str:
    lines = ["", "---", "", APPENDIX_HEADING, ""]
    if raw_path:
        lines.append(f"Zoom AI Companion 원문은 `{raw_path}`에 그대로 남아 있습니다.")
        lines.append("")

    if applied:
        lines += ["자동 치환:", "", "| 원문 | 보정 | 횟수 |", "|---|---|---|"]
        for entry, n in applied:
            lines.append(f"| {entry.pattern} | {entry.replacement} | {n} |")
        lines.append("")
    else:
        lines += ["자동 치환된 항목 없음.", ""]

    if flagged:
        lines += ["검토 필요 (자동 치환하지 않음):", ""]
        for entry, n in flagged:
            suffix = ""
            if entry.replacement not in ("", "?"):
                suffix += f" → {entry.replacement} 추정."
            if entry.note:
                suffix += f" {entry.note}" if suffix else f": {entry.note}"
            lines.append(f"- `{entry.pattern}` ({n}회){suffix}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("file", help="markdown file, or - for stdin")
    ap.add_argument("--glossary", action="append", default=[],
                    help="extra glossary file (repeatable, applied last)")
    ap.add_argument("--in-place", action="store_true",
                    help="rewrite the file, keeping the original as <stem>.raw.md")
    ap.add_argument("--report-only", action="store_true",
                    help="print the report to stderr and change nothing")
    ap.add_argument("--no-appendix", action="store_true",
                    help="do not append the correction table to the output")
    args = ap.parse_args()

    if args.in_place and args.file == "-":
        print("zoom-correct: --in-place needs a real file", file=sys.stderr)
        return 64

    raw_src: Path | None = None
    if args.file == "-":
        text = sys.stdin.read()
        src = None
    else:
        src = Path(args.file)
        if not src.is_file():
            print(f"zoom-correct: no such file: {src}", file=sys.stderr)
            return 1
        # A previous run left the pristine summary next door. Always work from
        # that, so re-running stays idempotent, keeps the full substitution
        # record, and picks up glossary edits against untouched text.
        candidate = src.with_suffix(".raw.md")
        if candidate.is_file() and candidate != src:
            raw_src = candidate
            text = candidate.read_text(encoding="utf-8")
            print(f"zoom-correct: re-deriving from {candidate.name}", file=sys.stderr)
        else:
            text = src.read_text(encoding="utf-8")

    paths = list(DEFAULT_GLOSSARIES) + [Path(p) for p in args.glossary]
    entries = load_glossaries(paths)
    if not entries:
        print(f"zoom-correct: no glossary entries found in {[str(p) for p in paths]}",
              file=sys.stderr)
        return 1

    body = split_existing_appendix(text)

    applied: list[tuple[Entry, int]] = []
    flagged: list[tuple[Entry, int]] = []
    for entry in entries:
        n = entry.count(body)
        if n == 0:
            continue
        if entry.tier == "high":
            body = entry.regex.sub(entry.replacement.replace("\\", "\\\\"), body)
            applied.append((entry, n))
        else:
            flagged.append((entry, n))

    for entry, n in applied:
        print(f"zoom-correct: {entry.pattern} -> {entry.replacement} ({n})", file=sys.stderr)
    for entry, n in flagged:
        print(f"zoom-correct: REVIEW {entry.pattern} ({n}) {entry.note}", file=sys.stderr)
    if not applied and not flagged:
        print("zoom-correct: nothing matched", file=sys.stderr)

    if args.report_only:
        return 0

    raw_path = None
    if args.in_place and src is not None:
        raw = raw_src if raw_src is not None else src.with_suffix(".raw.md")
        if not raw.exists():
            raw.write_text(text, encoding="utf-8")
        raw_path = raw.name

    out = body.rstrip() + "\n"
    if not args.no_appendix and (applied or flagged):
        out += build_appendix(applied, flagged, raw_path)

    if args.in_place and src is not None:
        src.write_text(out, encoding="utf-8")
        print(str(src))
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
