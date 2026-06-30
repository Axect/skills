---
name: academic-slides
description: Build a clean, modern academic presentation deck (Slidev) for any research project. Scaffolds a deck folder from a proven design system, drives a scienceplots figure pipeline, and bakes in the battle-tested layout / mdc-math / footer rules so the recurring rendering bugs never come back. Use when the user wants slides / a talk / a presentation deck for a paper, result, or project.
---

# academic-slides

Generate a polished academic Slidev deck in a consistent house style (Geist headings on light content slides + Source Serif 4 titles on the dark cover/section slides + Inter body + JetBrains Mono accents, deep-blue gradient section dividers, blue/amber/slate emphasis, minimal tables, figure cards, step-card chains). The hard part of a deck like this is not the content, it is the dozen small Slidev/mdc/LaTeX/layout traps that silently corrupt a slide. This skill front-loads all of them.

## When to use
- "Make slides / a deck / a talk for <project / paper / result>."
- "Turn this analysis into a presentation."
- The user references this skill or "my standard slide template".

## The deliverable
A self-contained folder `outputs/<slug>/` (or a path the user gives) containing:
- `slides.md` — the deck (Slidev markdown).
- `style.css`, `global-top.vue`, `global-bottom.vue`, `package.json` — copied verbatim from `assets/` (the design system; do not rewrite them).
- `public/` — every figure PNG, referenced as `/<name>.png`, plus `logo-fudan.svg` + `logo-riken.png` (institution marks).
- `figscripts/` — `deck_style.py` (shared scienceplots style) + one `g_*.py` per figure group.
- `deck.pdf` — exported.
- `registry.toml` — provenance: each figure/number → data + script (see `references/build-verify.md`).

## Workflow

1. **Scope** (ask only what you cannot infer): the title, presenter + affiliation (+ collaborators), the narrative as a list of **Parts** (each Part = a section divider, then 2-5 content slides), and where the figures/data come from. Do NOT invent results; pull numbers from the user's files.

2. **Scaffold**. Create the deck folder and copy the assets:
   ```bash
   mkdir -p outputs/<slug>/public outputs/<slug>/figscripts
   cp <skill>/assets/{style.css,global-top.vue,global-bottom.vue,package.json} outputs/<slug>/
   cp <skill>/assets/logos/{logo-fudan.svg,logo-riken.png} outputs/<slug>/public/   # institution marks (cover chips + corner)
   cp <skill>/assets/deck_style.py outputs/<slug>/figscripts/
   cp <skill>/assets/slides.template.md outputs/<slug>/slides.md   # then rewrite
   cd outputs/<slug> && pnpm install && pnpm exec playwright install chromium
   ```
   (Use `pnpm`; if `esbuild`/`vue-demi` build scripts are blocked, run `pnpm rebuild esbuild vue-demi`. If `@slidev/theme-default` is missing at export, `pnpm add @slidev/theme-default`.)

3. **Author `slides.md`**. Follow `references/design-system.md` for the slide types and classes, and obey EVERY rule in `references/gotchas.md` (the math/footer/layout traps). Start from `assets/slides.template.md`. Pick the layout per figure **by aspect ratio**, never default to 50/50 (see gotchas §5).

4. **Figures**. One `figscripts/g_<group>.py` per group of figures; each imports `deck_style` and writes to `public/`. scienceplots `science`+`nature`, **no in-figure titles**, raw-string LaTeX, `save(fig, "<name>")`. Details in `references/figures.md`. For heavy figures (model sampling) write a separate sampler script. Delegate independent groups to parallel subagents if many.

5. **Build + verify loop** (mandatory, see `references/build-verify.md`):
   ```bash
   node node_modules/@slidev/cli/bin/slidev.mjs export slides.md --output deck.pdf --timeout 60000
   ```
   Then ALWAYS check: `pages`, em/en-dash count `= 0`, literal-`$...$` count `= 0`, and **render the changed pages to PNG and look at them** (footer overlap, overflow, text-figure match). Never trust that a slide is fine without rendering it.

## Critical rules (the ones that bit us repeatedly — full detail in references/gotchas.md)

1. **Math only renders in markdown, not in raw block HTML.** A line starting with `<p>` or `<div>` is an HTML block; `$...$` inside it stays literal. Use an mdc paragraph (`text {.class}`) or a grid `<div>` whose content is separated by **blank lines**. Inline `<strong>`/`<span>`/`<em>` inside a markdown paragraph are fine.
2. **Visible-class attrs after math go on their OWN line.** `...$x$. {.lead}` attaches `.lead` to only the trailing token (the famous "only the last paren is red" / "tail is tiny" bug). Put `{.lead}` / `{.fig-cap}` / `{.bad}` on the next line. Margin-only classes (`.mt-2`) can stay inline.
3. **`$...$` immediately followed by a digit breaks.** KaTeX's price heuristic treats the closing `$` as non-closing before a digit: `$\sim$5%` fails. Write `$\sim 5\%$`.
4. **No em/en-dashes anywhere** (user rule). Also `\text{--}` renders as an en-dash → use `\text{ to }`. Verify with a pdftotext grep.
5. **Layout by aspect ratio, not 50/50.** Wide figures (w/h ≳ 1.7: 3-panels, P(E) overlays) → full-width `.fig-full` + one line of text below. Square figures (≈1.1–1.5) → `two-cols-header` with `.fig-card` left, text right.
6. **Footer overlap is structural.** Figure heights are capped in `style.css` (`.fig-card` 300, `.fig-full` 290, `.two-col-img` 300px); a full-width fig + 3+ lines of text still overflows — shrink that image inline (`style="max-height:250px"`) and/or trim text. The footer lives at the bottom ~30px; content must clear it.
7. **Verify, don't trust** (subagents, your own edits). Re-render and eyeball; grep the PDF.
8. **Inline code (backticks) is invisible by default.** The theme's `prism.css` paints inline `` `code` `` with its dark code-block background, so every backtick token renders black-on-black. The shipped `style.css` overrides this with a light accent chip (`:not(pre) > code`); **never remove that rule**, and if you restyle, keep the `:not(pre)` guard so fenced ``` code blocks stay dark. Verify by rendering a backtick slide and looking — `pdftotext` will still extract the text, so the grep checks do not catch it.

The `style.css` already ships the `#slidev-goto-dialog` leak fix, the inline-code chip fix, and `pointer-events:none` on the decorative top-bar/footer — keep them.
