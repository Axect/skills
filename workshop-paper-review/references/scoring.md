# OpenReview 1–10 scoring rubric + anti-anchoring discipline

## OpenReview workshop rubric (exact labels)

These labels are **exactly** what the user must select on the OpenReview form. Match them in the review's `## Rating:` line verbatim.

| Rating | Label | Verdict | When to use |
|--------|-------|---------|-------------|
| 10 | Top 5% of accepted papers, seminal paper | Award candidate | Field-changing work |
| 9 | Top 15% of accepted papers, strong accept | Strong accept | Oral/Spotlight tier |
| 8 | Top 50% of accepted papers, clear accept | Clear accept | Above-average accept, theorem + execution coherent |
| 7 | Good paper, accept | Clear accept | A paper you would not hesitate to accept |
| 6 | Marginally above acceptance threshold | Marginal accept | Real contribution, layered weaknesses |
| 5 | Marginally below acceptance threshold | Marginal reject | Fixable defects, weak evidence |
| 4 | Ok but not good enough - rejection | Rejection | Substrate has value, but execution gaps prevent acceptance |
| 3 | Clear rejection | Rejection | Fundamental conceptual flaws |
| 2 | Strong rejection | Rejection | Serious methodological problems |
| 1 | Trivial or wrong | Rejection | Out of scope, unethical, demonstrably wrong |

**Key non-uniformities**:
- 7 is **not** borderline-accept. It is a clear, comfortable accept.
- 6 **is** the borderline-accept tier.
- 4 is "OK substrate, but not good enough" — milder than 3 (Clear rejection).
- 3 should be reserved for fundamentals-broken papers, not for under-baked but legitimate work.

The Korean phrasing "rejection 권장" maps to Rating 4 by default; only escalate to 3 if conceptually flawed.

## Confidence rubric (1–5)

| Confidence | Description |
|------------|-------------|
| 5 | Reviewer's own subfield; full literature familiarity; can verify all technical detail. |
| 4 | Adjacent subfield; comfortable with most claims; some details unchecked. |
| 3 | Some familiarity; can evaluate the substantive contribution but not every technical step. **The most common honest answer for workshop reviews.** |
| 2 | Limited familiarity; can evaluate framing and clarity but not deep technical claims. |
| 1 | Outside the reviewer's areas of competence. |

**At Confidence 3, the review should avoid absolute claims** like `cannot be reproduced`, `is impossible`, `is incorrect`. Prefer factually-grounded weaker forms: `is not provided`, `is not demonstrated`, `cannot be decomposed (without baseline X)`.

## Anti-anchoring protocol

In multi-paper batches, the gravitational pull of the "comfortable" middle rating (typically 7) is the single biggest threat to honest reviewing. The following rules apply whenever the reviewer is rating 3+ papers within a few days of each other.

### Rule 1 — Distinct-rating preference

If 3+ papers in a batch are landing on the same rating, audit. A typical 4-paper batch should produce a distribution like **3 / 6 / 7 / 8** or **4 / 5 / 7 / 8** — not **6 / 7 / 7 / 7**.

### Rule 2 — Pairwise pre-commit

Before fixing a rating, articulate two specific contrasts, in writing if needed:

1. Compared to the next *higher*-rated paper in the batch: what specifically does this paper lack?
2. Compared to the next *lower*-rated paper: what specifically does this paper have that the lower one does not?

If either question fails to produce a substantive answer, the rating is anchored.

This contrast is **reviewer-internal only** — never mention other batch papers in the author-visible review (confidentiality).

### Rule 3 — Score-justification audit (post-fact-check)

If fact-check reveals that one of the Critical-tier weaknesses driving the rating is wrong:

- Remove the disputed weakness from the review.
- Re-evaluate the rating. Does the *remaining* set of weaknesses still justify the original rating?
- If not, adjust honestly.

Concrete example: a paper rated 3 (Clear rejection) on the basis of "two Critical weaknesses (reward spec missing + internal contradictions)". Fact-check shows one of the internal contradictions was actually the paper's honest disclosure of failure, not a contradiction. With only one Critical weakness remaining, Rating 4 ("Ok but not good enough") becomes the honest call.

### Rule 4 — Confidence-rating coupling

- Rating 8+ requires either Confidence 4+ OR a clear case of theorem-empirical coherence that any competent reader can verify.
- Rating 1–2 requires Confidence 4+ — extreme reject without confidence is unfair.

## Verdict-to-language coupling

| Rating | Acceptable phrasing | Avoid |
|--------|---------------------|-------|
| 8 | "Clear accept", "strong contribution", "coherent across theory and empirics" | Spotlight nomination in body |
| 7 | "Good paper", "well-motivated combination", "self-acknowledged weaknesses" | "Could be improved with..." (too tentative for Rating 7) |
| 6 | "Marginal accept", "layered weaknesses limit the contribution to..." | "Strong contribution" (Rating-mismatched) |
| 4 | "Underspecified", "limits reproducibility", "leaves the claim unverified" | "fundamentally non-reproducible", "self-undermining", "Non-negotiable", "Major revision and resubmit" |
| 3 | "Fundamentally", reserved language for conceptual flaws | "Underbaked but valuable" (that is Rating 4) |

## Don't fight the rubric

The OpenReview rubric is fixed. If the reviewer's instinct is "this is a borderline accept", the rating is **6** (the rubric's actual borderline-accept label), not 7. Aligning instinct to rubric is part of the discipline.
