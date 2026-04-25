#!/usr/bin/env python3
"""Generic line-plot template for training curves or time-series diagnostics.

Input CSV columns:
- x: numeric axis (epoch, step, time, threshold, ...)
- series: line label
- y: primary value
- y_low / y_high: optional uncertainty band

Replace INPUT_CSV and OUTPUT_STEM with project-specific paths before use.
Requires `_plot_style.py` (from research-report/assets/plot_templates/) in
the same directory or anywhere on `sys.path`.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from _plot_style import (
    FIGSIZE_SINGLE,
    apply_style,
    assert_english,
    save_figure,
)

INPUT_CSV = Path("plots/data/training_curves.csv")
OUTPUT_STEM = Path("plots/training_curves")
TITLE = "Training and Validation Curves"
X_LABEL = "Step"
Y_LABEL = "Metric"
USE_LOG_Y = False


def main() -> None:
    apply_style()
    assert_english(TITLE, X_LABEL, Y_LABEL)

    df = pd.read_csv(INPUT_CSV)
    required = {"x", "series", "y"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    fig, ax = plt.subplots(figsize=FIGSIZE_SINGLE)
    for series_name, frame in df.groupby("series", sort=False):
        assert_english(str(series_name))
        frame = frame.sort_values("x")
        line, = ax.plot(frame["x"], frame["y"], label=str(series_name))
        if {"y_low", "y_high"}.issubset(frame.columns):
            ax.fill_between(
                frame["x"], frame["y_low"], frame["y_high"],
                color=line.get_color(), alpha=0.18,
            )

    ax.set_title(TITLE)
    ax.set_xlabel(X_LABEL)
    ax.set_ylabel(Y_LABEL)
    if USE_LOG_Y:
        ax.set_yscale("log")
    ax.legend(loc="best")
    fig.tight_layout()
    save_figure(fig, OUTPUT_STEM)


if __name__ == "__main__":
    main()
