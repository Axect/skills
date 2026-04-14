#!/usr/bin/env python3
"""Generic line-plot template for training curves or time-series diagnostics.

Input CSV columns:
- x: numeric axis (epoch, step, time, threshold, ...)
- series: line label
- y: primary value
- y_low / y_high: optional uncertainty band

Replace INPUT_CSV and OUTPUT_STEM with project-specific paths before use.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

INPUT_CSV = Path("plots/data/training_curves.csv")
OUTPUT_STEM = Path("plots/training_curves")
TITLE = "Training and Validation Curves"
X_LABEL = "Step"
Y_LABEL = "Metric"
USE_LOG_Y = False
STYLE_PREFERENCE = ["science", "nature"]
COLOR_CYCLE = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]


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
    required = {"x", "series", "y"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    for index, (series_name, frame) in enumerate(df.groupby("series", sort=False)):
        frame = frame.sort_values("x")
        color = COLOR_CYCLE[index % len(COLOR_CYCLE)]
        ax.plot(frame["x"], frame["y"], label=str(series_name), color=color, linewidth=1.5)
        if {"y_low", "y_high"}.issubset(frame.columns):
            ax.fill_between(frame["x"], frame["y_low"], frame["y_high"], color=color, alpha=0.18)

    ax.set_title(TITLE)
    ax.set_xlabel(X_LABEL)
    ax.set_ylabel(Y_LABEL)
    if USE_LOG_Y:
        ax.set_yscale("log")
    ax.legend(fontsize=7, frameon=True)
    ax.grid(alpha=0.25, linewidth=0.4)
    fig.tight_layout()
    save_figure(fig, OUTPUT_STEM)


if __name__ == "__main__":
    main()
