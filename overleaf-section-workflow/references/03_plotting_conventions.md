# Plotting conventions

All plots for the paper follow strict scienceplots discipline. Deviations from these rules will be requested by the user and must be applied uniformly.

## Mandatory style

```python
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401

with plt.style.context(["science", "nature"]):
    fig, ax = plt.subplots()
    pparam = dict(
        xlabel=r"$X\ [\mathrm{units}]$",
        ylabel=r"$Y\ [\mathrm{units}]$",
        xscale="log",
        yscale="log",
        xlim=(x_lo, x_hi),
        ylim=(y_lo, y_hi),
    )
    # plot data
    ax.set(**pparam)
    ax.legend(loc=...)
    fig.savefig(out / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(out / f"{stem}.pdf", dpi=300, bbox_inches="tight")
    plt.close(fig)
```

## Forbidden options

- **NO** `usetex=False` or `--no-latex` flag. Use full LaTeX rendering (requires `sfmath.sty`).
- **NO** title (`ax.set_title(...)` or `plt.title(...)`). Data plots, not slides.
- **NO** font-size override (`fontsize=...`, `rcParams["font.size"]=...`). Trust scienceplots defaults.
- **NO** background color tweaks.
- **NO** ad-hoc grid styling (let scienceplots default handle it).

## Output requirements

- `dpi=300` always.
- `bbox_inches="tight"` always.
- Output BOTH `.png` AND `.pdf`. The Korean draft embeds the PNG (markdown inline); the LaTeX `.tex` includes the PDF.
- Save with `plt.close(fig)` to free memory in batch scripts.

## Legend placement

**Default**: `ax.legend(loc="best")` — but only safe when data leaves an empty quadrant.

When data covers most of the plot area, the legend will overlap curves. Real example: the family_overview plot with 5 distributions covered the entire xlim, and legend at `loc="best"` ended up at the upper right, blocking 30% of the plot area.

**Standard fix**: move legend outside the axes:
```python
ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
```
This places the legend to the right of the axes. The figure becomes wider but `bbox_inches="tight"` handles cropping.

When to apply:
- Multi-line plots (≥4 lines) on log-log axes where peaks cluster
- Limit-convergence plots where curves overlap near the limit
- Any plot where `loc="best"` results in overlap during review

## Axis range tuning

xlim/ylim must match the data:

- Don't include 5+ decades of empty space.
- Real example: `family_overview` initial `xlim=(1e13, 1e22)` was 9 decades, but all distributions peaked in $10^{14}$--$10^{16}$. Distributions squeezed to leftmost 30% of plot. Fix: tighten to `xlim=(1e13, 1e18)` (5 decades) so distributions span full plot width.

Tuning rule: include 1 decade beyond the largest peak and 1 decade beyond the smallest tail you want to show. Tails extending further can be truncated — `bbox_inches="tight"` doesn't help here, you need explicit `xlim`.

## Directory layout

Plot scripts live under the *research* project, not the paper project:

```
~/Documents/Project/Research/<PROJECT>/
└── operator/
    └── outputs/
        └── <section_topic>/
            ├── families.py          # reusable PDF definitions
            ├── plot_individual.py   # one plot per family
            ├── plot_limits.py       # limit convergence plots
            ├── plot_overview.py     # multi-family overview
            └── plots/
                ├── *.png
                └── *.pdf
```

The plot scripts are NOT inside `~/zbin/OverLeaf/<PROJECT>/` (sync folder). They live with the experiment / analysis code, and only the PDF outputs are copied to `~/zbin/OverLeaf/<PROJECT>/figs/`.

## Markdown embedding

In the Korean draft, embed plots as inline markdown images:

```markdown
![Caption text. `fig:label`](figs_<short>/plot_name.png)
```

The `figs_<short>` is a symlink in `<PROJECT>_draft/` pointing to the plots directory or to `<PROJECT>/figs/`. Set this up once per project:

```bash
ln -sf ~/Documents/Project/Research/<PROJECT>/operator/outputs/<topic>/plots \
       ~/zbin/OverLeaf/<PROJECT>_draft/figs_<short>
```

## Main-body vs Appendix decision

Decide per-figure which goes to main body vs Appendix:

| Figure type | Placement |
|---|---|
| Schematic / pipeline overview | Main body (introduce reader to flow) |
| Family / template overview (one panel, all families) | Main body |
| Limit-convergence (math claim) | Main body if claim is load-bearing, else Appendix |
| Per-family parameter sweeps | **Appendix** (reference figures) |
| Detailed numerical comparisons / ablations | Appendix |

When in doubt, ask the user. Default to Appendix for per-family detail.

## Caption discipline

Figure captions should be self-contained:

> "Five canonical PBH mass-function families overlaid on a common axis: Log-Normal ($\sigma = 0.5$), Power-Law ($\alpha = 2$), Smooth Power-Law ($\alpha = 2$, $\beta = 1$), Critical Collapse ($\alpha = 2.85$), and Generalized Beta Prime ($\alpha = 1.5$, $\beta = 1.5$, $\gamma = 3$)."

Bad: "Five distributions." (no parameter values)
Bad: "See text for description." (forces reader to scroll back)

Include:
- What is plotted (axes, units)
- Parameter values for each curve
- Any qualitative observation if the figure makes a load-bearing claim

## Reproducibility

Each plot script should be a single command to regenerate:

```bash
cd ~/Documents/Project/Research/<PROJECT>/operator/outputs/<topic>
uv run python plot_overview.py
```

After regenerating, copy PDFs to JCAP/figs/:
```bash
cp plots/<name>.pdf ~/zbin/OverLeaf/<PROJECT>/figs/
```

Build pipeline picks up the new PDFs on the next build pass automatically.
