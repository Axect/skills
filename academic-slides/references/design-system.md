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
  serif: 'IBM Plex Sans'       # (serif slot hack so headings load IBM Plex Sans)
  mono: 'IBM Plex Mono'        # kicker / footer / captions
  weights: '400,500,600,700'
layout: cover
class: is-cover
transition: slide-left
mdc: true                      # REQUIRED: enables the {.class} attribute syntax
---
```

## Color tokens (in style.css `:root`)
`--ink #101b33` (headings), `--ink-soft #33415c` (body), `--muted #7c879b`, `--accent #2f5cc7` (blue), `--accent-deep #1c3c84`, `--accent-soft #eaf0fb` (card bg), `--green #0c7a42`, `--red #c92518`, `--amber #99650a`, `--line #e7ebf2`. The ink and semantic colors are deliberately dark/saturated so they stay legible at projector contrast; do not lighten them.

Semantic spans: `<span class="ok">…</span>` (green), `<span class="bad">…</span>` (red), `<span class="warn">…</span>` (amber), all weight 700. Inline emphasis: `<em>` renders accent-blue (not italic, weight 700); `<strong>` renders ink, weight 700.

## Slide types

**Cover** (`layout: cover`, `class: is-cover`): deep-blue radial gradient. Kicker, big h1, a `.lead` subtitle, an author block:
```html
<div class="pt-8 author">
<strong>First Last</strong><br>
<span class="affil">Institution A · Institution B</span>
</div>
```
For collaborators add a second `.author` block with smaller font and `Collaborated with …`.

**Section divider** (`layout: section`, `class: is-section`): same deep gradient. Kicker = `Part N` (keep it plain — no "Act 1/2/3", that reads as childish), an h1, one short sentence.

**Content, full-width figure** (`class: text-left`): kicker, h1, then
```html
<div class="fig-full mt-1">
<img src="/name.png" />
</div>
One or two lines of text describing it. {.mt-2}
```
Use for **wide** figures (aspect ≳ 1.7).

**Content, figure + text** (`layout: two-cols-header`, `layoutClass: gap-8`): kicker + h1 span the top; then `::left::` `.fig-card` and `::right::` text. Use for **square-ish** figures.

**Two images side by side** (`class: text-left` + `.two-col-img`): a 2-col grid of images, text below. When the two images have **different** aspect ratios, the fixed `1fr 1fr` grid distorts them; instead use `<div class="flex justify-center items-end gap-8">` with a per-image `style="max-height:..."` on each so they align on a common baseline (the deck's prior-work slide does this).

## Reusable classes
- `.kicker` — mono uppercase eyebrow above the h1 (`<div class="kicker">…</div>`).
- `.lead` — larger intro/punch-line paragraph. Apply via mdc `{.lead}` (own line if the paragraph ends in math).
- `.fig-card` (centered, bordered, shadow, max-height 300px) / `.fig-wide` / `.fig-full` (full width, max-height 290px) / `.two-col-img` (2-col grid, 300px).
- `.fig-cap` — small mono caption. (For a slide's main explanatory line, use a normal paragraph, not `.fig-cap` — fig-cap is tiny mono.)
- `.tiny` — small body text (0.74rem). Pair with `.muted` for a sub-figure note / sampling caveat line under a panel (`{.tiny.muted.mt-2}`).
- `.cite` — inline reference in muted small text. Use inside a bullet for a related-work entry: `<strong>Theme:</strong> <span class="cite">A. Author et al., "Title," Journal Vol, pages (Year).</span>`.
- `.figcite` — extra-tiny (0.6rem) muted figure-source line directly under a figure (e.g. `<div class="figcite">Source: dataset / method, Author et al., Year.</div>`). Smaller than `.fig-cap`; use it to attribute a figure or data source without stealing visual weight.
- `.callout` — left-accent highlighted box (for one key statement).
- `.step-card` — card with a top accent rule + bold accent header; put 3–4 in a `grid grid-cols-2`/`grid-cols-3` to turn a bullet list into a scannable card chain (great for "implications"/"why universal" slides that otherwise look sparse). Header = `<strong>1 · Title</strong>`, then a blank line, then one sentence.
- Minimal tables: standard markdown tables get a thick top rule, thin row separators, tabular-nums, colored cells via `<span class="ok/bad/warn">`. Keep one metric per column; do not mix a scale value and a fraction in one cell. Headers are uppercased via CSS, but `style.css` exempts rendered KaTeX (`th .katex`) so a math header like `$\xi_k$` is not mangled into `\Xi`; you can put math in a `th` safely.

## UnoCSS utilities you can append in `{...}` or on divs
`mt-1..12`, `pt-*`, `text-sm`/`text-lg`/`text-xl`, `muted`, `tiny`, `grid grid-cols-2/3 gap-4`, `leading-loose`. The cover/section gradient and the top accent bar + footer come from `global-top.vue` / `global-bottom.vue` (auto-loaded).

## Canvas budget
Slidev canvas is 980×552 CSS px (PDF page 735×414 pt). After top padding + heading (~120px) and the footer zone (~30px at the bottom), content has ~400px of height. A full-width figure at 290px leaves room for ~1–2 lines of text; 3+ lines overflow → shrink the image inline. This is why figure max-heights are capped and why text-heavy figure slides need a smaller image.
