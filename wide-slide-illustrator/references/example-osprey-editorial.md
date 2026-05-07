---
name: Example — OSPREY v0.21 Editorial Magazine Prompt
description: Worked example of the editorial-magazine-style block applied to the OSPREY v0.21 unified data-generation pipeline. 5-panel 18:9 magazine-spread infographic. User-approved on 2026-05-08 after one v1 → v2 hardening pass.
type: reference
---

# Worked Example — OSPREY v0.21 Editorial Magazine (5 panels, 18:9)

Sister example to `example-osprey-v021.md` (friendly whiteboard variant). Same
panel content; surface swapped for the editorial-magazine style block. When a
new task wants the editorial look, reuse this prompt 1-for-1 and only swap
per-panel content.

## Final approved prompt (v2)

```
A cinematic-wide 18:9 horizontal infographic illustrating a five-stage data
generation pipeline for a physics machine-learning project, designed as a
refined magazine-style spread — feel of a Quanta Magazine / NYT Upshot /
The Atlantic feature-article infographic. NOT a friendly whiteboard sketch
and NOT a stiff academic figure. The whole spread should look engraved /
printed, not sketched. All text in the image MUST be in English only — no
other languages, no garbled glyphs.

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
  small numeric marker in the top-left ("01" "02" "03" "04" "05") set
  in a tabular figure style with a foil-gold underline.
- Editorial flourishes (NOT stickers): a small drop-cap-style serif
  initial "O" tucked into Panel 1, a typeset italic pull-quote under
  Panel 4 (precisely set between two hair-thin rules — see Pull-quote
  pattern below), a hairline-bordered "fig. 1" tag on Panel 3.

TITLE BAR (top, full width, sits below a hairline rule):
- Small italic eyebrow line above the headline:
  "methodology · v0.21"
- Bold serif headline (Tiempos / Mercury feel):
  "OSPREY — How We Cook the Training Data"
- Small subtitle in upright sans, set in small-caps tracking:
  "Unified pipeline: GBP base + Fold + FCP perturbations → Hawking spectrum"

PANEL 1 — "Sample a base GBP":
- Numeric marker "01" top-left with foil-gold underline.
- Centered: a precision-rendered, mathematically smooth bell curve drawn
  on log-log axes labeled "log₁₀ M  [13 → 22]" (x-axis) and "ψ(M)"
  (y-axis), with soft tonal fill under the curve and a subtle long drop
  shadow.
- Italic typeset caption under the curve: "Generalized Beta Prime (GBP)
  base distribution".
- A small hairline-bordered side card to the right listing
  "α, β, p, q ~ priors" in upright sans with italic variables.
- A discreet serif drop-cap "O" set at the start of the caption.

PANEL 2 — "Roll the perturbation type":
- Numeric marker "02" top-left with foil-gold underline.
- A flat editorial four-slice pie chart with mathematically clean arcs,
  uniform-width vector outline, and a slim navy pointer — NO wobble, NO
  hand-drawn outline. Slices labeled and color-coded in the editorial
  palette:
  • "Exact GBP — 20%" (sage)
  • "Fold — 30%" (terracotta)
  • "FCP — 20%" (ochre)
  • "Combined — 30%" (muted lilac)
- Italic typeset caption: "Categorical type + HalfCauchy budget B".
- A small refined die glyph rendered as a precise vector icon (linework
  only) next to the chart.

PANEL 3 — "Perturb in log₁₀(ψ) space" (split into TWO sub-panels stacked
vertically, divided by a hairline rule):
- Numeric marker "03" top-left with foil-gold underline. Hairline-
  bordered "fig. 1" tag in the lower-right of the panel.
  TOP HALF — "Fold (Catastrophe injection)":
    • Three precision-rendered Gaussian-windowed cubic bumps drawn over
      a flat baseline — mathematically smooth curves, uniform 1.5px
      stroke, NO wobble. Thin straight lead lines with small filled
      dots at the local "fold" anchors.
    • Equation card (hairline border): "g(u) = α u³ + β u · e^(−u²/2)"
    • Small upright-sans note: "K ∈ {0,1,2,3} anchors"
  BOTTOM HALF — "FCP (Filtered Compound Poisson)":
    • A precision-rendered staircase step function with 3–4 jumps
      (perfectly orthogonal step edges), and a smoothed Gaussian
      overlay drawn as a clean dashed curve (uniform dash). NO
      sketch quality.
    • Equation card (hairline border): "Σ Jᵢ · 1[log M > μᵢ]  ∗  Gσ"
    • Small upright-sans note: "N_jumps ≥ 2,  |J| ≥ 1 dex"
- The whole panel labeled at the top in small-caps tracking:
  "Step 3 — Inject perturbation δ".

PANEL 4 — "Compose, spline, validate":
- Numeric marker "04" top-left with foil-gold underline.
- Three mini sub-graphics arranged in a row inside the panel:
  (a) A small typeset "+" and the original GBP curve plus a smooth δ
      curve yielding a perturbed shape; label "log₁₀ ψ  +=  δ". All
      curves precision-rendered.
  (b) A clean cubic-spline curve drawn through scattered control points
      (small filled dots), labeled "Akima cubic spline".
  (c) STATUS-BADGE PATTERN — replace any rubber-stamp metaphor with two
      small hairline-bordered editorial status badges sitting side-by-
      side, separated by a mid-dot bullet, in small-caps tracking:
        • Sage filled dot (#6B8E5E) + "weighted_log_std  OK"
        • Terracotta filled dot (#B85A47) + "rapid cutoff  REJECT"
      NOT angled. NOT a stamp. NOT cartoon. Refined UI badge feel.
- PULL-QUOTE PATTERN — under the panel, a single italic serif pull-quote
  precisely typeset between two hair-thin horizontal rules:
      "≈ 2% pass rate — keep retrying."
  NOT handwritten, NOT a sticky note, NOT angled.

PANEL 5 — "Hawking spectrum & parquet":
- Numeric marker "05" top-left with foil-gold underline.
- Center: a stylized event-horizon disk rendered as a refined editorial
  vignette with crisp uniform-width contour. CONNECTION-LINE PATTERN —
  radiation rendered as a subtle navy radial gradient halo around the
  disk PLUS a small set of fine straight lead lines (1px feel)
  terminating in tiny filled dots at the rim of the integrator box.
  NEVER chunky arrows, NEVER comic-style motion lines, NEVER sketched
  rays.
- A hairline-bordered integrator box reads "BlackHawk + PYTHIA /
  HDMSpectra" in small-caps tracking.
- Output of the integrator: a precision-rendered downward-sloping
  power-law curve on log-log axes labeled "E [GeV]" and "dN/dE", with
  primary + secondary components shown as two stacked tonal bands
  (navy + ochre), edges crisp.
- Below the curve, a small "parquet file" glyph (refined cylinder /
  database, uniform vector linework) with the schema label set in
  upright sans + italic fields:
      "[ M, ψ, E, primary, secondary ]   shape (N, 500)"
- Italic typeset footer note inside the panel: "100,000 samples →
  unified training set."

BOTTOM RIBBON (full width, sits above a hairline rule at the very bottom):
- Four small labeled chips spaced evenly, separated by mid-dot bullets,
  set in small-caps tracking, warm charcoal on cream:
    "GRID = 500"  ·  "log M ∈ [13, 22]"  ·  "log E ∈ [−4, 6]"  ·  "seed = 42"
- A tiny italic credit on the far right: "OSPREY · v0.21 unified".

TYPOGRAPHY:
- Headlines: refined transitional serif (Tiempos Headline / Mercury /
  GT Sectra feel) — generous letterspacing, slight optical refinement.
- Subheads & captions: small-caps tracking on labels, italic for
  pull-quotes (always typeset, never handwritten), regular weight for
  body annotations.
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

COMPOSITION:
- Strict 18:9 aspect ratio, generous editorial margins.
- Hairline rules (0.5pt feel) run full-width above the title and below
  the bottom ribbon, anchoring the layout like a print article.
- Panels are roughly equal width with the middle (Panel 3) slightly
  wider to fit the two stacked sub-panels. Vertical hairline dividers
  between panels with a small navy chevron (›) at each break — no
  arrows, no chunky strokes.
- Avoid clutter: lots of breathing room, no overlapping text, no
  watermark, no fake logos, no stock photography.

MOOD: a feature-article infographic from Quanta Magazine or The New York
Times — refined, warm, and printed-feeling, illustrating a research
methodology for an informed but non-specialist reader. Smart and
considered, never childish, never corporate-flat, never sketched.

IMPORTANT: every character on the canvas must be readable English. Render
math with plain ASCII / Greek letters only (α β σ μ Σ are fine); no
decorative non-Latin script anywhere. No watermarks, no fake logos, no
brand names. The whole spread is precision vector / engraved / printed —
absolutely no sketched, hand-drawn, or whiteboard cues anywhere.
```

## v1 → v2 hardening notes

The v1 generation (without explicit hard negatives) still leaked friendly
cues:

| Leak                                  | v2 fix                                                    |
|---------------------------------------|-----------------------------------------------------------|
| Wobbly Gaussian / staircase / pie arc | "precision-rendered, mathematically smooth, uniform 1.5px stroke, NO wobble" per-curve |
| Cartoon ✓ / ✗ rubber stamps in P4     | Replaced with **STATUS-BADGE PATTERN** (hairline UI badge + colored dot) |
| Hand-lettered "≈ 2% pass rate" note   | Replaced with **PULL-QUOTE PATTERN** (italic serif typeset between hair-thin rules) |
| Chunky comic-style radiation arrows   | Replaced with **CONNECTION-LINE PATTERN** (radial gradient halo + 1px lead lines) |
| Generally sketchy stroke feel         | "Hard negatives" bullet listing what must NOT appear, plus closing line "absolutely no sketched cues anywhere" |

These three named patterns now live in `editorial-magazine-style.md` and
should be referenced by name whenever a new editorial-style prompt has a
panel that would otherwise want a stamp / sticky-note / motion-arrow.

## What was reused vs. swapped (vs. v0.21 friendly variant)

| Reuse verbatim from friendly v0.21          | Swap for editorial            |
|---------------------------------------------|-------------------------------|
| All per-panel scientific content            | OVERALL LOOK block (palette, surface, dividers) |
| Equations and parameter cards               | TITLE BAR (eyebrow + serif headline + small-caps subtitle) |
| Bottom ribbon chips (GRID / log M / log E / seed) | Numeric markers ("01"…"05" with foil-gold underline) |
| Sub-panel split inside Panel 3              | Status / pull-quote / connection-line patterns |
| English-only guard rail                     | Typography (serif headline + small-caps + italic typeset captions) |
