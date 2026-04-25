#!/usr/bin/env python3
"""Grouped comparison bar-chart template for model, dataset, or ablation summaries.

Input CSV columns:
- category: x-axis label
- group: bar grouping label
- value: bar height
- error: optional error bar

Replace INPUT_CSV and OUTPUT_STEM with project-specific paths before use.
Requires `_plot_style.py` (from research-report/assets/plot_templates/) in
the same directory or anywhere on `sys.path`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _plot_style import (
    FIGSIZE_SINGLE,
    apply_style,
    assert_english,
    save_figure,
)

INPUT_CSV = Path("plots/data/comparison_summary.csv")
OUTPUT_STEM = Path("plots/comparison_summary")
TITLE = "Comparison Summary"
Y_LABEL = "Metric"


def main() -> None:
    apply_style()
    assert_english(TITLE, Y_LABEL)

    df = pd.read_csv(INPUT_CSV)
    required = {"category", "group", "value"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    categories = list(dict.fromkeys(df["category"].astype(str)))
    groups = list(dict.fromkeys(df["group"].astype(str)))
    assert_english(*categories, *groups)

    positions = np.arange(len(categories), dtype=float)
    width = 0.8 / max(len(groups), 1)

    fig, ax = plt.subplots(figsize=FIGSIZE_SINGLE)
    for index, group_name in enumerate(groups):
        subset = pd.DataFrame(df[df["group"].astype(str) == group_name]).copy()
        subset["category"] = subset["category"].astype(str)
        series: list[float] = []
        errors: list[float] = []
        for category in categories:
            row = pd.DataFrame(subset[subset["category"] == category])
            if row.empty:
                series.append(np.nan)
                errors.append(np.nan)
                continue
            series.append(float(row.iloc[0]["value"]))
            errors.append(float(row.iloc[0]["error"]) if "error" in row.columns else np.nan)

        offset = (index - (len(groups) - 1) / 2) * width
        kwargs: dict[str, Any] = {"label": group_name, "alpha": 0.88}
        if not np.isnan(errors).all():
            kwargs.update({
                "yerr": np.array(errors, dtype=float),
                "capsize": 3,
                "error_kw": {"linewidth": 0.8},
            })
        ax.bar(positions + offset, np.array(series, dtype=float), width=width, **kwargs)

    ax.set_title(TITLE)
    ax.set_ylabel(Y_LABEL)
    ax.set_xticks(positions)
    ax.set_xticklabels(categories, rotation=20, ha="right")
    ax.legend(loc="best")
    fig.tight_layout()
    save_figure(fig, OUTPUT_STEM)


if __name__ == "__main__":
    main()
