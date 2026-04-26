---
name: research-report
description: Create or revise a structured markdown research or experiment report with integrated plots, optional literature/reference support, plot manifest tracking, report version history, and report-body validation inside a single Harness without external Codex or Gemini calls. Use when you need to generate `report.md`, inventory or validate plots, create `plots/plot_manifest.json`, manage `report_versions.json`, connect report sections to supporting references, or turn an experiment or output directory into a reusable report workflow.
---

# Research Report

Use this skill to produce a self-contained research or experiment report from an output directory that may contain notes, source code, tests, metrics, tables, and plots. The skill is **harness-only**: it never calls external Gemini or Codex MCP tools. Where the magi-researchers pipeline uses BALTHASAR (Gemini) and CASPER (Codex) reviewers, this skill spawns Claude subagents with cognitive-style framing instead.

## Inputs to confirm

Ask for only what is missing:
- target output directory
- report title
- domain or audience (used to load `references/domains/<domain>.md`; default: `general`)
- whether existing plots already exist in `plots/`
- whether a lightweight plot metadata file should be supplied for better captions or section mapping
- whether section-level reference support is needed for background, methodology, baseline comparisons, benchmark context, or claim-heavy passages

## Expected directory shape

The skill works best when the target directory looks roughly like this:

```text
{output_dir}/
  report.md
  report_versions.json
  plots/
    *.png
    *.pdf | *.svg
    plot_manifest.json
    _plot_style.py            # copy of the helper used by every plot script
    *.py                      # plot generation scripts
    data/<stem>.csv           # raw data consumed by each script
  src/
  tests/
  notes/ | brainstorm/ | plan/ | results/ | tables/
  references/ | bib/ | related_work/
```

Missing folders are acceptable. Adapt the report to whatever evidence actually exists.

## Report workflow conventions

When tailoring this skill to a project that already uses `outputs/` directories:

- Prefer a self-contained target like `outputs/{report_slug}/`.
- Keep `report.md`, `report_versions.json`, and `plots/plot_manifest.json` in the same report root.
- Copy or regenerate only artifacts that belong to the current report narrative. Do not mix unrelated experiment outputs.
- Treat `report_v{N}.md` files as immutable archives once versioned.
- Keep plot paths relative to the report root so the directory can move without edits.
- Reuse existing project metrics, CSV or JSON summaries, tables, and previous report drafts before creating new artifacts.

## Single-Harness workflow

The workflow has nine ordered steps. Steps marked **(gate)** must pass before continuing.

### Step 1 — Gather materials

- Inventory `src/`, `tests/`, notes, metrics, tables, any prior `report.md` or `report_v*.md`, and any existing `references/`, `bib/`, or related-work notes.
- Read the report template in `references/report_template.md`.
- Read the domain template at `references/domains/<domain>.md` for tone and visualization conventions. Fall back to `references/domains/general.md` when the domain is unknown.
- If `plots/` exists, build or refresh `plots/plot_manifest.json`:
  ```bash
  python skills/research-report/scripts/build_plot_manifest.py \
    "{output_dir}/plots" \
    --report-root "{output_dir}"
  ```
  Pass `--metadata path/to/plot_metadata.json` for richer captions or section hints.

### Step 2 — Plot-style pre-flight (gate)

Before drafting prose, audit every plot generation script for compliance with the shared style helper. This is the local equivalent of magi's BALTHASAR/CASPER style-compliance check, but enforced statically over scripts instead of begging an LLM to spot regressions.

1. Ensure `plots/_plot_style.py` exists. If the project does not have it yet, copy it from `assets/plot_templates/_plot_style.py` so `from _plot_style import ...` resolves.
2. Run the plot-script auditor:
   ```bash
   python skills/research-report/scripts/validate_plot_scripts.py "{output_dir}" --json
   ```
   The auditor flags:
   - scripts that import `matplotlib` but do **not** import `_plot_style` or `scienceplots`,
   - scripts that call `plt.style.use(['science', ...])` without `'no-latex'` while also setting `text.usetex=False` (silent-fallback bug, pitfall #21),
   - scripts that override `font.family` or `font.size` after `apply_style()`,
   - scripts that call `plt.savefig(...)` only as PNG (PDF/SVG missing),
   - scripts that hardcode `dpi` below 300,
   - scripts that fail to call `assert_english(...)` on label/title strings.
3. Resolve every error before continuing. Warnings should be fixed or explicitly justified in the report.
4. If a plot is non-compliant, regenerate it via the `assets/plot_templates/*.py` family and re-run `build_plot_manifest.py`.
5. Run the JSON-artifact validator afterwards:
   ```bash
   python skills/research-report/scripts/validate_artifacts.py "{output_dir}" --json
   ```
   Treat errors as blockers. Treat warnings as items to fix or explicitly mention in the report.

### Step 3 — Map evidence to sections

- Background: problem, context, assumptions, prior notes, and literature context.
- Analysis or discovery summary: exploratory findings, trade-offs, or problem framing.
- Methodology: approach, algorithms, data flow, experimental design, and method citations when external grounding matters.
- Implementation or setup: architecture, components, environment, constraints.
- Results and visualization: quantitative outcomes, comparisons, plots, tables, and baseline or benchmark context when needed.
- Validation: tests, checks, edge cases, failure modes, limitations, and benchmark-protocol references when they clarify interpretation.
- Conclusion: contributions, limitations, next steps.

**Plot → section mapping** uses the manifest's `section_hint`:

| `section_hint` | Report section |
|----------------|----------------|
| `methodology` | §3 Methodology |
| `results` | §5.1 Primary Results |
| `comparison` | §5.2 Comparative or Ablation Findings |
| `validation` | §6 Validation |
| `testing` | §6 Validation |

### Step 4 — Attach literature support where needed

- Use the companion `reference-search` skill whenever a section depends on prior work, external benchmark framing, method lineage, or an externally grounded claim that cannot be supported by local artifacts alone.
- Typical mappings:
  - background or introduction → `background` or `survey`
  - methodology rationale → `method`
  - comparison targets → `baseline`
  - dataset, metric, or benchmark protocol context → `evaluation`
  - standalone factual claims → `claim-support`
- Prefer weaving only the strongest 2–5 references into the report prose instead of dumping long bibliographies.
- Only save section-level reference notes when the user asks for them or the project already maintains a `references/` or similar folder.

### Step 5 — Handle plots

- Reuse existing plots when they already support the narrative.
- Generate missing plots only from real data already present in the workspace.
- Preferred stack: `matplotlib` + `scienceplots` + the shared helper at `assets/plot_templates/_plot_style.py`. Copy the helper into the project's `plots/` directory next to any template script you adapt so `from _plot_style import ...` resolves.
- **Plot text must be English.** Korean or other non-ASCII characters in axis labels, titles, legends, or tick labels typically render as missing-glyph boxes (`□`) and the failure is silent. Move localized commentary to the report caption. The shared `assert_english(...)` helper enforces this at runtime; call it on every user-facing string before plotting.
- **LaTeX `%` rule.** When `text.usetex=True`, `%` starts a comment and silently truncates the rest of the string (`"95%"` becomes `"95"`). The shared `apply_style()` keeps `text.usetex=True` whenever LaTeX is usable (so `science`/`nature` render correctly) and falls back to scienceplots' `no-latex` style only when LaTeX is unavailable. Always route user-controlled strings through `latex_escape(...)` (covers `% & # _ $ { }`) before passing them to axis labels, legends, or titles.
- **Output formats:** PNG at `dpi=300` plus PDF (vector). SVG is an acceptable PDF substitute when PDF is impractical. The shared `save_figure()` enforces this and always closes the figure.
- **LaTeX is the default rendering path** for `science` and `nature` styles. `apply_style()` defaults to `use_latex=True` and probes for `latex` + `dvipng` at runtime. If LaTeX is unavailable, the helper automatically appends scienceplots' `no-latex` style modifier and emits a `RuntimeWarning` so you know the rendering downgraded. Never call `plt.style.use(['science'])` and then set `text.usetex=False` by hand — that combination silently substitutes DejaVu Sans for Times and the resulting figures are indistinguishable from default matplotlib (scienceplots is loaded but invisible). Always go through `apply_style()` so the LaTeX/no-LaTeX decision is made coherently.
- **Recording the decision:** `apply_style()` returns a dict containing `latex_active`, `latex_probe_error`, and `scienceplots_available`. Persist these into `plot_manifest.json` (or per-plot metadata) so downstream readers can tell which rendering mode produced the figure.
- **PDF font embedding:** the shared helper sets `pdf.fonttype=42` and `ps.fonttype=42` so PDFs embed TrueType fonts. Type-3 fonts are rejected by many journals.
- **Color palette:** Okabe-Ito (colorblind-safe) by default; `TAB10` is available as a fallback constant. The cycle is unified across all templates so the same series gets the same color across plots in a report. When series ordering varies between plots, pin colors with an explicit `series -> color` dict.
- **Figure size standards** (constants in `_plot_style.py`):
  - `FIGSIZE_SINGLE` = (3.5, 2.6) — single-column journal figure (Nature single-column = 3.5 in)
  - `FIGSIZE_ONE_HALF` = (5.0, 3.2) — 1.5-column
  - `FIGSIZE_DOUBLE` = (7.0, 3.6) — full-width / double-column (Nature double-column = 7.2 in)
  - `FIGSIZE_PANEL_WIDE` = (7.2, 2.8) — 2-up panel base height
- **In-figure title vs. caption:** journal-style figures usually keep the title in the caption only. Templates include `ax.set_title(...)` for convenience; remove it (or leave empty) when the report caption already states the same thing.
- **Raw-data contract:** save the CSV consumed by each plot script to `plots/data/<stem>.csv` and record the path in `plot_metadata.source_context`. Scripts should be reproducible from a single CSV input.
- Keep filenames stable and descriptive; rebuild `plot_manifest.json` after any plot change.
- Use the templates in `assets/plot_templates/` as starting points for learning curves, grouped comparisons, or multi-panel ablations.

#### Common plot pitfalls to prevent

The most frequent silent failures when generating research plots. The shared `_plot_style.py` helper guards against most of these; the rest belong to drafting discipline.

| # | Pitfall | Why it bites | Prevention |
|---|---------|--------------|------------|
| 1 | Unescaped `%` under `text.usetex=True` | `%` is a LaTeX comment; `"95%"` silently becomes `"95"` | Default `use_latex=False`; otherwise wrap text with `latex_escape()` |
| 2 | Other unescaped LaTeX specials (`& # _ $ { }`) | Same class as #1 — silent or noisy errors | `latex_escape()` covers all of them |
| 3 | Korean / CJK in axis labels, legends, titles | Glyph fallback to `□`, no warning | English-only rule + `assert_english()` runtime check |
| 4 | Type-3 fonts in saved PDFs | Many journals reject; reviewers cannot select text | `pdf.fonttype=42`, `ps.fonttype=42` set in `apply_style()` |
| 5 | Non-colorblind-safe palette (red+green) | ~8% of male readers cannot distinguish | Okabe-Ito default in `apply_style()` |
| 6 | Inconsistent series-to-color mapping across plots | "Series A" is blue in fig 1 but red in fig 2 | Single shared cycle; pin colors via dict when ordering varies |
| 7 | `legend(loc="best")` on dense plots | Non-deterministic placement, layout shifts run-to-run | Pick an explicit `loc=...` for production figures |
| 8 | `tight_layout()` clipping `suptitle` | suptitle gets cut off | `constrained_layout=True` or `subplots_adjust(top=0.85)` |
| 9 | Forgetting `plt.close(fig)` in batch generation | Memory leak; "RuntimeWarning: figures retained" | `save_figure()` always closes |
| 10 | `np.log` of zero/negative on log axis | Silent NaN, missing data | Validate inputs; use `symlog` if zero is meaningful |
| 11 | Categorical x-axis without `set_xticklabels` | Numeric tick labels appear instead of names | Always call `set_xticks` and `set_xticklabels` together |
| 12 | Grid drawn over data | Distracting; data legibility hurt | `axes.axisbelow=True` (set in shared helper) |
| 13 | `plt.show()` in scripts run by automation | Blocks pipelines; CI hangs | Templates never call `plt.show()` |
| 14 | `.savefig()` after `plt.close()` (or vice versa) | Empty/black PDFs | `save_figure()` enforces correct order |
| 15 | 96 dpi PNG used for print | Pixelation in printed reports | `savefig.dpi=300` enforced |
| 16 | Hardcoded font (`Times New Roman`, etc.) not installed | Silent fallback to DejaVu — different look from preview | Do not override `font.family` per-script; use shared helper |
| 17 | `transparent=True` on a white-background figure | Background drops, looks wrong on colored pages | Leave default white background |
| 18 | Mismatched DPI between PNG and PDF | Tick label spacing differs across formats | Set `savefig.dpi` once globally |
| 19 | Empty alt text in `![](plots/x.png)` | Validator warns; accessibility regression | Always pass meaningful alt; copy from manifest caption |
| 20 | Plot manifest path drift after directory rename | Captions reference stale paths; build fails | Keep paths relative to report root; rebuild manifest after moves |
| 21 | `science`/`nature` styles WITHOUT LaTeX rendering | scienceplots' `science.mplstyle` sets `text.usetex: True` AND `font.family: serif`. Override `text.usetex=False` and Times silently substitutes to DejaVu Sans on machines without Times — figures look like default matplotlib, scienceplots is invisible. | `apply_style()` defaults to `use_latex=True`; auto-probes for `latex` + `dvipng` and appends scienceplots' `no-latex` style to the chain when LaTeX is missing. **Never set `text.usetex=False` after `plt.style.use(['science'])` without also adding `'no-latex'` to the chain.** |
| 22 | Silent fallback when `scienceplots` is missing | Final figures look unlike previews | Record `scienceplots_available` from `apply_style()` in plot metadata |
| 23 | Hardcoded `font.family` override after `apply_style()` | Re-introduces pitfall #21 | Treat the helper output as authoritative; do not touch `font.*` rcParams in scripts |

### Step 6 — Draft the report

- Use `references/report_template.md` as the starting structure.
- Embed each plot inline near the paragraph that interprets it. Never write a "list of figures" appendix table — that is an anti-pattern.
- Never use passive references such as "as shown in the figure below" or "see Figure X" without an accompanying concrete quantitative observation in the same paragraph (e.g., specific deltas, percentages, R², slope, p-values, runtime). The figure earns its space by being interpreted.
- When a section depends on prior work or benchmark framing, use curated results from `reference-search` and mention only references you actually reviewed.
- Avoid fake citation placeholders or generic "prior work shows" wording without concrete support.
- Avoid orphaned figures and unsupported quantitative claims.
- If a canonical section has no source material, rename or repurpose it instead of leaving a hollow placeholder.
- For dense reports, add `<!-- EVIDENCE BLOCK: ev-N -->` markers near the paragraph that consumes evidence id `ev-N`, and list the evidence inventory at the top of the report or in `evidence/inventory.json` so the validator can cross-check.

#### Report-body math conventions (LaTeX-only)

Every mathematical expression in `report.md` MUST use LaTeX. Unicode math symbols are **not acceptable** in the report body — they cause inconsistent rendering across PDF exporters (Typora, Pandoc, Marp, GitHub) and many journal stylesheets refuse to typeset them.

**Inline math** (`$...$`) — use for variable names, parameter values, complexity notation, short expressions. Examples:

| Concept | Wrong (Unicode) | Right (LaTeX) |
|---|---|---|
| Greek | `α = 0.05`, `σ₁`, `λ`, `θ̂` | `$\alpha = 0.05$`, `$\sigma_1$`, `$\lambda$`, `$\hat{\theta}$` |
| Number sets | `ℝⁿ`, `ℕ`, `ℤ`, `ℂ` | `$\mathbb{R}^n$`, `$\mathbb{N}$`, `$\mathbb{Z}$`, `$\mathbb{C}$` |
| Operators | `≈`, `≤`, `≥`, `≠`, `≪`, `≫`, `±`, `×`, `·`, `÷` | `$\approx$`, `$\leq$`, `$\geq$`, `$\neq$`, `$\ll$`, `$\gg$`, `$\pm$`, `$\times$`, `$\cdot$`, `$\div$` |
| Logic / sets | `∈`, `∉`, `⊂`, `⊆`, `∪`, `∩`, `∀`, `∃` | `$\in$`, `$\notin$`, `$\subset$`, `$\subseteq$`, `$\cup$`, `$\cap$`, `$\forall$`, `$\exists$` |
| Sub/super | `²`, `³`, `⁴`, `ⁿ`, `xᵢ`, `H₂O` | `$^2$`, `$^3$`, `$^4$`, `$^n$`, `$x_i$`, `$\mathrm{H}_2\mathrm{O}$` |
| Arrows | `→`, `←`, `↔`, `⇒`, `⇔` | `$\to$`, `$\leftarrow$`, `$\leftrightarrow$`, `$\Rightarrow$`, `$\Leftrightarrow$` |
| Calculus | `∂`, `∇`, `∫`, `∑`, `∏`, `√` | `$\partial$`, `$\nabla$`, `$\int$`, `$\sum$`, `$\prod$`, `$\sqrt{}$` |
| Infinity / Const. | `∞`, `π`, `ℏ`, `°` | `$\infty$`, `$\pi$`, `$\hbar$`, `$^{\circ}$` |

**Display math** (`$$...$$`) — use for key formulas, derivations, loss functions, and main results.

```
✘  Inline-style display equation (silently breaks Pandoc/Typora):
$$L = \frac{1}{N}\sum_i (y_i - \hat{y}_i)^2$$

✓  Display equation on its own lines (correct):

$$
L = \frac{1}{N}\sum_i (y_i - \hat{y}_i)^2
$$
```

Always:
- Put `$$` on a line by itself, with one blank line above and below the block.
- Use `\text{...}` for textual labels inside math (`$L_{\text{train}}$`, not `$L_{train}$`, which renders as $L \cdot t \cdot r \cdot a \cdot i \cdot n$).
- Use `\,`, `\;`, `\quad` to control spacing inside math; never insert literal spaces or unicode whitespace.
- Use `\mathrm{}` for upright multi-letter operators (e.g., `$\mathrm{erf}(x)$`, `$\mathrm{KL}(p \,\|\, q)$`).

The validator (`validate_artifacts.py`) flags single-line `$$..$$` and unicode math characters in the report body as errors.

### Step 7 — Coverage & gap-detection loop

After the first complete draft, walk every section and answer this checklist before presenting the draft.

| Question | If the answer is bad |
|----------|---------------------|
| Does every quantitative claim point to a number, a table cell, a CSV column, or a figure? | Add the missing artifact, weaken the claim, or remove the claim |
| Does every figure get at least one paragraph that quotes specific numbers from it? | Either add the interpretation, or remove the figure |
| Does the methodology cite the canonical reference for any non-trivial method? | Use `reference-search` and weave the citation into the prose |
| Do comparisons report uncertainty (CI, std, error bars) or at least say why they don't? | Add error bars or an explicit caveat |
| Could a reader regenerate every figure from `plots/data/*.csv` + the script in `plots/`? | Restore the data file, point `source_script` at the right file, or remove the figure |
| Are limitations honest and specific (not "may not generalize")? | Rewrite with the specific failure modes you actually observed |

**Gap-fill plot budget** (per draft pass):

| Draft depth | Max new plots | Max iterations |
|-------------|--------------|---------------|
| `min` | 2 | 1 |
| `default` | 4 | 2 |
| `high` | 8 | 3 |

If a gap requires data the workspace does not have, **do not fabricate**. Add an explicit caveat instead.

### Step 8 — Dual-subagent traceability review

Spawn two Claude subagents simultaneously (single message, two `Agent` tool uses, `subagent_type: general-purpose`). They must run independently — neither sees the other's output. This is the harness-only equivalent of magi's BALTHASAR + CASPER pair.

**Subagent A — Scientific Rigor (Creative-Divergent framing):**

> Prompt template: "Use the Read tool to read `{output_dir}/report.md` and `{output_dir}/plots/plot_manifest.json`. Review for claim–evidence integrity and identify, per issue, the section, the problematic text or figure, and a concrete fix.
> 1. **Orphaned claims** — text assertions without a supporting figure, table, metric, or citation.
> 2. **Orphaned plots** — figures embedded but never discussed.
> 3. **Weak links** — a claim references a figure that does not actually support the claim.
> 4. **Caption quality** — captions must be precise, quantitative, publication-ready (state what the figure shows in numbers, not just `Comparison of methods`).
> 5. **Math rendering** — flag any unicode math symbol or single-line `$$..$$` you encounter.
> Return structured text. Do not save to a file."

**Subagent B — Visualization Quality (Analytical-Convergent framing):**

> Prompt template: "Use the Read tool to read `{output_dir}/report.md`, `{output_dir}/plots/plot_manifest.json`, and any `{output_dir}/plots/*.py` scripts. Review for visualization correctness and identify, per issue, the section, the figure, and a concrete fix.
> 1. **Missing visualizations** — quantitative claims that would benefit from a chart but have none.
> 2. **Plot–narrative mismatch** — caption or surrounding text does not match what the plot shows.
> 3. **Chart-type fixes** — better encodings (bar→box, linear→log, grouped bars→error-bar dot plot) for clarity.
> 4. **Reproducibility gaps** — plots without a `source_script` or `source_context` in the manifest.
> 5. **Style compliance** — every script must import `_plot_style` (or scienceplots) and call `apply_style()`; no per-script `font.*` overrides; PNG@300dpi + PDF; Nature widths; Okabe-Ito palette.
> Return structured text. Do not save to a file."

After both reviews return, synthesize:

1. **Consensus issues** (flagged by both subagents) → fix first.
2. **Divergent suggestions** → evaluate on merit; apply when defensible.
3. Apply revisions:
   - orphaned claim → add a supporting plot/table/citation OR weaken the claim,
   - orphaned plot → add an interpretation paragraph OR remove the figure,
   - weak link → strengthen the connecting prose or replace with a more apt figure,
   - chart-type fix → regenerate via `assets/plot_templates/*.py`,
   - reproducibility gap → restore the missing CSV / source script.
4. Re-run `validate_artifacts.py` and `validate_plot_scripts.py` after all edits.

**Anti-consensus discipline.** When both subagents agree on an issue, the fix MUST cite at least one independent piece of evidence — a concrete number, a specific section line, a named pitfall — not just "both reviewers agreed".

### Step 9 — Versioning & finalization

- If `report_versions.json` already exists, archive the current report before overwriting:
  - read `current_version`
  - copy `report.md` to `report_v{current_version}.md`
- After writing the new `report.md`, record the new version:
  ```bash
  python skills/research-report/scripts/record_report_version.py \
    "{output_dir}" \
    --summary "Summarize the update" \
    --tier 1
  ```
- `--tier` corresponds to the feedback loop tiers below:
  - `1` — wording, structure, captions, formatting
  - `2` — plot/figure changes, scale/encoding swaps, manifest updates
  - `3` — substantive methodology or result changes (re-run experiments, change baselines)
- Add structured change records with repeated `--change '{...json...}'` arguments when useful.
- Re-run the JSON-artifact validator and the plot-script auditor.
- Report file locations, plot count, validation findings, thin sections, missing figure references, sections that still need stronger literature support, and any known caveats.

## User-feedback loop (Tier 1 / 2 / 3)

When the user reviews `report.md` and asks for changes, classify the request before applying it. The classification keywords mirror magi's tiered feedback loop.

| Tier | Signals | Action |
|------|---------|--------|
| **1 — Cosmetic** | "reword", "rephrase", "move section", "fix typo", "shorten", "expand on", "rename", "reformat", "caption" | Edit `report.md` directly. Archive previous version, bump tier=1. |
| **2 — Visualization** | "add plot", "change chart", "log scale", "bar chart instead", "overlay", "heatmap", "color", "axis", "resize figure", "add error bars" | Generate or modify plot via templates, rebuild manifest, re-run dual-subagent review on the affected sections only, archive previous version, bump tier=2. |
| **3 — Substantive** | "rerun", "different method", "add experiment", "change algorithm", "new baseline", "fix the code", "wrong results" | This skill cannot resolve substantive changes alone. Tell the user which experiment / source / test must be re-executed and pause. Do not bump the version. |

If the request is mixed-tier, decompose: apply Tier 1 / Tier 2 first, then escalate Tier 3.

If a request does not clearly match any tier, ask the user to confirm the classification before acting.

Maximum 3 feedback iterations per entry into the loop without explicit user re-approval.

## Anti-patterns (flag and fix on sight)

- Ending the report with a "List of Figures" or "Figure Inventory" table that re-lists already-embedded plots. Every figure should be embedded inline beside its interpretation.
- "As shown in the figure below" / "see Figure X" / "the plot illustrates" without a quantitative observation in the same paragraph. Replace with concrete numbers.
- Captions that name only the chart type (`Bar chart of metrics`). Captions must state the takeaway in numbers (`AdamW lowers val NLL from 0.94 to 0.71 at 200 steps; SGD plateaus at 1.02`).
- Display equations on a single line (`$$x = y$$` inline). Always put `$$` on its own line with the equation between.
- Unicode math characters in the report body (`σ`, `²`, `≈`, `→`, `ℝ`, `∈`, `±`, `°`, ...). Use the LaTeX equivalents from the table above.
- Hand-rolled `plt.style.use(['science', 'nature'])` in plot scripts that bypass `apply_style()`. The hand-rolled call leaves Times-vs-DejaVu fallback unhandled (pitfall #21).
- "Prior work shows that X" without a citation. Either cite or remove the claim.
- Section bodies that are only bullet points with no narrative. Each section needs at least one paragraph of prose so a reader can follow the argument without reverse-engineering bullets.

## Plot metadata file contract

Use a JSON object keyed by plot stem or plot id when default inference is not enough.

```json
{
  "training_curves": {
    "description": "Training and validation metrics across optimization steps",
    "section_hint": "results",
    "caption": "Validation loss stabilizes after the early rapid descent phase while the baseline remains consistently higher.",
    "source_context": "metrics/train_history.csv",
    "source_script": "plots/training_curves.py",
    "source_function": "main",
    "style": ["science", "nature"],
    "palette": "okabe_ito",
    "language": "en",
    "dpi": 300
  }
}
```

## Template resources

- `references/report_template.md`: baseline report structure aligned with the report workflow, with embedded `<!-- EVIDENCE BLOCK -->` and `<!-- WORD_BUDGET -->` hints.
- `references/domains/<domain>.md`: tone, methodology, and visualization conventions per domain (`ai_ml`, `physics`, `statistics`, `mathematics`, `general`).
- `reference-search`: companion skill for background references, method citations, baseline references, benchmark context, and claim-support searches while drafting the report.
- `assets/plot_templates/_plot_style.py`: shared styling helper (color palette, figure sizes, rcParams, `apply_style`, `save_figure`, `assert_english`, `latex_escape`). Copy into the project's `plots/` directory next to any template you adapt.
- `assets/plot_templates/training_curves_template.py`: line-plot template for learning curves or time-series diagnostics.
- `assets/plot_templates/comparison_bars_template.py`: grouped comparison template for model, dataset, or ablation summaries.
- `assets/plot_templates/multi_panel_ablation_template.py`: faceted multi-panel template for ablation or per-regime comparisons.
- `assets/plot_templates/plot_metadata_template.json`: starter metadata payload for `build_plot_manifest.py --metadata`.

## Quality bar

- Prefer concrete quantitative statements over vague summaries.
- Keep every file path relative to the report root.
- Never fabricate data for missing plots.
- Preserve reproducibility hints: source script, source context, and generation timestamp.
- Keep `plot_id` stable once published.
- Plot text is English-only; localized commentary belongs in the report caption, not the figure.
- Every plot script goes through `apply_style()` and `save_figure()` from `_plot_style.py` — do not hand-roll style/save logic in new scripts.
- Every math expression in `report.md` is LaTeX. Unicode math is a validator error.
- Every figure is embedded inline next to its interpretation and accompanied by at least one quantitative observation.

## When sections are missing

Adapt rather than apologizing:
- no brainstorming artifacts → rename to `Analysis Summary` or `Problem Framing`
- no tests → use `Validation & Limitations`
- no implementation code → use `Experimental Setup` or `Materials`

## Outputs

- `report.md`
- `report_versions.json`
- `plots/plot_manifest.json`
- optional archived reports: `report_v{N}.md`
- optional section-level reference support notes only when the user requests saved citation outputs or the project already uses a references directory

After creating or updating this skill, suggest starting a new session so the new skill is discoverable from session start.
