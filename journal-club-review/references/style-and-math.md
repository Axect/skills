---
name: Journal-Club Style, Math, and Language
description: Output language detection rule, mandatory LaTeX math formatting, journal-club tone, and the anti-patterns to avoid in the rendered review.
type: reference
---

# Style, Math, and Language

## Output language (auto-detect)

Match the review's language to the **source paper's language**, unless the user
explicitly requests a language.

- Detect the dominant language of the extracted source text (the body, not just
  metadata). English source -> English review. Korean source -> Korean review.
- If the user says "in Korean" / "한국어로" / "in English", obey that instead.
- When you translate headings, use the KO column in
  `section-pipeline.md`. Keep these in their original form regardless of
  language: technical terms, model/dataset/method names, proper nouns,
  acronyms, math notation, URLs, and arXiv IDs.

## Math formatting (mandatory)

Render every mathematical expression as LaTeX so it displays correctly in
Markdown viewers (Typora, the PDF export, GitHub with math, etc.).

- Inline math: `$...$`. Display equations: `$$...$$`.
- Variables, symbols, units with powers/subscripts, and numeric ranges are math:
  - write `$10^{17}$--$10^{23}\,\mathrm{g}$`, not `10^17-10^23 g`
  - write `$M_\odot$`, not `M_sun`
  - write `$\rho \propto r^{-2}$`, not `rho ~ r^-2`
- This applies to all prose and tables, but **not** to figure panel descriptions
  (those stay plain English with ASCII/Greek per `figure-generation.md`).
- Source PDFs lose their LaTeX during text extraction, so you must re-render
  math as LaTeX yourself based on what the symbols mean.

## Tone

- Enthusiastic, clear, collegial presenter. Help the room understand and
  discuss, never gatekeep.
- Evidence-grounded: cite sections/equations/figures/tables for claims.
- Honest about limitations, never adversarial. No accept/reject verdict, no
  scores, no severity tags (those belong to a referee report, not a journal
  club; for that use the `workshop-paper-review` or `adversarial-review` skill).

## Anti-patterns (avoid)

These follow the user's global writing rules.

- No em-dashes or en-dashes (`—` / `–`). Use commas, periods, colons,
  parentheses, or restructure. Plain hyphens are fine only in hyphenated words
  and CLI flags. (In LaTeX numeric ranges use `--`, e.g. `$10^{17}$--$10^{23}$`.)
- No "not just X, but Y" / "It's not X, it's Y" inflated contrast.
- No filler transitions: "Moreover", "Furthermore", "Importantly", "It's worth
  noting that", "Let's dive in", "Certainly!".
- No hype adjectives: "seamless", "robust", "powerful", "cutting-edge",
  "leverage" (verb), "delve", "realm", "landscape", "testament to".
- No emoji. No rule-of-three padding for rhythm. No needless bolding.
- Prefer plain, direct sentences. Cut throat-clearing intros and summary outros.
