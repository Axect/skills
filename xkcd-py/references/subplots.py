import pandas as pd
import matplotlib.pyplot as plt

# Import parquet file
df = pd.read_parquet('data.parquet')

# Prepare Data to Plot
x  = df['x']
y1 = df['y1']
y2 = df['y2']

# Per-panel params
pparam_a = dict(
    xlabel = r'$x$',
    ylabel = r'$y_1$',
    title  = r"Panel A",
    xscale = 'linear',
    yscale = 'linear',
)
pparam_b = dict(
    xlabel = r'$x$',
    ylabel = r'$y_2$',
    title  = r"Panel B",
    xscale = 'linear',
    yscale = 'linear',
)

# Plot
with plt.xkcd():
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for a in axes:
        a.autoscale(tight=True)

    axes[0].set(**pparam_a)
    axes[0].plot(x, y1, label=r'$y_1$')
    axes[0].legend()

    axes[1].set(**pparam_b)
    axes[1].plot(x, y2, label=r'$y_2$')
    axes[1].legend()

    fig.tight_layout()
    fig.savefig('plot.png', dpi=300, bbox_inches='tight')
