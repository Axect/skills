"""Function plot skeleton — one or more closed-form curves f(x).

Adapt:
- Replace `f1`, `f2`, ... with the closed-form expressions to plot.
- Update `pparam` labels, scales, and limits.
- Update savefig output path.

Invariants to preserve verbatim:
- `import scienceplots` (registers styles by side effect; linter will flag it).
- `with plt.style.context(["science", "nature"]):` — NEVER add `"no-latex"`.
- `pparam` dict applied via `ax.set(**pparam)`.
- `ax.autoscale(tight=True)` before `ax.set(**pparam)`.
- Raw-string LaTeX (`r'...'`) in every label, title, legend entry.
- `dpi=300, bbox_inches='tight'` on savefig.
"""

import numpy as np
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401  -- side-effect import registers styles


# Domain
x = np.linspace(0.0, 1.0, 400)

# Functions to plot — replace with the actual closed forms.
def f1(x):
    return x**2

def f2(x):
    return x * (1.0 - x)


# Axis configuration
pparam = dict(
    xlabel=r"$x$",
    ylabel=r"$f(x)$",
    title=r"Title",
    xscale="linear",
    yscale="linear",
    xlim=(0.0, 1.0),
    ylim=(0.0, 1.0),
)

with plt.style.context(["science", "nature"]):
    fig, ax = plt.subplots()
    ax.autoscale(tight=True)
    ax.set(**pparam)
    ax.plot(x, f1(x), label=r"$f_1(x) = x^2$")
    ax.plot(x, f2(x), label=r"$f_2(x) = x(1 - x)$")
    ax.legend()
    fig.savefig("function_plot.png", dpi=300, bbox_inches="tight")
