---
name: Hand-Drawn Schematic Style Block
description: The canonical pure-white friendly hand-drawn whiteboard style block for one-glance schematic figures, plus the figure-brief schema, the English guard, and the exact codex exec invocation. Use the style wording verbatim; it is load-bearing.
type: reference
---

# Hand-Drawn Schematic Style Block

One friendly hand-drawn whiteboard illustration on a **pure white background**.
The wording below is validated and load-bearing: drop it into the prompt
verbatim, do not paraphrase. The only change from the journal-club
friendly-whiteboard block is the background (pure white, no cream tint).

## Figure-brief schema

Compose this small structure from the schema before writing the prompt:

```
{
  "headline": "<= 8 words, the figure title",
  "subtitle": "one sentence describing what the figure shows",
  "panels": [
    {"name": "Panel label", "content": "short visual description: boxes, arrows, labels, small charts"},
    ...
  ]
}
```

- Panels flow left to right (input -> ... -> output) or as parallel facets of
  one idea. 3 to 6 panels; widen the most content-heavy one slightly.
- `content` is a **visual** description (what to draw), not prose.
- Every label is a **hand-written note drawn beside the shape**, never a pasted
  box or floating caption.
- Panels are **English-only** and carry short labels (<= 6 words per line),
  regardless of the conversation language.
- A panel with a chart must say the chart stays hand-drawn ("wobbly hand-drawn
  marker bars with uneven tops, hand-lettered numbers, NOT a clean
  digital/matplotlib chart"), so it does not clash with the sketch.

## Canonical style block (use verbatim; adjust the panel-count line)

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
- Pure white (#FFFFFF) background: clean, bright, completely white, with NO
  cream / beige / warm tint and NO dotted grid. Just white paper.
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

## Title bar + panels (fill from the brief)

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

## English guard (append verbatim)

```
IMPORTANT: every character on the canvas must be readable English, hand-lettered
as part of the illustration. Render math with plain ASCII / Greek letters only
(alpha beta sigma mu Sigma are fine); no decorative non-Latin script anywhere.
No watermarks, no fake logos, no brand names, and no separate text/sticker layers
pasted over the drawing. The background stays pure white (#FFFFFF), no cream tint.
```

## Render with codex

Write the composed prompt to a temp file, then:

```bash
mkdir -p <out_dir>/.codex-logs
codex exec \
  --sandbox workspace-write \
  --skip-git-repo-check \
  --cd <out_dir> \
  -o <out_dir>/.codex-logs/schematic.md \
  "Use the image_generation tool to create the following wide 18:9 infographic slide and save it as ./schematic.png in the current directory. Do not edit any other files. Report only the saved file path.

PROMPT:
<composed prompt>"
```

For multiple figures, launch the codex jobs in the same turn with
`run_in_background: true` so they render concurrently. After each finishes,
verify the PNG is non-empty (`[ -s <out_dir>/schematic.png ]`) before reporting
it.

> The broader family of alternative styles (editorial magazine, engineering
> blueprint, swiss minimalist, dark tech/neon, scientific poster) lives in the
> `wide-slide-illustrator` skill. This pure-white friendly whiteboard block is
> the default for hand-drawn schematics.
