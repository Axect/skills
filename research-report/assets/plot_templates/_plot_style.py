"""Shared plot styling helpers for research-report plot templates.

One source of truth for color cycles, figure sizes, and matplotlib rcParams.
Keep this module alongside any template script you copy into a project so the
`from _plot_style import ...` import resolves.

Conventions enforced here (so individual scripts don't have to think about them):

- PDF/PS save with `fonttype=42` so TrueType fonts are embedded (journal-safe).
- Default color cycle is the Okabe-Ito colorblind-safe palette.
- Plot text is required to be ASCII/English; `assert_english()` raises on CJK.
- `text.usetex` defaults to False; mathtext (`$...$`) handles math without TeX.
- `save_figure()` always closes the figure to avoid memory leaks in batch runs.
- Grid sits below data (`axes.axisbelow=True`).

If you need LaTeX rendering, call `apply_style(use_latex=True)` and route any
user-controlled string through `latex_escape()` so '95%' does not become '95'.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.figure import Figure

OKABE_ITO: tuple[str, ...] = (
    "#0072B2",
    "#D55E00",
    "#009E73",
    "#CC79A7",
    "#E69F00",
    "#56B4E9",
    "#F0E442",
    "#000000",
)

TAB10: tuple[str, ...] = (
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
)

FIGSIZE_SINGLE = (3.5, 2.6)
FIGSIZE_ONE_HALF = (5.0, 3.2)
FIGSIZE_DOUBLE = (7.0, 3.6)
FIGSIZE_PANEL_WIDE = (7.2, 2.8)

DEFAULT_DPI = 300

_LATEX_SPECIALS = re.compile(r"(?<!\\)([%&#_${}])")
_NON_ASCII = re.compile(r"[^\x00-\x7F]")


def apply_style(
    style_preference: tuple[str, ...] = ("science", "nature"),
    palette: Iterable[str] = OKABE_ITO,
    use_latex: bool = False,
) -> dict[str, object]:
    """Configure matplotlib for publication-quality output.

    Returns a dict describing the resolved style so callers can record it in
    plot metadata (e.g., whether scienceplots was actually available).
    """
    resolved_styles: list[str]
    try:
        import scienceplots as _scienceplots  # noqa: F401
        del _scienceplots
        resolved_styles = list(style_preference)
        plt.style.use(resolved_styles)
        scienceplots_available = True
    except ImportError:
        plt.style.use("default")
        resolved_styles = ["default"]
        scienceplots_available = False

    mpl.rcParams.update({
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.dpi": DEFAULT_DPI,
        "savefig.bbox": "tight",
        "axes.prop_cycle": cycler(color=list(palette)),
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.alpha": 0.25,
        "grid.linewidth": 0.4,
        "legend.frameon": True,
        "legend.fontsize": 7,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "lines.linewidth": 1.5,
        "figure.autolayout": False,
        "text.usetex": use_latex,
    })

    return {
        "style": resolved_styles,
        "scienceplots_available": scienceplots_available,
        "use_latex": use_latex,
        "palette_name": "okabe_ito" if tuple(palette) == OKABE_ITO else "custom",
    }


def assert_english(*texts: str | None) -> None:
    """Raise if any text contains non-ASCII characters.

    Plot labels, titles, and legends must be English. Non-ASCII text typically
    falls back to a missing-glyph box and the failure is silent. Localized
    explanations belong in the report caption, not in the figure.
    """
    for text in texts:
        if not text:
            continue
        if _NON_ASCII.search(text):
            raise ValueError(
                f"Plot text must be ASCII/English; got non-ASCII characters in: {text!r}. "
                "Move localized commentary to the report caption."
            )


def latex_escape(text: str) -> str:
    """Escape LaTeX specials so user text renders literally under text.usetex.

    Covers `% & # _ $ { }`. The lookbehind avoids double-escaping already
    escaped sequences. Does NOT handle `~` or `^` (these need full macro
    replacement and are rare in plot text); avoid them in axis labels.
    """
    return _LATEX_SPECIALS.sub(r"\\\1", text)


def save_figure(
    fig: Figure,
    output_stem: Path | str,
    formats: tuple[str, ...] = ("png", "pdf"),
) -> None:
    """Write the figure to all requested formats and close it."""
    output_stem = Path(output_stem)
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    for ext in formats:
        path = output_stem.with_suffix(f".{ext}")
        kwargs: dict[str, Any] = {"bbox_inches": "tight"}
        if ext == "png":
            kwargs["dpi"] = DEFAULT_DPI
        fig.savefig(path, **kwargs)
    plt.close(fig)
