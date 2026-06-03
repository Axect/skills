---
name: Journal-Club Section Pipeline
description: The nine ordered sections of a journal-club paper presentation, with what each must contain and how to ground it in the source. Ported from the arXiv Explorer review engine.
type: reference
---

# Journal-Club Section Pipeline

Produce these nine sections, in this order. Each section is grounded in the
source text: cite specific sections, equations, figures, or tables when you make
a claim (e.g. "(Sec. 3.2)", "(Eq. 4)", "(Fig. 2)", "(Abstract)"). Never invent
numbers or results that are not in the source.

If only an abstract is available (no full text), still produce every section but
keep claims at the level the abstract supports and say so in the header.

## Presenter persona (applies to every section)

You are an enthusiastic, clear research presenter leading a journal club for
graduate students and fellow researchers. The goal is to help the room
UNDERSTAND and DISCUSS the paper, not to gatekeep, score, or accept/reject it.
Explain intuitively, use analogies when they help, stay accurate and grounded in
the paper's actual content, and be honest about limitations without an
adversarial tone.

## Section order and required content

| # | Heading (EN) | Heading (KO) | Must contain |
|---|---|---|---|
| 1 | TL;DR | 한 줄 요약 | one_liner, why it's worth a slot, field label |
| 2 | The Problem | 문제 | the core problem, motivation/stakes, what prior work was missing |
| 3 | Key Idea | 핵심 아이디어 | the central insight, the intuition for *why* it works, an analogy |
| 4 | How It Works | 작동 방식 | pipeline overview, ordered steps, key components, **method figure** |
| 5 | Key Results | 핵심 결과 | headline finding, a metric table (metric/value/meaning), takeaway, **results figure** |
| 6 | Why It Matters | 의의 | significance beyond benchmarks, concrete applications, who should care |
| 7 | Strengths, Limitations & Open Questions | 강점·한계·열린 질문 | honest strengths, constructive limitations, unanswered questions. NO score/verdict/severity |
| 8 | Discussion Questions | 토론 질문 | 4-6 questions mixing conceptual, methodological, forward-looking, each with why it's interesting |
| 9 | Takeaways | 핵심 정리 | 3-5 crisp bullets + one memorable closing sentence |

Sections 4 and 5 are the **figure anchors**: they drive the two generated
infographics (see `figure-generation.md`).

## Per-section guidance

**1. TL;DR.** One sentence capturing the core contribution and why it's
exciting, then 2-3 sentences on what gap it fills and who benefits, then a short
field label (e.g. "Probabilistic ML", "High-Energy Astrophysics").

**2. The Problem.** State the core problem in the paper's own framing. Give the
practical or theoretical stakes. Say what existing approaches were missing or
where they failed.

**3. Key Idea.** Distill the central insight into 1-2 precise sentences. Then
explain in plain language *why* it works (what it exploits or avoids). Add a
relatable analogy that makes it click for someone outside the subfield (omit if
nothing fits honestly).

**4. How It Works.** Walk through the method step by step: a 1-2 sentence
overview of the pipeline, an ordered list of steps, and the key components with
their roles. Cite method/architecture sections. Produce a `method` figure brief
(see `figure-generation.md`).

**5. Key Results.** Summarize the main empirical findings. Build a small table
of the most important numbers: each row = metric, reported value with units, and
what it means. Cite the results/experiments sections. Add a one-line takeaway.
Produce a `results` figure brief.

**6. Why It Matters.** Why the work is significant beyond its benchmark numbers.
List concrete applications or use cases it enables. Name the communities or
practitioners who should pay attention and why.

**7. Strengths, Limitations & Open Questions.** Honest and collegial. Specific
strengths (not generic praise). Constructive limitations (not adversarial). Open
questions the paper leaves. No accept/reject verdict, no severity labels, no
scores.

**8. Discussion Questions.** 4-6 questions that would spark a productive
journal-club conversation. Mix conceptual, methodological, and forward-looking.
For each, add a short note on why it's worth the group's time.

**9. Takeaways.** 3-5 concise bullets plus one memorable closing sentence that
captures the paper's lasting contribution.

## Output skeleton (English; translate headings for other languages)

```markdown
# <Paper Title>

| | |
|:--|:--|
| **Authors** | ... |
| **arXiv / Source** | ... |
| **Categories** | ... |
| **Published** | ... |
| **Analysis source** | Full text / Abstract only |

---

## TL;DR
> <one-liner>

<why care>

**Field:** <field>

## The Problem
...

## Key Idea
...

## How It Works
...
![Method overview](figures/method.png)

## Key Results
...
| Metric | Value | What it means |
|:--|:--|:--|
| ... | ... | ... |
![Key results](figures/results.png)

## Why It Matters
...

## Strengths, Limitations & Open Questions
**Strengths:**
- ...
**Limitations:**
- ...
**Open questions:**
- ...

## Discussion Questions
1. <question> (*why interesting*)
...

## Takeaways
- ...
**<one memorable sentence>**

---
*Journal-club review generated with the journal-club-review skill | <date> | 9/9 sections*
```

Embed the `![Method ...]` / `![Key results ...]` image lines only when the
corresponding figure was actually generated; otherwise leave the section
text-only.
