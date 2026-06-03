# Final verification — automated audit

Before declaring a review final, run the audit script below over each `*_submission.md` and `*_submission_en.md` file. Every check should return 0 (or a known-OK exception, e.g., `ò` inside `Aricò`).

## Audit script

```python
#!/usr/bin/env python3
"""Workshop-review submission audit. Run on *_submission.md and *_submission_en.md."""
import re
import sys
from pathlib import Path

# Forbidden Unicode (math + section sign + arrow + super/subscript)
FORBIDDEN_UNICODE = re.compile(
    r'[α-ωΑ-Ω²³⁴∈∉⊂⊆∪∩∀∃≈≤≥≠≪≫±×÷∞∂∇∫∑∏√→←↔↑↓⇒⇔ℝℕℤℂℓ°§]'
)

AI_PATTERNS = {
    "Em-dash in body":          r'(?<![\w])—(?![\w])',
    "Indeed/Moreover/Furthermore/Additionally":
                                 r'\b(Indeed|Moreover|Furthermore|Additionally),',
    "'suggesting X rather than Y'":
                                 r'suggesting [^.]+ rather than',
    "Semicolon + therefore":     r';[^.]*therefore',
    "'making it/the'":           r'making (it|the) \w+',
    "Although + therefore":      r'Although[^.]+therefore',
    "valuable substrate/strength/etc.":
                                 r'valuable (substrate|strength|insight|contribution|addition)',
    "Severity tag":              r' \((Critical|Major|Moderate|Minor|Moderate-Major|Moderate–Major|Minor-Moderate|Minor–Moderate)\)\.',
    "Orphan **(§N.X)**":          r'\*\*\(§\d+(?:\.\d+)?\)\*\*',
    "Non-negotiable":             r'\bNon-negotiable\b',
    "self-undermining":          r'self-undermining',
    "rarely seen / 보기 드문":      r'(rarely seen|보기 드문|흔치 않[다은]|워크샵 분량)',
    "Major revision and resubmit":
                                 r'(Major revision|재제출 권장|revise and resubmit)',
}

REQUIRED_SECTIONS = [
    "## Title",
    "## Rating",
    "## Confidence",
    "## Summary",
    "## Strengths",
    "## Weaknesses",
    "## Questions for Authors",
]

FORBIDDEN_SECTIONS = ["## Overall", "## Recommendation"]

OPENREVIEW_LABELS = {
    1: "Trivial or wrong",
    2: "Strong rejection",
    3: "Clear rejection",
    4: "Ok but not good enough - rejection",
    5: "Marginally below acceptance threshold",
    6: "Marginally above acceptance threshold",
    7: "Good paper, accept",
    8: "Top 50% of accepted papers, clear accept",
    9: "Top 15% of accepted papers, strong accept",
    10: "Top 5% of accepted papers, seminal paper",
}


def audit(path: Path) -> dict:
    content = path.read_text()
    body = "\n".join(content.split("\n")[1:])  # skip file-header line

    findings = {}

    # 1. Forbidden Unicode (with Aricò exception)
    unicode_hits = FORBIDDEN_UNICODE.findall(body)
    findings["unicode"] = sorted(set(unicode_hits))

    # 2. AI patterns
    for label, pattern in AI_PATTERNS.items():
        hits = re.findall(pattern, body, flags=re.IGNORECASE if not pattern.startswith(r'\b') else 0)
        if hits:
            findings[f"ai:{label}"] = len(hits)

    # 3. Section structure
    found_sections = re.findall(r'^## ([^\n]+)', content, flags=re.MULTILINE)
    for req in REQUIRED_SECTIONS:
        req_label = req.replace("## ", "")
        if not any(s.startswith(req_label) for s in found_sections):
            findings[f"missing:{req}"] = True

    for forb in FORBIDDEN_SECTIONS:
        forb_label = forb.replace("## ", "")
        if any(s.startswith(forb_label) for s in found_sections):
            findings[f"forbidden_section:{forb}"] = True

    # 4. Rating label exact match
    rating_match = re.search(r'## Rating: \*\*(\d+) ?/ ?10\*\* \((.*?)\)', content)
    if rating_match:
        rating = int(rating_match.group(1))
        label = rating_match.group(2)
        expected = OPENREVIEW_LABELS.get(rating)
        if expected and label != expected:
            findings["wrong_rating_label"] = (rating, label, expected)
    else:
        findings["missing_rating_line"] = True

    # 5. Title word count
    title_match = re.search(r'## Title\s*\n\n([^\n]+)', content)
    if title_match:
        title_wc = len(title_match.group(1).split())
        if not (8 <= title_wc <= 15):
            findings["title_wc"] = title_wc

    # 6. Body word count (allows extra room when Minor points section is present)
    body_wc = len(content.split())
    has_minor = '## Minor points' in content
    upper = 750 if has_minor else 600
    if not (300 <= body_wc <= upper):
        findings["body_wc"] = body_wc

    # 7. Fig refs in Summary
    summary_match = re.search(r'## Summary\s*\n\n([^#]+)', content)
    if summary_match:
        summary = summary_match.group(1)
        fig_in_summary = len(re.findall(r'\(Fig\.\s*\d+\)', summary))
        if fig_in_summary > 0:
            findings["fig_in_summary"] = fig_in_summary

    return findings


if __name__ == "__main__":
    for path in sys.argv[1:]:
        p = Path(path)
        f = audit(p)
        # Drop Aricò's 'ò' from unicode if it's the only one
        if f.get("unicode") and set(f["unicode"]) <= {"ò"}:
            f.pop("unicode")
        if not f:
            print(f"✅ {p.name}: clean")
        else:
            print(f"⚠️  {p.name}:")
            for k, v in f.items():
                print(f"     {k}: {v}")
```

## Expected output (clean review)

```
✅ 60_submission.md: clean
✅ 60_submission_en.md: clean
✅ 61_submission.md: clean
✅ 61_submission_en.md: clean
✅ 62_submission.md: clean
✅ 62_submission_en.md: clean
✅ 158_submission.md: clean
✅ 158_submission_en.md: clean
```

## How to invoke

```bash
python3 verify.py path/to/*_submission*.md
```

Save the script to `verify.py` in the working directory, or extract from this file as needed.

## Known exceptions

- **`ò`** in `Aricò` — author surname. The script auto-strips this from the Unicode findings.
- Sectioning `;` in citation lists like `(Schneider 2015; Aricò 2020)` — legitimate semicolons in citation context. The "Semicolon + therefore" check only triggers when `therefore` follows.
- Sectioning `;` in enumerations like `(a) ... ; (b) ... ; (c) ...` — legitimate. Only triggers as AI pattern when combined with `therefore`.
- **First-person hedges with substance** — `I'd suggest demoting X to Y because Z`, `I'm most confident on X-type critiques`, `I would move my rating to N+1 if X` are valid and should remain. The auditor does not flag first-person broadly; it would only flag a vague first-person like `I think this is interesting.` if such a pattern is added to `AI_PATTERNS`. Currently the script does not check first-person — that check is left to manual review (see `anti_patterns.md` §B1b).
- **Body word count up to 750** when a `## Minor points` section is present (vs 600 default).

## What to do when audit fails

For each finding:

| Finding | Fix |
|---------|-----|
| `unicode` | Replace per `references/anti_patterns.md` §B7 |
| `ai:Em-dash in body` | Replace `—` with `:`, `,`, sentence split, or `(...)` |
| `ai:Indeed/Moreover/...` | Remove the transition word; restart sentence |
| `ai:'suggesting X rather than Y'` | State the observation directly |
| `ai:Semicolon + therefore` | Split into two sentences |
| `ai:'making it/the'` | Replace formulaic closer with direct statement |
| `ai:valuable substrate/strength` | Replace with specific substance |
| `ai:Severity tag` | Remove tag; ordering conveys priority |
| `ai:Orphan **(§N.X)**` | Strip the bold reference; the question's content is self-contained |
| `ai:Non-negotiable` | Remove or replace with "essential for ..." |
| `ai:self-undermining` | Replace with "weakened by absence of ..." |
| `ai:rarely seen / 보기 드문` | Replace with substance-focused phrasing |
| `ai:Major revision and resubmit` | Reframe as declarative ("would clarify the contribution") |
| `missing:## <section>` | Add the section |
| `forbidden_section:## Overall` | Remove the section |
| `wrong_rating_label` | Use the exact OpenReview rubric string |
| `title_wc` | Tighten or expand the title to 10–14 words |
| `body_wc` | Compress (>600) or expand (<300) the body |
| `fig_in_summary` | Move Fig references out of Summary into Strengths/Weaknesses |
