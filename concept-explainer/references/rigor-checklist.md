# Rigor Checklist

A draft is **not done** until every item below holds. Run the checks in
order; an earlier failure usually surfaces a later one.

## Symbol discipline

- [ ] Every symbol in every equation is defined no later than the line
      immediately after the equation it first appears in.
- [ ] Variables, constants, operators, and indices are visually distinct
      (`x` scalar, `\mathbf{x}` vector, `X` matrix, `\mathcal{X}` set, `i`
      index — pick a convention and hold it).
- [ ] Units appear on first use of any dimensioned quantity. Re-derived
      quantities preserve units (an `[\mathrm{energy}]` cannot become an
      `[\mathrm{action}]` mid-line).
- [ ] No symbol carries two distinct meanings in the document. If you
      need `t` for both time and a generic parameter, rename one
      (`s` or `\tau`).

## Equation discipline

- [ ] `=` vs `≈` vs `∼` vs `∝` is used consistently. Scan every relation
      and ask: "is this equal, or only approximately equal, or only
      proportional?" When unsure, fall to the weaker symbol.
- [ ] Every `≈` says the order of the omitted terms ("to leading order in
      `ε`", "neglecting `O(α²)`") — unless `approximation_tolerance` is
      `casual` in the calibration.
- [ ] No equation introduces more than one new symbol per line. If you
      need to introduce three at once, write three lines.
- [ ] Display equations are punctuated correctly: if the line ends a
      sentence, end with `.`; if it continues, end with `,`.

## Derivation discipline

- [ ] Every step in a chain of equations names the rule: "by linearity",
      "integration by parts", "chain rule", "applying assumption A1",
      "Taylor-expanding to second order".
- [ ] No "it can be shown that" without (a) a one-line sketch, (b) a
      reference, or (c) "we omit this; see §X". A bare hand-wave is
      forbidden.
- [ ] No use of "obviously", "clearly", "trivially", "evident", or
      "it is well-known that" as a load-bearing inference. Grep for them
      and rewrite.
- [ ] Branching cases ("if `x > 0` … else …") cover the full domain. If
      the boundary case is special, state what happens there.

## Assumption discipline

- [ ] An `## Assumptions` block (or equivalent) lists every regime
      condition the derivation needs: smoothness, boundary conditions,
      domain restrictions, regularity, independence.
- [ ] When an assumption is dropped in a generalization, the document
      says so explicitly ("releasing A2, the result becomes…").
- [ ] Hidden assumptions caught? Common ones:
  - swapping limits and integrals (uniform convergence?)
  - differentiation under the integral (dominated convergence?)
  - assuming a series converges (radius?)
  - assuming a matrix is invertible (non-singular?)
  - assuming probability density exists (absolute continuity?)

## Reference discipline

- [ ] Every empirical fact has a citation.
- [ ] Every named theorem used without proof has a citation or a
      reference to a standard text.
- [ ] No citation is fabricated. If `reference-search` returned nothing,
      either rewrite the claim or invoke `reference-search` again with a
      better query.
- [ ] Numerical constants beyond textbook precision (e.g. CODATA values,
      fitted constants) carry their source.

## Reader-path discipline

- [ ] No forward references. Section N never depends on a concept first
      defined in section N+k.
- [ ] The motivation section actually motivates — a reader who stops
      after §1 should know *why* the rest of the document exists.
- [ ] The first time a non-trivial result appears, the reader can already
      decode every symbol and every assumption involved.

## Figure discipline

- [ ] Every figure has a caption that *interprets* the figure, not just
      names it. "Action vs path length" is incomplete; "Action vs path
      length — the minimum identifies the classical trajectory; small
      wiggles raise the action quadratically, large wiggles raise it
      faster than linearly" is right.
- [ ] Every figure referenced from prose actually exists on disk (PNG
      file present and non-empty).
- [ ] Every figure file referenced from prose is reached by at least one
      sentence in the prose. Orphan figures get removed.
- [ ] Matplotlib figures use `scienceplots ["science", "nature"]`, **not**
      `no-latex`. Raw-string LaTeX in labels. `dpi=300`,
      `bbox_inches='tight'`.

## Misconception discipline

- [ ] §9 (Limitations and common misconceptions) lists at least two
      concrete misconceptions in `오개념 N` / `Misconception N` callout
      form, each with: (i) the wrong statement in italics, (ii) the
      correction, (iii) where the wrong intuition typically comes from.
- [ ] Failure modes of the method or formula are stated: where does it
      break, what goes wrong at boundaries, what numerical hazards
      appear.

## End-to-end audit

Grep the document for these patterns and review each hit:

```bash
grep -nE '(obviously|clearly|trivially|evident|well[- ]known|it can be shown|it is easy to see|it follows that(?! from)|leave .* as an exercise)' explanation.md
grep -nE '≈|~' explanation.md   # every match must justify itself
grep -nE '\$\$' explanation.md  # every display block has a symbol-def line after
```

A clean grep on the first line is mandatory. A noisy grep is the smell
test for unaudited hand-waving.
