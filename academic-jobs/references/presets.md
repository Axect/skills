# Field presets

Presets are saved in `~/.local/share/academic-jobs/config.toml`. A preset is a named search
profile:

```toml
default_preset = "physics-ml"

[presets.physics-ml]
keywords            = ["cosmology", "dark matter", "machine learning", "astrophysics"]
position_types      = ["postdoc"]                         # substring match: AJO "Position Type" / InspireHEP ranks
countries           = []                                  # substring match: institution string (+ InspireHEP region)
sources             = ["ajo", "inspire"]                  # which job boards to search
preferred_countries = [["KR", "DE"], ["JP", "HK", "GB", "US"]]  # soft: reorders results, tier 0 first
excluded_countries  = ["IN", "IL", "Middle East"]         # hard: drops matching postings at fetch time
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
- **preferred_countries**: optional. An ordered list of tiers, each tier a list of country/region
  selectors. Tier 0 (the first inner list) is most preferred. This is a soft filter: it only
  reorders fetch results so that lower-tier postings appear first; nothing is dropped. Each
  fetched posting gets a `pref_tier` integer (0 = top tier; postings matching no tier get the
  highest number and sort last). Selectors accept three forms: an ISO 3166-1 alpha-2 code
  (`"KR"`, `"DE"`), a country name (`"Korea"`, `"Germany"`), or a region alias (`"Europe"`,
  `"Asia"`, `"North America"`, `"South America"`, `"Oceania"`, `"Africa"`, `"Middle East"`;
  short aliases: `"EU"`, `"APAC"`, `"MENA"`). Country/region is inferred from the institution
  string by the built-in classifier (`ajo/classify.py`); for InspireHEP the API region field
  is used as a fallback.
- **excluded_countries**: optional. A flat list of country/region selectors (same three forms
  as above). This is a hard filter: any posting whose inferred country or region matches is
  dropped at fetch time and counted in `stats.per_source.<board>.excluded`. Composes with
  `countries` (include filter) and `preferred_countries` (ordering): you can include via
  `countries`, drop via `excluded_countries`, and sort via `preferred_countries`.

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

# set preferred tiers (';' separates tiers, ',' separates entries within a tier)
# and drop postings from specific countries/regions
uv run ajo config --set-preset physics-ml \
  --preferred "KR,DE; JP,HK,GB,US" \
  --excluded "IN,IL,Middle East"

# clear preferred_countries without touching other fields
uv run ajo config --set-preset physics-ml --preferred ""
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
- For `preferred_countries` and `excluded_countries`, prefer ISO2 codes (`KR`, `DE`) or region
  aliases (`Europe`, `APAC`) over free-form country names. The classifier handles all three
  forms, but codes and aliases are unambiguous and match more consistently. Remember:
  `excluded_countries` drops postings at fetch time (hard), while `preferred_countries` only
  reorders them (soft) and never removes anything.
