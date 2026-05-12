# Sources

This skill talks to four external services. None require an API key.

## InspireHEP

**Endpoint**: `https://inspirehep.net/api/literature`

```
GET /api/literature?q={query}&format=bibtex&size=1
Accept: application/x-bibtex
```

- `q` accepts the same query DSL InspireHEP's web UI uses, including:
  - `arxiv:2301.00001`
  - `doi:10.1103/PhysRevD.98.030001`
  - `title:"Higgs boson"`
  - free text — also works, just slightly less precise
- `format=bibtex` returns bibtex bytes directly. No need to parse JSON.
- The endpoint is fast and free; rate limits are generous for low-volume
  use. Be polite — the orchestrator sleeps 0.5 s between batch queries by
  default.

**Quirks**:

- For records without an InspireHEP-curated bibtex (rare for HEP papers),
  the endpoint returns an empty body.
- BibTeX keys are `Author:YYYYabc` style (e.g. `Aad:2012tfa`). Do not
  rewrite them — that style is canonical in HEP citation lists and tools
  like JabRef / Overleaf will look them up by that exact key.

## arXiv API

**Endpoint**: `http://export.arxiv.org/api/query`

```
GET /api/query?id_list={arxiv_id}
Accept: application/atom+xml
```

Used only as a **classifier signal** — the orchestrator parses
`<category term="hep-ex"/>` style tags from the Atom response and
short-circuits classification to HEP if any category starts with `hep-`
or `nucl-`. The bibtex itself is never sourced from arXiv directly.

## Google Scholar (via `scholarly`)

**Library**: [`scholarly`](https://pypi.org/project/scholarly/)

```python
from scholarly import scholarly
pub = next(scholarly.search_pubs(query))
bibtex = scholarly.bibtex(pub)
```

- No API key. Google Scholar is the source of truth for non-HEP citation
  styles favored by humanities, biology, social science, ML/AI, etc.
- BibTeX keys are `firstauthorYYYYword` style (e.g. `vaswani2017attention`).
- **Fragility**: Google Scholar aggressively rate-limits scrapers.
  `scholarly` retries internally, but expect occasional `MaxTriesExceeded`.
  When that happens, the orchestrator falls through to CrossRef.
- **Install**: not normally needed. The orchestrator's PEP 723 header
  (`# /// script ... dependencies = ["scholarly"] ///`) makes `uv run`
  provision `scholarly` automatically. The only time you need to install
  it explicitly is when running the orchestrator under bare `python3`
  without `uv`:
  ```bash
  uv add scholarly        # in the project venv
  # or ad-hoc:
  uv pip install scholarly
  ```

## CrossRef

**Endpoint**: `https://api.crossref.org/works/{DOI}/transform/application/x-bibtex`

```
GET /works/{DOI}/transform/application/x-bibtex
Accept: application/x-bibtex
```

- Returns publisher-grade bibtex for any registered DOI. Used as the
  **publisher fallback** when Google Scholar is unavailable or returns no
  hit.
- If the query is free text (not a DOI), the orchestrator first hits
  `https://api.crossref.org/works?query={q}&rows=1` to resolve a DOI, then
  re-enters the bibtex transform endpoint.
- BibTeX keys are DOI-derived (often `Lastname_Year` or
  `Lastname_Year_TitleWord`).

**Quirks**:

- Some publishers register sparse metadata in CrossRef (no `journal`, no
  `pages`, etc.). The orchestrator does not patch these — surface the
  sparse bibtex as-is and let the user fill gaps from the publisher site.
- CrossRef occasionally returns HTTP 200 with a body that is not a bibtex
  entry (rare, but seen for malformed DOIs). The orchestrator checks for a
  leading `@` and treats anything else as a failure.

## Why this routing order?

The user's preference is:

1. **HEP citations should look like every other HEP paper's bibliography.**
   InspireHEP keys and journal abbreviations are the de facto standard in
   particle / nuclear physics; anything else (Scholar, CrossRef) breaks
   that convention.
2. **Non-HEP citations should follow Google Scholar.** Scholar's bibtex
   reflects the form most non-HEP papers actually cite, including
   conference proceedings and preprints.
3. **Publisher (CrossRef) bibtex is only a fallback.** It is the most
   structurally correct but often differs in journal-abbreviation style
   from how a field actually cites the paper.

This matches the user's spoken rule: *"HEP는 InspireHEP, 그 외는 Google
Scholar, Scholar가 부족하면 출판사 bibtex."*

## Upstream: OpenAlex (via `reference-search`)

When the user does not yet know *which* papers to cite, the
**`reference-search` skill** sits upstream of this one. It queries
OpenAlex with topic / claim / section-goal style inputs and returns a
JSON list of candidates with DOI / authors / year / citation count.

`bibtex-gen --from-search <file>.json` consumes that JSON: for each
result, the DOI (if present, parsed from the `https://doi.org/...`
identifier) becomes one query through the normal HEP / Scholar /
CrossRef pipeline. Falls back to the title when DOI is missing.

Why route through HEP/Scholar/CrossRef instead of using OpenAlex's own
metadata as bibtex? Because OpenAlex is built for **discovery and
citation-graph analytics**, not for bibtex fidelity — its records often
miss journal abbreviations, eprint fields, and collaboration tags that
HEP and publisher records have. Treating OpenAlex as a candidate
generator and letting InspireHEP / CrossRef provide the actual bibtex
keeps the citation style canonical for each subfield.
