import pandas as pd
import matplotlib.pyplot as plt

# Import parquet file
df = pd.read_parquet('data.parquet')

# Prepare Data to Plot
x = df['x']
y = df['y']

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
    ax.plot(x, y, label=r'$y=x$')
    ax.legend()
    fig.savefig('plot.png', dpi=300, bbox_inches='tight')
