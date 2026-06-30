# Design system

The look is defined entirely by `assets/style.css` (copied into the deck verbatim) plus the headmatter fonts. Do not restyle ad hoc; use the classes below.

## Headmatter (top of slides.md)
```yaml
---
theme: default
title: <Deck Title>            # shown in the footer via $slidev.configs.title
titleTemplate: '%s'
fonts:
  sans: Inter                  # body
  serif: 'Geist'               # (serif slot hack so headings load Geist)
  mono: 'JetBrains Mono'       # kicker / footer / captions
  weights: '400,500,600,700'
layout: cover
class: is-cover
transition: slide-left
mdc: true                      # REQUIRED: enables the {.class} attribute syntax
---
```
A fourth face, **Source Serif 4**, is used only for the large titles on the dark cover + section slides (academic serif contrast against the geometric Geist of the light content headings). The Slidev `fonts` slots (sans/serif/mono) are all taken, so it loads via an `@import` at the very top of `style.css` and is applied through `.is-cover h1, .is-section h1`. Do not move that `@import` below other rules (CSS requires `@import` first) and do not delete it, or the dark titles silently fall back to a default serif.

## Color tokens (in style.css `:root`)
`--ink #101b33` (headings), `--ink-soft #33415c` (body), `--muted #7c879b`, `--accent #2d5ad1` (blue), `--accent-deep #173679`, `--accent-soft #eef3fd` (card bg), `--pos #2d5ad1` (positive, blue), `--neg #b5821a` (negative, amber), `--note #5f6b80` (caution, slate), `--line #e7ebf2`. The ink and emphasis colors are deliberately dark/saturated so they stay legible at projector contrast; do not lighten them.

Semantic spans (blue/amber/slate, deliberately not green/red): `<span class="ok">…</span>` (positive, accent blue), `<span class="bad">…</span>` (negative, amber), `<span class="warn">…</span>` (caution, slate), all weight 700. Because `.ok` shares the accent blue with `<em>`, do not put an `.ok` span and an `<em>` in the same clause where the distinction matters. Inline emphasis: `<em>` renders accent-blue (not italic, weight 700); `<strong>` renders ink, weight 700.

## Slide types

**Cover** (`layout: cover`, `class: is-cover`): deep-blue radial gradient. Kicker, big h1, a `.lead` subtitle, an author block:
```html
<div class="pt-8 author">
<strong>First Last</strong><br>
<span class="affil">Institution A · Institution B</span>
</div>
```
For collaborators add a second `.author` block with smaller font and `Collaborated with …`. Institution logos go in a `.cover-logos` row of white `.logo-chip` pills below the author block (the source marks are dark, so the white chip keeps them legible on the deep-blue cover):
```html
<div class="cover-logos">
<span class="logo-chip"><img src="/logo-fudan.svg" alt="Fudan University" /></span>
<span class="logo-chip"><img src="/logo-riken.png" alt="RIKEN" /></span>
</div>
```
The same two logos also appear as a small persistent corner mark (top-right, full brand color, no pill) on every content slide via `global-top.vue` (`.deck-logos`); it is auto-hidden on cover/section slides (which carry the large `.cover-logos`). If a long slide title collides with that corner mark, remove the `.deck-logos` block from `global-top.vue`. Swap the institution by replacing the two files in `public/` (`logo-fudan.svg`, `logo-riken.png`) and updating the `alt`/filenames; both are copied from `assets/logos/` at scaffold time.

**Section divider** (`layout: section`, `class: is-section`): same deep gradient. Kicker = `Part N` (keep it plain — no "Act 1/2/3", that reads as childish), an h1, one short sentence.

**Content, full-width figure** (`class: text-left`): kicker, h1, then
```html
<div class="fig-full mt-1">
<img src="/name.png" />
</div>
One or two lines of text describing it. {.mt-2}
```
Use for **wide** figures (aspect ≳ 1.7).

**Content, figure + text** (`layout: two-cols-header`, `layoutClass: gap-8`): kicker + h1 span the top; then `::left::` `.fig-card` and `::right::` text. Use for **square-ish** figures. `style.css` already fixes Slidev's default `two-cols-header`, which hard-codes `grid-template-rows: 1fr 1fr` and opens a large empty gap above the columns; the override collapses the header row to its content height so the columns sit right under it. **Column ratio:** the default is 50/50; opt into another split by adding a `cols-*` class to `layoutClass`, e.g. `layoutClass: gap-8 cols-5545` (left 55% / right 45%). Available: `cols-5545`, `cols-4555`, `cols-6040`, `cols-4060` (left number = left column). The same classes work on a `.two-col-img` grid.

**Two images side by side** (`class: text-left` + `.two-col-img`): a 2-col grid of images, text below. Add a `cols-*` class for an unequal split. When the two images have **different** aspect ratios, the fixed grid distorts them; instead use `<div class="flex justify-center items-end gap-8">` with a per-image `style="max-height:..."` on each so they align on a common baseline (the deck's prior-work slide does this).

## Reusable classes
- `.kicker` — mono uppercase eyebrow above the h1 (`<div class="kicker">…</div>`).
- `.lead` — larger intro/punch-line paragraph. Apply via mdc `{.lead}` (own line if the paragraph ends in math).
- `.fig-card` (centered, bordered, shadow, max-height 300px) / `.fig-wide` / `.fig-full` (full width, max-height 290px) / `.two-col-img` (2-col grid, 300px).
- `.fig-cap` — small mono caption, always center-aligned. (For a slide's main explanatory line, use a normal paragraph, not `.fig-cap` — fig-cap is tiny mono.)
- `.tiny` — small body text (0.74rem). Pair with `.muted` for a sub-figure note / sampling caveat line under a panel (`{.tiny.muted.mt-2}`).
- `.cite` — inline reference in muted small text. Use inside a bullet for a related-work entry: `<strong>Theme:</strong> <span class="cite">A. Author et al., "Title," Journal Vol, pages (Year).</span>`.
- `.figcite` — extra-tiny (0.6rem) muted, center-aligned figure-source line directly under a figure (e.g. `<div class="figcite">Source: dataset / method, Author et al., Year.</div>`). Smaller than `.fig-cap`; use it to attribute a figure or data source without stealing visual weight.
- `.callout` — left-accent highlighted box (for one key statement).
- `.step-card` — card with a top accent rule + bold accent header; put 3–4 in a `grid grid-cols-2`/`grid-cols-3` to turn a bullet list into a scannable card chain (great for "implications"/"why universal" slides that otherwise look sparse). Header = `<strong>1 · Title</strong>`, then a blank line, then one sentence.

## High-impact slide patterns (alternatives to step-card)
Pick by intent; each has a worked example in `slides.template.md`. All are raw-HTML blocks, so keep markdown content (lists, `<strong>`) separated by blank lines and follow the math-in-block-HTML rule (use mdc paragraphs / blank-line separation for `$...$`).
- **Big-number stats** (`.stat-grid` > N × `<div>` each with `.stat-num` / `.stat-label` / optional `.stat-sub`): a row of 2–4 large metrics. Far more impact than a bullet list of numbers. Put a unit inside the number with `<span class="unit">×</span>`. Use for a results headline.
- **Hero statement** (`.hero-statement` with `.big` + optional `.sub`): one large centered claim that fills the slide, no h1 — the single thing to remember. `<em>` inside `.big` renders accent-blue. Pair with a small `.kicker` at the top.
- **Comparison, highlighted winner** (`.cmp-grid` > `.cmp-card.cmp-prior` + `.cmp-card.cmp-this`): two panels where the prior approach is a flat faded card and *this work* is a deep-blue filled card with an elevation shadow, so the winner pops (pricing-table style). Each card = a `.cmp-tag` mono eyebrow, a `.cmp-title`, and a `<ul>`. Body text on the dark card is kept bright for readability. Use as the high-impact before-vs-after.
- **Comparison, feature table** (`.cmp-table` > `.ct-row` rows, first row `.ct-head`): a criteria-by-method grid with check/cross marks (`.ct-ok` accent ✓, `.ct-x` amber ✗) or short value words (`.ct-mid`); the *this work* column is tinted so the eye lands on it. Use when there are 3+ criteria to compare.
- **Pull quote** (`.pull-quote` with `.q` + `.by`): a large editorial quotation in Source Serif 4 with an accent rule. Attribution in `.by` (no em-dash). Use to frame a guiding principle.
- Minimal tables: standard markdown tables get a thick top rule, thin row separators, tabular-nums, colored cells via `<span class="ok/bad/warn">`. Keep one metric per column; do not mix a scale value and a fraction in one cell. Headers are uppercased via CSS, but `style.css` exempts rendered KaTeX (`th .katex`) so a math header like `$\xi_k$` is not mangled into `\Xi`; you can put math in a `th` safely.

## UnoCSS utilities you can append in `{...}` or on divs
`mt-1..12`, `pt-*`, `text-sm`/`text-lg`/`text-xl`, `muted`, `tiny`, `grid grid-cols-2/3 gap-4`, `leading-loose`. The cover/section gradient and the top accent bar + footer come from `global-top.vue` / `global-bottom.vue` (auto-loaded).

## Canvas budget
Slidev canvas is 980×552 CSS px (PDF page 735×414 pt). After top padding + heading (~120px) and the footer zone (~30px at the bottom), content has ~400px of height. A full-width figure at 290px leaves room for ~1–2 lines of text; 3+ lines overflow → shrink the image inline. This is why figure max-heights are capped and why text-heavy figure slides need a smaller image.
