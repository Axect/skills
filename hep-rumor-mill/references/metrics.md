# Metrics

## Per-person metrics (compute_metrics)

All metrics are computed by `prm/metrics.py:compute_metrics` and cached in the `metrics`
table. They are recomputed each time `enrich` or `analyze` processes a person.

| Key | Meaning |
| --- | ------- |
| `n_papers` | Total distinct papers across all sources, deduplicated by normalized title + year. InspireHEP is preferred when two sources share the same paper. |
| `n_first_author` | Count of InspireHEP papers where `author_pos == 1`. Only InspireHEP provides reliable author-position data. |
| `n_large_collab` | InspireHEP papers with more than 50 listed authors. These inflate the headline paper and citation counts; a high value means the record reflects collaboration membership, not lead-author output. Pair with `n_first_author`. |
| `total_citations` | Sum of citations across the deduplicated paper set. |
| `h_index` | Standard h-index computed over the deduplicated citation list. |
| `top_venues` | JSON list of `[venue, count]` pairs, up to 8 most-frequent non-empty venues in the deduplicated set. |
| `field_mix` | JSON object `{field: count}` aggregated from all source papers before deduplication. |
| `years_since_phd` | `current_year - phd_year` from the InspireHEP author record. Null if PhD year is unknown. |
| `interdisciplinary` | 1 if either (a) the InspireHEP author `arxiv_categories` include a non-physics category (`cs`, `eess`, `stat`, `q-bio`, `econ`, `q-fin`), or (b) at least 2 papers are adjacent-field AND those are at least 15% of `n_papers`; 0 otherwise. See the rule below. |
| `cross_disc` | JSON object keyed by source (`openalex`, `orcid`, `ss`). Each entry holds `{n_papers, total_citations, h_index, top_venues}` for that source's raw papers (before deduplication with InspireHEP). The `orcid` source is the ORCID-claimed-works rescue used when an OpenAlex ORCID cluster is discarded as conflated. Its arXiv-only works have no DOI, so their citations are backfilled by a Semantic Scholar title match (a conservative floor, lower than Google Scholar); works Semantic Scholar does not index stay at 0. |

## Venue tier table

Tiers are assigned by `venue_tier()` via case-insensitive substring matching against
`JOURNAL_TIERS` in `prm/metrics.py`. This is an editable opinion seeded with hep-th/ph
convention. Edit the dict to change it.

**Tier A**
- Phys.Rev.Lett. / Physical review letters
- Nature Physics, Nature Communications, Nature, Science
- Phys.Rev.X, Rev.Mod.Phys.
- NeurIPS / Conference on Neural Information Processing Systems
- ICML / International Conference on Machine Learning
- ICLR / International Conference on Learning Representations

**Tier B**
- JHEP / Journal of High Energy Physics
- Phys.Rev.D / Physical review. D
- JCAP / Journal of Cosmology and Astroparticle Physics
- Eur.Phys.J.C, Nucl.Phys.B, Phys.Lett.B
- SciPost Phys.
- Astrophys.J., Mon.Not.Roy.Astron.Soc.
- Class.Quant.Grav., Phys.Rev.Res.

**preprint** - venue is null/empty or contains `arxiv` or `arxiv.org`.

**Tier C** - anything that does not match A or B and is not a preprint.

## Field classification (field_class)

Each paper is classified by `field_class(field, venue)` into one of four categories.

| Class | Meaning | Examples |
| ----- | ------- | ------- |
| `physics` | Physics-family field; never triggers interdisciplinary. | hep-th, hep-ph, gr-qc, astro-ph, cosmology, "Physics and Astronomy" (OpenAlex coarse label) |
| `adjacent` | Plausible genuine cross-over for a HEP person. This is the interdisciplinary signal. | computer science, machine learning, artificial intelligence, statistics, data science, information science, computational; also ML-flagship venues (NeurIPS, ICML, ICLR) regardless of field label. Mathematics and mathematical physics are deliberately NOT adjacent: math / math-ph are standard for formal hep-th and would over-flag ordinary theorists. |
| `distant` | Almost always an OpenAlex author-conflation artefact (a different same-named person merged into the cluster). Dropped before metrics. | biology, biochemistry, chemistry, crystallography, medicine, neuroscience, economics, econometrics, materials science, environmental science, geology, psychology, social science, sociology, linguistics, agriculture, veterinary, dentistry, nursing |
| `unknown` | Field string is null or does not match any token. |  |

## Interdisciplinary rule

A person is flagged `interdisciplinary = 1` when EITHER signal fires:

1. **Author categories.** The InspireHEP author record's `arxiv_categories` include a
   non-physics category: `cs`, `eess`, `stat`, `q-bio`, `econ`, or `q-fin`. This is robust even
   for a sparse publication record (a physics + ML person with only a couple of HEP papers still
   gets caught). `math` and `math-ph` are excluded on purpose, since they are normal for formal
   hep-th and would over-flag ordinary theorists.
2. **Adjacent papers.** In the deduplicated paper set, at least 2 papers are classified
   `adjacent` AND they represent at least 15% of `n_papers`.

Distant-field works are dropped at the `enrich` stage (conflation noise) and therefore cannot
inflate this flag. A single stray ML paper on an otherwise pure HEP record does not trigger it.

## Cohort statistics (cohort_stats)

`cohort_stats(metric_dicts)` summarizes a list of per-person metrics dicts. Returns:

| Key | Meaning |
| --- | ------- |
| `n` | Number of people in the cohort. |
| `citations` | `{median, q1, q3, min, max}` over `total_citations`. |
| `papers` | Same shape over `n_papers`. |
| `h_index` | Same shape over `h_index`. |
| `years_since_phd` | Same shape over `years_since_phd` (nulls excluded). |
| `field_mix` | Aggregated `{field: count}` summed across all cohort members. |
| `interdisciplinary_frac` | Fraction of cohort members with `interdisciplinary == 1`. |

Quartiles use simple index-based selection: Q1 = index `n//4`, Q3 = index `(3*n)//4`.
