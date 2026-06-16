# Figure pipeline

All figures share one style helper so the deck looks uniform. Match the user's lab convention: scienceplots `science`+`nature`, real LaTeX, no in-figure titles (the slide carries the title).

## deck_style.py (shipped in assets/, copy into `figscripts/`)
Provides:
- `style_ctx()` → `plt.style.context(["science","nature"])` context manager; do ALL plotting inside it.
- `save(fig, "name")` → writes `<deck>/public/name.png` at `dpi=300, bbox_inches='tight'` and closes the fig.
- `SERIES` → per-series color+marker+label dict (generic example keys `a..f`; rename per project, but keep ONE palette so a series gets the same color across every figure).
- `ACCENT` (model/measured blue), `EXACT` (black, ground truth).

## Mandatory style (the lab template invariants)
1. `import scienceplots` (side-effect registers the styles; linters flag it unused — keep it). It is already imported inside `deck_style`.
2. All plotting inside `with style_ctx():`.
3. Axis config via a `pparam` dict applied with `ax.set(**pparam)`; call `ax.autoscale(tight=True)` before it (loop over axes for subplots).
4. **No `set_title` / `suptitle` anywhere.** Panel identity comes from axis labels, legends, or a/b/c letters.
5. Every label/legend/annotation is a **raw string** `r'...'`. Real LaTeX — never add `no-latex`; if a glyph fails, fix the label.
6. Save with `save(fig, "name")` (never raw `fig.savefig`).

## One script per figure group
Put `figscripts/g_<group>.py` files, each importing deck_style and producing a few related PNGs. Read data with pandas/numpy from the user's CSV/parquet/npz; do not hardcode results. For figures that need model sampling (e.g. re-sampling a checkpoint), write a separate sampler script that emits a CSV/npy, then plot from that — keep sampling (slow, GPU) out of the plotting script.

Skeleton:
```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from deck_style import style_ctx, save, SERIES, ACCENT, EXACT
import numpy as np, pandas as pd, matplotlib.pyplot as plt

def fig_example():
    df = pd.read_csv("path/to/data.csv")
    with style_ctx():
        fig, ax = plt.subplots()
        ax.plot(df.x, df.y, marker="o", color=ACCENT, label=r"model")
        ax.axhline(1.0, ls="--", c="grey", lw=0.8)
        ax.autoscale(tight=True)
        ax.set(**dict(xlabel=r"$x$", ylabel=r"$y / y_{\mathrm{ref}}$"))
        ax.legend(fontsize=6)
        save(fig, "example")

if __name__ == "__main__":
    fig_example()
```

## Figsize by panel count
Single panel: scienceplots default. 1×3 row of panels: ~`figsize=(6.5, 2.1)`. A matched pair (e.g. two thermo plots) must share identical figsize/layout. Wide figures will be placed full-width (`.fig-full`) on the slide — see gotchas §5.

## Explicit x-ticks for sweeps
For a log-x window/size sweep, set explicit ticks at the actual values and turn off minor ticks, or the axis shows a lonely `10^1`:
```python
ax.set_xscale("log", base=2)
ax.set_xticks([8,16,32,64,128,256]); ax.set_xticklabels(["8","16","32","64","128","256"])
ax.minorticks_off()
ax.set_xlim(7, 300)   # start near the smallest point, no dead space
```
Put a legend OUTSIDE the data if it would overlap (`fig.legend(loc="lower center", ncol=4, bbox_to_anchor=(0.5,0))` + `plt.subplots_adjust(bottom=0.28)`).

## Hand-drawn / schematic figures
For a whiteboard-style schematic or a flow/gate diagram, generate it with an image-generation tool (the `journal-club-review` / `wide-slide-illustrator` / `codex-image` skills) rather than matplotlib — a hand-lettered cohesive illustration reads better than a clean plot for a concept slide. Save the PNG to `public/` and place it full-width with a one-line caption.

## Smoke test before a fleet of figures
Run one tiny `with style_ctx(): ... savefig` first to confirm scienceplots + LaTeX actually render in this environment before generating N figures (LaTeX must be installed for science+nature).
