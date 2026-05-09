import pandas as pd
import matplotlib.pyplot as plt
import scienceplots

# Import parquet file
df = pd.read_parquet('data.parquet')

# Prepare Data to Plot
x    = df['x']
y    = df['y']
yerr = df['yerr']

# Plot params
pparam = dict(
    xlabel = r'$x$',
    ylabel = r'$y$',
    title  = r"Title",
    xscale = 'linear',
    yscale = 'linear',
)

# Plot
with plt.style.context(["science", "nature"]):
    fig, ax = plt.subplots()
    ax.autoscale(tight=True)
    ax.set(**pparam)
    # Errorbar variant — swap to ax.scatter(x, y, s=8, label=...) for a plain
    # scatter without error bars.
    ax.errorbar(x, y, yerr=yerr, fmt='o', ms=3, capsize=2, label=r'data')
    ax.legend()
    fig.savefig('plot.png', dpi=300, bbox_inches='tight')
