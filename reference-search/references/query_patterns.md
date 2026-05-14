# Query Patterns for Reference Search

Use these patterns to turn a rough request into a better query for `reference_search.py`.

## Modes and query shapes

### `background`
Use when the user wants a quick literature snapshot or introductory references.

Patterns:
- `"{topic}"`
- `"{topic} recent advances"`
- `"{topic} overview"`

Bias toward recent papers. Default year cutoff: 2021+.

### `survey`
Use when the user wants review papers, surveys, or broad framing.

Patterns:
- `"{topic} survey"`
- `"{topic} review"`
- `"{topic} literature review"`

Default sort: citation count desc (older highly-cited reviews surface).

### `method`
Use when the user wants references for a method family, technique, or design choice.

Patterns:
- `"{method name}"`
- `"{method name} {domain}"`
- `"{method name} benchmark"`

Include the application domain if the method name is overloaded.

### `baseline`
Use when the user needs canonical comparison targets.

Patterns:
- `"{task} baseline"`
- `"{task} benchmark methods"`
- `"{task} state of the art"`
- `"{named method}"`

Default sort: citation count desc, no year cap. Mix older seminal papers with newer strong baselines.

### `evaluation`
Use when the user needs citations for datasets, benchmarks, or metrics.

Patterns:
- `"{task} benchmark dataset"`
- `"{metric name}"`
- `"{dataset name}"`
- `"{task} evaluation protocol"`

### `claim-support`
Use when the user has a specific statement and wants evidence.

Workflow:
1. Remove hedging or prose.
2. Keep technical nouns and measurable concepts.
3. Search the core concept, not the whole sentence.

Example:
- claim: `"Diffusion models often require many denoising steps at inference time."`
- search candidates:
  - `"diffusion models inference acceleration"`
  - `"diffusion models denoising steps"`
  - `"diffusion sampling efficiency"`

## Domain hints

The router infers domain from the query. For ambiguous topics you can override:

```bash
--domain hep-th       # for SMEFT, gauge theory, holography
--domain cosmology    # for halo / CMB / inflation / large-scale structure
--domain ml           # for transformers, diffusion, optimization
--domain ml-physics   # for PINN, neural operators, ML for physics
```

See `domain_topics.md` for the full list of domain keys and which source each routes to.

## Query refinement heuristics

- If the result set is empty:
  - shorten the query to the main nouns
  - lower `--min-coverage` (try 0.05 or 0)
  - try `--source all`
  - check that auto-domain inference is correct (`--domain none` disables it)
- If the result set is too broad, add one domain qualifier (e.g., "for galaxies", "in HEP").
- If results are trendy but shallow, switch to `--mode survey` to sort by citations.
- If results are old but canonical and you want them, use `--mode baseline` (no year cap).
- If searching for evidence, prefer titles and abstracts that directly mention the phenomenon in question — the matched-sentence quote in the output makes this visible.

## Reading the output

The script already drops low-coverage and low-source-score results and reranks. Still inspect each result:

- **Matched terms**: high count = strong topical fit. Low count (1-2 out of 8+) often means tangential match.
- **Quoted abstract sentence**: if the sentence directly states the phenomenon you searched, the paper is strong support. If the sentence mentions the keywords only in passing, the paper is weak support.
- **Citation count + year**: useful tiebreaker between similar papers.
- **Source**: `inspire` results are high-precision HEP; `openalex` is broad but filtered; `semscholar` includes TLDR summaries.

## Report section mapping

Use these mappings when `research-report` needs literature support:

- `Research Background` → prioritize `background` and `survey`
- `Methodology` → prioritize `method`
- `Results & Visualization` for external comparisons → prioritize `baseline`
- `Validation` when discussing datasets, metrics, or benchmark protocol → prioritize `evaluation`
- isolated statements like trend claims, historical claims, or external factual context → prioritize `claim-support`

For report support, prefer 2-5 strong references over long result dumps.
