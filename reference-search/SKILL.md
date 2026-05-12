---
name: reference-search
description: Search and curate academic references for a topic, claim, section, baseline, method, evaluation need, or report section using OpenAlex, with markdown-ready summaries and optional save paths. Use when the user asks for papers, references, citations, related work, supporting literature, survey papers, background sources, baseline citations, evidence to support a report or research claim, or wants section-by-section citation help while drafting `report.md`.
---

# Reference Search

Use this skill to find and curate literature for research writing, report support, method comparison, or quick topic familiarization.

It is especially useful as a companion to `research-report` when a report section needs external literature support beyond local experiment artifacts.

## Inputs to confirm

Ask only for what is missing:
- search target: topic, claim, section goal, or method name
- desired use mode: `background`, `survey`, `method`, `baseline`, `evaluation`, or `claim-support`
- if this is for a report, which section needs support and what kind of support is missing
- time window or recency preference
- preferred result count
- whether the user wants a file saved or inline output

If the user provides only a broad topic, default to `background` mode.

## Default behavior

- Search OpenAlex first.
- Prefer recent papers for `background`, `evaluation`, and `claim-support` unless the user asks for classics.
- Prefer review or survey papers in `survey` mode.
- Prefer seminal and widely cited papers in `baseline` mode.
- Return concise, markdown-ready results with enough metadata to cite or follow up.
- Do not fabricate claims about paper contents beyond title, metadata, and retrieved abstract text.

## Report-oriented workflow

When the user is drafting or revising a report:

1. Identify the target section and the citation role.
2. Choose one primary mode for that section:
   - `Research Background` -> `background` or `survey`
   - `Methodology` -> `method`
   - `Results & Visualization` comparison paragraphs -> `baseline`
   - `Validation` benchmark or protocol discussion -> `evaluation`
   - any isolated factual statement -> `claim-support`
3. Turn the section need into a compact query rather than searching the whole paragraph verbatim.
4. Return only the strongest 2-5 references unless the user asks for a long list.
5. If saving notes for a report, prefer a section-scoped filename such as:
   - `references/background_references.md`
   - `references/method_references.md`
   - `references/validation_references.md`
6. Make the output easy to transplant into prose by emphasizing why each source matters.

## Recommended workflow

1. **Clarify the search intent**
   - Map the request into one of the supported modes.
   - If the user gives a sentence or claim, extract the core technical concepts before searching.
   - If the user mentions a report section, infer the citation role:
     - introduction or context -> `background`
     - related work overview -> `survey`
     - method justification -> `method`
     - comparison target -> `baseline`
     - benchmark or metrics discussion -> `evaluation`
     - evidence for a specific statement -> `claim-support`

2. **Choose a query and filter**
   - Use the guidance in `references/query_patterns.md`.
   - Start with a narrow query that includes the main concepts.
   - Default filters by mode:
     - `background`: `publication_year:>2021,type:article|review`
     - `survey`: `publication_year:>2019,type:review|article`
     - `method`: `publication_year:>2020,type:article|review|preprint`
     - `baseline`: `type:article|review|preprint`
     - `evaluation`: `publication_year:>2020,type:article|review|dataset`
     - `claim-support`: `publication_year:>2021,type:article|review|report`
   - Default sort by mode:
     - `survey`, `baseline`: `cited_by_count:desc`
     - otherwise: `relevance_score:desc`

3. **Run the search script**
   - Use:
     ```bash
     python reference-search/scripts/openalex_search.py \
       "{query}" \
       --mode {mode} \
       --filter "{filter}" \
       --sort "{sort}" \
       --limit {limit} \
       --format md
     ```
   - If the user wants structured downstream processing, use `--format json`.

4. **Broaden when results are sparse**
   - If fewer than 3 relevant results appear:
     - simplify the query to the main nouns
     - relax year filter to `publication_year:>2018`
     - expand types to include `preprint` or `report`
     - retry once without a type restriction if still sparse
   - State when the search had to be broadened.

5. **Curate, do not just dump results**
   - For each selected paper, provide:
     - title
     - year
     - first author or short author string
     - citation count
     - DOI or OpenAlex URL
     - 1–2 line relevance note grounded in the query and abstract
   - Then add a short synthesis:
     - dominant themes
     - one recommended starting paper
     - one gap or uncertainty if the search looks noisy or weak

6. **Format for the user’s context**
   - For a general literature request, return a numbered shortlist.
   - For report-writing support, group results under headings like `Background References`, `Baseline References`, or `Evidence for Claim`.
   - For claim support, explicitly say whether the retrieved references look like strong, partial, or weak support.
   - For section support, end with a short `How to use in the report` note describing where the references belong and what they can support.

## Output template

Use this structure unless the user asks for something else:

```markdown
## Reference Search: "{query}"

**Mode**: {mode}  
**Filter**: {filter}  
**Sort**: {sort}  
**Results reviewed**: {count}

### Recommended references
1. **Paper title** ({year}, cited: {citations})
   - Authors: {authors}
   - DOI/URL: {identifier}
   - Why it matters: {relevance note}

### Synthesis
- Dominant themes: ...
- Best starting point: ...
- Caveat: ...
- How to use in the report: ...
```

## Save behavior

If the user asks to save the results, write the formatted markdown to the requested path after reviewing the results. If the path is relative, resolve it from the current working directory.

## Downstream: producing bibtex from results

When the user wants a real `.bib` file (not just a curated markdown shortlist), pair this skill with the **`bibtex-gen`** companion. The flow is:

1. Run this skill with `--format json` and save the output:
   ```bash
   uv run reference-search/scripts/openalex_search.py \
     "{query}" --mode {mode} --limit {limit} --format json \
     > /tmp/{slug}.json
   ```
2. Pipe that JSON into `bibtex-gen`:
   ```bash
   uv run bibtex-gen/scripts/bibtex_gen.py \
     --from-search /tmp/{slug}.json \
     --output paper/refs.bib --verbose
   ```

`bibtex-gen` extracts each result's DOI from `identifier` and routes it through HEP (InspireHEP) → non-HEP (Google Scholar → CrossRef) so that HEP papers land with `Author:YYYYabc` keys and non-HEP papers land with Scholar / CrossRef keys. OpenAlex is **discovery only**; canonical bibtex always comes from the field-appropriate authoritative source.

If the user asks for `references` *and* a `.bib` in the same step, run both skills back-to-back rather than fabricating bibtex from the OpenAlex metadata directly.

## Resources

- `scripts/openalex_search.py`: OpenAlex query helper with markdown and JSON output.
- `references/query_patterns.md`: query construction heuristics and mode examples.
- `research-report`: companion reporting skill that can consume section-level reference support from this skill.
- `bibtex-gen`: companion skill that turns this skill's JSON output into a real `.bib` file (`bibtex-gen --from-search <file>.json`). Use it whenever the user wants citations materialized, not just curated.

After creating or updating this skill, suggest starting a new session so the new skill is discoverable from session start.
