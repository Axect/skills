# Templates by rating tier

Fill-in templates for the four typical rating tiers, with example phrasing calibrated to OpenReview's 1–10 rubric.

The template structure is identical across tiers — only the tone and Title shape change.

## Common structure

```markdown
# OpenReview Submission — Paper #<id>

## Title

<one declarative sentence, 10–13 words>

## Rating: **N / 10** (<exact OpenReview rubric label>)
## Confidence: **N / 5**

<Granular confidence: which dimensions the reviewer is most confident about,
which are partial, and which type of critique the AC should weight more.>

---

## Summary

<3–5 sentences. Neutral. No Fig references.>

## Strengths

1. **<short title>**. <1–2 sentences, substance-focused. Where applicable,
name the broader-community takeaway, not just paper-internal value.>
2. **<short title>**. <...>
3. **<short title>**. <...>

## Weaknesses

1. **<short title>**. <1–3 sentences, factual problem statement + one concrete evidence>
2. **<short title>**. <...>
3. **<short title>**. <...>
4. **<short title>**. <...>

## Questions for Authors

1. <Rebuttal-actionable, "Could the authors ..." form>
2. <...>
3. <...>
4. <...>

## Minor points on figures and tables (optional)

These are bookkeeping observations, not substantive critiques. Include only
if the paper has 2+ such issues that would friction a careful reader.

1. <cross-reference inconsistency between caption and body>
2. <bolding / "best" claim that does not match the headline metric>
3. <unexplained asymmetry between two parts of the same table>
4. <careful-reading insight: e.g., "the same channel is weakest in both
architectures — suggests intrinsic difficulty rather than architecture-dependent
failure">
```

### Granular confidence statement patterns

| Confidence | Strong pattern | Weak pattern |
|------------|----------------|--------------|
| 5 | "Comfortable across all of [ML methodology, physics framing, identifiability theory]; can independently verify every quantitative claim." | "Very familiar with the area." (no breakdown) |
| 4 | "Comfortable with the ML side (Transformers, PLE, TTR, pseudoinverse and Gauss–Markov); can follow the broader physics framing." | "Familiar with the topic." |
| 3 | "Comfortable with the ML side. Not a SMEFT expert — cannot independently judge whether [specific claim] is well-known or novel. Most confident on attribution and baseline critiques, less confident on physics-novelty observations. Please weight my comments accordingly." | "Some familiarity. Partial verification." |
| 2 | "Limited familiarity with [domain]; can evaluate framing and clarity but not deep technical correctness." | "I am not in this field." |

The Confidence-3 strong pattern is the most common honest workshop-review case and the one to internalize.

### Score-mobility declaration patterns (for ratings 5–6)

Insert as the final sentence of the **last Weakness** or the **last Question**:

- "If the authors add [NNLS baseline / analytic-TTR comparison / one specific item], I would move my rating to [N+1]."
- "Adding [item] in revision would settle the open question and move my rating to [N+1]."
- "Either [item A] or [item B] would address my main reservation; one of them in revision moves the rating to [N+1]."

This gives the author a concrete rebuttal target and signals to the AC how elastic the score is. Reserved for borderline ratings; for clear-accept (7+) or rejection (4–), the score-mobility is not the salient question.

### Structural / editorial suggestion patterns

The reviewer's job is not just to identify problems but, where applicable, to propose **constructive structural fixes**:

| Problem | Constructive suggestion |
|---------|-------------------------|
| Theorem is essentially a textbook restatement | "Consider demoting from Theorem to Proposition; the genuine contribution is the identification of [X], not the optimality result." |
| Claim is over-stated relative to evidence | "Consider hedging from 'X improves Y' to 'X improves Y under [specific conditions]'." |
| Figure shows weakest channel but caption is ambiguous | "Stating the selection criterion (per-WC min) in the caption, or bolding the per-WC column, would clarify." |
| Bundled architectural claim | "An NNLS baseline as one row in Table 2 would directly test whether the gain is architectural or just from the inequality prior." |
| Single seed | "A 3-seed retraining with reported variance would settle the stability question." |

### Community-level lesson framing (in Strengths)

Where the paper's empirical setup teaches a broader-community lesson, name it explicitly:

- "Reporting both surrogate and analytic reconstruction is excellent practice. It exposes [model]+TTR's failure mode and serves as a useful methodological warning to the broader community about TTR with learned forward models."
- "[Diagnostic finding] is independently informative as a worked example of [broader pattern]."

This connects the specific paper to the workshop community's takeaway. Especially valuable for borderline-accept reviews where the community-impact framing reinforces the accept verdict.

### Domain-appropriate baseline suggestions

When critiquing missing baselines, name the *specific* tools that would be informative for the problem's data modality:

| Problem modality | Standard baselines to suggest |
|------------------|-------------------------------|
| Tabular regression | XGBoost, LightGBM, FT-Transformer, TabPFN |
| Inverse linear problem | NNLS (non-negative least squares), Tikhonov regularization, constrained QP |
| Cosmological inverse | baryonification (Aricò 2020), HMCODE-2020 |
| Sequence / time-series RL | SAC, PPO, IQL (offline RL) |
| Field-level inference | SBI (sequential Bayesian inference), normalizing-flow posterior, ABC |

Naming the specific baselines (rather than "more baselines would help") demonstrates ML-domain familiarity and is more actionable for the author.

### Stratified-analysis request pattern

When the test distribution is non-uniform (e.g., dominated by one regime), request a per-bucket breakdown:

- "The 80/15/5 split is described as random and unstratified, so the test set inherits the training composition; a per-bucket breakdown (test $R^2$ at each [stratification variable] value) would be informative."

Especially important when the paper's *motivating* regime is a minority of the test distribution.

## Tier 1 — Clear accept (Rating 8)

**OpenReview label**: `Top 50% of accepted papers, clear accept`

Tone: the paper has a clear contribution that you would not hesitate to accept. Weaknesses are real but do not threaten the verdict. Spotlight signaling is omitted from the body (AC decision).

Title shape: `<Core contribution>: <single most striking property>.`
- Example: "Identifiability ceiling + PLEX architecture: empirical worst-5 matches theoretical bounds."

Confidence justification phrasing:
- "Some familiarity with X. Theorem 1's correctness is independently checked, but the completeness of Y is only partially verified."

Strengths typically: 4 items emphasizing the coherence of theory + empirical + diagnostic.

Weaknesses typically: 3–4 items, each clearly fixable and several self-acknowledged by the authors.

## Tier 2 — Good paper, accept (Rating 7)

**OpenReview label**: `Good paper, accept`

Tone: a clear accept, slightly weaker than Tier 1. The paper has 3+ Spotlight-quality dimensions but is not Tier-1 in execution depth.

Title shape: `<Core method>: <main characterization> with <main caveat>.`
- Example: "Bayesian void finding via graph flows: novel framing with honest dark-matter failure."

Confidence justification: similar to Tier 1.

Weaknesses typically: 4 items, mostly fixable; at least one is acknowledged by the authors as a known limitation.

## Tier 3 — Marginally above acceptance threshold (Rating 6)

**OpenReview label**: `Marginally above acceptance threshold`

Tone: the contribution is real but a layered set of weaknesses keeps it from a clean accept. Honest "barely above the line" framing.

Title shape: `<Novel framing>, limited by <weakness 1> and <weakness 2>.`
- Example: "Novel OT framing for baryonic feedback, limited by single-suite scope and missing baseline."

Confidence justification: same form.

Weaknesses typically: 4 items, often with 2–3 self-acknowledged by the authors. Phrasing emphasizes that the weaknesses *limit* (not invalidate) the contribution.

Questions: 3–5 items, each clearly addressable in the next revision.

## Tier 4 — Rejection (Rating 4)

**OpenReview label**: `Ok but not good enough - rejection` *(note: "Ok", regular hyphen, exact match required)*

Tone: the work has substrate value (problem framing, honest negative result, infrastructure potential) but one or two issues prevent acceptance in the current state.

Title shape: `<Substrate quality>, undermined by <central deficit>.`
- Example: "Honest fusion-RL negative result undermined by undisclosed reward and missing baselines."

Confidence justification: same form.

Weaknesses typically: 4 items, with the first being the central deficit that drives the verdict. Avoid the "(Critical)" tag — let ordering convey priority.

Questions: 3–5 items, prefer "Could the authors release / report / clarify" framing. Avoid `Non-negotiable` and similar dictatorial words.

Avoid: "Major revision and resubmit" framing (workshop-inappropriate); strong absolutes ("fundamentally non-reproducible", "evaluable한 상태가 아니다"); recommending Spotlight/rejection to the PC (out of scope for author-visible body).

## Tier 5 — Clear rejection (Rating 3) — rarely the right call

**OpenReview label**: `Clear rejection`

Use only when the paper has fundamental conceptual flaws (not just execution gaps). A paper with multiple Major weaknesses but a legitimate problem framing and honest reporting is **not** Tier 5 — it is Tier 4 ("Ok but not good enough"). Reserve Tier 5 for out-of-scope, methodologically wrong, or unethical work.

## Rating-to-section length mapping (rough)

| Rating | Strengths | Weaknesses | Questions | Total |
|--------|-----------|------------|-----------|-------|
| 8 | 4 | 4 | 4–5 | ~380 words |
| 7 | 4 | 4 | 4 | ~410 words |
| 6 | 3 | 4 | 4 | ~430 words |
| 4 | 3 | 4 | 5 | ~490 words |

Rejection-tier reviews tend to be slightly longer because the weaknesses need more concrete evidence to justify the verdict.
