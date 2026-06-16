"""Shared scienceplots style for every deck figure.

Each figure script imports this module, plots inside `with style_ctx():`, and
saves with `save(fig, name)`. This is the single place that pins the look so
every deck figure is visually consistent.

Rules (do not violate in any figure script):
  - real LaTeX via the science+nature styles. Never add "no-latex". If a glyph
    fails, fix the label (use raw-string LaTeX), do not fall back.
  - NO in-figure titles. The slide carries the title.
  - every axis label / legend entry is a raw string r'...'.
  - savefig is dpi=300, bbox_inches='tight' (handled by save()).
"""
from pathlib import Path

import matplotlib.pyplot as plt
import scienceplots  # noqa: F401  registers 'science'/'nature' by import side effect

STYLE = ["science", "nature"]
PUBLIC = Path(__file__).resolve().parent.parent / "public"

# Per-series colors + markers, kept in ONE place so a series gets the same
# color/marker in every figure. Rename the keys and labels for your project;
# keep the palette small so the legend stays consistent across slides.
SERIES = {
    "a": dict(color="#1f4e9c", marker="o", label=r"series A"),
    "b": dict(color="#2a9d5a", marker="s", label=r"series B"),
    "c": dict(color="#e08a1e", marker="^", label=r"series C"),
    "d": dict(color="#d4453d", marker="v", label=r"series D"),
    "e": dict(color="#7a4fb0", marker="D", label=r"series E"),
    "f": dict(color="#4d4d4d", marker="P", label=r"series F"),
}
ACCENT = "#2f5cc7"   # deck accent blue (model / measured)
EXACT = "black"      # reference / ground truth


def style_ctx():
    """Context manager: `with style_ctx(): ...`."""
    return plt.style.context(STYLE)


def save(fig, name):
    """Save a figure to the deck's public/ dir as <name>.png (dpi=300, tight)."""
    PUBLIC.mkdir(exist_ok=True)
    fname = name if name.endswith(".png") else name + ".png"
    out = PUBLIC / fname
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {out} ({out.stat().st_size} bytes)")
    return out
