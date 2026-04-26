"""Shared plot styling helpers for research-report plot templates.

One source of truth for color cycles, figure sizes, and matplotlib rcParams.
Keep this module alongside any template script you copy into a project so the
`from _plot_style import ...` import resolves.

Conventions enforced here (so individual scripts don't have to think about them):

- PDF/PS save with `fonttype=42` so TrueType fonts are embedded (journal-safe).
- Default color cycle is the Okabe-Ito colorblind-safe palette.
- Plot text is required to be ASCII/English; `assert_english()` raises on CJK.
- `save_figure()` always closes the figure to avoid memory leaks in batch runs.
- Grid sits below data (`axes.axisbelow=True`).

LaTeX rendering convention (auto-detected — read this carefully)
================================================================

The default `style_preference=("science", "nature")` from scienceplots is
*designed for LaTeX rendering*. The upstream `science.mplstyle` sets
`text.usetex: True` AND `font.family: serif`. If a script later overrides
`text.usetex` to `False`, the `font.family: serif` is honored but **Times /
Computer Modern fonts are silently substituted by DejaVu Sans on systems
without those fonts installed**. The result looks indistinguishable from
default matplotlib — scienceplots is loaded but its visual identity is gone.
This is the single most common silent-fallback failure with this stack.

`apply_style()` therefore handles the LaTeX decision automatically:

1. `use_latex=True` (default, recommended): require LaTeX.
   - At runtime, attempt to compile a tiny LaTeX snippet via matplotlib.
   - If it works, leave `text.usetex=True` (proper science+nature rendering).
   - If it fails, automatically append `no-latex` to the scienceplots style
     chain (scienceplots' own non-LaTeX variant), set `text.usetex=False`,
     and emit a warning so the user knows fonts will not match the LaTeX
     preview.
2. `use_latex=False` (explicit override): force the no-LaTeX path
   regardless of system state. Same automatic `no-latex` style insertion.

In either case the returned dict contains `latex_active` (bool) and
`latex_probe_error` (str | None) so plot metadata can record what actually
happened. Hardcoding `text.usetex=False` after `plt.style.use(['science'])`
WITHOUT `'no-latex'` in the chain is the bug pattern this helper prevents.

If you write text under LaTeX rendering, route any user-controlled string
through `latex_escape()` so '95%' does not become '95' (silent eat-of-comment)
and identifiers with underscores like `qq1_3333` render as `qq1\\_3333`.
"""
from __future__ import annotations

import logging
import re
import shutil
import subprocess
import warnings
from pathlib import Path
from typing import Any, Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)

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

# Style names that REQUIRE a working LaTeX install when the chain does NOT
# also contain the scienceplots `no-latex` modifier.
_LATEX_REQUIRING_STYLES: frozenset[str] = frozenset({"science", "nature", "ieee"})


def _latex_is_usable() -> tuple[bool, str | None]:
    """Probe whether matplotlib can actually render with text.usetex=True.

    Two cheap checks:
    1. `which latex` and `which dvipng` — both binaries needed.
    2. Run a tiny `latex` invocation in a tmpdir to confirm it works.

    Returns (usable, error_message_if_not).
    """
    for binary in ("latex", "dvipng"):
        if shutil.which(binary) is None:
            return False, f"`{binary}` not on PATH"
    try:
        result = subprocess.run(
            ["latex", "-interaction=nonstopmode", "-halt-on-error", "\\documentclass{article}\\begin{document}x\\end{document}"],
            cwd="/tmp",
            capture_output=True,
            timeout=15,
            text=True,
        )
        if result.returncode != 0:
            tail = (result.stdout or result.stderr or "")[-300:]
            return False, f"latex returned {result.returncode}: ...{tail}"
    except Exception as exc:  # subprocess error, timeout, etc.
        return False, f"latex probe raised: {exc!r}"
    return True, None


def apply_style(
    style_preference: tuple[str, ...] = ("science", "nature"),
    palette: Iterable[str] = OKABE_ITO,
    use_latex: bool = True,
) -> dict[str, object]:
    """Configure matplotlib for publication-quality output.

    LaTeX is auto-detected: when `use_latex=True` (default) the helper
    probes for a working `latex` install, and silently appends `no-latex`
    to the scienceplots style chain if one is not available. This avoids
    the common silent-fallback bug where `science` style is loaded but
    Times serif silently substitutes to DejaVu Sans.

    Returns a dict describing the resolved style so callers can record it
    in plot metadata. Keys:
      - `style`: the actual style chain that was applied
      - `scienceplots_available`: bool
      - `use_latex_requested`: caller's argument
      - `latex_active`: whether `text.usetex=True` ended up being used
      - `latex_probe_error`: None on success, error string when LaTeX
        was requested but unusable
      - `palette_name`: "okabe_ito" or "custom"
    """
    style_chain = list(style_preference)
    needs_latex = bool(_LATEX_REQUIRING_STYLES.intersection(style_chain))

    if use_latex and needs_latex:
        latex_ok, latex_err = _latex_is_usable()
        if not latex_ok:
            warnings.warn(
                "apply_style: LaTeX rendering was requested (default for science/nature/ieee), "
                f"but `latex` is not usable on this system ({latex_err}). "
                "Appending 'no-latex' to the style chain so scienceplots renders without TeX. "
                "Final fonts will be sans-serif (DejaVu/Helvetica fallback) instead of Times/Computer Modern. "
                "If you want LaTeX-quality output, install texlive and dvipng and re-run.",
                RuntimeWarning,
                stacklevel=2,
            )
            if "no-latex" not in style_chain:
                style_chain.append("no-latex")
            latex_active = False
        else:
            latex_active = True
    else:
        latex_active = False
        latex_err = None
        if needs_latex and "no-latex" not in style_chain:
            # User explicitly opted out of LaTeX while keeping science/nature.
            style_chain.append("no-latex")

    try:
        import scienceplots as _scienceplots  # noqa: F401
        del _scienceplots
        plt.style.use(style_chain)
        scienceplots_available = True
        resolved_styles = list(style_chain)
    except ImportError:
        warnings.warn(
            "apply_style: scienceplots is not installed; falling back to matplotlib defaults. "
            "Final figures will look unlike a previewed scienceplots-styled draft. "
            "Install with `pip install scienceplots` to restore.",
            RuntimeWarning,
            stacklevel=2,
        )
        plt.style.use("default")
        resolved_styles = ["default"]
        scienceplots_available = False
        latex_active = False  # default style, no LaTeX

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
        # text.usetex is set by the style chain (science: True, no-latex: False);
        # we only override when the caller explicitly asked for the no-LaTeX path
        # AND the chain didn't already include `no-latex` (defensive belt-and-braces).
        **({"text.usetex": False} if not latex_active else {}),
    })

    return {
        "style": resolved_styles,
        "scienceplots_available": scienceplots_available,
        "use_latex_requested": use_latex,
        "latex_active": latex_active,
        "latex_probe_error": None if latex_active or not needs_latex else latex_err,
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
