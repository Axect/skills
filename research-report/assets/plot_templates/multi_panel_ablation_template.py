#!/usr/bin/env python3
"""Multi-panel ablation template for regime-by-regime or per-panel comparisons.

Input CSV columns:
- panel: subplot label
- x: numeric axis
- series: curve label
- y: value
- y_low / y_high: optional uncertainty band

Replace INPUT_CSV and OUTPUT_STEM with project-specific paths before use.
Requires `_plot_style.py` (from research-report/assets/plot_templates/) in
the same directory or anywhere on `sys.path`.
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from _plot_style import (
    FIGSIZE_PANEL_WIDE,
    FIGSIZE_SINGLE,
    apply_style,
    assert_english,
    save_figure,
)

INPUT_CSV = Path("plots/data/ablation_grid.csv")
OUTPUT_STEM = Path("plots/ablation_grid")
TITLE = "Ablation Grid"
X_LABEL = "Condition"
Y_LABEL = "Metric"


def main() -> None:
    apply_style()
    assert_english(TITLE, X_LABEL, Y_LABEL)

    df = pd.read_csv(INPUT_CSV)
    required = {"panel", "x", "series", "y"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    panels = list(dict.fromkeys(df["panel"].astype(str)))
    series_names = list(dict.fromkeys(df["series"].astype(str)))
    assert_english(*panels, *series_names)

    ncols = min(2, max(len(panels), 1))
    nrows = math.ceil(len(panels) / ncols)
    base_w, base_h = FIGSIZE_PANEL_WIDE if ncols == 2 else FIGSIZE_SINGLE
    fig, axes = plt.subplots(nrows, ncols, figsize=(base_w, base_h * nrows), squeeze=False)
    flat_axes = axes.flatten()

    color_map: dict[str, str] = {}
    for ax, panel_name in zip(flat_axes, panels):
        panel_df = pd.DataFrame(df[df["panel"].astype(str) == panel_name])
        for series_name, raw_frame in panel_df.groupby("series", sort=False):
            frame: pd.DataFrame = pd.DataFrame(raw_frame).sort_values("x")
            label = str(series_name)
            if label in color_map:
                line, = ax.plot(frame["x"], frame["y"], label=label, color=color_map[label])
            else:
                line, = ax.plot(frame["x"], frame["y"], label=label)
                color_map[label] = line.get_color()
            if {"y_low", "y_high"}.issubset(frame.columns):
                ax.fill_between(
                    frame["x"], frame["y_low"], frame["y_high"],
                    color=color_map[label], alpha=0.18,
                )
        ax.set_title(str(panel_name), fontsize=9)
        ax.set_xlabel(X_LABEL)
        ax.set_ylabel(Y_LABEL)

    for ax in flat_axes[len(panels):]:
        ax.axis("off")

    handles, labels = flat_axes[0].get_legend_handles_labels() if panels else ([], [])
    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=min(len(labels), 4))
        fig.subplots_adjust(top=0.85)
    fig.suptitle(TITLE, fontsize=10)
    fig.tight_layout()
    save_figure(fig, OUTPUT_STEM)


if __name__ == "__main__":
    main()
