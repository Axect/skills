---
name: Scientific Poster Slide Style
description: Reusable visual-style block for image-generation prompts that produce journal-figure-style infographic slides — feel of a Physical Review / Nature / Science figure or a preprint cover plot — with English-only text on a wide 18:9 canvas. Sister style to friendly-whiteboard-style.md, editorial-magazine-style.md, engineering-blueprint-style.md, swiss-minimalist-style.md, and dark-tech-neon-style.md.
type: reference
---

# Scientific Poster Slide — Canonical Style Block

Drop the blocks below verbatim into any image-generation prompt. Same 5-panel
left-to-right composition as the other variants, but the surface is reduced
to journal-figure conventions: white paper, black ink, viridis-style sequential
data colors, serif body typography, panel labels "(a) (b) (c) (d) (e)", a
single bold "FIG. N." caption, and clean inward tick marks. Reads as a
published article figure, not a slide and not an infographic in the
journalistic sense.

This variant is the right call when the user wants the spread to live inside
a paper, preprint cover, talk slide that masquerades as a paper figure, or
poster session display.

---

## OVERALL LOOK block

```
OVERALL LOOK:
- Pure white paper background (#FFFFFF) — never cream, never off-white
  unless the target venue specifies otherwise. No texture, no gradient,
  no grid pattern.
- Strict journal-figure style: precision-rendered vector linework
  (matplotlib / PGFPlots quality), uniform thin strokes (typically
  0.75pt for axes, 1pt–1.5pt for data lines), perfectly anti-aliased
  edges. All curves (Gaussians, splines, staircases, power laws) are
  mathematically smooth — NO organic wobble, NO sketch strokes, NO
  hand-drawn unevenness anywhere.
- Hard negatives — DO NOT include any of: cream / off-white / dark
  backgrounds, drop shadows, gradients (except inside heatmap data
  fills), neon colors, casual / friendly cues, sticker doodles, sticky
  notes, hand-lettered notes, magazine flourishes (drop caps,
  foil-gold rules, pull-quotes), journalistic eyebrows or feature-spread
  headlines, blueprint cyan-on-navy, Swiss huge-number markers, neon
  glow halos, decorative ribbon chips. The whole spread should look
  like a figure that was just dropped into a Phys Rev or Nature paper.
- Restrained academic palette: black ink (#000000) for ALL linework,
  axes, ticks, panel labels, and body text. Sequential data colors
  use a viridis-style ramp (#440154 → #3B528B → #21908C → #5DC863 →
  #FDE725) OR a Tableau-Colorblind-10 set if categorical. ONE accent
  red (#C1272D) reserved strictly for emphasis (e.g., a critical
  threshold line, a rejected branch). No other colors. No pastel.
- Five panels flow LEFT to RIGHT, each enclosed in a thin black axis
  frame (0.75pt) where appropriate. Panels separated by generous
  whitespace (no rules, no chevrons) — the reader navigates by the
  bold panel labels "(a)" "(b)" "(c)" "(d)" "(e)" in the top-left of
  each panel.
- Journal flourishes (NOT decorative): small serif "FIG. 1." prefix
  introducing the running caption; tick marks pointing INWARD on every
  axis (not outward); axis labels in italic for variables (M, ψ, E)
  with units in upright parentheses; equations rendered in proper math
  italics (Computer Modern feel). NO infographic-style stage names.
```

> Adjust the panel count line ("Five panels…") to match the actual N.

---

## TYPOGRAPHY block

```
TYPOGRAPHY:
- Body, captions, panel labels: serif throughout (Computer Modern / Source
  Serif Pro / Linux Libertine / Times-like feel). Body weight regular.
- Bold serif used for the "FIG. N." prefix, panel-label letters
  ("(a) (b) (c) (d) (e)"), and any inline emphasis.
- Italic serif used for variables in math AND in caption text (per
  journal convention: "where M denotes the mass…").
- Axis labels: small sans-serif (Helvetica feel) is acceptable as a
  graphics convention; OR keep serif throughout for stricter coherence.
  Pick one and stay consistent within the spread.
- Equations rendered as proper LaTeX-style math: italic variables
  (α β σ μ Σ M ψ E are fine), upright operators, proper subscripts and
  superscripts, no calligraphic decoration.
- Caption text is sentence-case running prose, NOT bullet points, NOT
  fragments. Per journal convention, panel descriptions are stitched
  together inside one running sentence: "(a) Sample base GBP. (b) Roll
  perturbation type. (c) …".
- Annotations short and sober — no exclamations, no rhetorical
  questions, no second-person voice.
- IMPORTANT: every character on the canvas must be readable English.
  Render math with plain ASCII / Greek letters only (α β σ μ Σ are fine);
  no decorative non-Latin script anywhere.
```

---

## COMPOSITION block

```
COMPOSITION:
- Strict 18:9 aspect ratio. Margins are journal-figure tight (about
  4–6% on every side) — use the canvas efficiently like a published
  figure rather than a slide.
- Five panels are roughly equal width with the middle panel slightly
  wider if it carries sub-panels labeled (c1) and (c2). Panels are
  separated by generous whitespace, NOT by rules or chevrons.
- Panel labels "(a)"…"(e)" sit in the top-left INSIDE each panel
  (typically just inside the axis frame), bold serif, ~10–12pt feel.
- The "FIG. N." running caption sits below the panel row, full width,
  serif body, sentence-case, with each panel introduced parenthetically
  by its letter ("(a) … (b) … (c) …").
- Avoid clutter: lots of breathing room, no watermarks, no fake logos,
  no journalistic ribbon chips. Optional small footer text below the
  caption for grant / data acknowledgement, italic serif.
```

> Change "18:9" to the requested aspect (16:9, 3:2, 4:3) if user overrides.

---

## MOOD block

```
MOOD: a figure pulled directly from a Phys Rev / Nature / Science
article, or from a preprint that takes itself seriously. Sober, precise,
and nearly silent — the figure does the talking via clean axes,
data-driven curves, and a tightly written running caption. Reads like
peer-reviewed work, not a slide and not a magazine spread.
```

---

## TITLE BAR pattern (replaced by FIG-CAPTION)

The Scientific Poster variant does NOT have a "title bar" in the
infographic sense. Instead, the running caption sits BELOW the panel row.
There is no eyebrow, no headline, no subtitle — only the figure caption.

```
FIG-CAPTION (full width, sits below the panel row):
- Bold serif "FIG. N." prefix, followed by a sentence-case sober title:
  "<figure title — descriptive, no rhetorical questions>."
- Then a running caption that introduces each panel parenthetically by
  its letter, in serif body, sentence-case:
  "(a) <one-clause description>. (b) <one-clause description>. (c) <…>.
   (d) <…>. (e) <…>. <Optional closing sentence with key parameters or
   observations.>"
- Optional small italic-serif footer below the caption for grant or
  data attribution (~8pt feel).
```

> Figure title ≤ 12 words. Each panel clause ≤ 14 words. Closing
> sentence (if any) ≤ 25 words. English only. No rhetorical questions.
> No second person.

---

## PANEL pattern

```
PANEL (a) — "<short name>":
- Bold serif label "(a)" in the top-left corner, just inside the axis
  frame.
- Centered: <main visual element>, rendered as a precision data plot
  with a thin black axis frame (0.75pt), inward-pointing tick marks on
  every axis, italic-serif axis labels for variables (e.g., italic M,
  italic ψ) and upright units in parentheses (e.g., "log₁₀ M (M_⊙)").
- Data curves use the viridis sequential ramp OR Tableau-Colorblind-10
  if categorical. ONE accent red (#C1272D) reserved strictly for
  emphasis (a critical line, a rejected branch).
- NO stage-name banner above the plot. NO ribbon chips next to the
  plot. NO side cards. The plot is the panel.
- A small italic-serif annotation INSIDE the axis frame (top-right) is
  acceptable for a single key value (e.g., "≈ 2% pass"). Use sparingly.
```

### Panel-letter pattern (use INSTEAD of numeric markers)

Replace the "01" / "[01]" / huge "01" markers used by other variants
with bold serif lowercase letters in parentheses: "(a) (b) (c) (d) (e)",
positioned in the top-left corner INSIDE each panel's axis frame. Per
journal convention. NEVER use numbered badges, neon chips, or huge
numerals.

### Fig-caption pattern (use INSTEAD of title bar + ribbon)

Replace the headline + subtitle + bottom ribbon with a single FIG-CAPTION
block sitting BELOW the panel row: bold serif "FIG. N." + sober figure
title + running sentence-case caption introducing each panel
parenthetically. Optional italic footer for attribution. NO journalistic
eyebrows, NO marketing-style subtitles, NO ribbon chips with constants
(constants belong inside the running caption text).

### Axis-label pattern (use INSTEAD of stage names)

Every plot carries proper axis labels: italic variable + upright unit in
parentheses (e.g., "log₁₀ M (M_⊙)", "E (GeV)", "dN/dE (GeV⁻¹)"). Tick
marks ALWAYS point INWARD, not outward. Logarithmic axes labeled
explicitly ("log₁₀ ψ"). NEVER replace axis labels with infographic-style
stage names like "INIT" / "FLOW" / "NOISE".

For panels with sub-content, use journal-style sub-labels (a1), (a2):

```
PANEL (c) — "<umbrella name>" (split into TWO sub-panels stacked vertically
or side-by-side, each labeled (c1) and (c2)):
  (c1) — "<sub name>":
    • <data plot>
    • <axis labels>
  (c2) — "<sub name>":
    • <data plot>
    • <axis labels>
```

---

## BOTTOM RIBBON pattern (omitted)

The Scientific Poster variant does NOT include the bottom ribbon used by
other variants. Constants and parameters live inside the running figure
caption text instead (e.g., "…with N=10⁴ samples, σ=0.05, seed=42").

If a small footer line is genuinely needed (grant attribution, data
release), use a single italic-serif line at the bottom of the canvas,
left-aligned, ~8pt feel. NO chips, NO mid-dot bullets, NO key=value
columns.

---

## English-only text guard rail (always last)

```
IMPORTANT: every character on the canvas must be readable English. Render
math with plain ASCII / Greek letters only (α β σ μ Σ M ψ E are fine);
no decorative non-Latin script anywhere. No watermarks, no fake logos,
no brand names. The whole spread is a journal figure — no infographic,
sketched, magazine, blueprint, Swiss-minimal, or neon cues anywhere.
```

---

## Tone dials

| User asks for…                  | Add / Remove                                                  |
|---------------------------------|---------------------------------------------------------------|
| Stricter Phys Rev style         | Restrict body face to Computer Modern; drop sans axis labels and use serif throughout; tighten margins further |
| Slightly Nature-style           | Allow color-coded data ribbons spanning panels; allow wider use of Tableau-Colorblind-10 categorical colors; permit a gentle italic-serif side annotation |
| Preprint-cover hybrid           | Allow a single small bold serif title above the FIG. N. caption (≤ 6 words); keep everything else strict |
| Korean caption hybrid           | The figure title may stay English; explicitly allow `Korean serif caption text` running below the FIG. N. line and drop the English-only guard for that zone only |

---

## Lineage note

This style block is the **Scientific Poster** sister of
`friendly-whiteboard-style.md`, `editorial-magazine-style.md`,
`engineering-blueprint-style.md`, `swiss-minimalist-style.md`, and
`dark-tech-neon-style.md`. Same 5-panel composition, same English-only
guard rail, same skill-level structure — but the surface is reduced to
published-figure conventions: white paper, black ink, viridis data
colors, serif body, panel labels (a)…(e), running FIG. N. caption,
inward tick marks. Use the named sub-patterns (PANEL-LETTER,
FIG-CAPTION, AXIS-LABEL) whenever a panel would otherwise want a
numbered badge, a journalistic title bar, or an infographic stage name.
The bottom ribbon is intentionally omitted in this variant — constants
live inside the running caption. The hard-negatives bullet is
mandatory — without it, infographic flourishes leak through and the
spread stops looking like a journal figure.
