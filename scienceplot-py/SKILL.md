---
name: scienceplot-py
description: >
  Generate a Python matplotlib plot script that follows the user's mandatory
  scienceplots style — `with plt.style.context(["science", "nature"]):`,
  the `pparam = dict(...)` axis-config pattern, raw-string LaTeX labels, and
  `dpi=300, bbox_inches='tight'` savefig. Supports parquet, CSV,
  and NumPy (`.npy` / `.npz`) data sources, and four plot variants: single line,
  multi-line + legend, scatter / errorbar, and multi-panel subplots. Produces
  the `.py` file only — does NOT execute it. The user runs it themselves
  (typically with `uv run`).
  Use when the user asks to: write a matplotlib script, draft a publication-style
  plot, plot data from parquet / CSV / `.npy`, generate a science / nature
  style figure, set up a quick line / scatter / errorbar / subplot script, or
  scaffold a plot matching their lab template.
  Triggers on: "scienceplots", "science nature style", "matplotlib script",
  "plot script", "publication plot", "line plot script", "scatter plot script",
  "errorbar plot", "subplot figure", "plot from parquet", "plot from csv",
  "plot from npy", "lab plot template", "pq_plot template",
  "플롯 스크립트", "그래프 스크립트", "matplotlib 코드", "사이언스 플롯",
  "산점도 스크립트", "서브플롯 스크립트", "에러바 플롯".
allowed-tools: Read, Write, Edit, Glob, Grep
---

# scienceplot-py — Matplotlib Script Generator (scienceplots / science+nature)

Generate a Python plotting script that **always** follows the user's lab
template shape. The skill writes a `.py` file and returns its path; it does
not run the script. The user executes it themselves (the user prefers
`uv run <path>` per their global preferences).

The canonical template lives at
`~/Socialst/Templates/PyPlot_Template/pq_plot.py`. Every variant in this
skill is a structural extension of that file.

## Mandatory style invariants

Every generated script MUST keep these load-bearing patterns intact. Do not
"clean up" any of them, even if they look redundant or unused.

1. **`import scienceplots`** — required. It registers the `science` and
   `nature` styles by import side-effect; the symbol is never referenced
   directly. Linters will flag it as unused — keep it anyway.
2. **Style context block** — all plotting code lives inside
   `with plt.style.context(["science", "nature"]):`. Never substitute
   `plt.style.use(...)` or call any plotting outside this block.
3. **`pparam` dict** — axis configuration is a dict, applied with
   `ax.set(**pparam)`. Do not inline `ax.set_xlabel(...)`, `set_ylabel(...)`,
   `set_title(...)` calls when `pparam` would do.
4. **`ax.autoscale(tight=True)`** — called on every axis, before
   `ax.set(**pparam)`. For subplots, loop over all axes.
5. **Raw-string LaTeX** — every label, title, legend entry uses `r'...'`.
   Non-raw `'$x$'` works for the literal `$x$` but breaks the moment a
   backslash appears (`\alpha`, `\sigma`, `\mathrm{...}`). Always `r`-prefix.
6. **savefig** — `fig.savefig(<path>, dpi=300, bbox_inches='tight')`.
   Default filename is `plot.png`. PDF/SVG output is fine if asked, but keep
   `dpi=300` and `bbox_inches='tight'`. (Bump higher only if the user
   explicitly asks for it — the lab default is 300.)

## Workflow

1. Gather what the user has not already given:
   - Data source: parquet / CSV / `.npy` / `.npz`, plus the file path
   - x / y column or array names (and y-error if errorbar)
   - Plot variant: single line, multi-line + legend, scatter / errorbar, or
     subplots (rows × cols)
   - Axis labels, title, legend labels (LaTeX OK — strings will be wrapped
     in raw-string form)
   - Output path (default: `plot.png` next to the data file or in cwd)
2. Pick the matching template under `references/`:
   - `single_line.py` — one series, one ax (mirrors `pq_plot.py`)
   - `multi_line.py` — multiple series, one ax, with legend
   - `scatter_errorbar.py` — `ax.errorbar(...)` (or `ax.scatter(...)`)
   - `subplots.py` — multi-panel `fig, axes = plt.subplots(rows, cols)`
3. Swap in the requested data-loader block. See
   `references/data_loaders.md` for parquet / CSV / `.npy` / `.npz`
   snippets.
4. Substitute column names, label strings, title, output filename. Preserve
   every invariant from the section above.
5. Write the `.py` file with the Write tool. **Do not execute it.**
6. Print the output path and a one-line "run with `uv run <path>`" hint.
   Do not invoke `uv` / `python` from this skill.

## Data sources

| Source        | Imports                | Read call                                          |
|---------------|------------------------|----------------------------------------------------|
| Parquet       | `import pandas as pd`  | `df = pd.read_parquet('data.parquet')`             |
| CSV           | `import pandas as pd`  | `df = pd.read_csv('data.csv')`                     |
| NumPy `.npy`  | `import numpy as np`   | `data = np.load('data.npy')` (then column-slice)   |
| NumPy `.npz`  | `import numpy as np`   | `data = np.load('data.npz'); x = data['x']`         |

Full snippets in `references/data_loaders.md`.

## Templates

Each reference is a self-contained, runnable skeleton matching the
mandatory style invariants. Read the file, adapt strings/columns in memory,
then Write the result to the user's chosen path.

| Variant                | File                                  |
|------------------------|---------------------------------------|
| Single line (base)     | `references/single_line.py`           |
| Multi-line + legend    | `references/multi_line.py`            |
| Scatter / errorbar     | `references/scatter_errorbar.py`      |
| Subplots (multi-panel) | `references/subplots.py`              |
| Data loaders           | `references/data_loaders.md`          |

## What this skill does NOT do

- It does not run the generated script. The user runs it (preferred:
  `uv run <path>`).
- It does not install `scienceplots` / `matplotlib` / `pandas` / `numpy`.
  Assume they are already available in the target environment.
- It does not produce methodology / architecture / pipeline diagrams. For
  those, use the `paperbanana` skill or `wide-slide-illustrator`.
- It does not change the style invariants. If the user asks for a different
  style (e.g., `seaborn`, `ggplot`, plain matplotlib), tell them this skill
  is specifically for the science+nature template and offer to write the
  alternative as a plain script outside the skill.
