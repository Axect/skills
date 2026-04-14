# Query Patterns for Reference Search

Use these patterns to turn a rough request into a better OpenAlex query.

## Modes and query shapes

### `background`
Use when the user wants a quick literature snapshot or introductory references.

Patterns:
- `"{topic}"`
- `"{topic} recent advances"`
- `"{topic} overview"`

Bias toward recent papers.

### `survey`
Use when the user wants review papers, surveys, or broad framing.

Patterns:
- `"{topic} survey"`
- `"{topic} review"`
- `"{topic} literature review"`

Prefer `type:review|article` and sort by citations.

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

Mix older seminal papers with newer strong baselines.

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

## Query refinement heuristics

- If the result set is empty, shorten the query.
- If the result set is too broad, add one domain qualifier.
- If results are trendy but shallow, sort by citations.
- If results are old but canonical, add a recency filter only after identifying seminal papers.
- If searching for evidence, prefer titles and abstracts that directly mention the phenomenon in question.

## Reading the results

When curating references, prefer papers with at least one of:
- title strongly aligned with the query
- abstract language that directly matches the user need
- high citation count for canonical references
- review-paper framing for survey requests
- recent publication years for fast-moving topics

## Report section mapping

Use these mappings when `research-report` needs literature support:

- `Research Background` -> prioritize `background` and `survey`
- `Methodology` -> prioritize `method`
- `Results & Visualization` for external comparisons -> prioritize `baseline`
- `Validation` when discussing datasets, metrics, or benchmark protocol -> prioritize `evaluation`
- isolated statements like trend claims, historical claims, or external factual context -> prioritize `claim-support`

For report support, prefer 2-5 strong references over long result dumps.
