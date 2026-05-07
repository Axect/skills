---
name: Friendly Whiteboard Slide Style
description: Reusable visual-style block for image-generation prompts that produce friendly, casual lab-meeting / workshop slide infographics with English-only text on a wide 18:9 canvas. Validated by the user on 2026-04-27 (OSPREY v0.21 prompt).
type: reference
---

# Friendly Whiteboard Slide — Canonical Style Block

Drop the blocks below verbatim into any image-generation prompt. The wording
itself is what the user validated as "굉장히 좋다"; do not paraphrase.

---

## OVERALL LOOK block

```
OVERALL LOOK:
- Clean off-white / warm cream background with subtle dotted grid.
- Modern flat-illustration style with a hand-drawn / whiteboard-sketch feel:
  slightly wavy strokes, soft drop shadows, rounded corners on every box.
- Friendly palette: teal (#2EC4B6), coral (#FF6B6B), mustard (#FFB627),
  soft purple (#7C5CFF), forest green (#3FA34D), charcoal (#2B2D42) for
  text. No pure black, no neon.
- Five panels flow LEFT to RIGHT, separated by chunky chalk-style arrows
  with little motion lines, like a comic strip. Each panel has a numbered
  circular badge ("1", "2", "3", "4", "5") in the top-left corner.
- Small playful touches: a tiny domain-relevant sticker doodle in one
  corner, a coffee-cup sticker, a sticky note pinned to a panel for a
  key takeaway. Avoid overly cute / childish; aim for a research-group
  whiteboard vibe.
```

> Adjust the panel count line ("Five panels…") to match the actual N.

---

## TYPOGRAPHY block

```
TYPOGRAPHY:
- Headlines: bold geometric sans (Inter / Manrope feel).
- Body labels: friendly humanist sans, slightly looser tracking.
- Equations rendered cleanly, NOT as garbled math glyphs.
- All annotations short — never more than 6 words per line.
- IMPORTANT: every character on the canvas must be readable English.
  Render math with plain ASCII / Greek letters only (α β σ μ Σ are fine);
  no decorative non-Latin script anywhere.
```

---

## COMPOSITION block

```
COMPOSITION:
- Strict 18:9 aspect ratio, generous internal margins.
- Panels are roughly equal width; widen the most content-heavy panel
  slightly if it carries sub-panels.
- Arrows between panels are chunky, slightly tilted, with small dashed
  motion marks — playful but readable.
- Avoid clutter: lots of breathing room, no overlapping text, no
  watermark, no fake logos.
```

> Change "18:9" to the requested aspect (16:9, 3:2, 4:3) if user overrides.

---

## MOOD block

```
MOOD: a research postdoc's friendly explainer slide for a small group
talk — clear, warm, a bit playful, but every label is technically correct.
```

---

## TITLE BAR pattern

```
TITLE BAR (top, full width):
- Bold sans-serif headline:
  "<HEADLINE>"
- Small subtitle: "<SUBTITLE>"
```

> Headline ≤ 8 words. Subtitle ≤ 14 words. English only.

---

## PANEL pattern

```
PANEL N — "<short name>":
- Centered: <main visual element with axes / labels / icons>.
- Caption under the visual: "<one short caption>".
- A small <card / sticky note / chip> floating to the side listing
  "<key parameters or formula>" in handwritten style.
```

For panels with sub-content, nest sub-bullets:

```
PANEL N — "<umbrella name>" (split into TWO sub-panels stacked vertically):
  TOP HALF — "<sub name>":
    • <element 1>
    • <equation / label>
  BOTTOM HALF — "<sub name>":
    • <element 1>
    • <equation / label>
```

---

## BOTTOM RIBBON pattern

```
BOTTOM RIBBON (full width, thin strip below panels):
- Four small labeled chips spaced evenly:
    "<chip 1>"   "<chip 2>"   "<chip 3>"   "<chip 4>"
- A tiny credit on the far right: "<project · version>".
```

> Chips are constants / scales / seeds — short factual labels, not narrative.

---

## English-only text guard rail (always last)

```
IMPORTANT: every character on the canvas must be readable English. Render
math with plain ASCII / Greek letters only (α β σ μ Σ are fine); no
decorative non-Latin script anywhere. No watermarks, no fake logos, no
brand names.
```

---

## Tone dials

| User asks for…           | Add / Remove                                                  |
|--------------------------|---------------------------------------------------------------|
| More playful             | Add `+ a coffee-cup sticker, +1 sticky-note doodle in a panel` |
| Calmer / more corporate  | Remove `chunky chalk-style arrows`, swap to `thin sharp arrows`; remove sticker doodles |
| Black-and-white / print  | Replace palette with `charcoal #2B2D42, mid-grey #6C757D, off-white #FAF8F5`; remove all color fills, keep stroke-only |
| Korean caption hybrid    | Title bar can stay English; explicitly allow `Korean caption text below each panel` and drop the English-only guard for that zone only |

---

## Validation note

This style block was first deployed on the **OSPREY v0.21 data-generation
prompt** (2026-04-27). The user response was *"오 지금 프롬프트의 스타일
Description이 굉장히 좋네"* and asked for it to be saved as a skill — that is
why this file exists. Treat the wording as load-bearing.
