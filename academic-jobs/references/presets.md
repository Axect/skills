# Field presets

Presets are saved in `~/.local/share/academic-jobs/config.toml`. A preset is a named search
profile:

```toml
default_preset = "physics-ml"

[presets.physics-ml]
keywords       = ["cosmology", "dark matter", "machine learning", "astrophysics"]
position_types = ["postdoc"]      # substring match against the AJO "Position Type" field
countries      = []               # substring match against the institution string
```

- **keywords**: each keyword runs a separate AJO full-text search (title / university /
  department / description). Results are deduped across keywords, and each stored posting
  records which keywords matched it (`matched_keywords`).
- **position_types**: optional. Case-insensitive substring filter on the detail-page
  `Position Type` (e.g. `postdoc` matches "Postdoctoral"; `faculty`/`tenure` for faculty).
- **countries**: optional. Substring filter on the institution string (which includes the
  university name; country is not a separate field on AJO, so match on institution/region text
  you care about, e.g. `Korea`, `Germany`, university names).

## Viewing

```bash
uv run ajo config            # human view
uv run ajo config --json     # full config as JSON
```

## Creating / editing

```bash
# create or overwrite a preset
uv run ajo config --set-preset hep \
  --keywords "high energy theory,phenomenology,collider" \
  --types postdoc \
  --make-default

# clear a filter by passing an empty value
uv run ajo config --set-preset physics-ml --types ""
```

`--set-preset` only updates the fields you pass; omitted fields keep their current values
(a brand-new preset starts with empty lists). `--make-default` points `default_preset` at it.

## Tips
- Keep keyword lists focused. Each keyword is a separate search and every unique candidate
  costs one detail fetch, so very broad presets can hit the per-run detail cap.
- For position types, AJO uses values like `Postdoctoral`, `Tenured/Tenure-track`,
  `Open Rank`, `Fellowship`, `Other`. Substring-match the part that matters (`tenure`, `post`).
