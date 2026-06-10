# hep-rumor-mill

Pulls the HEP-theory postdoc rumor mill (the public Google Sheet at
`sites.google.com/site/postdocrumor`) for a given year, resolves each offer-holder's
publication record from external APIs, and lets you study what kind of profile landed
where. Two first-class uses: institute intelligence (what do the people who got offers
at a given place look like?) and self-benchmarking (how does your own record compare to
the accepted cohort?).

## Data sources

- **InspireHEP** (primary) - HEP papers, citations, PhD year, ORCID, advisors.
- **OpenAlex** (cross-disciplinary augmentation for everyone with an ORCID) - catches
  ML/CS/stats venues (NeurIPS, ICML, ICLR, journals) that InspireHEP does not index.
- **Semantic Scholar** (name-based fallback when there is no ORCID) - used for h-index
  cross-check and papers for people who lack an ORCID.

## Quickstart

```bash
# 1. Pull the rumor sheet for 2026 and store it.
uv run prm fetch --year 2026

# 2. Resolve publication records for accepted people.
uv run prm enrich --year 2026 --status Accepted

# 3. Explore.
uv run prm institute "Perimeter Institute" --status Accepted
uv run prm analyze --me 1804701
```

Every command accepts `--json` for machine-readable output.

## Local database

`~/.local/share/hep-rumor-mill/rumor.db` (SQLite). Override the directory with the
`PRM_DATA_DIR` environment variable.

## Honesty note

The rumor mill is self-reported and incomplete. Offers that were never posted are simply
absent, per-institute sample sizes are usually single digits, and the same person may
appear multiple times (one row per institution). Treat results as a qualitative signal,
not a statistic.
