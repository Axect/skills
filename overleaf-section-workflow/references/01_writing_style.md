# Writing style rules

These rules are absolute for paper drafts produced via this workflow. Each is the result of a concrete pain point in real drafting sessions.

## Rule 1: No em-dashes or en-dashes

**Forbidden characters**:
- Em-dash `—` (U+2014)
- En-dash `–` (U+2013)

These are AI-writing-style markers and physics papers do not use them in body text. Replace with:
- Period + new sentence
- Comma
- Parentheses for asides
- Hyphen `-` for compound words

**Verification**: after every edit, run
```bash
grep -cP "[\x{2013}\x{2014}]" <file>
```
The count must be `0`. If non-zero, find the offenders and replace.

Common AI-style patterns to scrub:
- `즉 X — Y` → `즉 X, Y` or `즉 X. Y`
- `range A–B` → `range A-B` or `A to B`
- `(a)–(c)` → `(a)-(c)`

## Rule 2: No forward references in background sections

Background / setup sections (§Introduction, §Background, §Physics setup) must stand alone. They may **not** preview methodology, results, or discussion.

**Forbidden patterns** in background sections:
- `§\ref{sec:inverse} 에서 다루는 DeCLA ...`
- `본 연구의 §5 에서 ... 을 정량적으로 통제한다`
- `이는 §3.3 에서 ... 으로 보완한다`
- "App. B 의 normalization floor 와 직결된다"

Methodology / results sections may reference earlier sections (they build *on* background). The asymmetry is intentional.

If a forward reference is removed, also remove the inline label "(App. B)" or "(§5)" that was being previewed. Don't leave dangling labels.

## Rule 3: "본 연구는" / "in this work" only for design statements

Allowed:
- `본 연구는 GBP 를 backbone 으로 채택한다` (design choice, in-section claim)
- `본 연구의 중심 대상인 Hawking 연산자` (central-object declaration)
- `In this work we adopt X` (design choice)

Forbidden:
- `본 연구의 §5 에서 다루는 ...` (forward reference disguised as self-mention)
- `본 연구의 normalization floor 와 직결된다 (App. B)` (forward reference)

Rule of thumb: if "본 연구" is followed by a `\ref{}` to a later section, it's a forward reference. Remove.

## Rule 4: Soften absolute claims

Physics papers prefer hedged language. Avoid:
- "표준이다" / "is the standard"
- "확실하다" / "is certain"
- "최선이다" / "is the best"
- "처음이다" / "is the first"

Use instead:
- "표준으로 여겨진다" / "is the conventional choice"
- "널리 사용된다" / "is widely used"
- "우리가 아는 한 ... 없다" / "to our knowledge ... has not been adopted"
- "기존 ... 에 비해 더 ..." / "improves over prior ... by ..."

For novelty claims specifically, see Rule 6.

## Rule 5: Avoid blog-tone phrases

Forbidden register:
- "왜 단순한 직접 역산이 통하지 않으며" (rhetorical question)
- "본 연구의 §X 에서 다루는 Y 는 이 문제를 정량적으로 통제한다" (forecasting)
- "부수적으로, ... 는 별도의 audit 이 필요하며 §Y 에서 다룬다" (preview)

These read like tutorial blog posts, not papers. Replace with declarative mathematical statements that do not preview later content.

Test: if a sentence describes what *will be done* in another section, delete it. The other section will speak for itself.

## Rule 6: Novelty claim hedging

When claiming a contribution is "new", always:
1. Hedge with "우리가 아는 한" / "to our knowledge" / "we are not aware of"
2. Cite the closest prior art to show you searched
3. Distinguish what is new (e.g., "PBH 문헌에 도입") from what is not (e.g., the distribution itself was defined by McDonald 1984)
4. Acknowledge near-misses that a referee might point at (e.g., BPL on $\mathcal{P}_\zeta(k)$ vs BPL on $\psi(M)$)

Pattern:
```
[Closest prior art] has quantitatively recognized [X], and [related construction] has been used in [adjacent context] (cite). To our knowledge, however, no prior work has [strict claim]. We introduce [contribution] as [specific role].
```

Verify novelty claims with `/deep-research` in fact-check mode before final submission.

## Rule 7: First-use spell-out for acronyms

Every acronym must be spelled out on first use. Examples encountered:

- ChPT → "Chiral Perturbation Theory (ChPT)"
- DGLAP → "Dokshitzer-Gribov-Lipatov-Altarelli-Parisi (DGLAP)"
- GBP → "Generalized Beta Prime (GBP)"
- FSR → "Final State Radiation (FSR)"
- BBKS → "BBKS peak theory" (Bardeen-Bond-Kaiser-Szalay; can spell out fully on first use depending on context)
- PBH → "Primordial Black Hole (PBH)" on first use in the abstract / §1 only

Subsequent uses can be the acronym alone.

## Rule 8: Standard textbook references for canonical results

Some results are textbook material and should be cited to canonical textbooks, not journal papers:

- Hadamard well-posedness three conditions → Hadamard 1902 (Princeton Univ. Bull. 13, 49)
- Compact operator on infinite-dim space → unbounded inverse → Engl-Hanke-Neubauer 1996 (Springer)
- Hilbert-Schmidt integral operator continuous kernel → compact → Kress 2014 (Springer, Applied Math. Sci.)
- ChPT foundational → Weinberg 1979 + Gasser-Leutwyler 1984
- DGLAP foundational → Gribov-Lipatov 1972 + Dokshitzer 1977 + Altarelli-Parisi 1977

Do not cite recent journal articles for these; the canonical textbook is the right answer.

## Rule 9: Self-evaluation before applying user-suggested wording

When the user proposes specific wording, *do not* simply apply it. Evaluate first:
- Is the technical terminology standard for the field?
- Does the sentence claim something the citations support?
- Does it introduce non-standard jargon (e.g., "biased solver" instead of "regularization")?

If the user's wording is non-standard, say so. Propose alternatives that combine the user's framing with standard terminology. The user expects critical evaluation, not stenography.

Example: User suggests "biased solver". You should evaluate that "biased solver" is non-standard in inverse-problem literature (standard is "regularization"), then propose a combined version: "stability 를 얻는 대신 bias 를 받아들이는 정규화 (regularisation)".

## Rule 10: Section narratives, not stitched paragraphs

Each section should have a clear narrative arc, signposted in the opening paragraph (roadmap). Avoid stitching together independent paragraphs.

Good opening:
> "본 절은 PBH 문헌에서 canonical 한 3 개 parametric family (Log-Normal, Power-Law, Critical Collapse) 를 먼저 정리하고, Power-Law 의 불연속성을 해소하는 Smooth Power-Law 의 도입을 거쳐 이들이 Stacy 의 generalized gamma family 안에서 어떻게 통합되는지를 보인다. 마지막으로 Stacy 의 *고질량 지수 cutoff* 한계가 ... 본 연구가 도입하는 GBP family 를 제시한다."

This previews the narrative arc *within the section*, which is fine. Forward references *outside the section* are forbidden (Rule 2).
