---
name: Example — OSPREY v0.21 Data Pipeline Prompt
description: Worked example of a friendly-slide-illustrator prompt — the OSPREY v0.21 unified data-generation pipeline as a 5-panel 18:9 infographic. User-approved on 2026-04-27.
type: reference
---

# Worked Example — OSPREY v0.21 Data Pipeline (5 panels, 18:9)

This is the canonical reference prompt. When a new task is also a multi-stage
methodology / data-pipeline figure, reuse this structure 1-for-1 and only swap
the per-panel content. The framing, OVERALL LOOK, TYPOGRAPHY, COMPOSITION,
MOOD, and English-only guard sections are reusable verbatim.

```
A cinematic-wide 18:9 horizontal infographic illustrating a five-stage data
generation pipeline for a physics machine-learning project, designed as a
friendly conference-slide visual (NOT a stiff academic figure). All text in
the image MUST be in English only — no other languages, no garbled glyphs.

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
- Small playful touches: a tiny black-hole sticker doodle in one corner,
  a coffee-cup sticker, a sticky note labeled "≈2% pass rate" pinned
  to panel 4. Avoid overly cute / childish; aim for a research-group
  whiteboard vibe.

TITLE BAR (top, full width):
- Bold sans-serif headline:
  "OSPREY v0.21 — How we cook the training data"
- Small subtitle: "Unified pipeline: GBP base + Fold + FCP perturbations
  → Hawking spectrum"

PANEL 1 — "Sample a base GBP":
- Centered: a smooth bell-shaped curve drawn on log-log axes labeled
  "log₁₀ M  [13 → 22]" (x-axis) and "ψ(M)" (y-axis).
- Caption under the curve: "Generalized Beta Prime (GBP) base distribution".
- A small parameter card floating to the right of the curve listing
  "α, β, p, q ~ priors" in handwritten style.

PANEL 2 — "Roll the perturbation type":
- A flat illustrated four-slice pie chart / spinner with a chunky pointer.
  Slices labeled and color-coded:
  • "Exact GBP — 20%" (teal)
  • "Fold — 30%" (coral)
  • "FCP — 20%" (mustard)
  • "Combined — 30%" (purple)
- Caption: "Categorical type + HalfCauchy budget B".
- Tiny dice icon next to the spinner.

PANEL 3 — "Perturb in log₁₀(ψ) space" (split into TWO sub-panels stacked
vertically, sharing one big panel frame):
  TOP HALF — "Fold (Catastrophe injection)":
    • Three bell-shaped Gaussian-windowed cubic bumps drawn over a flat
      baseline, with arrows pointing to local "fold" anchors.
    • Equation card: "g(u) = α u³ + β u · e^(−u²/2)"
    • Tiny note: "K ∈ {0,1,2,3} anchors"
  BOTTOM HALF — "FCP (Filtered Compound Poisson)":
    • A staircase step function with 3–4 jumps, then the same staircase
      smoothed by a Gaussian (drawn as a dashed soft curve overlay).
    • Equation card: "Σ Jᵢ · 1[log M > μᵢ]  ∗  Gσ"
    • Tiny note: "N_jumps ≥ 2,  |J| ≥ 1 dex"
- The whole panel labeled at the top: "Step 3 — Inject perturbation δ".

PANEL 4 — "Compose, spline, validate":
- Three mini sub-graphics arranged in a row inside the panel:
  (a) An addition icon and the original GBP curve plus a wiggly δ curve
      yielding a perturbed shape; label "log₁₀ ψ  +=  δ".
  (b) A cubic-spline curve drawn through scattered control points,
      labeled "Akima cubic spline".
  (c) A pair of stamped icons: a green check stamp labeled
      "weighted_log_std OK" and a red × stamp labeled "rapid cutoff REJECT".
- A sticky-note doodle in the bottom-right of the panel reading
  "≈ 2% pass rate — keep retrying".

PANEL 5 — "Hawking spectrum & parquet":
- Center: a stylized black-hole disk with subtle radiation arrows pointing
  outward into an integrator box labeled "BlackHawk + PYTHIA / HDMSpectra".
- Output of the integrator: a downward-sloping power-law-like curve on
  log-log axes labeled "E [GeV]" and "dN/dE", with primary + secondary
  components shown as two stacked colored bands.
- Below the curve, a small "parquet file" icon (cylinder/database glyph)
  with the schema label:
      "[ M, ψ, E, primary, secondary ]   shape (N, 500)"
- Footer note in this panel: "100,000 samples → unified training set".

BOTTOM RIBBON (full width, thin strip below panels):
- Four small labeled chips spaced evenly:
    "GRID = 500"   "log M ∈ [13, 22]"   "log E ∈ [−4, 6]"   "seed = 42"
- A tiny credit on the far right: "OSPREY · v0.21 unified".

TYPOGRAPHY:
- Headlines: bold geometric sans (e.g. Inter / Manrope feel).
- Body labels: friendly humanist sans, slightly looser tracking.
- Equations rendered cleanly, NOT as garbled math glyphs.
- All annotations short — never more than 6 words per line.
- IMPORTANT: every character on the canvas must be readable English.
  Render math with plain ASCII / Greek letters only (α β σ μ Σ are fine);
  no decorative non-Latin script anywhere.

COMPOSITION:
- Strict 18:9 aspect ratio, generous internal margins.
- Panels are roughly equal width with the middle (Panel 3) slightly wider
  to fit the two stacked sub-panels.
- Arrows between panels are chunky, slightly tilted, with small dashed
  motion marks — playful but readable.
- Avoid clutter: lots of breathing room, no overlapping text, no
  watermark, no fake logos.

MOOD: a research postdoc's friendly explainer slide for a small group
talk — clear, warm, a bit playful, but every label is technically correct.
```

## What was reused vs. swapped

When adapting this for a new pipeline:

| Reuse verbatim                                         | Swap per task                          |
|--------------------------------------------------------|----------------------------------------|
| OVERALL LOOK block                                     | Title bar text                         |
| TYPOGRAPHY block                                       | Per-panel content (Panels 1..N)        |
| COMPOSITION block (only change aspect if needed)       | Panel count line ("Five panels …")     |
| MOOD block                                             | Bottom ribbon chips (constants)        |
| English-only guard rail at the bottom                  | Sticker doodle subject (black hole →   |
|                                                        | domain-relevant icon)                  |
