#!/usr/bin/env python3
"""Mechanical checks for academic CVs (Markdown, Typst, LaTeX, plain text, or PDF via pdftotext).

Reports: pages (PDF) or estimated length, publication status labels found, "under review/submitted" lines without
a journal name, years out of reverse order within sections, whether the own name appears in bold in source files,
impact-factor or h-index mentions, em/en dashes, placeholders, and --max-pages overflow.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

DASH = re.compile(r"[\u2013\u2014]")
RANGE_DASH = re.compile(r"(?<=[\dA-Za-z.])\s?\u2013\s?(?=[\dA-Z]|present|now)", re.I)
PLACEHOLDER = re.compile(r"(\[확인 필요[^\]]*\]|\bTODO\b|\bTBD\b|\bXXX\b|\[PLACEHOLDER[^\]]*\])")
METRIC = re.compile(r"\b(impact factor|JIF|h-index|h index|i10)\b", re.I)
STATUS = {
    "accepted/in press": re.compile(r"\b(accepted|in press|forthcoming)\b", re.I),
    "preprint/arXiv": re.compile(r"\b(preprint|arXiv:\s*\d{4}\.\d{4,5})", re.I),
    "submitted/under review": re.compile(r"\b(submitted|under review|in review|in revision)\b", re.I),
    "in preparation": re.compile(r"\b(in preparation|in prep\.?|work in progress)\b", re.I),
}
JOURNAL_HINT = re.compile(r"(Phys\.|Rev\.|J\.|Journal|Lett\.|Nature|Science|Proc\.|JCAP|JHEP|Prog\.|Eur\.|Mon\.|Astrophys|NeurIPS|ICML|ICLR|IEEE|Trans\.|to [A-Z])")
HEADING = re.compile(r"^\s*(#{1,4}\s|=+\s|#\w*section\[|\\(sub)*section\*?\{|\*\*[A-Z][^*]{2,40}\*\*\s*$)", re.I)
YEAR = re.compile(r"\b(19[89]\d|20[0-4]\d)\b")


def load(path):
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        if not shutil.which("pdftotext"):
            sys.exit("pdftotext not found; install poppler-utils or pass the source file")
        text = subprocess.run(["pdftotext", "-layout", str(p), "-"], capture_output=True, text=True).stdout
        pages = text.count("\f") + (0 if text.endswith("\f") else 1)
        return text, pages, False
    text = p.read_text(encoding="utf-8")
    return text, None, True


def bold_name(text, names):
    pats = [r"\*\*[^*\n]*{n}[^*\n]*\*\*", r"(?<![*\w])\*[^*\n]*{n}[^*\n]*\*(?!\*)", r"\\textbf\{{[^}}]*{n}[^}}]*\}}", r"#strong\[[^\]]*{n}[^\]]*\]"]
    for n in names:
        en = re.escape(n)
        if any(re.search(pt.format(n=en), text) for pt in pats):
            return True
    return False


def year_order_issues(text):
    issues, section, last = [], "start", None
    for i, line in enumerate(text.splitlines(), 1):
        if HEADING.match(line):
            section, last = line.strip()[:40], None
            continue
        years = [int(y) for y in YEAR.findall(line)]
        if not years:
            continue
        y = years[0]  # start year of the item; ranges like 2017--2025 compare by start
        if last is not None and y > last:
            issues.append((i, section, last, y))
        last = y
    return issues


def check(path, names, max_pages, no_metrics):
    text, pages, is_source = load(path)
    r = {"file": path, "pages": pages}
    r["words"] = len(re.findall(r"\S+", text))
    r["status"] = {k: len(v.findall(text)) for k, v in STATUS.items()}
    r["review_no_journal"] = [ln.strip()[:90] for ln in text.splitlines()
                              if STATUS["submitted/under review"].search(ln) and not JOURNAL_HINT.search(ln)]
    r["order_issues"] = year_order_issues(text)
    r["bold_name"] = bold_name(text, names) if (is_source and names) else None
    r["metrics"] = sorted({m.group(0) for m in METRIC.finditer(text)})
    r["range_dashes"] = len(RANGE_DASH.findall(text))
    r["dashes"] = len(DASH.findall(text)) - r["range_dashes"]
    r["placeholders"] = PLACEHOLDER.findall(text)
    r["overflow"] = bool(max_pages and pages and pages > max_pages)
    fails = []
    if r["dashes"]:
        fails.append("em/en dash")
    if r["placeholders"]:
        fails.append("placeholders")
    if r["overflow"]:
        fails.append(f"{pages} pages > {max_pages}")
    if no_metrics and r["metrics"]:
        fails.append("metrics mentioned")
    if r["bold_name"] is False:
        fails.append("own name not bolded")
    r["fails"] = fails
    return r


def show(r, max_pages):
    print(f"== {r['file']}")
    size = f"pages: {r['pages']}" if r["pages"] else f"words: {r['words']} (source; render to count pages)"
    print(f"  {size}" + (f" (limit {max_pages})" if max_pages else ""))
    print("  status labels: " + ", ".join(f"{k} {v}" for k, v in r["status"].items()))
    if r["review_no_journal"]:
        print(f"  submitted/under review without a journal name: {len(r['review_no_journal'])}")
        for ln in r["review_no_journal"][:5]:
            print(f"    - {ln}")
    if r["order_issues"]:
        print(f"  years out of reverse order (check; tables and ranges can trigger this): {len(r['order_issues'])}")
        for i, sec, a, b in r["order_issues"][:6]:
            print(f"    - line {i} in [{sec}]: {b} after {a}")
    if r["bold_name"] is not None:
        print(f"  own name bolded: {r['bold_name']}")
    print(f"  metrics: {', '.join(r['metrics']) or 'none'}   prose em/en dashes: {r['dashes']} (en dashes in date or page ranges: {r['range_dashes']}, allowed)   placeholders: {len(r['placeholders'])}")
    print(f"  issues: {'; '.join(r['fails']) or 'none'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--name", action="append", default=[], help="own name as printed in author lists (repeatable)")
    ap.add_argument("--max-pages", type=int, default=0)
    ap.add_argument("--no-metrics", action="store_true", help="treat impact factor or h-index mentions as failures")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    bad = False
    for f in a.files:
        r = check(f, a.name, a.max_pages, a.no_metrics)
        show(r, a.max_pages)
        bad |= bool(r["fails"])
    sys.exit(1 if a.strict and bad else 0)


if __name__ == "__main__":
    main()
