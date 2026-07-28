#!/usr/bin/env python3
"""Normalise Markdown for pandoc before HTML conversion.

Paths arrive as argv, never as shell-interpolated source text, so this file is
safe to call from any shell without heredoc quoting hazards.

Two fixes, both observed in production:

1. Typora writes ``[TOC]`` as an inline table-of-contents marker. Pandoc does
   not understand it and leaves the literal text in the output, so strip it and
   let ``--toc`` build the real one.

2. A horizontal rule ``---`` immediately followed by a ``## `` heading with no
   blank line between them is parsed by pandoc's markdown reader as a
   setext-style table fragment. The heading and several following paragraphs get
   swallowed into a single ``<table><td>`` cell: the TOC entry disappears and
   the body renders as one run-on paragraph. Chunked-translation workflows hit
   this whenever chunk N ends with ``---`` and chunk N+1 starts with ``## ``.
   Inserting a blank line is enough to keep the two constructs separate.
"""
from __future__ import annotations

import sys


def preprocess(lines: list[str]) -> list[str]:
    out: list[str] = []
    for i, line in enumerate(lines):
        if line.strip() == "[TOC]":
            continue
        out.append(line)
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if line.rstrip() == "---" and nxt.lstrip().startswith("#"):
            out.append("\n")
    return out


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <in.md> <out.md>", file=sys.stderr)
        return 2
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        lines = f.readlines()
    with open(dst, "w", encoding="utf-8") as f:
        f.writelines(preprocess(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
