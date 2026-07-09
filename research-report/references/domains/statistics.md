# Statistics Domain Notes

## Tone & framing
- Say what question the analysis answers and why it matters before the machinery of the test. The core idea (§2) is the inferential logic in plain words: what would count as evidence, and for what.
- State the inferential target precisely: estimation, hypothesis test, prediction, decision. Each carries different reporting standards.
- Distinguish between population-level claims and sample-level observations.
- Report an effect as a finding with meaning ("the treatment shifts the mean by 0.4 SD"), then the test statistic and p-value as the evidence for it, not the other way around.

## Mandatory reporting
- **Sample sizes** for every group / split.
- **Estimator + uncertainty**: point estimate, standard error or CI, with the CI level (`95\%` not `95%`; under LaTeX `%` is a comment — escape it).
- **Test statistic, df, p-value**, exact (not just `p < 0.05`).
- **Effect size** alongside any significance test (Cohen's $d$, $r$, odds ratio, ...).
- **Multiple-testing correction** when applicable (Bonferroni, Benjamini-Hochberg). Name the correction and the family-wise error rate.
- **Pre-registration / analysis plan** status, when relevant.

## Visualization checklist
- Box plots / violin plots for distributional comparisons.
- Forest plots for meta-analyses and multi-cohort effect summaries.
- Q-Q plots for residual diagnostics.
- Always include CIs as error bars or shaded bands; never just the point estimate.
- Use `\,\%` (escaped percent under LaTeX) when labelling axes with percentages.

## Math conventions
- LaTeX only. Routinely needed: `$\mathbb{E}$`, `$\mathrm{Var}$`, `$\mathrm{Cov}$`, `$\mathbb{P}$`, `$\sim \mathcal{N}(\mu, \sigma^2)$`.
- Distinguish parameters and estimators visually: `$\theta$` vs `$\hat{\theta}$`, `$\mu$` vs `$\bar{x}$`.
- Use `\sim` (`$\sim$`) for "distributed as", not the unicode tilde.
