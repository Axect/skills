"""Heatmap skeleton — 2D scalar field f(x, y) over a rectangle.

Adapt:
- Replace `f(X, Y)` with the closed-form scalar field.
- Update domain ranges (`x = ...`, `y = ...`).
- Update `pparam` labels and the colorbar label.
- Pick a colormap that suits the quantity: `viridis` (default, sequential),
  `RdBu_r` (diverging, for signed quantities), `magma` (sequential dark-to-light).
- Update savefig output path.

Invariants to preserve verbatim:
- `import scienceplots` (registers styles by side effect; linter will flag it).
- `with plt.style.context(["science", "nature"]):` — NEVER add `"no-latex"`.
- `pparam` dict applied via `ax.set(**pparam)`.
- `ax.autoscale(tight=True)` before `ax.set(**pparam)`.
- Raw-string LaTeX in every label, title, legend, colorbar label.
- `dpi=300, bbox_inches='tight'` on savefig.
"""

import numpy as np
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401


# Domain
x = np.linspace(-2.0, 2.0, 200)
y = np.linspace(-2.0, 2.0, 200)
X, Y = np.meshgrid(x, y)


# Scalar field — replace with the actual closed form.
def f(X, Y):
    return np.exp(-(X**2 + Y**2))


Z = f(X, Y)

pparam = dict(
    xlabel=r"$x$",
    ylabel=r"$y$",
    title=r"$f(x, y)$",
    xlim=(x[0], x[-1]),
    ylim=(y[0], y[-1]),
)

with plt.style.context(["science", "nature"]):
    fig, ax = plt.subplots()
    ax.autoscale(tight=True)
    ax.set(**pparam)
    im = ax.imshow(
        Z,
        origin="lower",
        extent=(x[0], x[-1], y[0], y[-1]),
        aspect="equal",
        cmap="viridis",
    )
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(r"$f(x, y)$")
    fig.savefig("heatmap.png", dpi=300, bbox_inches="tight")
