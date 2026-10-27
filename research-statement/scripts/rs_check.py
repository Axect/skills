#!/usr/bin/env python3
"""Mechanical checks for research-statement drafts (Markdown, Korean or English).

Reports per file: share of each `## ` section (whitespace-free characters, references excluded),
em/en dashes, non-Hangul CJK characters, weak verbs, hype words, placeholder slots, and citation
markers versus reference entries. `--strict` exits 1 when dashes, hype words, CJK, or placeholders remain.
"""
import argparse
import re
import sys
from pathlib import Path

REF_HEADINGS = re.compile(r"^##\s+(참고문헌|References|Bibliography)\s*$", re.M)
DASH = re.compile(r"[\u2013\u2014]")
CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
WEAK_EN = re.compile(r"\b(explor(e|es|ed|ing)|stud(y|ies|ied|ying)|investigat(e|es|ed|ing)|worked on|look(ed)? into)\b", re.I)
WEAK_KO = re.compile(r"(탐구|탐색해|살펴보|알아보|공부하)")
HYPE_EN = re.compile(r"\b(pioneer(ing)?|revolution(ary|ize|ise)?|unprecedented|groundbreaking|ground-breaking|perfect(ly)?|novel paradigm|first(-ever)? to)\b", re.I)
HYPE_KO = re.compile(r"(최초|혁신적|혁명적|완벽|획기적|전례 없)")
PLACEHOLDER = re.compile(r"(\[확인 필요[^\]]*\]|\[기관별[^\]]*\]|\bTODO\b|\bTBD\b|\[PLACEHOLDER[^\]]*\]|\[[^\]]*기입[^\]]*\])")
CITE = re.compile(r"\[(\d+(?:\s*[,\u2013-]\s*\d+)*)\]")
REF_ENTRY = re.compile(r"^\s*\[(\d+)\]", re.M)


def cited_numbers(text):
    nums = set()
    for group in CITE.findall(text):
        for part in re.split(r"\s*,\s*", group):
            if re.search(r"[\u2013-]", part):
                a, b = re.split(r"\s*[\u2013-]\s*", part)
                nums.update(range(int(a), int(b) + 1))
            else:
                nums.add(int(part))
    return nums


def check(path):
    text = Path(path).read_text(encoding="utf-8")
    m = REF_HEADINGS.search(text)
    body, refs = (text[: m.start()], text[m.end():]) if m else (text, "")
    report = {"file": path}

    sections, total = [], 0
    for chunk in re.split(r"\n(?=##\s)", "\n" + body):
        lines = chunk.strip().split("\n", 1)
        if not lines[0].startswith("## "):
            continue
        n = len(re.sub(r"\s", "", lines[1] if len(lines) > 1 else ""))
        sections.append((lines[0][3:].strip(), n))
        total += n
    report["sections"] = [(h, n, round(100 * n / total) if total else 0) for h, n in sections]

    report["dashes"] = len(DASH.findall(text))
    report["cjk"] = len(CJK.findall(body))
    report["weak"] = sorted({w.group(0) for w in WEAK_EN.finditer(body)} | {w.group(0) for w in WEAK_KO.finditer(body)})
    report["hype"] = sorted({w.group(0) for w in HYPE_EN.finditer(body)} | {w.group(0) for w in HYPE_KO.finditer(body)})
    report["placeholders"] = PLACEHOLDER.findall(text)
    report["placeholders"] = [p[0] if isinstance(p, tuple) else p for p in report["placeholders"]]
    used = cited_numbers(body)
    listed = {int(n) for n in REF_ENTRY.findall(refs)}
    report["cited_not_listed"] = sorted(used - listed)
    report["listed_not_cited"] = sorted(listed - used)
    report["n_refs"] = len(listed)
    return report


def show(r):
    print(f"== {r['file']}")
    for h, n, pct in r["sections"]:
        print(f"  {pct:3d}%  {n:6d}  {h}")
    print(f"  em/en dashes: {r['dashes']}   non-Hangul CJK in body: {r['cjk']}")
    print(f"  weak verbs: {', '.join(r['weak']) or 'none'}")
    print(f"  hype words: {', '.join(r['hype']) or 'none'}")
    print(f"  placeholders: {len(r['placeholders'])}" + (f"  {r['placeholders'][:5]}" if r["placeholders"] else ""))
    print(f"  references: {r['n_refs']}   cited but not listed: {r['cited_not_listed'] or 'none'}   listed but not cited: {r['listed_not_cited'] or 'none'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--strict", action="store_true", help="exit 1 if dashes, hype words, CJK, or placeholders remain")
    a = ap.parse_args()
    bad = False
    for f in a.files:
        r = check(f)
        show(r)
        bad |= bool(r["dashes"] or r["cjk"] or r["hype"] or r["placeholders"])
    sys.exit(1 if a.strict and bad else 0)


if __name__ == "__main__":
    main()
