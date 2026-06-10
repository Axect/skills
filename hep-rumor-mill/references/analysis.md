# Analysis rule: how to turn the rumor mill into a report

This is the mandatory process for producing a job-market report from the rumor mill. It exists
because the numbers alone mislead: a paper count is inflated by large-collaboration membership,
an OpenAlex profile can be a merge of several same-named people, "machine learning + cosmology"
keyword co-occurrence is not interdisciplinary fit, and a single-digit per-institute cohort is
not a statistic. Every honest conclusion comes from reading the actual records, not from the
headline metrics.

## Iron rule: the rumor mill is self-reported and incomplete

Say this in every report, and let it shape the conclusions:

- Offers that nobody reported are absent. The sheet is a lower bound, not a census.
- Per-institute N is usually single digits. Report it as a qualitative signal, never as a rate
  ("3 of the people who reported an offer here had ...", not "people here have ...").
- The same person appears multiple times: one row per institution, and `Offered` is later
  updated to `Accepted` or `Declined`. Deduplicate by person when counting people.
- The analysis is **descriptive**, never predictive. Describe what kind of profile landed where.
  Never tell the user they will or will not get an offer.

## Deep-read before you judge fit

`prm` gives you metrics; it does not give you research fit. For any person or cohort you draw a
conclusion about, read their actual papers (titles, and abstracts via InspireHEP / arXiv) before
characterising their research. The metrics tell you scale; the papers tell you topic. Do not
infer a research theme from `arxiv_cats` or a venue list alone.

## Verify the data-quality flags before quoting numbers

The tool computes these; you must check each one against the record before it goes in a report:

1. **`n_large_collab`** (InspireHEP papers with > 50 authors). When this is a large share of the
   record, the person is on big experimental / collaboration papers and the citation and paper
   counts do not reflect lead-author output. Report `n_first_author` alongside the totals, and
   say so. A theory postdoc with 60 papers and `n_large_collab` 25 is not "more productive" than
   one with 15 first-author papers.
2. **OpenAlex author-conflation.** If `enrich` logged "discarded all N works (... conflation
   suspected)" or "dropped K distant-field works", the person's OpenAlex cluster was unreliable.
   Do not reintroduce those numbers. A person can be InspireHEP-only by design; that is correct,
   not a gap.
3. **`interdisciplinary`.** Treat it as a flag to investigate, not a label to repeat. Confirm by
   looking at the adjacent-field papers (are they real CS/ML/stats work by this person?).
4. **Stale / recycled rows.** A row's `Timestamp` and the `Remarks` can reveal an old or
   speculative entry. Note when a row looks stale.

## What to put in an institute profile

For `prm institute "NAME"`, report all of these (write the honest N first):

1. **N and resolution**: how many people, how many enriched, how many unresolved.
2. **Profile distribution**: median and quartiles of citations, papers, h-index, years-since-PhD.
   Always pair citation/paper medians with the large-collaboration caveat where relevant.
3. **Subfield mix**: the aggregate field mix (hep-th vs hep-ph vs astro vs gr-qc), so the user
   sees whether the institute's offers cluster in their subfield.
4. **Named fellowships**: pull the `Remarks` (Humboldt, Leinweber, James Arthur, ...) and say
   which profiles they went to.
5. **The people**: list them with their headline numbers, so the distribution is auditable.

## What to put in a self-benchmark

For `prm analyze --me RECID`:

1. The user's own metrics, computed by the same pipeline (so it is apples-to-apples).
2. Their percentile on each axis (citations, papers, h-index) within each cohort.
3. A concrete, honest gap note per axis. If the user is interdisciplinary (few InspireHEP papers,
   real ML/stats output), say plainly that an InspireHEP-only comparison undercounts them and
   lean on the OpenAlex/Semantic Scholar cross-disciplinary numbers for the fair comparison.
4. Caveats: small cohort N, self-reported data, descriptive-not-predictive.

## Writing the report

`prm report --year Y [--me RECID]` emits a Korean markdown skeleton: the data-backed tables
(status breakdown, top institutes, cohort distribution, your percentile table) are pre-filled,
and the qualitative sections are left as blank checkboxes. Complete the qualitative sections by
reading the records; do not let the skeleton's numbers stand in for judgment.

- Write in Korean (the user's preference) and follow the global writing style: no em-dashes, no
  hype adjectives, plain direct sentences.
- For each target institute, write the real research themes of the people who got offers, and
  what (if anything) they have in common, grounded in their papers.
- Map named fellowships to the profiles that won them.
- State the gap between the user's profile and each cohort concretely, with the benchmark numbers
  as evidence, and keep it descriptive.
- Where a cohort is too small or too noisy to support a claim, say so instead of inflating it.

## Honesty requirements

- Always print N and how many people were actually resolved / enriched.
- Surface large-collaboration inflation and OpenAlex conflation rather than quoting clean-looking
  but contaminated totals.
- Keep interdisciplinary judgments grounded in the actual adjacent-field papers.
- Descriptive, not predictive. No "you will get an offer" framing, ever.
