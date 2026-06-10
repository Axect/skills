# Schema

## SQLite store

Location: `~/.local/share/hep-rumor-mill/rumor.db`. Override with `PRM_DATA_DIR`.

### rumors

One row per rumor-mill entry. The same person appears multiple times (different
institutions, or `Offered` then `Accepted`/`Declined`).

| Column | Type | Meaning |
| ------ | ---- | ------- |
| `year` | INTEGER | Rumor-mill year (PK part) |
| `name` | TEXT | Display name from the sheet (PK part) |
| `recid` | INTEGER | InspireHEP author id parsed from the Inspire link; NULL when no link |
| `inspire_url` | TEXT | Raw URL from the sheet |
| `institution` | TEXT | Free-text institution name (PK part) |
| `status` | TEXT | `Offered`, `Accepted`, `Declined`, or verbatim sheet value (PK part) |
| `remarks` | TEXT | Named fellowship or extra context |
| `timestamp` | TEXT | Verbatim sheet timestamp (PK part; empty string when missing) |
| `country` | TEXT | ISO2 country code inferred from institution |
| `region` | TEXT | Region inferred from institution |
| `first_seen` | TEXT | ISO timestamp of the first time this row was stored |
| `last_fetched` | TEXT | ISO timestamp of the most recent fetch that touched this row |

Primary key: `(year, name, institution, status, timestamp)`.

### authors

One row per resolved person, keyed by InspireHEP recid. `enriched` flips to 1 once
the author's papers have been fetched, so `enrich` can skip already-done people.

| Column | Type | Meaning |
| ------ | ---- | ------- |
| `recid` | INTEGER | InspireHEP author record id (PK) |
| `bai` | TEXT | INSPIRE BAI, e.g. `Mudit.Rai.1` |
| `orcid` | TEXT | ORCID identifier; used to route OpenAlex lookup |
| `openalex_id` | TEXT | OpenAlex author id, filled after OpenAlex lookup |
| `ss_id` | TEXT | Semantic Scholar authorId |
| `display_name` | TEXT | Name from InspireHEP |
| `phd_year` | INTEGER | PhD year from InspireHEP; NULL if unknown |
| `current_inst` | TEXT | Current institution from InspireHEP |
| `current_rank` | TEXT | Current position/rank from InspireHEP |
| `arxiv_cats` | TEXT | Comma-separated arXiv categories, e.g. `hep-th,hep-ph,gr-qc` |
| `advisors` | TEXT | JSON list of `{name, degree_type}` objects |
| `enriched` | INTEGER | 0 until author record and papers are captured; then 1 |
| `fetched_at` | TEXT | ISO timestamp of the most recent author record fetch |

Primary key: `recid`.

### papers

One row per (recid, source, paper_id) triple. `source` distinguishes which API the
record came from. The same physical paper can appear under more than one source;
deduplication happens at metrics time, not storage time.

| Column | Type | Meaning |
| ------ | ---- | ------- |
| `recid` | INTEGER | Author recid (PK part) |
| `source` | TEXT | `inspire`, `openalex`, `orcid` (ORCID-claimed rescue), or `ss` (PK part) |
| `paper_id` | TEXT | Source-specific paper identifier (PK part) |
| `year` | INTEGER | Publication year |
| `venue` | TEXT | Journal or conference name |
| `venue_tier` | TEXT | `A`, `B`, `C`, `preprint`, or empty; filled by metrics |
| `citations` | INTEGER | Citation count from the source |
| `n_authors` | INTEGER | Total number of listed authors |
| `author_pos` | INTEGER | 1-based position of this person in the author list; NULL if unknown |
| `doctype` | TEXT | Document type (article, proceedings, etc.) |
| `field` | TEXT | Primary subject or field of study from the source |
| `title` | TEXT | Paper title |

Primary key: `(recid, source, paper_id)`.

### metrics

One cached aggregate row per recid, computed by `prm/metrics.py:compute_metrics`.
Recomputed each time `enrich` or `analyze` processes a person.

| Column | Type | Meaning |
| ------ | ---- | ------- |
| `recid` | INTEGER | Author recid (PK) |
| `n_papers` | INTEGER | Deduplicated paper count across all sources |
| `n_first_author` | INTEGER | InspireHEP papers where author_pos == 1 |
| `n_large_collab` | INTEGER | InspireHEP papers with more than 50 authors |
| `total_citations` | INTEGER | Sum of citations across deduplicated set |
| `h_index` | INTEGER | Standard h-index over deduplicated citation list |
| `top_venues` | TEXT | JSON: `[[venue, count], ...]` up to 8 entries |
| `field_mix` | TEXT | JSON: `{field: count}` aggregated from all sources |
| `years_since_phd` | INTEGER | current_year minus phd_year; NULL if phd_year unknown |
| `interdisciplinary` | INTEGER | 1 if adjacent papers >= 2 AND >= 15% of record |
| `cross_disc` | TEXT | JSON: `{source: {n_papers, total_citations, h_index, top_venues}}` |
| `computed_at` | TEXT | ISO timestamp of the most recent computation |

Primary key: `recid`.

### meta

Key-value store for internal bookkeeping (currently holds `schema_version`).

| Column | Type | Meaning |
| ------ | ---- | ------- |
| `key` | TEXT | Unique key (PK) |
| `value` | TEXT | Value |

---

## --json output shapes

Every command prints a single JSON object to stdout when `--json` is passed.

### fetch

```json
{
  "year": 2026,
  "total": 312,
  "unique_people": 148,
  "institutions": 67,
  "status_counts": {"Offered": 180, "Accepted": 95, "Declined": 37},
  "with_recid": 289
}
```

### enrich

```json
{
  "requested_unenriched": 95,
  "enriched": 90,
  "failed": [{"recid": 1234567, "error": "connection timeout"}],
  "remaining_unenriched": 5
}
```

### profile

```json
{
  "author": { ...authors row as dict... },
  "metrics": { ...metrics row with top_venues/field_mix/cross_disc decoded from JSON... },
  "papers": [ ...list of papers rows as dicts... ]
}
```

### institute

```json
{
  "institution": "Perimeter Institute",
  "status": "Accepted",
  "year": 2026,
  "n_resolved": 4,
  "n_unenriched": 1,
  "cohort": {
    "n": 4,
    "citations": {"median": 412, "q1": 280, "q3": 610, "min": 120, "max": 890},
    "papers": {"median": 18, "q1": 12, "q3": 24, "min": 9, "max": 31},
    "h_index": {"median": 9, "q1": 7, "q3": 12, "min": 5, "max": 14},
    "years_since_phd": {"median": 3, "q1": 2, "q3": 4, "min": 1, "max": 5},
    "field_mix": {"hep-th": 62, "gr-qc": 8},
    "interdisciplinary_frac": 0.25
  },
  "people": [
    {"recid": 1804701, "name": "Jane Smith", "remarks": "Leinweber Fellow"},
    ...
  ]
}
```

### analyze

```json
{
  "me": { ...metrics dict for the --me recid... },
  "cohorts": [
    {
      "label": "Perimeter Institute",
      "n": 4,
      "n_unenriched": 1,
      "axes": {
        "total_citations": {"me": 310, "percentile": 45.0, "cohort_median": 412},
        "n_papers":        {"me": 15,  "percentile": 38.0, "cohort_median": 18},
        "h_index":         {"me": 8,   "percentile": 40.0, "cohort_median": 9}
      }
    }
  ]
}
```

`percentile` is the fraction of the cohort with a value less than or equal to `me`,
expressed as 0-100. `axes` is null when the cohort has no enriched members.

### report

`report` does not use `--json`. It writes a Korean markdown skeleton to disk and prints
`wrote skeleton: <path>` to stdout. The default output path is
`~/Dropbox/RumorMill/RumorMill_{year}.md`; override with `--out PATH`.
