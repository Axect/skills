# Usage examples

All examples assume the repo is cloned and the user runs them via `uv`.
The skill never executes itself — these are commands the user (or Claude)
runs from the shell.

## Single query

```bash
# arXiv ID — auto-classified as HEP via arXiv categories, routed to InspireHEP.
uv run bibtex-gen/scripts/bibtex_gen.py arxiv:1207.7214

# DOI — auto-classified by probing InspireHEP. PRD typically classifies as HEP.
uv run bibtex-gen/scripts/bibtex_gen.py 10.1103/PhysRevD.98.030001

# Title — auto-classified by probing InspireHEP. ML paper → Scholar/CrossRef.
uv run bibtex-gen/scripts/bibtex_gen.py "Attention is all you need"
```

## Force routing

```bash
# Force InspireHEP even if the auto-probe missed (e.g. brand-new paper).
uv run bibtex-gen/scripts/bibtex_gen.py --hep "2405.12345"

# Force non-HEP path (Scholar → CrossRef) for an InspireHEP-indexed paper.
uv run bibtex-gen/scripts/bibtex_gen.py --no-hep "Attention is all you need"
```

## Append to a .bib file

```bash
# Append, don't overwrite. Re-running appends duplicates — dedupe separately.
uv run bibtex-gen/scripts/bibtex_gen.py \
  arxiv:1207.7214 \
  10.1038/nature14539 \
  "Attention is all you need" \
  --output paper/refs.bib --verbose
```

## Batch mode

Given `refs.txt`:

```text
# HEP papers
arxiv:1207.7214
arxiv:1207.7235
10.1103/PhysRevD.98.030001

# Non-HEP
Attention is all you need
10.1038/nature14539
```

Run:

```bash
uv run bibtex-gen/scripts/bibtex_gen.py --batch refs.txt --output paper/refs.bib --verbose
```

Each line is processed independently. `#` and blank lines are skipped.
The script sleeps 0.5 s between queries by default (`--sleep 0` to disable
for tiny batches).

## Verbose audit of routing

```bash
uv run bibtex-gen/scripts/bibtex_gen.py --batch refs.txt --verbose > refs.bib
```

stderr will show:

```
-- [1/5] arxiv:1207.7214
   source=inspirehep; reason=arXiv categories include HEP: ['hep-ex']
-- [2/5] arxiv:1207.7235
   source=inspirehep; reason=arXiv categories include HEP: ['hep-ex']
-- [3/5] 10.1103/PhysRevD.98.030001
   source=inspirehep; reason=InspireHEP returned a match
-- [4/5] Attention is all you need
   source=scholar; reason=InspireHEP returned no match
-- [5/5] 10.1038/nature14539
   source=crossref; reason=InspireHEP returned no match
```

stdout (or `refs.bib`) holds only the bibtex entries.

## When Scholar is missing

The orchestrator's PEP 723 header declares `scholarly` as a dependency, so
`uv run bibtex-gen/scripts/bibtex_gen.py …` auto-installs it into an
ephemeral cached env on first run. No `uv add` / `uv pip install` step
needed.

If you invoke the orchestrator with bare `python3` (no `uv`), `scholarly`
may be missing. In that case the orchestrator silently falls through to
CrossRef — non-HEP queries still resolve, just with publisher-style keys
(`Lastname_Year`) instead of Scholar style (`firstauthorYYYYword`). HEP
queries are unaffected.

If you want `scholarly` available outside of `uv run` for some reason
(e.g. running under plain `python3`), install it into the active env:

```bash
uv add scholarly                # in the project that runs the skill
# or, ad-hoc:
uv pip install scholarly
```

## Failure handling

The orchestrator never fabricates bibtex. If all sources return nothing,
the query is listed on stderr and the exit code is 2. Typical fixes:

- Add a DOI to the query.
- Force the other routing with `--hep` or `--no-hep`.
- For a paywalled paper with no DOI, fetch the publisher's bibtex
  manually and paste it in.

## Inside an existing paper repo

If the user is working on a paper draft, a common pattern is to maintain a
`refs.txt` queue and a `refs.bib` output:

```bash
# Add a new reference to the queue.
echo "10.1088/1475-7516/2024/01/001" >> refs.txt

# Re-run for new entries only — dedupe by hand or with `bibtool`.
uv run bibtex-gen/scripts/bibtex_gen.py --batch refs.txt --output refs.bib --verbose
```

The skill does not implement dedupe. Use `bibtool -d`, `biber --tool`, or
`bib-dedupe` if you need it.
