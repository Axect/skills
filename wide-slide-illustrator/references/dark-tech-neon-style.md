---
name: Dark Tech / Neon Slide Style
description: Reusable visual-style block for image-generation prompts that produce modern AI-lab / SaaS-keynote infographic slides — feel of a Linear / Anthropic / Cursor product page or a NeurIPS keynote backdrop — with English-only text on a wide 18:9 canvas. Sister style to friendly-whiteboard-style.md, editorial-magazine-style.md, engineering-blueprint-style.md, and swiss-minimalist-style.md.
type: reference
---

# Dark Tech / Neon Slide — Canonical Style Block

Drop the blocks below verbatim into any image-generation prompt. Same 5-panel
left-to-right composition as the other variants, but the surface is dark mode
with thin neon-accented vector linework and subtle outer glow. Reads like a
modern AI-lab keynote or a developer-tool product page, not a slide and not a
schematic.

---

## OVERALL LOOK block

```
OVERALL LOOK:
- Charcoal background (#0E1116) with a very subtle radial gradient that
  is slightly lighter at the geometric center (#1A1F2A in the middle,
  fading to #0E1116 at the corners). No paper texture, no grid pattern.
- Dark-mode tech-illustration style: precision-rendered vector linework,
  uniform thin strokes (1px / 1.5px), every accented stroke and chip
  carries a subtle outer glow (4–6px Gaussian blur, 25–35% opacity, in
  the same color as the stroke). All curves (Gaussians, splines,
  staircases, power laws) are mathematically smooth — NO organic wobble,
  NO sketch strokes anywhere.
- Hard negatives — DO NOT include any of: cream / paper / off-white
  backgrounds, drop shadows (use glow instead, never both), serif
  typography, sketched / wobbly strokes, comic-style motion lines,
  chunky arrows, sticker doodles, sticky notes, hand-lettered notes,
  rubber-stamp graphics, magazine flourishes (drop caps, foil-gold
  rules, pull-quotes), blueprint cyan-on-navy schematic look,
  saturated rainbow palette, skeuomorphic 3D, glassy reflections,
  emoji icons. The whole spread should look like a modern dark-mode
  product page or keynote slide.
- Restrained neon palette: charcoal ground (#0E1116), inner panel fill
  slightly lighter (#15191F), primary accent electric cyan (#00E5FF),
  secondary accent magenta (#FF3DAA), tertiary accent lime (#C8FF3D),
  optional warm amber (#FFB200) for emphasis only. Use AT MOST two
  accents per panel. Body text is off-white (#E6EAF0) with a small
  amount of mid-grey (#8892A6) for de-emphasized labels.
- Five panels flow LEFT to RIGHT, each rendered as a NEON-CHIP rounded
  rectangle (8px radius) with a 1px cyan border + outer glow + slightly
  lighter inner fill (#15191F). Panels separated by short cyan chevron
  arrows ("›") between chips, each chevron carrying its own subtle
  glow. Each panel is anchored by a small monospace marker in the
  top-left ("01" "02" "03" "04" "05") inside its own neon chip
  (rounded rectangle 4px radius) with cyan border + glow.
- Tech flourishes: a thin "::" delimiter in the title bar between the
  project name and the descriptor, monospace build-tag in the bottom
  ribbon (e.g., "0xA21F"), small monospace status dots ("●") next to
  state labels.
```

> Adjust the panel count line ("Five panels…") to match the actual N.

---

## TYPOGRAPHY block

```
TYPOGRAPHY:
- Headlines: bold geometric sans (Inter / Geist / Söhne feel), tight
  tracking, off-white on charcoal.
- Subheads & stage names: ALL-CAPS sans with wide tracking, off-white
  or accent-cyan.
- Monospace labels & equations: JetBrains Mono / Geist Mono / Berkeley
  Mono feel, used for all parameter lists, build IDs, equations,
  bottom-ribbon chips, and stage-marker chip text.
- Equations rendered in monospace with italic Greek variables (α β σ μ Σ
  are fine), upright operators, proper subscripts.
- Stage names use ALL-CAPS tracking. Body annotations are sentence-case
  sans, mid-grey (#8892A6) for de-emphasis where needed.
- All annotations short — never more than 7 words per line.
- IMPORTANT: every character on the canvas must be readable English.
  Render math with plain ASCII / Greek letters only (α β σ μ Σ are fine);
  no decorative non-Latin script anywhere.
```

---

## COMPOSITION block

```
COMPOSITION:
- Strict 18:9 aspect ratio, generous internal margins.
- Subtle radial gradient on the background (lighter near center, fading
  to charcoal at corners). No grid lines, no rules at top/bottom — the
  layout is held by the panel chips and ribbon chips themselves, not by
  hairline rules.
- Five panel chips are roughly equal width with the middle chip
  slightly wider if it carries sub-panels. Each chip has 8px corner
  radius, 1px cyan border, outer glow, and a slightly lighter inner
  fill (#15191F).
- Connectors between panels: short cyan chevron arrows ("›") with their
  own subtle outer glow. Inside-panel relationships use GLOW-PATH
  connectors (1px lines with outer glow, terminating in small chevron
  tips). NEVER chunky arrows, NEVER comic-style motion lines, NEVER
  sketched arrows.
- Avoid clutter: lots of breathing room, no overlapping text, no
  watermark, no fake logos. The dark ground does most of the
  composition work — give it space.
```

> Change "18:9" to the requested aspect (16:9, 3:2, 4:3) if user overrides.

---

## MOOD block

```
MOOD: a modern AI-lab keynote slide or developer-tool product page —
Linear, Anthropic dark mode, Cursor IDE, NeurIPS keynote backdrop. Cool,
restrained, technically confident, slightly futuristic. Reads like a
2026 product announcement, not a slide deck and not a schematic.
```

---

## TITLE BAR pattern

```
TITLE BAR (top, full width, no rule, breathing room above):
- Bold geometric sans headline, off-white on charcoal:
  "<PROJECT>  ::  <descriptor>"
  (the "::" delimiter is signature — keep it.)
- Small monospace subtitle below in mid-grey:
  "<SUBTITLE>"
- Optional small monospace version chip top-right ("v0.21") in a small
  rounded rectangle with cyan border + glow.
```

> Project name ≤ 3 words, all-caps optional. Descriptor ≤ 6 words,
> sentence-case. Subtitle ≤ 14 words. English only.

---

## PANEL pattern

```
PANEL N — "<short name>":
- Panel container is a NEON-CHIP rounded rectangle (8px radius, 1px
  cyan border, outer glow, inner fill #15191F).
- Marker chip in the top-left of the panel: small rounded rectangle
  (4px radius) with cyan border + glow, monospace "0N" inside.
- Centered: <main visual element with axes / labels / icons>, rendered
  with thin (1px–1.5px) accent-colored strokes carrying subtle outer
  glow. Mathematically smooth curves, no fills (or very dark fills
  ~10% lighter than panel fill).
- ALL-CAPS stage name below the visual in tracked sans:
  "<STAGE NAME>"
- Short sentence-case caption below the stage name, mid-grey:
  "<one short caption>".
- A small monospace side card (rounded rectangle, 4px radius, faint
  cyan border) listing "<key parameters or formula>" — monospace,
  italic Greek variables, low-contrast text on inner fill.
```

### Neon-chip pattern (use INSTEAD of plain badges / hairline-bordered cards)

ANY badge, marker, or small label container is a NEON-CHIP: rounded
rectangle (4px or 8px radius depending on size), 1px colored border in
the active accent (cyan / magenta / lime / amber), subtle outer glow,
slightly lighter inner fill than the panel ground. Monospace text inside.
NEVER a flat badge, NEVER a hairline-only card, NEVER a friendly bubble.

### Glow-path pattern (use INSTEAD of arrows / motion lines)

Connectors inside a panel (radiation, flow, "X feeds into Y") are 1px
lines with outer glow, terminating in small chevron tips (›). For
inter-panel flow, use small standalone cyan chevrons between chips.
NEVER chunky arrows, NEVER motion lines, NEVER dashed comic-style
strokes, NEVER sketched arrows.

### Monospace-label pattern (use INSTEAD of italic typeset captions)

All annotations, equations, parameter lists, build IDs, ribbon chips,
and side-card content are set in monospace (JetBrains Mono / Geist
Mono / Berkeley Mono feel) with light tracking. NEVER italic-serif
pull-quotes, NEVER hand-lettered notes, NEVER calligraphic flourishes.

For panels with sub-content, nest sub-bullets:

```
PANEL N — "<umbrella name>" (split into TWO sub-panels stacked vertically
inside the same NEON-CHIP container, divided by a 1px low-opacity cyan
rule):
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
BOTTOM RIBBON (full width, no rule, breathing room above):
- Four small NEON-CHIPs spaced evenly, each rounded rectangle 4px radius
  with cyan border + glow, monospace key=value inside, mid-grey keys +
  off-white values:
    [ N=1e4 ]    [ σ=0.05 ]    [ seed=42 ]    [ build 0xA21F ]
- A tiny monospace credit on the far right in mid-grey: "<project> ::
  v<N.NN>".
```

> Chips are constants / scales / seeds / build IDs — short factual
> labels in monospace.

---

## English-only text guard rail (always last)

```
IMPORTANT: every character on the canvas must be readable English. Render
math with plain ASCII / Greek letters only (α β σ μ Σ are fine); no
decorative non-Latin script anywhere. No watermarks, no fake logos, no
brand names. The whole spread is dark-mode neon-accented tech — no
sketched, hand-drawn, magazine, blueprint, or Swiss-minimal cues
anywhere.
```

---

## Tone dials

| User asks for…                  | Add / Remove                                                  |
|---------------------------------|---------------------------------------------------------------|
| More restrained / Anthropic-y   | Drop magenta and lime; restrict accents to cyan + amber only; reduce glow intensity by ~40% |
| More vibrant / Cursor-y         | Allow all four accents (cyan, magenta, lime, amber) and let two appear in each panel; increase glow intensity slightly |
| Print-safe dark variant         | Replace true charcoal with deep navy #0A1F3D; replace neon glow with thin clean outlines (no glow); keep monospace + accent palette |
| Korean caption hybrid           | Title bar stays English; explicitly allow `Korean sans caption text below each panel in mid-grey` and drop the English-only guard for that zone only |

---

## Lineage note

This style block is the **Dark Tech / Neon** sister of
`friendly-whiteboard-style.md`, `editorial-magazine-style.md`,
`engineering-blueprint-style.md`, and `swiss-minimalist-style.md`. Same
5-panel composition, same English-only guard rail, same skill-level
structure — but the surface is dark-mode with thin neon-accented
linework, subtle outer glow, and monospace labels throughout. Use the
named sub-patterns (NEON-CHIP, GLOW-PATH, MONOSPACE-LABEL) whenever a
panel would otherwise want a flat badge, a sketched arrow, or an italic
serif caption. The hard-negatives bullet is mandatory — without it,
serif typography, paper backgrounds, or magazine flourishes leak through
and the dark-tech identity collapses.
