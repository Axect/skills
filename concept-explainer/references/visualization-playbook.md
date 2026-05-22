# Visualization Playbook

A pedagogical figure earns its place by *shortening the gap* between a
formula and an intuition. If it does neither, drop it.

This file picks the right tool per visualization need and gives the
caption pattern that makes a figure actually teach.

## Schematic vs data plot — the dividing line

| If the figure shows…                                       | Use…                                                  |
|------------------------------------------------------------|-------------------------------------------------------|
| Boxes, arrows, components, pipelines, "how it fits together" | `wide-slide-illustrator` Friendly Whiteboard prompt |
| A taxonomy, a decision tree, a flowchart                     | `wide-slide-illustrator` Friendly Whiteboard prompt |
| The big picture / mental model / "the cartoon"               | `wide-slide-illustrator` Friendly Whiteboard prompt |
| A function `f(x)` evaluated over a range                     | matplotlib + `function_plot.py`                     |
| The effect of varying a parameter `α`                        | matplotlib + `parametric_sweep.py`                  |
| A 2D field, density, potential, energy surface               | matplotlib + `heatmap.py`                           |
| Convergence / error scaling                                  | matplotlib + `function_plot.py` (log-log scales)    |
| Exact vs approximation                                       | matplotlib multi-line variant                       |
| Phase portrait, vector field, flow                           | matplotlib `quiver` / `streamplot` (adapt skeleton) |
| Real measured / simulated data from a file                   | `scienceplot-py` skill, output under `plots/`       |

**Hard rule:** never draw boxes-and-arrows in matplotlib, and never plot
`f(x)` curves through an image-generation model. Each tool has a
comparative advantage; mixing them gives ugly figures and broken
pedagogy.

## Choosing what to plot, per section

| Section            | Typical figure                                                        |
|--------------------|------------------------------------------------------------------------|
| §1 Why this matters | (rare) one motivating data plot from a famous experiment              |
| §2 Setup           | optional schematic — "here's the system we're studying"               |
| §3 Definitions     | (none — definitions are textual)                                      |
| §4 Intuition       | schematic OR a single `function_plot.py` showing the headline curve   |
| §5 Derivation      | (rare — usually no figures, prose carries the steps)                  |
| §6 Worked example  | `function_plot.py` with the example's numerical values               |
| §7 Visualizations  | `parametric_sweep.py` and/or `heatmap.py` — the heart of the section  |
| §8 Generalization  | optional sweep showing the result holds in a broader regime          |
| §9 Misconceptions  | comparison plot: wrong-intuition curve vs correct curve              |
| §10 Where to go    | (none)                                                                |

## Caption pattern

Every caption has three beats:

1. **What is plotted** — the axes and the curves, in plain language.
2. **What to look at** — the salient feature ("notice that the minimum…",
   "the curves cross at `x = …`", "the slope on log-log is `-2`").
3. **What it means** — the pedagogical takeaway ("…confirming the
   classical trajectory is the action-minimizing path").

Anti-pattern: "Figure 3: action vs path length." Useless.

Good: "Figure 3 — Action `S` (vertical axis) vs path-length perturbation
amplitude `ε` (horizontal axis), for three trial paths. **Look at** the
minimum: it sits at the classical trajectory `ε = 0`, and the curve is
locally quadratic, meaning the action grows like `ε²` for small wiggles.
**Takeaway:** the principle of least action picks out the classical path
through second-order, not just first-order, stability."

## Plot styling invariants (recap)

Lifted from `scienceplot-py` and pinned here so the skill survives a
client that hasn't loaded that skill's instructions:

1. `import scienceplots` — required (side-effect registration).
2. `with plt.style.context(["science", "nature"]):` — wraps every figure.
   **Never** `["science", "nature", "no-latex"]`.
3. `pparam = dict(xlabel=..., ylabel=..., title=..., xscale=..., yscale=...,
   xlim=..., ylim=...)` and `ax.set(**pparam)`.
4. `ax.autoscale(tight=True)` before `ax.set(**pparam)`.
5. Every label in raw-string LaTeX: `r'$\\alpha$'`, `r'$E(\\mathbf{x})$'`.
6. `fig.savefig(<path>, dpi=300, bbox_inches='tight')`.

The skeletons in `plot_skeletons/` already satisfy all of the above —
when you adapt them, leave the structural lines alone and only change
the data-generation block and labels.

## Schematic prompt pattern (wide-slide-illustrator Friendly Whiteboard)

The skill consumes a small dossier per schematic:

- **Goal**: one sentence — what the reader should *understand* after
  looking at this figure.
- **Panel count**: 3–6 panels. Fewer for "one big picture", more for
  "five steps in sequence".
- **Per-panel content**: short label (1–4 words, English on canvas) + 1–2
  sentence sketch of the panel.
- **Visual motif**: any domain-relevant doodle (a spring for mechanics,
  a Gaussian for probability, a stylized circuit for EM, etc.) — feeds
  the Friendly Whiteboard "tiny sticker doodle" slot.
- **Color hints**: if the document uses a recurring color for a concept
  (red for "wrong", green for "right"), pass it through.

See `schematic_friendly.md` for the call protocol.

## When NOT to add a figure

- The concept is purely algebraic and the figure would just retype the
  equation. (E.g. defining the Kronecker delta does not benefit from a
  schematic.)
- The figure would only confirm what the prose already said in one
  sentence.
- The figure adds visual noise without adding inference — pretty does
  not equal pedagogical.
- The audience already knows the visual archetype (no need to draw a
  Gaussian bell to a stats audience).

A reasonable target: 4–8 figures for a `length: standard` document.
More if `worked_example_density: high`, fewer if `math_density: high`
and the audience is comfortable with pure-symbol treatment.
