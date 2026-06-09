---
name: journal-club-review
description: Produce a journal-club-style paper presentation (9 sections: TL;DR, The Problem, Key Idea, How It Works, Key Results, Why It Matters, Strengths/Limitations/Open Questions, Discussion Questions, Takeaways) from an arXiv ID/URL, a PDF, raw text/markdown, or a local LaTeX source (.tex / project dir). The goal is to help a reading group UNDERSTAND and DISCUSS the paper, not to score or accept/reject it. Grounds every claim in the source, renders math as LaTeX, auto-matches the source language (e.g. Korean source -> Korean review). When LaTeX source is available (arXiv e-print or local .tex), embeds the paper's real figures with their captions; also optionally generates two friendly-whiteboard infographic figures (method + results) with the bundled codex image_generation tool. Use when the user wants a journal-club review, a paper walkthrough/presentation, an explainer of a paper, to "review this PDF/paper like a journal club", or 논문 저널클럽 리뷰/발표자료/논문 설명. For an OpenReview referee report use workshop-paper-review; for an adversarial pre-submission audit use adversarial-review.
---

# Journal-Club Review

Turn any paper (arXiv ID/URL, PDF, text, or a local LaTeX source) into a
journal-club presentation: a warm, accurate, discussion-oriented walkthrough in
nine sections, with LaTeX math, the paper's real figures (when source is
available), and two optional infographic figures. This is a teaching/discussion
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
- a local LaTeX source: a `.tex` file or a project directory (e.g. an Overleaf
  checkout). Figures referenced by the source are harvested automatically.

## Workflow

### 1. Ingest the source

Run the extractor to get a uniform working directory with `source.md`:

```bash
uv run scripts/extract_text.py "<arxiv-id | url | path>"
```

(`scripts/extract_text.py` is relative to this skill's base directory; pass an
absolute path if your cwd is elsewhere.)

It prints a JSON summary (`slug`, `title`, `authors`, `categories`, `out_dir`,
`source_md`, `n_chars`, plus `n_figures`, `figures_dir`, `figures_manifest`)
and writes `<out_dir>/source.md` (default `./reviews/<slug>/`). For pasted text,
save it to a `.md` file first, then pass that path.

When LaTeX source is available (arXiv e-print tarball, or a local `.tex`/dir
input), the extractor also converts the paper's figures to PNG under
`<out_dir>/figures/paper/` and writes `<out_dir>/figures_manifest.json`
(`n_figures` > 0). For PDF-only or plain-text inputs there are no source
figures (`n_figures` is 0); that is fine, just skip step 3.

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
  `<out_dir>/review.md` (leave figure image lines out until steps 3-4 confirm
  which figures exist).

### 3. Embed the paper's real figures (when source available)

If `n_figures` > 0, read `references/figure-generation.md` ("Real source
figures") and `<out_dir>/figures_manifest.json`. Curate the most relevant
figures and embed them into the matching sections with their captions
(`figures/paper/<name>.png`): overview/architecture/schematic into **How It
Works**, result plots into **Key Results**. Verify each embedded PNG is
non-empty before referencing it. Do not dump every figure; note any a reader
might expect that you skipped.

Skip if `n_figures` is 0 (PDF/text input).

### 4. Generate infographics (optional, on by default)

Read `references/figure-generation.md` ("Generated infographics"). Check
`codex login status`. If logged in, compose the two friendly-whiteboard prompts
from the briefs and launch both `codex exec` jobs in parallel into
`<out_dir>/figures/`. After they finish, embed
`![Method overview](figures/method.png)` and
`![Key results](figures/results.png)` for whichever PNGs are non-empty; note any
that were skipped. These coexist with the real figures from step 3.

Skip this step if the user passed `--no-figures` / "no images" / "text only", or
if codex is not logged in (then say so and keep the review text-only).

### 5. Deliver

- Final file: `<out_dir>/review.md` (with figures alongside in
  `<out_dir>/figures/`: real figures in `figures/paper/`, infographics in
  `figures/`).
- Tell the user the path and give a 1-2 line summary.
- If the review is Korean, offer to export a PDF with the `md2pdf-typora` skill.

## Notes

- This skill is self-contained: it does not require the arXiv Explorer app. It
  reuses that project's journal-club section design and figure style, but Claude
  itself does the analysis here.
- For arXiv inputs the extractor uses the PDF for text and the e-print tarball
  for figures. If you have the LaTeX source already, pass the `.tex`/dir path
  instead for cleaner math and section structure plus the same figure harvest.
- Real-figure conversion uses whatever rasterizer is on PATH (`pdftoppm`,
  `magick`/`convert`, or `gs`); if none is present, vector figures are skipped
  and only raster (PNG/JPG) figures survive.
- Generated infographics depend on a logged-in bundled `codex` runtime (ChatGPT
  OAuth). Without it the review still renders, just text-only.

## Files

- `scripts/extract_text.py`: arXiv/PDF/text/LaTeX -> `source.md` + JSON metadata;
  harvests real figures to `figures/paper/` + `figures_manifest.json` when LaTeX
  source is available (PEP 723 inline deps: pdfplumber, httpx, feedparser; uses
  system pdftoppm/magick/gs for conversion; run with `uv run`).
- `references/section-pipeline.md`: the nine sections and output skeleton.
- `references/figure-generation.md`: real-figure embedding policy, infographic
  briefs, style block, codex command.
- `references/style-and-math.md`: language rule, LaTeX math, tone, anti-patterns.
