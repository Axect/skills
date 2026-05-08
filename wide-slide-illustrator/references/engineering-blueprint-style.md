---
name: Engineering Blueprint Slide Style
description: Reusable visual-style block for image-generation prompts that produce technical-blueprint / schematic-style infographic slides — feel of a NASA / SpaceX engineering diagram or a CAD blueprint sheet — with English-only text on a wide 18:9 canvas. Sister style to friendly-whiteboard-style.md and editorial-magazine-style.md.
type: reference
---

# Engineering Blueprint Slide — Canonical Style Block

Drop the blocks below verbatim into any image-generation prompt. Same 5-panel
left-to-right composition as the friendly and editorial variants, but with the
mood and surface of a technical drafting sheet — deep navy ground, cyan
linework, monospace annotations, dimension lines and terminal nodes. Reads as
a system schematic, not a slide doodle and not a magazine spread.

---

## OVERALL LOOK block

```
OVERALL LOOK:
- Deep navy blueprint background (#0A1F3D) with a faint cyan grid pattern
  at ~10mm × 10mm spacing (#143257 grid lines, low opacity), and a thin
  cyan trim border framing the full canvas.
- Strict technical-schematic style: precision-rendered vector linework,
  uniform stroke widths (0.5pt / 1pt / 2pt only — choose deliberately),
  orthogonal routing for all connectors (right-angle bends, never diagonal),
  perfect anti-aliased edges. All curves (Gaussians, splines, staircases,
  power laws) are mathematically smooth — NO organic wobble, NO sketch
  strokes, NO hand-drawn unevenness anywhere.
- Hard negatives — DO NOT include any of: warm/cream backgrounds,
  serif typography, soft drop shadows, watercolor or painterly fills,
  sticker doodles, sticky notes, hand-lettered notes, comic-style motion
  lines, sketched / chunky arrows, dashed wobble strokes, friendly
  palette colors (teal #2EC4B6 / coral #FF6B6B / mustard #FFB627 /
  purple #7C5CFF), magazine flourishes (drop caps, foil-gold rules,
  pull-quotes), neon glow halos. The whole spread should look like a
  printed engineering schematic, not a slide and not an article.
- Technical palette: navy ground (#0A1F3D), grid (#143257), primary
  linework cyan (#6FE4FF), white text and labels (#F4ECD8 cream-white),
  amber accent for critical values (#FFB000), pale green for OK
  indicators (#B8D8BE), red-orange for warnings/rejects (#FF6B5C). No
  pastel, no neon glow, no gradients in linework.
- Five panels flow LEFT to RIGHT, separated by thick orthogonal bus
  lines (2–3px cyan) routing along the bottom of the panel row, with
  small filled cyan terminal nodes (3px circles) where bus lines branch
  into each panel. Each panel is anchored by a small marker in the
  top-left ("[01]" "[02]" "[03]" "[04]" "[05]") in monospace, all-caps,
  cyan, with a 1px cyan underscore.
- Schematic flourishes (NOT decorative): a thin cyan dimension line
  with tick caps "┤  N=1e4  ├" floating above one panel; a small
  hexadecimal build-ID badge "0xA21F" in the title bar; a tiny
  "REV v0.21" stamp in monospace top-right of the canvas; subtle
  measurement marks along the canvas trim border.
```

> Adjust the panel count line ("Five panels…") to match the actual N.

---

## TYPOGRAPHY block

```
TYPOGRAPHY:
- Headlines: clean monospace (Berkeley Mono / JetBrains Mono / IBM
  Plex Mono feel), all-caps, generous letterspacing, white on navy.
- Subheads & stage names: monospace all-caps with wider tracking.
- Body labels & values: monospace upright, mixed case, tight tracking.
- Equations rendered as crisp typeset math but in a monospace-leaning
  feel — italic Greek variables (α β σ μ Σ) are fine, upright operators,
  proper subscripts. NO swash serifs, NO calligraphic flourishes.
- Numeric markers ("[01]"), build IDs, and ribbon values all in
  monospace with optional 1px cyan underscore.
- All annotations short — never more than 7 words per line.
- IMPORTANT: every character on the canvas must be readable English.
  Render math with plain ASCII / Greek letters only (α β σ μ Σ are fine);
  no decorative non-Latin script anywhere.
```

---

## COMPOSITION block

```
COMPOSITION:
- Strict 18:9 aspect ratio, generous schematic margins.
- Faint cyan grid running full-canvas (excluding title and bottom-ribbon
  zones) at ~10mm × 10mm. Cyan trim border 1px around the full canvas.
- Panels are roughly equal width with the middle panel slightly wider
  if it carries sub-panels. Each panel is a sharp-cornered cyan-bordered
  box (1px stroke, 2px-radius corners optional) with a faint
  semi-transparent inner fill (~5% lighter than ground).
- Connectors between panels: thick orthogonal bus lines (2–3px cyan)
  running along the bottom of the panel row, branching upward into each
  panel via a small terminal node (3px filled cyan circle). NO arrows,
  NO chevrons, NO chunky strokes — just orthogonal bus routing.
- Avoid clutter: lots of breathing room, no overlapping text, no
  watermark, no fake logos.
```

> Change "18:9" to the requested aspect (16:9, 3:2, 4:3) if user overrides.

---

## MOOD block

```
MOOD: a printed engineering schematic from an aerospace / instrumentation
team — precise, technical, restrained, and unmistakably drafted on
blueprint paper. Reads like a system diagram, not a slide. Cool, clear,
and a little severe; never warm, never playful, never magazine-like.
```

---

## TITLE BAR pattern

```
TITLE BAR (top, full width, cyan trim above, monospace):
- Small monospace eyebrow line above the headline:
  "<PROJECT> — <SUBSYSTEM>   ::   REV v<NN.NN>"
- Bold all-caps monospace headline:
  "<HEADLINE>"
- Small monospace subtitle:
  "<SUBTITLE>   ·   BUILD 0x<HEX>"
- A "REV vN.NN" stamp top-right, monospace cyan, small.
```

> Headline ≤ 8 words, all-caps. Subtitle ≤ 14 words. English only.

---

## PANEL pattern

```
PANEL N — "<short name>":
- Marker "[0N]" top-left in monospace cyan with 1px cyan underscore.
- Optional small hexadecimal stage-ID badge top-right of the panel
  (e.g., "0x03A1") in monospace, faint.
- Centered: <main visual element with axes / labels / icons>, rendered
  as a precision schematic — uniform 1–2px cyan strokes, mathematically
  smooth curves, white labels, amber for any critical numeric value.
- Caption under the visual in monospace, mixed case: "<one short caption>".
- A small sharp-cornered side card to the right (1px cyan border, faint
  inner fill) listing "<key parameters or formula>" in monospace upright
  with italic Greek variables.
```

### Dimension-line pattern (use INSTEAD of stickers / sticky notes for callouts)

For an annotated value or constraint that needs to live near a graphic,
NEVER use a sticky note or a hand-lettered note. Use a thin cyan
dimension line (0.5pt) with tick caps at both ends, value label centered
above the line in monospace:

```
┤   N = 1e4   ├
```

NOT a sticker. NOT a sticky note. NOT angled.

### Terminal-node pattern (use INSTEAD of arrowheads on connectors)

For any "X feeds into Y" relationship, use a 2–3px cyan orthogonal line
terminating in a small filled cyan circle (3px) at the destination — the
node is the connector, not an arrowhead. NEVER use chunky arrows, motion
lines, dashed comic-style strokes, sketched arrows.

### Stage-box pattern (use INSTEAD of rounded panel containers)

Each panel container is a sharp-cornered rectangle (or 2px-radius corners
maximum) with a 1px cyan border and a faint semi-transparent inner fill
(~5% lighter than ground). NOT a rounded card. NOT a magazine panel.
NOT a friendly bubble.

For panels with sub-content, nest sub-bullets:

```
PANEL N — "<umbrella name>" (split into TWO sub-panels stacked vertically,
divided by a 1px cyan rule):
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
BOTTOM RIBBON (full width, sits above a 1px cyan rule at the very bottom):
- Five small monospace key=value chips spaced evenly, separated by
  vertical bar dividers, set in monospace upright, cyan keys + white
  values:
    "N=1e4"  |  "σ=0.05"  |  "seed=42"  |  "dt=1e-3"  |  "BUILD 0xA21F"
- A tiny credit on the far right in monospace: "<project> · v<N.NN>".
```

> Chips are constants / scales / seeds / build IDs — short factual labels.

---

## English-only text guard rail (always last)

```
IMPORTANT: every character on the canvas must be readable English. Render
math with plain ASCII / Greek letters only (α β σ μ Σ are fine); no
decorative non-Latin script anywhere. No watermarks, no fake logos, no
brand names. The whole spread is precision technical schematic — no
sketched, hand-drawn, magazine, or neon cues anywhere.
```

---

## Tone dials

| User asks for…                  | Add / Remove                                                  |
|---------------------------------|---------------------------------------------------------------|
| Cream-paper blueprint hybrid    | Swap navy ground for cream paper #F4ECD8, swap cyan linework for navy #0A1F3D, keep monospace + amber accents |
| More CAD-precise / sterile      | Drop the build-ID stamp, drop the cyan trim border, increase grid contrast slightly, tighten panel margins |
| More retro drafting feel        | Add a faint linen paper texture overlay at low opacity, swap cyan for white linework on navy, add small pencil-tick measurement marks on the trim border |
| Korean caption hybrid           | Title bar can stay English; explicitly allow `Korean monospace caption text below each panel` and drop the English-only guard for that zone only |

---

## Lineage note

This style block is the **Engineering Blueprint** sister of
`friendly-whiteboard-style.md` and `editorial-magazine-style.md`. Same
5-panel composition, same English-only guard rail, same skill-level
structure — but the surface is technical drafting paper instead of
whiteboard or magazine spread. Use the named sub-patterns
(DIMENSION-LINE, TERMINAL-NODE, STAGE-BOX) whenever a panel would
otherwise want a sticker, an arrow, or a rounded card. The hard-negatives
bullet is mandatory — without it, friendly or magazine cues leak through.
