---
name: research-report
description: Create or revise a structured markdown research or experiment report with integrated plots, optional literature/reference support, plot manifest tracking, report version history, and report-body validation inside a single Harness without external Codex or Gemini calls. Use when you need to generate `report.md`, inventory or validate plots, create `plots/plot_manifest.json`, manage `report_versions.json`, connect report sections to supporting references, or turn an experiment or output directory into a reusable report workflow.
---

# Research Report

Use this skill to produce a self-contained research or experiment report from an output directory that may contain notes, source code, tests, metrics, tables, and plots.

## Inputs to confirm

Ask for only what is missing:
- target output directory
- report title
- domain or audience
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

1. **Gather materials**
   - Inventory `src/`, `tests/`, notes, metrics, tables, any prior `report.md` or `report_v*.md`, and any existing `references/`, `bib/`, or related-work notes.
   - Read the report template in `references/report_template.md`.
   - If `plots/` exists, build or refresh `plots/plot_manifest.json` with:
     ```bash
     python skills/research-report/scripts/build_plot_manifest.py \
       "{output_dir}/plots" \
       --report-root "{output_dir}"
     ```
   - If richer captions or section hints are needed, pass `--metadata path/to/plot_metadata.json`.

2. **Validate report artifacts early**
   - Run:
     ```bash
     python skills/research-report/scripts/validate_artifacts.py "{output_dir}" --json
     ```
   - Treat errors as blockers.
   - Treat warnings as items to fix or explicitly mention in the report.
   - The validator checks JSON artifacts and `report.md` body structure when present.

3. **Map evidence to sections**
   - Background: problem, context, assumptions, prior notes, and literature context.
   - Analysis or discovery summary: exploratory findings, trade-offs, or problem framing.
   - Methodology: approach, algorithms, data flow, experimental design, and method citations when external grounding matters.
   - Implementation or setup: architecture, components, environment, constraints.
   - Results and visualization: quantitative outcomes, comparisons, plots, tables, and baseline or benchmark context when needed.
   - Validation: tests, checks, edge cases, failure modes, limitations, and benchmark-protocol references when they clarify interpretation.
   - Conclusion: contributions, limitations, next steps.

4. **Attach literature support where needed**
   - Use the companion `reference-search` skill whenever a section depends on prior work, external benchmark framing, method lineage, or an externally grounded claim that cannot be supported by local artifacts alone.
   - Typical mappings:
     - background or introduction -> `background` or `survey`
     - methodology rationale -> `method`
     - comparison targets -> `baseline`
     - dataset, metric, or benchmark protocol context -> `evaluation`
     - standalone factual claims -> `claim-support`
   - Prefer weaving only the strongest 2-5 references into the report prose instead of dumping long bibliographies.
   - Only save section-level reference notes when the user asks for them or the project already maintains a `references/` or similar folder.

5. **Handle plots**
   - Reuse existing plots when they already support the narrative.
   - Generate missing plots only from real data already present in the workspace.
   - Preferred stack: `matplotlib` + `scienceplots` + the shared helper at `assets/plot_templates/_plot_style.py`. Copy the helper into the project's `plots/` directory next to any template script you adapt so `from _plot_style import ...` resolves.
   - **Plot text must be English.** Korean or other non-ASCII characters in axis labels, titles, legends, or tick labels typically render as missing-glyph boxes (`□`) and the failure is silent. Move localized commentary to the report caption. The shared `assert_english(...)` helper enforces this at runtime; call it on every user-facing string before plotting.
   - **LaTeX `%` rule.** When `text.usetex=True`, `%` starts a comment and silently truncates the rest of the string (`"95%"` becomes `"95"`). The shared `apply_style()` defaults `text.usetex` to `False` (mathtext handles `$...$` math without a TeX install). If you must opt in to LaTeX, run user-controlled strings through `latex_escape(...)` first; it covers `% & # _ $ { }`.
   - **Output formats:** PNG at `dpi=300` plus PDF (vector). SVG is an acceptable PDF substitute when PDF is impractical. The shared `save_figure()` enforces this and always closes the figure.
   - **PDF font embedding:** the shared helper sets `pdf.fonttype=42` and `ps.fonttype=42` so PDFs embed TrueType fonts. Type-3 fonts are rejected by many journals.
   - **Color palette:** Okabe-Ito (colorblind-safe) by default; `TAB10` is available as a fallback constant. The cycle is unified across all templates so the same series gets the same color across plots in a report. When series ordering varies between plots, pin colors with an explicit `series -> color` dict.
   - **Figure size standards** (constants in `_plot_style.py`):
     - `FIGSIZE_SINGLE` = (3.5, 2.6) — single-column journal figure
     - `FIGSIZE_ONE_HALF` = (5.0, 3.2) — 1.5-column
     - `FIGSIZE_DOUBLE` = (7.0, 3.6) — full-width / double-column
     - `FIGSIZE_PANEL_WIDE` = (7.2, 2.8) — 2-up panel base height
   - **In-figure title vs. caption:** journal-style figures usually keep the title in the caption only. Templates include `ax.set_title(...)` for convenience; remove it (or leave empty) when the report caption already states the same thing.
   - **Raw-data contract:** save the CSV consumed by each plot script to `plots/data/<stem>.csv` and record the path in `plot_metadata.source_context`. Scripts should be reproducible from a single CSV input.
   - Keep filenames stable and descriptive; rebuild `plot_manifest.json` after any plot change.
   - Use the templates in `assets/plot_templates/` as starting points for learning curves, grouped comparisons, or multi-panel ablations.

### Common plot pitfalls to prevent

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
| 21 | `text.usetex=True` on machines without LaTeX | Script fails when run elsewhere | Keep `use_latex=False` unless the project already pins a TeX install |
| 22 | Silent fallback when `scienceplots` is missing | Final figures look unlike previews | Record `scienceplots_available` from `apply_style()` in plot metadata |

6. **Draft the report**
   - Use `references/report_template.md` as the starting structure.
   - Embed each plot inline near the paragraph that interprets it.
   - When a section depends on prior work or benchmark framing, use curated results from `reference-search` and mention only references you actually reviewed.
   - Avoid fake citation placeholders or generic "prior work shows" wording without concrete support.
   - Avoid orphaned figures and unsupported quantitative claims.
   - If a canonical section has no source material, rename or repurpose it instead of leaving a hollow placeholder.
   - When the report is dense, optional `<!-- EVIDENCE BLOCK: ... -->` markers can help trace claims to figures or tables.

7. **Run two self-review passes locally**
   - **Traceability pass**: every claim should point to code, test output, metric, table, plot, or a curated literature source from `reference-search`.
   - **Visualization pass**: every plot should have a caption, section placement, interpretation, and reproducibility context.
   - Resolve issues first: unsupported claims, unlabeled figures, weak captions, stale paths, mismatched plot discussion, thinly supported literature statements, or manifest/report drift.

8. **Version the report when updating an existing draft**
   - If `report_versions.json` already exists, archive the current report before overwriting it:
     - read `current_version`
     - copy `report.md` to `report_v{current_version}.md`
   - After writing the new `report.md`, record the new version:
     ```bash
     python skills/research-report/scripts/record_report_version.py \
       "{output_dir}" \
       --summary "Summarize the update" \
       --tier 1
     ```
   - `--tier` is optional. Use:
     - `1` for wording or structure changes
     - `2` for plot/report linkage changes
     - `3` for substantial methodology or result changes
   - Add structured change records with repeated `--change '{...json...}'` arguments when useful.

9. **Validate again before finishing**
   - Re-run the validator on the output directory.
   - Report: file locations, plot count, validation findings, thin sections, missing figure references, sections that still need stronger literature support, and any known caveats.

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
    "dpi": 300
  }
}
```

## Template resources

- `references/report_template.md`: baseline report structure aligned with the report workflow.
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

## When sections are missing

Adapt rather than apologizing:
- no brainstorming artifacts -> rename to `Analysis Summary` or `Problem Framing`
- no tests -> use `Validation & Limitations`
- no implementation code -> use `Experimental Setup` or `Materials`

## Outputs

- `report.md`
- `report_versions.json`
- `plots/plot_manifest.json`
- optional archived reports: `report_v{N}.md`
- optional section-level reference support notes only when the user requests saved citation outputs or the project already uses a references directory

After creating or updating this skill, suggest starting a new session so the new skill is discoverable from session start.
