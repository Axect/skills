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
   - Preferred stack: `matplotlib` + `scienceplots`.
   - If `scienceplots` is unavailable, use clean matplotlib defaults and mention the styling deviation.
   - Save plots to both PNG and PDF when possible; SVG is an acceptable vector fallback.
   - Keep filenames stable and descriptive; refresh the manifest after any plot change.
   - Use the generic examples in `assets/plot_templates/` as starting points for learning curves, grouped comparisons, or multi-panel ablations.

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
