# Data loader snippets

Each block replaces the data-import section of the chosen plot template
(`# Import parquet file` … `y = df['y']`). Pick one, drop it in, and adjust
column / array names. The rest of the script (xkcd context, `pparam`,
`savefig`) stays untouched.

## Parquet (pandas) — default

```python
import pandas as pd

df = pd.read_parquet('data.parquet')

x = df['x']
y = df['y']
```

## CSV (pandas)

```python
import pandas as pd

df = pd.read_csv('data.csv')

x = df['x']
y = df['y']
```

For tab-separated or other delimiters, pass `sep='\t'` / `sep=';'` etc.
For files without a header row, pass `header=None` and reference columns by
positional index (`df[0]`, `df[1]`).

## NumPy `.npy` — single ndarray

A `.npy` file holds exactly one ndarray. Three common shapes:

```python
import numpy as np

data = np.load('data.npy')

# Shape (N, 2): columns are [x, y]
x = data[:, 0]
y = data[:, 1]

# Shape (2, N): rows are [x, y]
# x, y = data[0], data[1]

# Shape (N,): only y; construct x as an index
# y = data
# x = np.arange(len(y))
```

## NumPy `.npz` — named arrays

```python
import numpy as np

data = np.load('data.npz')

x = data['x']
y = data['y']
```

`np.load` on `.npz` returns a lazy `NpzFile`; key names come from whatever
was passed to `np.savez(...)` / `np.savez_compressed(...)` when the file
was written.

## Notes on imports

- All four loaders coexist with `import matplotlib.pyplot as plt` from the
  plot template. Unlike `scienceplot-py`, no `import scienceplots` is
  needed — `plt.xkcd()` is built into matplotlib.
- For parquet, pandas needs a backend (`pyarrow` or `fastparquet`). If the
  user's environment doesn't have one, `pd.read_parquet` will raise; that
  is the user's environment to fix, not this skill's concern.
