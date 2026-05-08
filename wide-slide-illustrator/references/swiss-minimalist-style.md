---
name: Swiss Minimalist Slide Style (reframed)
description: Reusable visual-style block for image-generation prompts that produce Swiss-design / Bauhaus-flavored infographic slides — Müller-Brockmann typography + strict grid + primary palette discipline — applied to METHODOLOGY content (equations, data plots, parameter cards, status indicators preserved). English-only text on a wide 18:9 canvas. Sister style to friendly-whiteboard-style.md, editorial-magazine-style.md, engineering-blueprint-style.md, dark-tech-neon-style.md, and scientific-poster-style.md.
type: reference
---

# Swiss Minimalist Slide — Canonical Style Block (reframed)

Drop the blocks below verbatim into any image-generation prompt. Same 5-panel
left-to-right composition as the other variants. The typographic and grid
discipline of Swiss design (single geometric sans, primary palette, strict
12-column grid, generous whitespace, hairline-rule dividers) is fully
preserved — but methodology content (equations, data plots, parameter cards,
status indicators) is *kept inside the panels* and rendered in Swiss manner.
NOT the orthodox Müller-Brockmann title-poster behavior that strips a panel
to a single primitive; this variant is for explaining a method while honoring
Swiss aesthetic discipline.

If you want the orthodox title-poster behavior (one shape per panel, all
methodology content stripped, HUGE 80pt hero numerals), use the explicit
"Orthodox Müller-Brockmann title poster" tone dial below — it is OFF by
default in this reframed variant.

---

## OVERALL LOOK block

```
OVERALL LOOK:
- Pure paper-white background (#F8F4EC) with no texture, no gradient, no
  grid pattern. The page itself is the canvas — let breathing room do
  much of the work (target ~30–40% negative space; less aggressive than
  orthodox Swiss to leave room for content).
- Strict Swiss-design / Bauhaus discipline: precision-rendered vector
  linework, uniform stroke widths (0.75pt for axes and hairline rules,
  1.5pt for data curves, 2–3pt for primary marks), perfectly orthogonal
  alignment to an invisible 12-column grid. Every element snaps to the
  grid — nothing rotated, nothing off-axis, nothing freely placed. All
  curves are mathematically smooth — NO organic wobble, NO sketch
  strokes anywhere.
- Hard negatives — DO NOT include any of: serif typography (zero
  exceptions, including math italics — Greek vars are set in the body
  sans face's italic, never swapped to Computer Modern serif), drop
  shadows, gradients of any kind, paper grain or texture, illustrations
  or pictorial drawings, watercolor or painterly fills, sticker doodles,
  sticky notes, hand-lettered notes, comic-style motion lines, sketched
  / chunky arrows, dashed wobble strokes, friendly palette colors,
  magazine flourishes (drop caps, foil-gold rules, italic-serif
  pull-quotes), neon glow halos, blueprint cyan linework on navy,
  journal-figure inward tick marks, infographic stage-name banners
  ("INIT" / "FLOW" / "NOISE" all-caps strips). The whole spread should
  read as a Swiss-typographic explanatory poster, not a slide with
  decorations.
- Restrained primary palette — at most FOUR colors total across the
  entire canvas: red (#E63946), yellow (#F4C95D), blue (#1D3557),
  black (#0B0B0B), on paper (#F8F4EC). Most panels use only black plus
  ONE accent color. Never use all four in a single panel.
- Five panels flow LEFT to RIGHT, separated by single 1pt black hairline
  rules running floor-to-ceiling. NO chevrons, NO arrows, NO icons in
  the dividers — just a hairline. The implied flow comes from reading
  order alone.
- Methodology content is welcome and load-bearing: data plots,
  equations, parameter cards, and status indicators all appear, but
  every single element is rendered in geometric sans, on the grid, in
  the primary palette. NOTHING is reduced to "just a primitive shape"
  unless the user explicitly asks for the orthodox title-poster mode.
```

> Adjust the panel count line ("Five panels…") to match the actual N.

---

## TYPOGRAPHY block

```
TYPOGRAPHY:
- Single typeface throughout — geometric sans (Akzidenz Grotesk /
  Helvetica Neue / Inter / Söhne feel). No serifs anywhere, ever — not
  even in math italics. Greek glyphs (α β σ μ Σ δ) rendered in the
  body sans face's italic.
- Headlines: ultra-bold sans, large (~48–64pt feel), left-aligned, tight
  tracking.
- Numeric markers: PROMINENT but not dominant ("01"…"05" rendered at
  ~32–48pt feel), bold sans, black or one accent color per panel.
  Anchors the top-left of each panel — NOT the panel's main content.
- Stage / sub-panel labels: regular sans, small-caps with wide tracking
  for short sentence-case identifiers (optional).
- Body labels and captions: regular weight sans, sentence-case, tight
  tracking.
- Equations rendered in geometric-sans math — italic-style Greek
  variables (α β σ μ Σ δ) in the body sans face's italic, upright
  operators, proper subscripts. NO LaTeX serif math, ever.
- Axis labels in regular sans, sentence-case (e.g., "log10 M (M_sun)").
- All annotations short — typically one line, never more than 8 words.
- IMPORTANT: every character on the canvas must be readable English.
  Render math with plain ASCII / Greek letters only (α β σ μ Σ are fine);
  no decorative non-Latin script anywhere.
```

---

## COMPOSITION block

```
COMPOSITION:
- Strict 18:9 aspect ratio, generous margins (target ~6–8% on every
  side; less aggressive than orthodox Swiss to make room for content).
- Invisible 12-column grid drives ALL alignment. Every element — title,
  panel number, plot axes, equation block, parameter card, caption,
  ribbon chip — snaps to a column edge or column center. Never freely
  placed.
- Five panels are exactly equal width. Panels separated by 1pt black
  hairline rules floor-to-ceiling.
- Avoid clutter — target ~30–40% negative space. No watermarks, no
  fake logos, no decorative flourishes.
```

> Change "18:9" to the requested aspect (16:9, 3:2, 4:3) if user overrides.

---

## MOOD block

```
MOOD: a Swiss design school explanatory poster — Müller-Brockmann or
Vignelli applied to a research methodology. Cool, rational, grid-
disciplined, considered. The content is recognizable as a methodology
figure (equations, data, status visible) but the surface is unmistakably
Swiss. Reads like a research-poster session that happens to have been
laid out by a Swiss typographer.
```

---

## TITLE BAR pattern

```
TITLE BAR (top, full width, snapped to top of grid):
- Ultra-bold sans headline, large (~48–64pt feel), left-aligned to
  column 1, black on paper:
  "<HEADLINE>"
- One thin line below in regular sans, sentence-case, left-aligned:
  "<SUBTITLE>."
- A 1pt black hairline rule running full-width below the title block.
```

> Headline ≤ 5 words. Subtitle ≤ 12 words, ends with a period.

---

## PANEL pattern

```
PANEL N — "<short name>":
- Marker "0N" top-left in bold sans (~32–48pt feel), black or one accent
  color (PROMINENT-NUMBER PATTERN — see below). Acts as a typographic
  anchor — not the panel's main content.
- Optional small-caps stage name beside or below the marker, regular
  sans, wide tracking: "STAGE NAME".
- Centered: a precision-rendered data plot OR a clean diagrammatic
  visualization (PRIMARY-PLOT PATTERN — see below). Mathematically
  smooth curves, sans axis labels.
- A small GRID-CARD (see pattern below) snapped to the right edge of
  the panel column, listing key parameters or an equation in sans-math.
- Single short caption below the visual, regular sans, sentence-case:
  "<one short caption>."
```

### Prominent-number pattern (use INSTEAD of huge dominant numerals)

The numeric marker "0N" is rendered at ~32–48pt feel — visibly larger
than body text and clearly a Swiss-typographic anchor, but NOT a
dominant 80pt hero numeral. The number identifies the panel; the
content explains it. Place top-left, snapped to column 1 of the panel.

### Primary-plot pattern (use INSTEAD of pure geometric primitives)

Data visualizations appear as actual plots: smooth curves on
grid-aligned axes (Swiss convention — open-ended axes, NOT closed boxes
on all four sides). Tick marks pointing OUTWARD or omitted entirely
(NEVER inward like a journal figure). Axis labels in regular sans,
sentence-case. Data drawn in 1.5pt black plus ONE accent color per
panel. NO viridis ramp, NO journal-figure conventions, NO blueprint
cyan-on-navy, NO neon glow. Pure geometric primitives (●▲■◆) are
allowed only as DATA MARKERS or as filled fills inside the plot, never
as a panel's sole content.

### Grid-card pattern (use INSTEAD of magazine pull-quotes / blueprint cyan boxes / friendly sticky notes)

Parameter cards and equation blocks are simple rectangles snapped to the
grid: thin 0.75pt black border (or no border at all — just a left-
aligned text block with a 0.75pt rule above), sans content set tight,
snapped to column edges. NO sharp-cornered cyan-bordered cards, NO
foil-gold accents, NO italic-serif body, NO neon-chip glow, NO sticky-
note tilts. ALL math content set in geometric sans (Greek glyphs in the
sans face's italic).

For panels with sub-content, nest sub-bullets:

```
PANEL N — "<umbrella name>" (split into TWO sub-panels stacked vertically
inside the same panel column, divided by a 1pt black hairline rule):
  TOP HALF — "<sub name>":
    • <data plot>
    • <equation in sans-math>
    • <one short caption>
  BOTTOM HALF — "<sub name>":
    • <data plot>
    • <equation in sans-math>
    • <one short caption>
```

---

## BOTTOM RIBBON pattern

```
BOTTOM RIBBON (full width, sits above a 1pt black hairline rule, snapped
to bottom of grid):
- Four small sans-serif chips spaced evenly across the row, set in
  small-caps tracking with wide letterspacing, black on paper:
    "N 10⁴"     "σ 0.05"     "SEED 42"     "v 0.21"
- NO mid-dot bullets. NO foil-gold accents. NO chevrons. NO equals
  signs. Just the four chips on the row.
```

> Chips are constants / scales / seeds — short factual labels.

---

## English-only text guard rail (always last)

```
IMPORTANT: every character on the canvas must be readable English. Render
math with plain ASCII / Greek letters only (α β σ μ Σ are fine, set in
the body sans face's italic — never serif math italics); no decorative
non-Latin script anywhere. No watermarks, no fake logos, no brand names.
The whole spread is Swiss-minimalist explanatory poster — no sketched,
hand-drawn, magazine, blueprint, journal-figure, or neon cues anywhere.
```

---

## Tone dials

| User asks for…                          | Add / Remove                                                  |
|-----------------------------------------|---------------------------------------------------------------|
| Orthodox Müller-Brockmann title poster  | Activate strict reductive mode: each panel reduced to ONE primitive shape (●▲■◆ or single arc/line), HUGE numerals at ~80pt as the dominant element, no equations, no axis labels, no parameter cards — only primitives + monoline captions + bottom ribbon. Use ONLY when the user explicitly asks for "title poster" or "Müller-Brockmann strict" — methodology content WILL be lost. |
| More aggressive whitespace              | Increase margins to ~10–12% on each side and reduce data plot sizes; trade content density for breathing room |
| Stricter monochrome                     | Drop all primary accents; only black on paper, with stroke weight variation as the only visual hierarchy |
| Korean caption hybrid                   | Title bar stays English; explicitly allow `Korean sans caption text below each panel` and drop the English-only guard for that zone only |

---

## Lineage note

This style block is the **Swiss Minimalist (reframed)** sister of
`friendly-whiteboard-style.md`, `editorial-magazine-style.md`,
`engineering-blueprint-style.md`, `dark-tech-neon-style.md`, and
`scientific-poster-style.md`. Same 5-panel composition, same English-only
guard rail, same skill-level structure — but the surface uses Swiss
typographic and grid discipline applied to METHODOLOGY content (equations,
data plots, parameter cards, status indicators preserved).

### v1 reframe (2026-05-08)

The first OSPREY v0.21 generation under orthodox Swiss orthodoxy
(HUGE-NUMBER + PRIMARY-SHAPE only + MONOLINE-LABEL only) produced a
beautiful but uninformative spread: each panel could have illustrated
any methodology because all method-specific content (equations,
parameters, plot data, status indicators) had been stripped per Swiss
reductive philosophy. The user pushed back ("디자인은 예쁘긴 한데 아무
의미가 없는데?"), and the variant was reframed to keep Swiss discipline
(typography, grid, palette, whitespace, hairline dividers) while
ALLOWING methodology content (data plots, equations, parameter cards,
status indicators) to live inside the panels — styled in Swiss manner.

The orthodox title-poster mode is preserved as an opt-in tone dial
("Orthodox Müller-Brockmann title poster") for use cases like project
announcements, launch posters, or "X at a glance" 1-page summaries
where methodology detail is explicitly out of scope.

Use the named sub-patterns (PROMINENT-NUMBER, PRIMARY-PLOT, GRID-CARD)
whenever a panel would otherwise want a HUGE dominant numeral, a pure
geometric primitive without data, or a magazine / blueprint / friendly
card.
