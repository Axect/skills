import pandas as pd
import matplotlib.pyplot as plt

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
with plt.xkcd():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.autoscale(tight=True)
    ax.set(**pparam)
    # Errorbar variant — swap to ax.scatter(x, y, s=20, label=...) for a plain
    # scatter without error bars.
    ax.errorbar(x, y, yerr=yerr, fmt='o', ms=5, capsize=3, label=r'data')
    ax.legend()
    fig.savefig('plot.png', dpi=300, bbox_inches='tight')
