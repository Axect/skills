---
name: Journal-Club Figure Generation
description: How to turn the method and results sections into two friendly-whiteboard infographic PNGs using the bundled codex image_generation tool. Includes the canonical style block, figure-brief schema, and the exact codex exec invocation.
type: reference
---

# Journal-Club Figure Generation

Two figures per review: one for **How It Works** (`method.png`) and one for
**Key Results** (`results.png`). Both are wide 18:9 friendly-whiteboard
infographics rendered by the bundled `codex` image_generation tool (ChatGPT
OAuth, no API key). Figures are optional: if codex is unavailable or a figure
fails, render that section text-only and move on.

## Step 1: check codex availability

```bash
codex login status        # need "Logged in using ChatGPT"
```

If not logged in, tell the user to run `codex login` and continue text-only.

## Step 2: build a figure brief for each anchor section

A brief is a small JSON-like structure you compose from the section content:

```
{
  "headline": "<= 8 words, the figure title",
  "subtitle": "one sentence describing what the figure shows",
  "panels": [
    {"name": "Panel label", "content": "short visual description: boxes, arrows, labels"},
    ...
  ]
}
```

- `method` brief: panels follow the pipeline left-to-right (input -> ... -> output).
- `results` brief: panels show bars, comparison callouts, before/after, key numbers.
- Panel `content` is a **visual** description (what to draw), not prose.
- Phrase every label as a **hand-written note drawn beside the shape**, never a
  pasted box or floating caption, so the image model integrates it into the one
  drawing instead of compositing a separate (and easily broken) text layer.
- **Panels are English-only and carry no formulas** even when the review body
  is in another language. Keep labels short (<= 6 words per line).

## Step 3: compose the full prompt

Concatenate the style block, the title bar, the panels, then the English guard.

### Canonical style block (use verbatim; adjust the panel-count line)

```
SINGLE COHESIVE ILLUSTRATION (read first):
- This is ONE flat hand-drawn whiteboard illustration. Every box, arrow,
  lattice, bar, curve, label, number and equation is drawn by the same hand in
  the same wavy marker stroke, as part of the one drawing.
- Do NOT paste any text as a separate overlay, floating caption, UI label, text
  box, or sticker layer on top of the artwork. There are NO compositing layers.
  All words are hand-lettered directly into the drawing in the same ink and style
  as the shapes around them. (gpt-image tends to break exactly the labels it
  treats as a separate pasted layer, so forbid that explicitly.)

OVERALL LOOK:
- Clean off-white / warm cream background with a subtle dotted grid.
- Modern flat-illustration style with a hand-drawn / whiteboard-sketch feel:
  slightly wavy strokes, soft drop shadows, rounded corners on every box.
- Friendly palette: teal (#2EC4B6), coral (#FF6B6B), mustard (#FFB627),
  soft purple (#7C5CFF), forest green (#3FA34D), charcoal (#2B2D42) for text.
  No pure black, no neon.
- Panels flow LEFT to RIGHT, separated by chunky chalk-style arrows with
  little motion lines, like a comic strip. Each panel has a numbered circular
  badge in its top-left corner.
- Annotations are short hand-written notes drawn beside the relevant shape,
  never floating boxes pasted on top. A small domain-relevant doodle drawn into
  one corner is fine. Research-group whiteboard vibe, not childish.

TYPOGRAPHY (all hand-lettered into the drawing, not a system-font overlay):
- Headlines: bold marker capitals (Inter / Manrope feel, but hand-drawn).
- Body labels: friendly hand-written humanist sans, slightly looser tracking.
- Equations drawn cleanly by hand, NOT garbled, NOT as a pasted text box.
- All annotations short, never more than 6 words per line.

COMPOSITION:
- Strict 18:9 aspect ratio, generous internal margins.
- Panels are roughly equal width; widen the most content-heavy panel slightly.
- Arrows between panels are chunky, slightly tilted, with small dashed motion
  marks, playful but readable.
- Avoid clutter: lots of breathing room, no overlapping text.

MOOD: a research postdoc's friendly explainer slide for a small group talk:
clear, warm, a bit playful, but every label is technically correct.
```

### Title bar + panels (fill from the brief)

```
TITLE BAR (top, full width):
- Bold headline: "<headline>"
- Subtitle: "<subtitle>"

<N> panels flow left to right:
PANEL 1 - "<name>":
  - <content>
PANEL 2 - "<name>":
  - <content>
...
```

### English guard (append verbatim)

```
IMPORTANT: every character on the canvas must be readable English, hand-lettered
as part of the illustration. Render math with plain ASCII / Greek letters only
(alpha beta sigma mu Sigma are fine); no decorative non-Latin script anywhere.
No watermarks, no fake logos, no brand names, and no separate text/sticker layers
pasted over the drawing.
```

## Step 4: generate (run the two in parallel)

Write each composed prompt to a temp file, then launch both codex jobs in the
same turn with `run_in_background: true` so they render concurrently (~1-2 min
each). Save into `<out_dir>/figures/`.

```bash
codex exec \
  --sandbox workspace-write \
  --skip-git-repo-check \
  --cd <out_dir>/figures \
  -o <out_dir>/figures/.codex-logs/method.md \
  "Use the image_generation tool to create the following wide 18:9 infographic slide and save it as ./method.png in the current directory. Do not edit any other files. Report only the saved file path.

PROMPT:
<composed method prompt>"
```

Repeat for `results.png` with the results prompt. (`mkdir -p
<out_dir>/figures/.codex-logs` first.)

## Step 5: embed only what succeeded

After both jobs finish, check each PNG exists and is non-empty:

```bash
[ -s <out_dir>/figures/method.png ] && echo method ok
[ -s <out_dir>/figures/results.png ] && echo results ok
```

Embed `![Method overview](figures/method.png)` at the end of **How It Works**
and `![Key results](figures/results.png)` at the end of **Key Results**, but
only for figures that were produced. Mention any figure that was skipped so the
review still reads cleanly text-only.

> The full set of alternative styles (editorial magazine, engineering blueprint,
> swiss minimalist, dark tech/neon, scientific poster) lives in the
> `wide-slide-illustrator` skill. The friendly whiteboard block above is the
> default for journal-club figures.
