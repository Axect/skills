---
name: Journal-Club Style, Math, and Language
description: Output language detection rule, mandatory LaTeX math formatting, journal-club tone, and the anti-patterns to avoid in the rendered review.
type: reference
---

# Style, Math, and Language

## Output language (auto-detect)

Match the review's language to the **language the user wrote their request in**.
The user's command language wins; the source paper's language is only a fallback.

- If the user's request itself is in Korean (e.g. "이 논문 리뷰해줘", "발표자료로
  정리해줘"), write the review in **Korean**, even when the source paper is in
  English. Likewise a request written in English -> English review. Asking in a
  language is an implicit request for that language; do not default to the
  paper's language just because the body is English.
- An explicit instruction always wins over everything: "in Korean" / "한국어로" /
  "in English" / "영어로" overrides both the command language and the source.
- Only when the request gives no language signal (e.g. invoked with just an
  arXiv id and no surrounding prose) fall back to the **source paper's
  language**: English source -> English review, Korean source -> Korean review.
- Detect the dominant language of the extracted source text from the body, not
  just metadata, when you need that fallback.
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
