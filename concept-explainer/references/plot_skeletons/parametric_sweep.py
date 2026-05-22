"""Parametric sweep skeleton — multi-panel "how does f change with alpha?".

Adapt:
- Replace `f(x, alpha)` with the closed-form expression to plot.
- Update `alphas` with the parameter values to sweep.
- Update `pparam` labels and panel titles.
- Update savefig output path.

Invariants to preserve verbatim:
- `import scienceplots` (registers styles by side effect; linter will flag it).
- `with plt.style.context(["science", "nature"]):` — NEVER add `"no-latex"`.
- `pparam` dict applied via `ax.set(**pparam)` for every panel.
- `ax.autoscale(tight=True)` on every panel before `ax.set(**pparam)`.
- Raw-string LaTeX in every label, title, legend, annotation.
- `dpi=300, bbox_inches='tight'` on savefig.
"""

import numpy as np
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401


# Domain and sweep
x = np.linspace(0.0, 1.0, 400)
alphas = [0.5, 1.0, 2.0, 4.0]


# Function to plot — replace with the actual closed form.
def f(x, alpha):
    return x**alpha


pparam = dict(
    xlabel=r"$x$",
    ylabel=r"$f(x; \alpha)$",
    xscale="linear",
    yscale="linear",
    xlim=(0.0, 1.0),
    ylim=(0.0, 1.0),
)

with plt.style.context(["science", "nature"]):
    fig, axes = plt.subplots(1, len(alphas), figsize=(2.0 * len(alphas), 2.0), sharey=True)
    for ax, alpha in zip(axes, alphas):
        ax.autoscale(tight=True)
        ax.set(**pparam)
        ax.set_title(rf"$\alpha = {alpha}$")
        ax.plot(x, f(x, alpha))
    fig.savefig("parametric_sweep.png", dpi=300, bbox_inches="tight")
