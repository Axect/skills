# General Domain Notes

Use this when no specialized domain template applies.

## Tone
- Academic-but-accessible. Third-person, declarative. Avoid hedging language ("may", "could perhaps").
- Lead each paragraph with the takeaway sentence; supporting detail follows.

## Quantitative discipline
- Every comparison reports the magnitude of the effect (delta, ratio, %), not just direction.
- Every metric should be paired with its uncertainty (CI, std, error bars) or with an explicit caveat about why uncertainty is not reported.

## Visualization
- Use the shared `apply_style()` from `_plot_style.py`. Single-column figures: `FIGSIZE_SINGLE` (3.5 x 2.6 in). Double-column: `FIGSIZE_DOUBLE` (7.0 x 3.6 in).
- Default to the Okabe-Ito palette (colorblind-safe).
- One idea per figure. Do not pack three claims into one chart.

## Math
- All math in LaTeX. No unicode (`α`, `²`, `≈`, `ℝ`, `∈`, ...). See SKILL.md §"Report-body math conventions".
- Display equations on their own lines surrounded by blank lines.
