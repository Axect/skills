import pandas as pd
import matplotlib.pyplot as plt

# Import parquet file
df = pd.read_parquet('data.parquet')

# Prepare Data to Plot
x  = df['x']
y1 = df['y1']
y2 = df['y2']
y3 = df['y3']

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
    ax.plot(x, y1, label=r'$y_1$')
    ax.plot(x, y2, label=r'$y_2$')
    ax.plot(x, y3, label=r'$y_3$')
    ax.legend()
    fig.savefig('plot.png', dpi=300, bbox_inches='tight')
