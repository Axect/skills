# Gotchas (the bugs that bit us, and the rules that kill them)

Every one of these cost real debugging time. Internalize them BEFORE authoring, and re-check them in the verify loop.

## 1. Math (`$...$`) only renders inside markdown, never inside raw block HTML
A line that **starts** with a block-level tag (`<p ...>`, `<div ...>`) is parsed as one HTML block; markdown-it passes its content through verbatim, so `$\xi$` shows up literally as `$\xi$`.

- BAD: `<p class="lead">Near $T_c$ the length $\xi$ diverges.</p>` → literal `$T_c$`, `$\xi$`.
- GOOD (mdc paragraph): `Near $T_c$ the length $\xi$ diverges. {.lead}`
- Inline tags *inside* a markdown paragraph are fine: `Near $T_c$, <strong>diverges</strong> $\xi$.` renders.
- A grid `<div>` renders math **only if its inner content is separated by blank lines**:
  ```html
  <div class="grid grid-cols-3 gap-4">
  <div class="step-card">

  <strong>1 · Title</strong>

  At $T_c$, $\chi\to\infty$.

  </div>
  ...
  </div>
  ```
  The blank lines after `<div>` and before `</div>` make markdown reprocess the inside (math + classes work). No blank lines → literal math.

Verify: `pdftotext deck.pdf - | grep -coE '\$[^$]{1,15}\$'` must be `0`.

## 2. A visible-class attribute after trailing math attaches to the wrong token
markdown-it-attrs binds `{.class}` written **inline at the end of a paragraph** to the last inline token, not the block — when that paragraph contains math, the last token is the text run *after* the final `$...$`. Symptoms seen: "only the last `)` is red", "the last sentence is tiny mono while the rest is body".

- Rule: for any **visible** class (`.lead`, `.fig-cap`, `.bad`, `.tiny`, `.callout`, `.muted`, `.text-*`), put the attribute on its **own line** right after the paragraph (no blank line between):
  ```
  ...so $\chi\to\infty \Rightarrow \xi\to\infty$.
  {.lead}
  ```
- Margin-only classes (`.mt-2` etc.) are invisible if mis-attached, so they may stay inline.
- To color only part of a sentence, wrap it explicitly: `<span class="bad">recovery 0/5</span> (truth 14).` — do not rely on `{.bad}` on a math-ending paragraph.

## 3. `$...$` immediately followed by a digit fails to close
KaTeX/markdown-math uses a "looks like a price" heuristic: a closing `$` followed by a digit is treated as not-a-close. `within $\sim$5%` → the whole thing stays literal.

- Rule: pull the number inside the math: `within $\sim 5\%$`. Same for `$x$2`, `$=$3`, etc.

## 4. No em/en-dashes — and `\text{--}` is an en-dash
House rule: never `—` or `–`. Use `:`/`,`/parentheses/restructure. In LaTeX, `\text{--}` renders as an en-dash → write `\text{ to }` (e.g. `$\approx 48\text{ to }64$`). Verify: `pdftotext deck.pdf - | grep -cE '—|–'` must be `0`.

## 5. Choose the layout by figure aspect ratio (never blanket 50/50)
Measure each figure: `identify -format "%[fx:w/h] %f\n" public/*.png`.
- **wide** (w/h ≳ 1.7 — 3-panel rows, P(E) overlays, schematics): full-width `.fig-full`, one line of text below. A wide figure squeezed into a half-column is tiny *and* leaves the other half empty (the classic "엉성" slide).
- **square-ish** (≈1.1–1.5 — single scatter/curve): `two-cols-header` with `.fig-card` left + text right.
- All-text "implications/conclusions" slides look flimsy as a bullet list → convert to a `grid grid-cols-2/3` of `.step-card`s (a logical-chain of cards fills the space and scans better).

## 6. Footer overlap is structural, not cosmetic
The footer sits at the bottom ~30px. Content must end above it. `style.css` caps figure heights (`.fig-card` 300, `.fig-full` 290, `.two-col-img` 300px) and reserves bottom padding, but a **full-width figure + 3+ lines of text still overflows**. Fixes, in order:
1. trim the text to ≤2 lines;
2. shrink that one image inline: `<img src="/x.png" style="max-height:250px" />`;
3. as a last resort lower the global `.fig-full` cap.
Always render the page and confirm the last text line clears the footer page number.

## 7. Slidev nav / dialog quirks (already patched in style.css — keep them)
- The bundled fuse.js returns ALL slides for an empty query, so the "Goto" dialog (`#slidev-goto-dialog`) renders its full slide list while *closed* and floats over the deck. Fix shipped: `#slidev-goto-dialog:has(#slidev-goto-input:disabled){display:none}`.
- The decorative top accent bar and the footer must have `pointer-events:none`, or they intercept the bottom-left nav-bar's hover/click and it won't auto-hide.

## 8. Figures are independent copies; regenerate THEN re-export
`public/*.png` are not symlinks. After editing a `g_*.py`, re-run it (writes to `public/`) and re-export the PDF; the dev server picks new PNGs up on reload. A stale copy silently shows the old figure.

## 9. Verify, never trust (your own edits and subagents)
Subagent reports describe intent, not reality. After any figure or slide change: (a) confirm the PNG exists/non-zero with a fresh mtime, (b) render the slide to PNG and look at it, (c) grep the PDF for em-dash and literal-`$`. A text claim about a figure (e.g. "curve X stays low") must match what the figure actually plots — check the data.

## 10. Data integrity
Pull every number from the user's files; never invent. Don't mix model/build versions in one figure (a stale "recovered" point hid in a months-old table and contradicted the rest of the deck until it was overridden with the latest value). When citing, verify published-vs-preprint and the correct first author via CrossRef/WebSearch — a paper "with only an arXiv number" is often already in a journal.
