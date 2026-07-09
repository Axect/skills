# {title}

**Date**: {date}  
**Domain**: {domain}  
**Written for**: {reader}

---

<!--
This report exists to make the work UNDERSTANDABLE, backed by traceable evidence.
Target reader: a sharp colleague who is new to THIS specific problem, and future-you months from now.
Order of every explanation: intuition first, then formalism. Analogy is allowed; hand-waving is not.
Every quantitative claim still points to a real number, table cell, CSV column, or figure.
Word budgets are advisory; the validator warns when a section runs more than 10% over.
Evidence-block IDs (`ev-N`) link prose claims to entries in `evidence/inventory.json` (optional).
-->

## TL;DR

<!-- WORD_BUDGET: 200 -->
<!-- One tight paragraph a reader grasps in 30 seconds: what problem, why it mattered,
     what you did, what you found, and what it means. Write this LAST; place it FIRST. -->

{tldr}

## 1. Why this matters

<!-- WORD_BUDGET: 600 -->
<!-- The stakes, not just the setup. A reader should WANT the answer by the end of this section.
     - What was blocked, wrong, or impossible before this? What becomes possible after?
     - Who feels the gap (which people, which downstream work)?
     - Why is this hard or non-obvious? If it were easy it would already be done.
     Lead with the tension, not with background trivia. -->

### 1.1 The gap
{gap}

### 1.2 The question
<!-- The single question this work answers, phrased so its answer would change what someone does next. -->
{research_question}

## 2. The core idea

<!-- WORD_BUDGET: 900 -->
<!-- THE section a reader should remember. Explain WHAT the work is at the level of the idea,
     not the implementation.
     - Give the one-sentence version first ("The key idea is that ...").
     - Then the intuition: the mental model, the picture, the analogy. Why should this work at all?
     - Then, and only then, the formal statement (definitions, the objective, the equation).
     - Say why THIS idea beats the obvious alternative, and what it buys you.
     If a reader forgets everything else, this is what should survive. -->

### 2.1 The idea in one sentence
{idea_oneliner}

### 2.2 Intuition
{intuition}

### 2.3 Formal statement
{formal}

<!-- Display equations live on their own lines:

$$
L = \frac{1}{N} \sum_i (y_i - \hat{y}_i)^2
$$

Inline math: $\alpha = 0.05$, $O(n \log n)$, $\hat{\theta} \in \mathbb{R}^d$. -->

## 3. How it works

<!-- WORD_BUDGET: 1200 -->
<!-- The mechanism, subordinate to the idea in §2. Every design choice should trace back to the idea:
     "because the idea needs X, we do Y." Give enough that a reader could rebuild it and trust the
     result; do not dump every config. Exhaustive hyperparameters and environment tables go in the appendix. -->

### 3.1 Data, materials, or inputs
{data_inputs}

### 3.2 Method
{methodology}

### 3.3 Setup worth trusting
<!-- Architecture, key components, the seeds/configs/environment that actually affect the result.
     Keep only what a reader needs to believe the numbers; the rest belongs in Appendix B. -->
{setup}

## 4. What we found

<!-- WORD_BUDGET: 1500 -->
<!-- Results as a story of discovery, not a metrics dump. For each finding:
     (1) state it in plain words and say what it MEANS, then
     (2) show the evidence (figure / table / number) that earns it.
     Embed each figure inline next to the paragraph that interprets it and quote specific numbers
     from it (deltas, %, R^2, slope, CI, runtime). No orphan figures, no bare "see Figure X". -->

### 4.1 Headline finding
<!-- EVIDENCE BLOCK: ev-1 -->
{headline}

### 4.2 Supporting and comparative findings
<!-- EVIDENCE BLOCK: ev-2 -->
{supporting}

### 4.3 What surprised us
<!-- The result you did not expect, and how you reconciled it. Delete this subsection if nothing
     genuinely surprised you; never fabricate surprise. -->
{surprises}

## 5. So what

<!-- WORD_BUDGET: 600 -->
<!-- Return to the stakes from §1 and pay them off.
     - What does this change about how we think, or what we can now do?
     - Concrete implications, and who should care.
     - How far does the claim reach? State the scope of the conclusion honestly. -->

{significance}

## 6. Limits & open questions

<!-- WORD_BUDGET: 600 -->
<!-- Honest, specific boundaries, not "may not generalize". Name the failure modes you actually
     observed. Each open question should be answerable by a concrete next experiment. -->

### 6.1 Where this breaks
{limitations}

### 6.2 What we still don't know
{open_questions}

---

## Appendix (optional)

<!-- Traceability material. Include only what supports reproduction. Do not let the appendix
     become the body of the report. -->

### A. Reproduction notes
<!-- Seeds, versions, compute, exact commands: enough to regenerate every figure and number. -->
{reproduction}

### B. Source / test / artifact inventory
{inventory}

### C. Plot manifest summary
{plot_manifest_summary}
