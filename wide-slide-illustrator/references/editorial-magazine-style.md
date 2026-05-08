---
name: Editorial Magazine Slide Style
description: Reusable visual-style block for image-generation prompts that produce refined, magazine-style infographic slides — Quanta / NYT / The Atlantic feel — with English-only text on a wide 18:9 canvas. Sister style to friendly-whiteboard-style.md; same composition, more grown-up surface.
type: reference
---

# Editorial Magazine Slide — Canonical Style Block

Drop the blocks below verbatim into any image-generation prompt. Same 5-panel
left-to-right composition as the friendly-whiteboard variant, but with the
mood and surface of a feature-article infographic in Quanta Magazine, The New
York Times, or The Atlantic. Refined, considered, warm — never stiff or
corporate.

---

## OVERALL LOOK block

```
OVERALL LOOK:
- Warm cream paper background (#FBF7F0) with a faint paper grain and a
  hairline rule across the top and bottom — like a magazine spread.
- Editorial flat-illustration style: precision-rendered vector linework
  with uniform stroke widths and crisp anti-aliased edges. All curves
  (Gaussians, splines, staircases, power laws, pie-chart arcs, axes)
  are mathematically smooth — NO organic wobble, NO sketch strokes, NO
  hand-drawn unevenness, NO notebook/scrapbook texture anywhere. Soft
  vector shading, subtle long drop shadows, gently rounded corners.
- Hard negatives — DO NOT include any of: whiteboard sketch, sticker
  doodles, rubber-stamp graphics, cartoon icons, sticky notes, hand-
  lettered notes, comic-style motion lines, sketched / chunky arrows,
  dashed wobble strokes. The whole spread should look engraved /
  printed, not sketched.
- Refined editorial palette: deep navy (#1A2E4F), ochre (#C8932F),
  terracotta (#B85A47), sage (#6B8E5E), muted lilac (#7C6BA1), warm
  charcoal (#1B1B1B) for text. Accents may use a thin foil-gold rule
  (#B8902E). No neon, no pure black, no candy-bright primaries.
- Five panels flow LEFT to RIGHT, separated by thin vertical hairline
  rules with a small navy chevron (›) at the rule's vertical midpoint —
  like section breaks in a print article. Each panel is anchored by a
  small numbered marker in the top-left ("01" "02" "03" "04" "05") set
  in a tabular figure style with a foil-gold underline.
- Editorial flourishes (NOT stickers): a small drop-cap-style initial in
  one panel, a thin italic pull-quote tucked under one illustration, a
  hairline-bordered "fig. 1" label on the most diagram-heavy panel.
- Aim for a Quanta Magazine / NYT Upshot / Aeon explainer vibe — smart,
  warm, technically accurate, and distinctly print-influenced.
```

> Adjust the panel count line ("Five panels…") to match the actual N.

---

## TYPOGRAPHY block

```
TYPOGRAPHY:
- Headlines: refined transitional serif (Tiempos Headline / Mercury /
  GT Sectra feel) — generous letterspacing, slight optical refinement.
- Subheads & captions: small-caps tracking on labels, italic for
  pull-quotes, regular weight for body annotations.
- Body labels: clean humanist sans (Söhne / Untitled Sans / Inter feel),
  set tight but not cramped.
- Equations rendered as crisp typeset math, NOT garbled glyphs — italic
  variables, upright operators, proper subscripts.
- Figure markers ("fig. 1", "01") in a tabular monospace-influenced
  numeric style, with a hair-thin foil-gold underline.
- All annotations short — never more than 7 words per line.
- IMPORTANT: every character on the canvas must be readable English.
  Render math with plain ASCII / Greek letters only (α β σ μ Σ are fine);
  no decorative non-Latin script anywhere.
```

---

## COMPOSITION block

```
COMPOSITION:
- Strict 18:9 aspect ratio, generous editorial margins (think magazine
  gutter and folio space).
- Hairline rule (0.5pt feel) runs full-width above the title and below
  the bottom ribbon, anchoring the layout like a print article.
- Panels are roughly equal width; widen the most content-heavy panel
  slightly if it carries sub-panels. Vertical hairline dividers between
  panels — no arrows, no chunky strokes. Flow is implied by the dividers
  and the small navy chevron at each break.
- Avoid clutter: lots of breathing room, no overlapping text, no
  watermark, no fake logos, no stock photography.
- Illustrations sit centered within each panel with a calm baseline; the
  whole spread should read as one coherent magazine page, not five
  stickers glued together.
```

> Change "18:9" to the requested aspect (16:9, 3:2, 4:3) if user overrides.

---

## MOOD block

```
MOOD: a feature-article infographic from Quanta Magazine or The New York
Times — refined, warm, and printed-feeling, illustrating a research
methodology for an informed but non-specialist reader. Smart and
considered, never childish, never corporate-flat.
```

---

## TITLE BAR pattern

```
TITLE BAR (top, full width, sits below a hairline rule):
- Small italic eyebrow line above the headline:
  "<EYEBROW — e.g. 'methodology · v0.21'>"
- Bold serif headline (transitional / Tiempos feel):
  "<HEADLINE>"
- Small subtitle in upright sans, set in small-caps tracking:
  "<SUBTITLE>"
```

> Eyebrow ≤ 6 words. Headline ≤ 8 words. Subtitle ≤ 14 words. English only.

---

## PANEL pattern

```
PANEL N — "<short name>":
- Small numeric marker top-left ("0N") with a foil-gold underline.
- Centered: <main visual element with axes / labels / icons>, rendered as
  a refined editorial vector illustration — clean lines, soft fills,
  subtle long shadow.
- Caption under the visual, set in italic sans: "<one short caption>".
- A small hairline-bordered side card listing "<key parameters or
  formula>" in upright sans + italic variables.
```

### Status-badge pattern (use INSTEAD of stamps)

For pass/fail, accept/reject, OK/error markers, NEVER use a rubber-stamp
metaphor and NEVER use angled cartoon stamps. Use a small hairline-
bordered status badge instead:

```
• Sage filled dot (#6B8E5E) + upright-sans label "<positive>  OK"
• Terracotta filled dot (#B85A47) + upright-sans label "<negative>  REJECT"
```

Both badges sit horizontally side-by-side with a mid-dot bullet between
them, set in small-caps tracking. The badge is a refined editorial UI
element, not a graphic stamp.

### Pull-quote pattern (use INSTEAD of sticky / handwritten notes)

For an emphasized takeaway line inside or under a panel, use a precisely
typeset italic serif pull-quote, set between two hair-thin horizontal
rules (or with a single foil-gold left border). The text is rendered as
proper typography — NOT handwritten, NOT a sticky note, NOT a doodle,
NOT angled.

### Connection-line pattern (use INSTEAD of arrows / motion lines)

For radiation, flow, or "X feeds into Y" relationships inside a panel,
use fine straight lead lines (1px feel) terminating in a small filled
dot or thin chevron tip, optionally combined with a subtle radial
gradient halo around the source. NEVER use chunky arrows, motion lines,
dashed comic-style strokes, sketched arrows, or hand-drawn flow
indicators.

For panels with sub-content, nest sub-bullets:

```
PANEL N — "<umbrella name>" (split into TWO sub-panels stacked vertically,
divided by a hairline rule):
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
BOTTOM RIBBON (full width, sits above a hairline rule at the very bottom):
- Four small labeled chips spaced evenly, separated by mid-dot bullets:
    "<chip 1>"  ·  "<chip 2>"  ·  "<chip 3>"  ·  "<chip 4>"
- Set in small-caps tracking, warm charcoal on cream — like a folio line
  in a magazine.
- A tiny credit on the far right in italic: "<project · version>".
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
| More print-zine feel     | Add `+ subtle paper grain noise, +1 slightly off-register foil-gold rule, +1 ornamental drop cap on the leftmost panel` |
| Cleaner / more Bauhaus   | Remove `paper grain, foil-gold underline, drop cap`; swap serif headline for a precise geometric sans (GT America / Söhne) |
| Black-and-white / print  | Replace palette with `warm charcoal #1B1B1B, mid-grey #6C757D, cream #FBF7F0`; keep only stroke + tonal fills, drop colored accents |
| Korean caption hybrid    | Title bar can stay English; explicitly allow `Korean italic caption text below each panel` and drop the English-only guard for that zone only |

---

## Lineage note

This style block is the **Editorial Magazine** sister of
`friendly-whiteboard-style.md`. Same 5-panel composition, same English-only
guard rail, same skill-level structure — but the surface is print-magazine
refined instead of whiteboard-friendly. Selected on 2026-05-08 from a 4-way
style menu (Editorial Magazine · Engineering Blueprint · Swiss Minimalist ·
Dark Tech) when the user asked for non-friendly variants of the same skill.

### v2 hardening (2026-05-08)

The first OSPREY v0.21 generation under this style still leaked friendly
cues — wobbly Gaussian curves, sketchy pie-chart outline, cartoon
pass/reject stamps, hand-lettered pull-quote, chunky radiation arrows in
the black-hole panel. Fix was to add explicit **hard negatives** in the
OVERALL LOOK block and to add three concrete sub-patterns (status badge,
pull-quote, connection line) so the prompt names refined replacements for
the residual whiteboard tropes. Always include those sub-patterns when a
panel needs a stamp / sticky-note / motion-arrow equivalent.

Invocation tags inside prompts use the ALL-CAPS form: **STATUS-BADGE PATTERN / PULL-QUOTE PATTERN / CONNECTION-LINE PATTERN** (section headings above are Title-case markdown convention; the prompt-side tag is ALL-CAPS for visibility — see `example-osprey-editorial.md`).
