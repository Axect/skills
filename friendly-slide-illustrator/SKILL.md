---
name: friendly-slide-illustrator
description: >
  Compose detailed image-generation prompts (ChatGPT Image 2.0 / gpt-image-1, DALL-E,
  Sora image, Midjourney) for friendly, whiteboard-style infographic slides — the
  kind used in casual lab meetings, group seminars, internal demos, or workshop
  talks rather than stiff conference posters. Output prompts always force on-image
  text to be English-only, request a wide cinematic aspect (default 18:9), and
  combine a reusable style block with task-specific panel content.
  Use when the user asks to: generate a slide illustration, make a friendly
  infographic, create a wide pipeline diagram, draw a "how it works" figure for
  an informal talk, or produce an image-generator prompt for a methodology /
  data-pipeline / architecture overview.
  Triggers on: "friendly slide", "lab meeting figure", "whiteboard style",
  "infographic prompt", "wide pipeline figure", "ChatGPT image prompt",
  "image generation prompt", "casual presentation diagram".
---

# Friendly Slide Illustrator — Image Prompt Composer

Generate detailed prompts for raster image-generation models (ChatGPT Image 2.0,
DALL-E 3, gpt-image-1, Sora image, Midjourney) that produce friendly,
whiteboard-flavored infographic slides for informal research talks.

The user already validated this style on the OSPREY v0.21 data-generation slide
prompt (2026-04-27). The reusable style block lives in
`references/friendly-whiteboard-style.md`; the full v0.21 prompt is preserved as
a worked example in `references/example-osprey-v021.md`.

## When to use

Trigger this skill when the user wants an **image-generator prompt** (not a
matplotlib/seaborn plot, not a paperbanana diagram) for one of:

- A **methodology / pipeline / architecture** overview slide for a friendly
  audience (lab meeting, seminar, workshop, informal demo).
- A **data-generation flowchart** with multiple stages flowing left-to-right.
- A **"how X works"** explainer figure for a blog post or casual deck.

Do NOT use for:

- Publication figures with strict statistical content → use `paperbanana` skill.
- Real plots from data (matplotlib, seaborn, plotly) → write code directly.
- Slide *decks* (multi-slide presentations) → use `claude-typst-slides` or
  `frontend-slides`.

## How to compose a prompt

### Step 1 — Read the style block

Always read `references/friendly-whiteboard-style.md`. It defines the canonical
visual identity (palette, typography, mood, composition rules) that the user
liked. Do not paraphrase — the wording itself is what the user validated.

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

1. **One-paragraph framing**: "A cinematic-wide {aspect} horizontal infographic
   illustrating {topic}, designed as a friendly conference-slide visual (NOT a
   stiff academic figure). All text in the image MUST be in English only."
2. **`OVERALL LOOK:` block** — copy the palette + stroke + sticker rules from
   `references/friendly-whiteboard-style.md`.
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
- **Tone dials**: tell the user which lines to drop for a calmer look (sticker
  doodles, chunky chalk arrows) or add for a more playful one.

## Worked example

See `references/example-osprey-v021.md` for the full prompt that the user
approved. Reuse its structure 1-for-1 when the new task is also a multi-stage
data/methodology pipeline; only swap the content of the panels and footer
chips.

## Style invariants (do not violate)

- **English-only on canvas** — every label, equation, footer chip.
- **Default 18:9 cinematic wide** unless the user explicitly says otherwise.
- **Whiteboard-sketch warmth, not corporate flatness** — wavy strokes, sticky
  notes, tiny doodles, off-white background, never pure white + pure black.
- **Friendly palette** (teal #2EC4B6, coral #FF6B6B, mustard #FFB627, soft
  purple #7C5CFF, forest green #3FA34D, charcoal #2B2D42 for text). Hex codes
  go in the prompt.
- **Numbered circular badges** on each panel ("1"…"N") in the top-left corner.
- **No watermarks, no fake logos, no brand names**.
