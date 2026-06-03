# Fact-check protocol

Every workshop review produced by this skill must pass a fact-check against the source PDF before it is declared final. Hallucinated contradictions, misattributed quotes, and invented section references are the single most credibility-damaging mistakes a reviewer can make.

This file specifies the protocol and provides a ready-to-dispatch subagent prompt.

## What to verify

Categorize every factual claim in the draft into one of these buckets, then verify each against the PDF.

### Bucket 1 — Numerical claims (always verify)

Examples: `mean reward 604.79 vs 3.35`, `48,000 timesteps × 4 parallel envs`, `raw UV $R^2$ from 0.29 to 0.83`, `$\sigma_{\log T} = 0.01\,\mathrm{dex}$`, `$\alpha = 10$`, `$\dim \ker M = 21$`.

Each number must match the PDF exactly. Workshop papers are short — looking up a specific Table entry takes seconds.

### Bucket 2 — Methodology claims (always verify)

Examples: "RAPTOR (Fortran plasma simulator)", "PLE + cross-attention + smooth-ReLU + TTR", "Sinkhorn OT with $\alpha=10$", "single seed (42) in App. E.2".

Includes implementation-language claims, architecture-component claims, hyperparameter claims, and dataset/simulation-suite claims.

**Common failure**: confusing the simulator's implementation language (e.g., MATLAB vs Fortran), or counting reward components incorrectly (e.g., "9-objective SoftHat reward" when paper has 9 objectives mapped to 5 reward components).

### Bucket 3 — Italic-quoted phrases (always verify verbatim)

Any phrase the draft wraps in italic-quote form (`*"..."*`) must be a verbatim string from the PDF. If the draft uses italic-quoting for the reviewer's paraphrase, that is a fact-check failure.

**Common failure**: italic-quoting `*"reward ↑ ≠ feasibility"*` when the paper says "Reward–feasibility mismatch" + "Constraint gap".

### Bucket 4 — Section / Table / Figure / Equation references

Every `Sec. 4`, `Table 1`, `Fig. 3`, `Eq. 6` must be a real reference in the PDF.

**Common failure**: writing `(§4.1)` when the paper has no subsections, only `§4`.

### Bucket 5 — "Internal contradiction" claims (high-risk, always verify)

If the draft claims the paper contradicts itself ("Abstract says X, but Sec. Y says Z"), this is the single most-disputed type of claim. Quote both passages verbatim before submitting the contradiction critique.

**Common failure**: confusing "target vs achieved" with "contradiction". If a paper's abstract reports the *achieved* outcome (e.g., "13 MA") and the methods section reports the *target* (e.g., "20 MA"), this is the paper's *honest disclosure of failure*, not a contradiction.

### Bucket 6 — Citation accuracy

Author names, years, paper titles. Especially important when the draft criticizes the absence of a comparison (`No comparison against Mitchell 2023 SQP feedforward`) — verify Mitchell 2023 is actually cited in the paper.

### Bucket 7 — Reviewer's external domain knowledge

Claims that originate in the reviewer's outside knowledge (`baryonification accuracy is $<2\%$ on $P(k)$ per Aricò 2020`) are **unverifiable from the PDF alone**. These should be:

- Either dropped if the reviewer is at Confidence 3 and lacks deep familiarity,
- Or kept if the reviewer is confident in their literature recall and willing to defend it in rebuttal.

Flag as UNVERIFIABLE-EXTERNAL in the audit.

### Bucket 8 — Figure/table cross-reference integrity

If the review's **Minor points on figures and tables** section makes cross-reference claims, every claim must be verified against the PDF. These minor-points claims look harmless but a wrong cross-reference is highly visible in rebuttal.

Verify:

- **Caption-vs-body grouping**: if the review claims "Fig. 2 caption uses X grouping, §Y body uses Z grouping", read both and confirm.
- **Bolded "best" entries**: if the review claims "PLEX+VW is bolded but is third on metric X, first on metric Y", read the table and check every cell.
- **Parameter / hyperparameter asymmetries**: e.g., "Forward PLEX has 2.2M params vs inverse 0.5M (4× asymmetry)" — verify both numbers.
- **"Weakest channel" attributions**: e.g., "Fig. caption says 'weakest channel for both' — this corresponds to $C_\varphi$ in Table 1" — verify the channel identity.

**Common failure mode**: writing a Minor point based on what the reviewer *expected* the table to say rather than what it actually says. Read the actual cells.

## Verification labels

For each claim, label one of:

- **VERIFIED** — claim is correct
- **DISPUTED** — claim is incorrect or significantly misleading; provide the actual PDF content
- **UNVERIFIABLE-EXTERNAL** — external domain knowledge, beyond PDF
- **NEEDS-CONTEXT** — technically correct but lacks context that changes interpretation

## Subagent dispatch

For PDFs of any non-trivial length, dispatch fact-check as a subagent task. Use a fresh Opus subagent per paper. For a 4-paper batch, dispatch 4 in parallel.

### Subagent prompt template

```
You are a strict fact-checker for an ICML workshop review.

## Task

Verify every factual claim in the OpenReview submission against the actual PDF. Flag any discrepancy, hallucination, mischaracterization, or unverifiable claim. False claims in a review undermine the reviewer's credibility and unfairly damage the authors.

## Files

- **Submission**: `<path to *_submission.md or *_submission_en.md>`
- **Source PDF**: `<path to the paper's PDF>`
  (If the PDF is >12 pages or >2 MB, use the `pages` parameter on `Read`, e.g. `pages: "1-10"` then `pages: "11-20"`.)

## Steps

1. Read the submission fully.
2. Read the PDF (chunked if necessary).
3. Extract every claim into the 7 buckets defined in fact_check.md.
4. For each claim, label VERIFIED / DISPUTED / UNVERIFIABLE-EXTERNAL / NEEDS-CONTEXT.
5. For DISPUTED items, quote the actual PDF content.

## High-priority claims to verify with particular care

[Customize per paper — examples below]

- Italic-quoted phrases: verify each is a verbatim PDF string.
- Numerical claims: verify each against the relevant table/equation.
- "Internal contradiction" claims: quote both passages verbatim and judge whether this is target-vs-achieved (honest disclosure) or genuine contradiction.
- Implementation-language claim (e.g., MATLAB vs Fortran): verify against the paper's setup section.
- Cited prior work: verify the named paper is actually cited.
- Section/subsection references (e.g., "§4.1"): verify the section exists in the PDF.

## Output

Return a structured fact-check report:
- Per-claim verification table (claim → label → evidence)
- Summary: N verified / M disputed / K unverifiable
- Critical issues affecting the verdict
- Recommended corrections (specific edits to the submission)

Keep the report focused. Do not rewrite the review — just the fact-check ledger.
```

## Handling DISPUTED items

If fact-check returns one or more DISPUTED items:

1. **Acknowledge internally**: this is a reviewer-process mistake. Note that it must **not** appear in the final review (no meta-commentary about the fact-check correction).
2. **Remove or rephrase** the disputed claim from the draft.
3. **Re-evaluate the rating**: if the disputed claim was load-bearing for the rating (e.g., one of two "Critical" weaknesses), re-examine whether the rating still holds. The skill applies anti-anchoring discipline (see `references/scoring.md`) — do not silently keep a rating that was justified by a now-disputed claim.
4. **Re-run the anti-pattern audit** after edits.
5. **Re-verify** that the corrected submission has no traces of the disputed claim.

## What the final review must NOT contain

- Any mention of the fact-check process itself.
- Any "anti-anchoring re-evaluation" meta-commentary.
- Any acknowledgement of a previous rating that was changed.
- Any reference to "an earlier draft said X but I now realize Y".

Reviewer-internal process artifacts stay reviewer-internal. The author sees only the corrected, polished review as if it had been the first and only draft.

## When fact-check is optional

For very short PDFs (4-page workshop submissions, simple methodology) where the reviewer is at Confidence 4–5, an inline fact-check during drafting is often sufficient. The dispatch protocol above is reserved for:

- PDFs of 8+ pages
- Confidence 3 reviews where the reviewer wants insurance
- Multi-paper batches (parallel dispatch saves wall-clock time)
- Any review whose Weaknesses include "internal contradiction" claims (these are high-risk; always dispatch fact-check)
