#!/usr/bin/env python3
"""Mechanical checks for research and project proposals (Markdown, Korean or English).

Reports per file: share of each `## ` section (whitespace-free characters, references excluded), required
elements found or missing, number of objective headings, em/en dashes, non-Hangul CJK, weak verbs, hype words,
placeholders, cited versus listed references, and characters against --max-chars.
--strict exits 1 on missing elements, dashes, CJK, hype, placeholders, citation mismatches, or overflow.
"""
import argparse
import re
import sys
from pathlib import Path

REF_HEADINGS = re.compile(r"^#{1,3}\s+(참고문헌|References|Bibliography)\s*$", re.M)
DASH = re.compile(r"[\u2013\u2014]")
CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
WEAK = re.compile(r"\b(explor(e|es|ed|ing)|stud(y|ies|ied|ying)|investigat(e|es|ed|ing)|worked on|look(ed)? into|understand)\b|탐구|탐색해|살펴보|알아보", re.I)
HYPE = re.compile(r"\b(pioneer(ing)?|revolution(ary|ize|ise)?|unprecedented|groundbreaking|ground-breaking|game[- ]chang\w*|perfect(ly)?|first(-ever)? to)\b|최초|혁신적|혁명적|완벽|획기적|전례 없", re.I)
PLACEHOLDER = re.compile(r"(\[확인 필요[^\]]*\]|\[기관별[^\]]*\]|\bTODO\b|\bTBD\b|\[PLACEHOLDER[^\]]*\]|\[[^\]]*기입[^\]]*\])")
CITE = re.compile(r"\[(\d+(?:\s*[,\u2013-]\s*\d+)*)\]")
REF_ENTRY = re.compile(r"^\s*\[(\d+)\]", re.M)
OBJECTIVE_HEAD = re.compile(r"^#{2,4}\s*(목표|과제|Objective|Aim|Specific Aim|WP|Work Package)\s*\d*", re.M | re.I)

ELEMENTS = {
    "objectives": r"목표|objective|\baims?\b",
    "state_of_the_art": r"선행\s*연구|기존\s*연구|연구\s*동향|state of the art|state-of-the-art|prior work|현재.{0,6}(방법|연구)",
    "methods": r"방법|접근|method|approach",
    "work_plan": r"일정|작업\s*계획|마일스톤|년차|개월|work plan|work package|timeline|milestone|month|year 1|first year",
    "risks": r"위험|대안|위험\s*요소|risk|fallback|mitigat|alternative",
    "expected_results": r"산출|성과|기대|deliverable|expected (result|outcome)|outcome|impact",
    "host": r"기관|호스트|이 곳|host|institute|environment",
    "summary": r"요약|summary|abstract|overview",
}
DEFAULT_REQUIRE = ["objectives", "state_of_the_art", "methods", "work_plan", "risks", "expected_results"]


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


def check(path, require, max_chars):
    text = Path(path).read_text(encoding="utf-8")
    m = REF_HEADINGS.search(text)
    body, refs = (text[: m.start()], text[m.end():]) if m else (text, "")
    r = {"file": path}
    sections, total = [], 0
    for chunk in re.split(r"\n(?=##\s)", "\n" + body):
        lines = chunk.strip().split("\n", 1)
        if not lines[0].startswith("## "):
            continue
        n = len(re.sub(r"\s", "", lines[1] if len(lines) > 1 else ""))
        sections.append((lines[0][3:].strip(), n))
        total += n
    r["sections"] = [(h, n, round(100 * n / total) if total else 0) for h, n in sections]
    r["chars"] = len(re.sub(r"\s", "", body))
    low = body.lower()
    r["missing"] = [e for e in require if not re.search(ELEMENTS[e], low, re.I)]
    r["objectives"] = len(OBJECTIVE_HEAD.findall(body))
    r["dashes"] = len(DASH.findall(text))
    r["cjk"] = len(CJK.findall(body))
    r["weak"] = sorted({w.group(0) for w in WEAK.finditer(body)})
    r["hype"] = sorted({w.group(0) for w in HYPE.finditer(body)})
    r["placeholders"] = [p if isinstance(p, str) else p[0] for p in PLACEHOLDER.findall(text)]
    used, listed = cited_numbers(body), {int(n) for n in REF_ENTRY.findall(refs)}
    r["cited_not_listed"], r["listed_not_cited"], r["n_refs"] = sorted(used - listed), sorted(listed - used), len(listed)
    r["overflow"] = bool(max_chars and r["chars"] > max_chars)
    r["max_chars"] = max_chars
    return r


def show(r):
    print(f"== {r['file']}")
    for h, n, pct in r["sections"]:
        print(f"  {pct:3d}%  {n:6d}  {h}")
    lim = f" (limit {r['max_chars']})" if r["max_chars"] else ""
    print(f"  characters without spaces (body): {r['chars']}{lim}")
    print(f"  missing elements: {', '.join(r['missing']) or 'none'}")
    note = "" if 2 <= r["objectives"] <= 3 else "  (expected 2~3)"
    print(f"  objective headings: {r['objectives']}{note}")
    print(f"  em/en dashes: {r['dashes']}   non-Hangul CJK in body: {r['cjk']}")
    print(f"  weak verbs: {', '.join(r['weak']) or 'none'}   hype words: {', '.join(r['hype']) or 'none'}")
    print(f"  placeholders: {len(r['placeholders'])}" + (f"  {r['placeholders'][:5]}" if r["placeholders"] else ""))
    print(f"  references: {r['n_refs']}   cited but not listed: {r['cited_not_listed'] or 'none'}   listed but not cited: {r['listed_not_cited'] or 'none'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--require", default=",".join(DEFAULT_REQUIRE),
                    help=f"comma-separated elements from: {', '.join(ELEMENTS)}")
    ap.add_argument("--max-chars", type=int, default=0, help="limit on whitespace-free characters of the body")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    require = [x.strip() for x in a.require.split(",") if x.strip()]
    bad_names = [x for x in require if x not in ELEMENTS]
    if bad_names:
        ap.error(f"unknown elements: {bad_names}")
    bad = False
    for f in a.files:
        r = check(f, require, a.max_chars)
        show(r)
        bad |= bool(r["missing"] or r["dashes"] or r["cjk"] or r["hype"] or r["placeholders"]
                    or r["cited_not_listed"] or r["listed_not_cited"] or r["overflow"])
    sys.exit(1 if a.strict and bad else 0)


if __name__ == "__main__":
    main()
