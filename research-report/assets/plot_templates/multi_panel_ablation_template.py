#!/usr/bin/env python3
"""Multi-panel ablation template for regime-by-regime or per-panel comparisons.

Input CSV columns:
- panel: subplot label
- x: numeric axis
- series: curve label
- y: value
- y_low / y_high: optional uncertainty band

Replace INPUT_CSV and OUTPUT_STEM with project-specific paths before use.
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

INPUT_CSV = Path("plots/data/ablation_grid.csv")
OUTPUT_STEM = Path("plots/ablation_grid")
TITLE = "Ablation Grid"
X_LABEL = "Condition"
Y_LABEL = "Metric"
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
    required = {"panel", "x", "series", "y"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    panels = list(dict.fromkeys(df["panel"].astype(str)))
    ncols = min(2, max(len(panels), 1))
    nrows = math.ceil(len(panels) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(7.2 if ncols == 2 else 3.6, 2.6 * nrows), squeeze=False)
    flat_axes = axes.flatten()

    for ax, panel_name in zip(flat_axes, panels):
        panel_df = df[df["panel"].astype(str) == panel_name]
        for index, (series_name, frame) in enumerate(panel_df.groupby("series", sort=False)):
            frame = frame.sort_values("x")
            color = COLOR_CYCLE[index % len(COLOR_CYCLE)]
            ax.plot(frame["x"], frame["y"], label=str(series_name), color=color, linewidth=1.4)
            if {"y_low", "y_high"}.issubset(frame.columns):
                ax.fill_between(frame["x"], frame["y_low"], frame["y_high"], color=color, alpha=0.18)
        ax.set_title(str(panel_name), fontsize=9)
        ax.set_xlabel(X_LABEL)
        ax.set_ylabel(Y_LABEL)
        ax.grid(alpha=0.25, linewidth=0.4)

    for ax in flat_axes[len(panels):]:
        ax.axis("off")

    handles, labels = flat_axes[0].get_legend_handles_labels() if panels else ([], [])
    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=min(len(labels), 4), fontsize=7, frameon=True)
        fig.subplots_adjust(top=0.85)
    fig.suptitle(TITLE, fontsize=10)
    fig.tight_layout()
    save_figure(fig, OUTPUT_STEM)


if __name__ == "__main__":
    main()
