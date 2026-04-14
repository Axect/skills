#!/usr/bin/env python3
"""Grouped comparison bar-chart template for model, dataset, or ablation summaries.

Input CSV columns:
- category: x-axis label
- group: bar grouping label
- value: bar height
- error: optional error bar

Replace INPUT_CSV and OUTPUT_STEM with project-specific paths before use.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

INPUT_CSV = Path("plots/data/comparison_summary.csv")
OUTPUT_STEM = Path("plots/comparison_summary")
TITLE = "Comparison Summary"
Y_LABEL = "Metric"
STYLE_PREFERENCE = ["science", "nature"]
COLOR_CYCLE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#8c564b"]


def apply_style() -> None:
    try:
        import scienceplots  # noqa: F401
    except ImportError:
        plt.style.use("default")
    else:
        plt.style.use(STYLE_PREFERENCE)


def save_figure(fig: plt.Figure, output_stem: Path) -> None:
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(output_stem.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    apply_style()
    df = pd.read_csv(INPUT_CSV)
    required = {"category", "group", "value"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    categories = list(dict.fromkeys(df["category"].astype(str)))
    groups = list(dict.fromkeys(df["group"].astype(str)))
    positions = np.arange(len(categories), dtype=float)
    width = 0.8 / max(len(groups), 1)

    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    for index, group_name in enumerate(groups):
        subset = df[df["group"].astype(str) == group_name].copy()
        subset["category"] = subset["category"].astype(str)
        series = []
        errors = []
        for category in categories:
            row = subset[subset["category"] == category]
            if row.empty:
                series.append(np.nan)
                errors.append(np.nan)
                continue
            series.append(float(row.iloc[0]["value"]))
            errors.append(float(row.iloc[0]["error"])) if "error" in row.columns else errors.append(np.nan)

        offset = (index - (len(groups) - 1) / 2) * width
        kwargs = {"label": group_name, "color": COLOR_CYCLE[index % len(COLOR_CYCLE)], "alpha": 0.88}
        if not np.isnan(errors).all():
            kwargs.update({"yerr": np.array(errors, dtype=float), "capsize": 3, "error_kw": {"linewidth": 0.8}})
        ax.bar(positions + offset, np.array(series, dtype=float), width=width, **kwargs)

    ax.set_title(TITLE)
    ax.set_ylabel(Y_LABEL)
    ax.set_xticks(positions)
    ax.set_xticklabels(categories, rotation=20, ha="right")
    ax.legend(fontsize=7, frameon=True)
    ax.grid(axis="y", alpha=0.25, linewidth=0.4)
    fig.tight_layout()
    save_figure(fig, OUTPUT_STEM)


if __name__ == "__main__":
    main()
