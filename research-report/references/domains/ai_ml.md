# AI / ML Domain Notes

## Tone & framing
- Frame the contribution as either a new method, a new application, or a new evaluation. State which up front.
- Position against current SOTA. Name the baselines explicitly; do not say "compared to prior work" without naming it.

## Reproducibility (mandatory)
- Fix random seeds. Report the seed(s) used and whether results are averaged over multiple seeds.
- Document hyperparameters (learning rate, batch size, optimizer, scheduler, weight decay, gradient clipping).
- Pin library versions for `torch`, `jax`, `transformers`, `numpy`, `scikit-learn` etc.
- Record GPU/CPU, training time, and total compute. Compute budget belongs in the Implementation section.

## Methodology framework
- **Problem formulation** must define: input space, output space, evaluation metric(s), and success criteria.
- **Baselines** are mandatory. A standalone result is uninterpretable.
- **Ablations** for any method with multiple components. State which component each ablation removes.
- **Statistical rigor**: error bars, confidence intervals, or std-over-seeds for every headline number. Single-run claims are a red flag.

## Visualization checklist
- Learning curves (train + val) with shaded uncertainty bands across seeds.
- Comparison bar charts MUST include error bars (std or 95% CI).
- For classification: include confusion matrix or PR/ROC curve when the binary positive class is informative.
- For language models: report perplexity, exact-match, F1, with the dataset and split named on the figure.
- Annotate the SOTA reference number on bar comparisons so the reader sees the gap at a glance.

## Common failure modes to flag in the Limitations section
- Train/test contamination (especially for LLMs).
- Hyperparameter advantage over baselines (you tuned yours, you re-used theirs as published).
- Cherry-picked seed.
- Domain shift between training data and reported benchmark.
- Compute budget mismatch when comparing to a baseline.
