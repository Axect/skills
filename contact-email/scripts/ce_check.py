#!/usr/bin/env python3
"""Mechanical checks for academic contact emails (host inquiry, sponsor request, referee request, follow-up).

Input: Markdown or text with a `Subject:` or `제목:` line; everything after it is the body. Reports subject,
body words, question sentences, salutation, attachment mention, date mention, apology/gratitude stacking,
hedges, "bumping" phrases, casual greetings, em/en dashes, non-Hangul CJK, placeholders, and expected or
forbidden names. --strict exits 1 on any failure for the chosen --kind.
"""
import argparse
import re
import sys
from pathlib import Path

LIMITS = {"host": 250, "sponsor": 350, "referee": 350, "followup": 100}
NEED_ATTACH = {"host", "sponsor", "referee"}
NEED_DATE = {"sponsor", "referee"}

SUBJECT = re.compile(r"^\s*(?:\*\*)?(Subject|제목)(?:\*\*)?\s*[:：]\s*(.+)$", re.M | re.I)
DASH = re.compile(r"[\u2013\u2014]")
CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
SALUTE_OK = re.compile(r"^\s*(Dear\s+(Professor|Prof\.|Dr\.|Members|Hiring|Search)|.+(교수님|박사님|선생님)\s*(께|,))", re.M)
CASUAL = re.compile(r"^\s*(Hi|Hey|Hello|Yo)\b|^\s*안녕(하세요)?[,!]", re.M | re.I)
APOLOGY = re.compile(r"\b(sorry|apologi[sz]e|apologies|forgive me|bother(ing)? you)\b|죄송|실례|폐를", re.I)
THANKS = re.compile(r"\b(thank(s| you)|grateful|appreciate)\b|감사", re.I)
HEDGE = re.compile(r"\b(I was wondering if|just wanted to|if it's not too much|I hope this email finds you|maybe you could|perhaps you might)\b|혹시나|괜찮으시다면 혹시", re.I)
BUMP = re.compile(r"\b(bump(ing)?|top of your inbox|circle back|ping(ing)? you)\b", re.I)
ATTACH = re.compile(r"\b(attach(ed|ing)?|enclos(ed|e))\b|첨부", re.I)
DATE = re.compile(r"\b(20\d\d[-./]\d{1,2}[-./]\d{1,2}|\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2})\b|\d{1,2}\s*월\s*\d{1,2}\s*일|\d{1,2}-\d{1,2}", re.I)
PLACEHOLDER = re.compile(r"(\[확인 필요[^\]]*\]|\bTODO\b|\bTBD\b|\[PLACEHOLDER[^\]]*\]|\[[A-Z][A-Za-z /]*\]|\[[^\]]*기입[^\]]*\])")
QUESTION = re.compile(r"[^.?!\n]*\?|[^.?!\n]*(실 수 있을까요|주실 수 있으신지|가능할까요|여쭙고 싶습니다|여쭤봐도)")


def check(path, kind, expect, forbid, max_words):
    text = Path(path).read_text(encoding="utf-8")
    m = SUBJECT.search(text)
    subject = m.group(2).strip() if m else ""
    body = text[m.end():] if m else text
    r = {"file": path, "kind": kind, "subject": subject}
    limit = max_words or LIMITS[kind]
    r["limit"] = limit
    r["words"] = len(re.findall(r"\S+", re.sub(r"^#.*$", "", body, flags=re.M)))
    r["questions"] = len([q.group(0) for q in QUESTION.finditer(body) if q.group(0).strip()])
    r["salutation_ok"] = bool(SALUTE_OK.search(body))
    r["casual"] = bool(CASUAL.search(body))
    r["apologies"] = len(APOLOGY.findall(body))
    r["thanks"] = len(THANKS.findall(body))
    r["hedges"] = sorted({h.group(0) for h in HEDGE.finditer(body)})
    r["bump"] = sorted({b.group(0) for b in BUMP.finditer(body)})
    r["attach"] = bool(ATTACH.search(body))
    r["date"] = bool(DATE.search(body))
    r["dashes"] = len(DASH.findall(text))
    r["cjk"] = len(CJK.findall(text))
    r["placeholders"] = [p if isinstance(p, str) else p[0] for p in PLACEHOLDER.findall(text)]
    low = text.lower()
    r["missing_expected"] = [e for e in expect if e.lower() not in low]
    r["forbidden_present"] = [f for f in forbid if f.lower() in low]
    fails = []
    if not subject:
        fails.append("no subject line")
    if r["words"] > limit:
        fails.append(f"body {r['words']} words > {limit}")
    if r["questions"] < 1:
        fails.append("no direct question (the ask)")
    if not r["salutation_ok"]:
        fails.append("no formal salutation (Dear Professor/Dr. Surname)")
    if r["casual"]:
        fails.append("casual greeting")
    if r["apologies"]:
        fails.append("apology")
    if r["thanks"] > 2:
        fails.append(f"gratitude repeated {r['thanks']} times")
    if r["hedges"]:
        fails.append("hedges")
    if r["bump"]:
        fails.append("bumping phrase")
    if kind in NEED_ATTACH and not r["attach"]:
        fails.append("no attachment mention")
    if kind in NEED_DATE and not r["date"]:
        fails.append("no date")
    if r["dashes"]:
        fails.append("em/en dash")
    if r["placeholders"]:
        fails.append("placeholders")
    if r["missing_expected"]:
        fails.append("missing expected names")
    if r["forbidden_present"]:
        fails.append("forbidden names present")
    r["fails"] = fails
    return r


def show(r):
    print(f"== {r['file']}  [{r['kind']}]")
    print(f"  subject: {r['subject'] or '(none)'}")
    print(f"  body words: {r['words']} (limit {r['limit']})   questions: {r['questions']}   salutation ok: {r['salutation_ok']}")
    print(f"  attachment mentioned: {r['attach']}   date present: {r['date']}   apologies: {r['apologies']}   thanks: {r['thanks']}")
    print(f"  hedges: {', '.join(r['hedges']) or 'none'}   bumping: {', '.join(r['bump']) or 'none'}   casual greeting: {r['casual']}")
    print(f"  em/en dashes: {r['dashes']}   non-Hangul CJK: {r['cjk']}   placeholders: {len(r['placeholders'])}" + (f" {r['placeholders'][:4]}" if r["placeholders"] else ""))
    if r["missing_expected"] or r["forbidden_present"]:
        print(f"  missing expected: {r['missing_expected'] or 'none'}   forbidden present: {r['forbidden_present'] or 'none'}")
    print(f"  issues: {'; '.join(r['fails']) or 'none'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--kind", choices=sorted(LIMITS), default="host")
    ap.add_argument("--expect", action="append", default=[])
    ap.add_argument("--forbid", action="append", default=[])
    ap.add_argument("--max-words", type=int, default=0)
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    bad = False
    for f in a.files:
        r = check(f, a.kind, a.expect, a.forbid, a.max_words)
        show(r)
        bad |= bool(r["fails"])
    sys.exit(1 if a.strict and bad else 0)


if __name__ == "__main__":
    main()
