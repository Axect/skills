---
name: wide-slide-illustrator
description: >
  Compose detailed image-generation prompts (ChatGPT Image 2.0 / gpt-image-1, DALL-E,
  Sora image, Midjourney) for wide cinematic infographic slides — multi-panel
  18:9 figures that explain a methodology, data pipeline, or architecture in
  one image. Two reusable style variants are supported: Friendly Whiteboard
  (warm, sketchy, lab-meeting feel) and Editorial Magazine (refined, Quanta /
  NYT feature-spread feel). Output prompts always force on-image text to be
  English-only and combine a reusable style block with task-specific panel
  content.
  Use when the user asks to: generate a slide illustration, make an infographic,
  create a wide pipeline diagram, draw a "how it works" figure, or produce an
  image-generator prompt for a methodology / data-pipeline / architecture
  overview — friendly-casual OR magazine-refined.
  Triggers on: "wide slide", "lab meeting figure", "whiteboard style",
  "editorial slide", "magazine infographic", "Quanta-style figure",
  "infographic prompt", "wide pipeline figure", "ChatGPT image prompt",
  "image generation prompt", "casual presentation diagram", "hero figure",
  "friendly slide".
---

# Wide Slide Illustrator — Image Prompt Composer

Generate detailed prompts for raster image-generation models (ChatGPT Image 2.0,
DALL-E 3, gpt-image-1, Sora image, Midjourney) that produce wide cinematic
multi-panel infographic slides for research talks, blog posts, and reports.

Two reusable style variants are available; both share the same 5-panel 18:9
composition and the English-only-on-canvas guard rail, and differ only in
surface treatment.

| Style                   | Style block                                       | Worked example                                |
|-------------------------|---------------------------------------------------|-----------------------------------------------|
| Friendly Whiteboard     | `references/friendly-whiteboard-style.md`         | `references/example-osprey-v021.md`           |
| Editorial Magazine      | `references/editorial-magazine-style.md`          | `references/example-osprey-editorial.md`      |

- **Friendly Whiteboard** — warm whiteboard sketch, wavy strokes, stickers,
  sticky notes, chalk-style chunky arrows. Approved on 2026-04-27.
- **Editorial Magazine** — Quanta / NYT / The Atlantic feature-spread feel:
  cream paper, hairline rules, serif headline, status-badge / pull-quote /
  connection-line patterns. Approved on 2026-05-08 after a v1→v2 hardening
  pass. **Always include the explicit hard-negatives bullet** from the style
  block — without it, friendly cues leak through (wobbly curves, rubber-stamp
  pass/reject, hand-lettered notes, chunky radiation arrows).

If the user does not specify a style, ask once before composing.

## When to use

Trigger this skill when the user wants an **image-generator prompt** (not a
matplotlib/seaborn plot, not a paperbanana diagram) for one of:

- A **methodology / pipeline / architecture** overview slide — for a lab
  meeting / seminar / workshop (friendly variant) OR a paper hero figure /
  blog post / report cover (editorial variant).
- A **data-generation flowchart** with multiple stages flowing left-to-right.
- A **"how X works"** explainer figure for a casual deck or a published
  article.

Do NOT use for:

- Publication figures with strict statistical content → use `paperbanana` skill.
- Real plots from data (matplotlib, seaborn, plotly) → write code directly.
- Slide *decks* (multi-slide presentations) → use `claude-typst-slides` or
  `frontend-slides`.

## How to compose a prompt

### Step 1 — Pick and read the style block

Decide which style applies (Friendly Whiteboard vs. Editorial Magazine — see
the table above). If unclear, ask the user. Then read the corresponding style
file in full. The wording in those files is what the user validated; do not
paraphrase.

For Editorial Magazine, also read the three sub-patterns inside that file
(STATUS-BADGE PATTERN, PULL-QUOTE PATTERN, CONNECTION-LINE PATTERN) and use
them by name whenever a panel would otherwise want a stamp, sticky note, or
motion arrow.

### Step 2 — Gather task-specific content

Ask (or infer from context) the answers to:

1. **Title** (one short headline + optional subtitle).
2. **Number of panels** (default 5, range 3–6).
3. **Per-panel content**: what each panel illustrates, what equations / labels
   / icons should appear, in plain English.
4. **Aspect ratio** (default 18:9 cinematic wide; alternatives 16:9, 3:2, 4:3).
5. **Footer ribbon facts** (small chips with constants, seeds, scales, etc.) —
   optional but recommended.
6. **Domain-specific accuracy constraints**: math symbols, axis labels, exact
   parameter names. The skill must reproduce these verbatim.

If the user gave a research-log entry, code file, or paper section as source,
extract these facts from it directly — do NOT hallucinate.

### Step 3 — Assemble the prompt

The output prompt must contain, in order:

1. **One-paragraph framing** — adjust per chosen style:
   - Friendly: "A cinematic-wide {aspect} horizontal infographic illustrating
     {topic}, designed as a friendly conference-slide visual (NOT a stiff
     academic figure). All text in the image MUST be in English only."
   - Editorial: "A cinematic-wide {aspect} horizontal infographic illustrating
     {topic}, designed as a refined magazine-style spread — Quanta / NYT
     feature-article feel (NOT a friendly whiteboard sketch and NOT a stiff
     academic figure). The whole spread should look engraved / printed, not
     sketched. All text in the image MUST be in English only."
2. **`OVERALL LOOK:` block** — copy verbatim from the chosen style file
   (`references/friendly-whiteboard-style.md` OR
   `references/editorial-magazine-style.md`).
3. **`TITLE BAR:` block** — headline + optional subtitle text.
4. **`PANEL N — "<short name>":`** blocks — one per panel, with concrete
   sub-bullets describing graphics, labels, equations, and tiny notes.
5. **`BOTTOM RIBBON:` block** — small chips with constants / metadata.
6. **`TYPOGRAPHY:`, `COMPOSITION:`, `MOOD:` closing blocks** — copy from the
   style reference.
7. **English-only text guard rail**, repeated at the end:
   "IMPORTANT: every character on the canvas must be readable English. Render
   math with plain ASCII / Greek letters only (α β σ μ Σ are fine); no
   decorative non-Latin script anywhere."

### Step 4 — Deliver to the user

Present the final prompt inside a fenced code block so the user can copy-paste
it directly into the image generator. Below the prompt, add a short usage tip
section covering:

- **Aspect-ratio reality check**: gpt-image-1 supports 1024×1024, 1024×1536,
  1536×1024 — for true 18:9 generate at 1536×1024 and crop top/bottom, or use
  a service that allows custom dimensions (Midjourney `--ar 18:9`).
- **Text rendering caveat**: even with the English-only guard, expect 1–2
  retries; pick the cleanest output or composite text in post.
- **Tone dials**: each style file ends with a tone-dials table. Friendly can
  go calmer (drop stickers + chalk arrows) or more playful (add coffee-cup +
  sticky-note). Editorial can go more print-zine (paper grain + drop cap) or
  cleaner Bauhaus (drop foil-gold + serif headline → geometric sans).

## Worked examples

- **Friendly Whiteboard** — `references/example-osprey-v021.md`
- **Editorial Magazine** — `references/example-osprey-editorial.md`

Both cover the same OSPREY v0.21 pipeline with identical per-panel scientific
content; only the surface differs. Reuse the matching example 1-for-1 when the
new task is also a multi-stage data/methodology pipeline; only swap the
per-panel content and the bottom-ribbon chips.

## Style invariants (do not violate, regardless of variant)

- **English-only on canvas** — every label, equation, footer chip.
- **Default 18:9 cinematic wide** unless the user explicitly says otherwise.
- **Numbered marker on every panel** (circular badge "1"…"N" for friendly;
  tabular "01"…"0N" with foil-gold underline for editorial), top-left corner.
- **No watermarks, no fake logos, no brand names**.

### Friendly-only invariants

- **Whiteboard-sketch warmth, not corporate flatness** — wavy strokes, sticky
  notes, tiny doodles, off-white background, never pure white + pure black.
- **Friendly palette** (teal #2EC4B6, coral #FF6B6B, mustard #FFB627, soft
  purple #7C5CFF, forest green #3FA34D, charcoal #2B2D42 for text). Hex codes
  go in the prompt.

### Editorial-only invariants

- **Precision vector linework, not sketched** — uniform stroke widths,
  mathematically smooth curves, NO organic wobble. Always include the
  "Hard negatives" bullet from the style block.
- **Editorial palette** (deep navy #1A2E4F, ochre #C8932F, terracotta
  #B85A47, sage #6B8E5E, muted lilac #7C6BA1, warm charcoal #1B1B1B, foil
  gold #B8902E for accents). Hex codes go in the prompt.
- **Use the three named sub-patterns** — STATUS-BADGE / PULL-QUOTE /
  CONNECTION-LINE — instead of stamps, sticky notes, or motion arrows.
