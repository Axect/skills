---
name: journal-club-review
description: Produce a journal-club-style paper presentation (9 sections: TL;DR, The Problem, Key Idea, How It Works, Key Results, Why It Matters, Strengths/Limitations/Open Questions, Discussion Questions, Takeaways) from an arXiv ID/URL, a PDF, or raw text/markdown. The goal is to help a reading group UNDERSTAND and DISCUSS the paper, not to score or accept/reject it. Grounds every claim in the source, renders math as LaTeX, auto-matches the source language (e.g. Korean source -> Korean review), and optionally generates two friendly-whiteboard infographic figures (method + results) with the bundled codex image_generation tool. Use when the user wants a journal-club review, a paper walkthrough/presentation, an explainer of a paper, to "review this PDF/paper like a journal club", or 논문 저널클럽 리뷰/발표자료/논문 설명. For an OpenReview referee report use workshop-paper-review; for an adversarial pre-submission audit use adversarial-review.
---

# Journal-Club Review

Turn any paper (arXiv ID/URL, PDF, or text) into a journal-club presentation: a
warm, accurate, discussion-oriented walkthrough in nine sections, with LaTeX
math and two optional infographic figures. This is a teaching/discussion
artifact, not a referee report: no scores, no accept/reject.

## When to use

- "Give me a journal-club review of 2401.00001"
- "Review this PDF like a journal club" / "make presentation notes for this paper"
- "이 논문 저널클럽 리뷰 만들어줘" / "발표자료처럼 정리해줘"
- Any text or markdown draft the user wants walked through for a reading group.

If the user wants a peer-review referee report (rating, confidence, weaknesses
for OpenReview) use `workshop-paper-review`. For an adversarial pre-submission
audit of their own draft use `adversarial-review`.

## Inputs

One of:
- arXiv id (`2401.00001`, `2401.00001v2`, `hep-ph/0101001`) or arXiv URL
- a local PDF path
- a local `.md` / `.txt` path, or pasted text

## Workflow

### 1. Ingest the source

Run the extractor to get a uniform working directory with `source.md`:

```bash
uv run ~/Documents/Project/AI_Project/skills/journal-club-review/scripts/extract_text.py \
  "<arxiv-id | url | path>"
```

It prints a JSON summary (`slug`, `title`, `authors`, `categories`,
`out_dir`, `source_md`, `n_chars`) and writes `<out_dir>/source.md`
(default `./reviews/<slug>/`). For pasted text, save it to a `.md` file first,
then pass that path.

Read `source.md`. If extraction yielded little text (scanned PDF, `n_chars`
small), tell the user and proceed with whatever is available (abstract-level).

### 2. Detect language and write the review

Read `references/style-and-math.md`, `references/section-pipeline.md`.

- Detect the source language; write the review in that language unless the user
  asked otherwise (see `style-and-math.md`).
- Produce all nine sections in order, grounded in `source.md` with section /
  equation / figure citations. Render all math as LaTeX (`$...$`, `$$...$$`).
- Build a `method` figure brief inside section 4 and a `results` figure brief
  inside section 5 (schema in `references/figure-generation.md`).
- Follow the output skeleton in `section-pipeline.md`. Save the draft to
  `<out_dir>/review.md` (leave figure image lines out until step 3 confirms
  which figures exist).

### 3. Generate figures (optional, on by default)

Read `references/figure-generation.md`. Check `codex login status`. If logged
in, compose the two friendly-whiteboard prompts from the briefs and launch both
`codex exec` jobs in parallel into `<out_dir>/figures/`. After they finish,
embed `![Method overview](figures/method.png)` and
`![Key results](figures/results.png)` for whichever PNGs are non-empty; note any
that were skipped.

Skip this step if the user passed `--no-figures` / "no images" / "text only", or
if codex is not logged in (then say so and keep the review text-only).

### 4. Deliver

- Final file: `<out_dir>/review.md` (with figures alongside in
  `<out_dir>/figures/`).
- Tell the user the path and give a 1-2 line summary.
- If the review is Korean, offer to export a PDF with the `md2pdf-typora` skill.

## Notes

- This skill is self-contained: it does not require the arXiv Explorer app. It
  reuses that project's journal-club section design and figure style, but Claude
  itself does the analysis here.
- For arXiv inputs the extractor uses the PDF; if you have the LaTeX source or an
  `arxiv-doc-builder` markdown already, pass that path instead for cleaner math
  and section structure.
- Figures depend on a logged-in bundled `codex` runtime (ChatGPT OAuth). Without
  it the review still renders, just text-only.

## Files

- `scripts/extract_text.py`: arXiv/PDF/text -> `source.md` + JSON metadata (PEP
  723 inline deps: pdfplumber, httpx, feedparser; run with `uv run`).
- `references/section-pipeline.md`: the nine sections and output skeleton.
- `references/figure-generation.md`: figure briefs, style block, codex command.
- `references/style-and-math.md`: language rule, LaTeX math, tone, anti-patterns.
