# Anti-patterns in LLM-drafted reviews

A consolidated catalog of phrases, constructions, and structural artifacts that creep into LLM-generated reviews and should be excised before submission. Audit after every revision — these patterns regenerate.

## Structural anti-patterns

### A1 — Severity tags `(Critical)` / `(Major)` / `(Moderate)` / `(Minor)`

Reviewer-internal scaffolding only. OpenReview reviewers communicate severity via the **ordering** of weaknesses (most severe first) and via the prose, not via formal tags.

**Remove**: `**Reward function 의 method core spec 미공개** (Critical). SoftHat ...`
**Keep**: `**Reward function 의 method core spec 미공개**. SoftHat ...`

### A2 — Overall section

Redundant with the Rating field. Removes ~30–50 words per review. The Strengths/Weaknesses/Questions structure plus the Rating is self-sufficient. **The skill emits reviews with no Overall section by default.**

### A3 — Spotlight / Oral / Best Paper recommendations in the body

AC decisions. Reviewer-side advocacy in the author-visible body is overreach. If a workshop has a separate "Spotlight recommendation" field on its form, use that field; otherwise, omit.

### A4 — Orphan section references `(§4.1)`, `(§4.2)` etc. in Questions

Often emitted because the reviewer's internal review used a section-numbered structure, but the submission's Weaknesses are a plain numbered list with no `§` numbering. The reference points to nothing. Remove the bold `**(§4.X)**` prefix entirely; the question's content is self-contained.

### A5 — "Major revision and resubmit" framing

Workshops are typically accept/reject — there is no revision cycle. This language is journal-appropriate but workshop-inappropriate.

**Replace**: `Major revision (reward 공개, SQP baseline, ...) 후 재제출 권장.`
**With**: `A full reward specification, an SQP baseline, ... would clarify the contribution's strength.` (declarative, no revise-and-resubmit framing)

### A6 — Fig references in Summary

Summary is a neutral overview; specific Fig pointers belong in Strengths/Weaknesses where a specific claim is being made about that Fig. Move Fig references out of Summary.

## Phrase-level anti-patterns

### B1 — Reviewer-centric phrasing (nuanced rule)

The anti-pattern is *comparative / rarity* claims and *vague* first-person, **not** first-person itself. Substance-bearing first-person is OK.

#### B1a — Always remove (comparative / rarity claims)

| Avoid | Why | Substitute |
|-------|-----|------------|
| `워크샵 분량에서 보기 드문 self-criticism` | Reviewer's experience leaks; backhanded | `... taxonomy identifies concrete problems for follow-up work` |
| `흔치 않은 contribution depth` | Same | Describe the depth substantively |
| `이 paper 의 가장 강한 strength` | Reviewer-ranking framing | Just state the strength |
| `rarely seen in workshop submissions` | Same as Korean equivalent | Substance |
| `in my experience this is unusual` | Same | Cut the comparison; describe what is unusual |

#### B1b — Remove if standalone, keep if followed by substance (first-person hedges)

| Pattern | Verdict |
|---------|---------|
| `I find this interesting.` | ❌ vague compliment — remove or follow with substance |
| `I find this interesting and novel because the linearity-in-monomials structure enables ...` | ✅ first-person + substance — keep |
| `I think the paper is good.` | ❌ vague — remove |
| `I'd suggest demoting Theorem 1 to Proposition because ...` | ✅ first-person + constructive editorial suggestion — keep |
| `I'm most confident on attribution critiques, less confident on physics-novelty observations.` | ✅ granular confidence statement — keep |
| `I enjoyed reading the paper and believe [audience] should engage with it.` | ✅ humanizing close + audience case — keep (in Strengths or as final sentence) |
| `In my opinion this method works.` | ❌ subjective opinion without substance — remove |
| `I recommend weak-accept.` | ✅ explicit verdict — keep (especially in score-mobility declarations) |

Rule of thumb: if a first-person sentence can be deleted *without losing information*, it is vague and should be removed. If deleting it would lose a *reason*, a *suggestion*, a *confidence calibration*, or a *constructive proposal*, keep it.

### B2 — Vague compliments

| Avoid | Why | Substitute |
|-------|-----|------------|
| `valuable substrate` | Vague | `useful starting point for follow-up RL-fusion work` |
| `valuable strength` | Vague | Name what specifically the strength enables |
| `interesting framing` | Vague | Name the substantive insight |
| `novel approach` | Vague (acceptable only in Title for brevity) | Name what is new |

In the **Title**, "novel" is acceptable as a brief descriptor (Titles trade verbosity for substance). In the **body**, replace with the specific contribution.

### B3 — AI-style transitions

| Avoid | Substitute |
|-------|------------|
| `Indeed,` (sentence start) | Direct statement, no transition |
| `Moreover,` / `Furthermore,` / `Additionally,` | Direct statement |
| `However,` (overused) | Often the sentence works without it |
| `On the one hand, ... on the other hand, ...` | Plain coordinate clauses |

### B4 — Hedged compound constructions

| Avoid | Why | Substitute |
|-------|-----|------------|
| `X is important to the likelihood, but its sensitivity is not demonstrated; Y may therefore depend on this hyperparameter` | Semicolon + `therefore` AI construction | Two short sentences |
| `suggesting partial learning rather than full recovery` | AI-style epistemic hedging | Just state the observation |
| `making the paper a strong fit for workshop discussion` | Formulaic closer | Cut or state directly |
| `Although the paper gives X, follow-up researchers therefore cannot...` | Concession-conclusion AI construction | Direct: "X is provided, but Y is not. Without Y, ..." |

### B5 — Absolutist verdicts (especially at Confidence 3)

| Avoid | Why | Substitute |
|-------|-----|------------|
| `재현 불가능` / `fundamentally non-reproducible` | Conf-3 reviewer asserting an absolute | `재현하기 어렵다` / `limits reproducibility` |
| `self-undermining` | Judgmental | `weakened` / `without substantive support` |
| `Non-negotiable` (in Questions) | Dictatorial | Cut, or "essential for reproducibility" |
| `impossible to decompose` | Absolute | `cannot be decomposed` |
| `evaluable 한 상태가 아니다` | Strong overreach | `limits the evaluability of the contribution` |

### B6 — Em-dash (`—`) in body

The body of a review should be em-dash-free. Em-dash is acceptable in the file header (`# OpenReview Submission — Paper #N`) but not in prose. Replace with:

- `:` (for elaboration)
- `,` (for an aside)
- `;` (sparingly, for parallel clauses)
- A period (split into two sentences)
- Parentheses (for parenthetical)

En-dash (`–`) for ranges (`Tables 1–3`, `0.1–0.3 dex`) is acceptable.

### B7 — Unicode math

All math goes through LaTeX. The skill enforces zero Unicode math in the body. Common offenders:

| Unicode | LaTeX |
|---------|-------|
| `α, β, γ, σ, λ, μ` | `$\alpha$, $\beta$, $\gamma$, $\sigma$, $\lambda$, $\mu$` |
| `²`, `³`, `⁴` | `$^2$`, `$^3$`, `$^4$` |
| `≈`, `≠`, `≤`, `≥` | `$\approx$`, `$\neq$`, `$\leq$`, `$\geq$` |
| `±`, `×`, `÷` | `$\pm$`, `$\times$`, `$\div$` |
| `→`, `←`, `↔`, `↑`, `↓` | `$\to$`, `$\leftarrow$`, `$\leftrightarrow$`, `$\uparrow$`, `$\downarrow$` |
| `ℝ`, `ℕ`, `ℤ`, `ℂ` | `$\mathbb{R}$`, `$\mathbb{N}$`, `$\mathbb{Z}$`, `$\mathbb{C}$` |
| `∈`, `⊂`, `∪`, `∩` | `$\in$`, `$\subset$`, `$\cup$`, `$\cap$` |
| `∞`, `∂`, `∇`, `∫`, `∑` | `$\infty$`, `$\partial$`, `$\nabla$`, `$\int$`, `$\sum$` |
| `§` (section sign) | `Sec.` (text replacement; this is **not** math) |
| `°` (degree) | `$^{\circ}$` |

### B8 — Italic-quoting paraphrases

If a phrase is in italic-quote form (`*"..."*`), it must be a verbatim quote from the paper. Paraphrases of the paper's wording must not be quoted.

**Wrong**: italic-quoting `*"reward ↑ ≠ feasibility"*` when the paper actually says "Reward–feasibility mismatch". The arrow-and-inequality form is the reviewer's coinage.

**Right**: italic-quote only `*"Reward–feasibility mismatch"*` and `*"Constraint gap"*` (the paper's actual phrasings).

When in doubt during fact-check: read the PDF passage and either re-quote verbatim or paraphrase without italic-quote.

### B9 — Checklist meta-references

Reviewer-internal references like `v3 §11`, `anti-anchoring 적용 후`, `criteria 중 N개 충족`, `본 batch 의 다른 paper` are invisible to the author. Strip them all.

## Verification heuristics

After every revision pass, run the audit script (`references/verify.md`) which checks:
- Em-dash in body (excluding file header line)
- Unicode math characters
- `§` characters
- `Indeed,` / `Moreover,` / `Furthermore,` / `Additionally,` at sentence start
- `valuable substrate`, `valuable strength`, `interesting framing` exact strings
- Other-paper number references (`#60`, `#61`, etc. when not the current paper)
- `(Critical)`, `(Major)`, `(Moderate)`, `(Minor)` tags
- Orphan `**(§N.X)**` references
- `Overall` section presence (should be 0)
- "Major revision" / "재제출 권장" phrasing
- Italic-quote contents (verify against PDF, manual step)

## Constructive patterns to *include* (not anti-patterns)

The following patterns were missing from v1 and should be actively included where applicable.

### C1 — Granular confidence statement (Confidence-3 standard)

Replace generic "some familiarity with X" with a structured per-claim-type breakdown:

> "Comfortable with [ML side / theory / framing]. Not [a domain] expert; cannot independently judge [specific item]. **Most confident on [X-type] critiques, less confident on [Y-type] observations. Please weight my comments accordingly.**"

The final sentence tells the AC how to weight different parts of the review.

### C2 — Cheap-but-clarifying experiment suggestions

When the paper has an *internal resource* (analytic forward model, simulation engine, automated tool used for data generation) that is *available at test time at no cost*, identify the ablation it could settle:

> "[Tool] is automated and was used to generate the training data, so it is available at test time. Comparing [tool-based] X to [learned] X would settle whether [the load-bearing claim is true]."

This is the highest-leverage type of weakness — the suggested experiment costs the author nothing and answers a question the reviewer is actually asking.

### C3 — Score-mobility declaration (borderline ratings only)

For Rating 5–6, conclude with explicit elasticity:

> "If the authors add [specific item] in revision, I would move my rating to [N+1]."

Gives the author a rebuttal target and the AC a sense of the score's flexibility.

### C4 — Structural / editorial suggestions

Where a critique points to a structural fix, propose it:

| Critique | Suggestion |
|----------|------------|
| "Theorem 1 is a textbook restatement" | "Consider demoting from Theorem to Proposition; the genuine contribution is [X], not the optimality result." |
| "Caption is ambiguous about selection criterion" | "Stating [criterion] in the caption, or bolding the [right] column, would clarify." |
| "Claim is over-stated" | "Consider hedging from 'A improves B' to 'A improves B under [conditions]'." |

### C5 — Community-level lesson framing (in Strengths)

When the paper's practice teaches a broader-community lesson, name it:

> "Reporting both surrogate and analytic reconstruction is excellent practice. It exposes [model]+TTR's failure mode and **serves as a useful methodological warning to the broader community about TTR with learned forward models**."

Connects the specific paper to the workshop community's takeaway.

### C6 — Minor points on figures and tables

A separate optional section (after Questions) for **bookkeeping observations**. Frame as: *"These are bookkeeping observations, not substantive critiques. Flagging them because a careful reader spends time reconciling them."*

Typical content:
- Caption text and body text use different groupings for the same set
- Bolded "best" entries that do not correspond to the headline metric (state the operative criterion)
- Unexplained asymmetries (e.g., forward vs inverse parameter counts)
- Insights triggered by careful reading (e.g., "same channel weakest in both architectures → intrinsic difficulty, not architecture-dependent failure")

These are not Weaknesses (do not affect the verdict) but they show the AC and author that the reviewer read the paper carefully.

### C7 — Domain-appropriate baseline naming

When critiquing missing baselines, name the *specific* standard tools for the data modality:

- Tabular regression → "XGBoost, FT-Transformer, or TabPFN would be more informative than an MLP-only baseline."
- Inverse linear problem → "Non-negative least squares (NNLS) directly tests whether the gain is from the inequality prior."
- Cosmology inverse → "Baryonification (Aricò 2020) is the most direct competitor on the same metric."

Naming specific tools demonstrates domain familiarity and is more actionable than "more baselines would help."

### C8 — Stratified-analysis request

When the test distribution is non-uniform, request per-bucket reporting:

> "The 80/15/5 split is described as random and unstratified, so the test set inherits the training composition. A per-bucket breakdown (test $R^2$ at each [stratification variable]) would be informative — especially when the paper's motivating regime is a minority of the test distribution."

## Korean ↔ English equivalence table

For bilingual workflow, the following Korean phrases have the corresponding English anti-pattern. Audit both directions:

| Korean anti-pattern | English anti-pattern |
|---------------------|----------------------|
| `보기 드문` / `흔치 않은` | `rarely seen` / `unusual for a workshop paper` |
| `재현 불가능하다` | `fundamentally non-reproducible` |
| `self-undermining` | `self-undermining` (same) |
| `valuable substrate` | `valuable substrate` (same) |
| `재제출 권장` | `Major revision and resubmit` |
| `Spotlight 적합` | `well-suited for spotlight` |
| `본 batch 의 가장 강한` | `the strongest paper in this batch` |
| `흔치 않다는 점에서` | `given the rarity of` |
| `v3 §11 적용` | `applying v3 criteria` |
