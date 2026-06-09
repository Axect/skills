# Field presets

Presets are saved in `~/.local/share/academic-jobs/config.toml`. A preset is a named search
profile:

```toml
default_preset = "physics-ml"

[presets.physics-ml]
keywords       = ["cosmology", "dark matter", "machine learning", "astrophysics"]
position_types = ["postdoc"]          # substring match: AJO "Position Type" / InspireHEP ranks
countries      = []                   # substring match: institution string (+ InspireHEP region)
sources        = ["ajo", "inspire"]   # which job boards to search
```

- **keywords**: each keyword runs a separate full-text search on every selected board (AJO
  title / university / department / description; InspireHEP `q`). Results are deduped within
  each board, and each stored posting records which keywords matched it (`matched_keywords`).
- **position_types**: optional. Case-insensitive substring filter applied to the AJO detail-page
  `Position Type` AND the InspireHEP `ranks` (so `postdoc` matches both "Postdoctoral" and
  `POSTDOC`; `faculty`/`tenure` for AJO faculty, `JUNIOR`/`SENIOR`/`PHD` for InspireHEP).
- **countries**: optional. Substring filter on the institution string (and, for InspireHEP, the
  `regions` field). Country is not a separate AJO field, so match on institution/region text you
  care about, e.g. `Korea`, `Germany`, `Europe`, university names.
- **sources**: optional. Which boards to search: any of `ajo`, `inspire`. Defaults to both
  (presets created before this field existed are treated as both).

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
  --sources inspire \
  --make-default

# clear a filter by passing an empty value
uv run ajo config --set-preset physics-ml --types ""

# search only InspireHEP from now on for this preset
uv run ajo config --set-preset physics-ml --sources inspire
```

`--set-preset` only updates the fields you pass; omitted fields keep their current values
(a brand-new preset starts with empty lists and both sources). `--make-default` points
`default_preset` at it. `--sources` rejects unknown board names.

## Tips
- Keep keyword lists focused. Each keyword is a separate search per board, and every unique AJO
  candidate costs one detail fetch, so very broad presets can hit the per-run AJO detail cap.
- For position types, AJO uses values like `Postdoctoral`, `Tenured/Tenure-track`,
  `Open Rank`, `Fellowship`, `Other`; InspireHEP uses `POSTDOC`, `JUNIOR`, `SENIOR`, `PHD`,
  `STAFF`, `VISITOR`. Substring-match the part that matters (`postdoc`, `tenure`, `phd`).
- InspireHEP is HEP / astro focused. For a pure-HEP search, set `--sources inspire`; for a
  broader cross-field search (ML, condensed matter, etc.) keep AJO in the mix.
