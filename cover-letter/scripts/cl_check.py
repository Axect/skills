#!/usr/bin/env python3
"""Mechanical checks for cover letters, supporting statements, and inquiry emails (Markdown or text).

Reports per file: word and character counts of the body (text before a References/참고문헌 heading),
em/en dashes, non-Hangul CJK, clichés and hype words, hedges, share of English sentences starting with
"I", placeholder slots, and institution names (--expect must appear, --forbid must not).
--strict exits 1 on dashes, CJK, clichés, hedges, placeholders, missing expected or present forbidden names,
or a body longer than --max-words.
"""
import argparse
import re
import sys
from pathlib import Path

END_HEADINGS = re.compile(r"^#{1,3}\s+(참고문헌|References|Bibliography)\s*$", re.M)
DASH = re.compile(r"[\u2013\u2014]")
CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
CLICHE_EN = re.compile(
    r"\b(passionate|passion for|perfect fit|ideal candidate|uniquely qualified|prestigious|world[- ]class|"
    r"excellent communicator|highly motivated|hard[- ]working|team player|dream (job|position)|"
    r"pioneer(ing)?|groundbreaking|revolutionary|unprecedented|cutting[- ]edge|renowned)\b", re.I)
CLICHE_KO = re.compile(r"(열정|최적의 후보|명문|세계 최고|완벽한 적임|꿈의|최초|혁신적|획기적)")
HEDGE_EN = re.compile(r"\b(I will try|I would try|I hope to|I hope that|I believe I|I think I|I feel that|might be able to)\b", re.I)
HEDGE_KO = re.compile(r"(노력해 보겠|시도해 보겠|할 수 있을 것 같|라고 생각합니다|하고 싶습니다만)")
PLACEHOLDER = re.compile(r"(\[확인 필요[^\]]*\]|\[기관별[^\]]*\]|\bTODO\b|\bTBD\b|\bPENDING\b|\[PLACEHOLDER[^\]]*\]|\[[^\]]*기입[^\]]*\])")
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def check(path, expect, forbid, max_words):
    text = Path(path).read_text(encoding="utf-8")
    m = END_HEADINGS.search(text)
    body = text[: m.start()] if m else text
    prose = re.sub(r"^#.*$", "", body, flags=re.M)
    r = {"file": path}
    r["words"] = len(re.findall(r"\S+", prose))
    r["chars"] = len(re.sub(r"\s", "", prose))
    r["dashes"] = len(DASH.findall(text))
    r["cjk"] = len(CJK.findall(body))
    r["cliches"] = sorted({x.group(0) for x in CLICHE_EN.finditer(prose)} | {x.group(0) for x in CLICHE_KO.finditer(prose)})
    r["hedges"] = sorted({x.group(0) for x in HEDGE_EN.finditer(prose)} | {x.group(0) for x in HEDGE_KO.finditer(prose)})
    r["placeholders"] = [p if isinstance(p, str) else p[0] for p in PLACEHOLDER.findall(text)]
    sents = [s.strip() for s in SENT_SPLIT.split(re.sub(r"\s+", " ", prose)) if re.search(r"[A-Za-z]", s)]
    i_start = [s for s in sents if re.match(r"^(I|I'm|I’m|I've|I’ve)\b", s)]
    r["i_share"] = round(100 * len(i_start) / len(sents)) if sents else 0
    low = text.lower()
    r["missing_expected"] = [e for e in expect if e.lower() not in low]
    r["forbidden_present"] = [f for f in forbid if f.lower() in low]
    r["too_long"] = bool(max_words and r["words"] > max_words)
    return r


def show(r, max_words):
    print(f"== {r['file']}")
    lim = f" (limit {max_words})" if max_words else ""
    print(f"  words: {r['words']}{lim}   characters without spaces: {r['chars']}")
    print(f"  em/en dashes: {r['dashes']}   non-Hangul CJK in body: {r['cjk']}")
    print(f"  clichés/hype: {', '.join(r['cliches']) or 'none'}")
    print(f"  hedges: {', '.join(r['hedges']) or 'none'}")
    print(f"  English sentences starting with I: {r['i_share']}%")
    print(f"  placeholders: {len(r['placeholders'])}" + (f"  {r['placeholders'][:5]}" if r["placeholders"] else ""))
    if r["missing_expected"] or r["forbidden_present"]:
        print(f"  missing expected names: {r['missing_expected'] or 'none'}   forbidden names present: {r['forbidden_present'] or 'none'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--expect", action="append", default=[], help="name that must appear (repeatable)")
    ap.add_argument("--forbid", action="append", default=[], help="name that must not appear (repeatable)")
    ap.add_argument("--max-words", type=int, default=0)
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    bad = False
    for f in a.files:
        r = check(f, a.expect, a.forbid, a.max_words)
        show(r, a.max_words)
        bad |= bool(r["dashes"] or r["cjk"] or r["cliches"] or r["hedges"] or r["placeholders"]
                    or r["missing_expected"] or r["forbidden_present"] or r["too_long"])
    sys.exit(1 if a.strict and bad else 0)


if __name__ == "__main__":
    main()
