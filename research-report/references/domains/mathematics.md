# Mathematics Domain Notes

## Tone & framing
- Theorem–proof structure where applicable: state theorem, give the proof or proof sketch, then discuss consequences.
- State all assumptions up front. Do not bury preconditions inside the proof.
- Distinguish "we prove" from "we conjecture" from "we observe numerically".

## Mandatory components
- Definitions before use. Every nonstandard symbol gets a definition somewhere visible.
- Existence and uniqueness, when relevant, treated separately.
- Counterexamples for any sharpness claim.

## Visualization checklist
- Phase portraits, level sets, contour plots — labelled with the function being plotted.
- Bifurcation / stability diagrams: mark transition values explicitly.
- Convergence plots use log-log axes; annotate the empirical rate alongside the theoretical rate.
- For numerical experiments accompanying a proof, show error vs. resolution and compare to the theoretical convergence rate.

## Math conventions
- LaTeX only. Common needs:
  - Number sets: `$\mathbb{R}$`, `$\mathbb{Z}$`, `$\mathbb{N}$`, `$\mathbb{C}$`, `$\mathbb{Q}$`.
  - Operators: `$\mathrm{rank}$`, `$\mathrm{det}$`, `$\mathrm{tr}$`, `$\mathrm{ker}$`, `$\mathrm{im}$`, `$\mathrm{spec}$`.
  - Quantifiers: `$\forall$`, `$\exists$`. Use `$\mathrm{s.t.}$` or "such that" — not unicode shorthand.
  - Norms: `$\|x\|$`, `$\|x\|_p$`, `$|A|$`. Use `\|` for double-bar norms, not `||`.
- Equation environments: prefer numbered `$$ ... $$` blocks for any equation referenced later. Number once, reference by `\eqref` only when the report is rendered with full LaTeX.
- For definitions/theorems/lemmas, use blockquotes or bold headers consistently, e.g.:
  > **Theorem 3.1 (Main).** Let $f \colon \mathbb{R}^n \to \mathbb{R}$ be ... Then ...
