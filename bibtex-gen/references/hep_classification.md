# HEP classification

The skill auto-classifies each query as HEP or non-HEP before fetching
bibtex. The rule is intentionally simple:

> **A query is HEP iff InspireHEP returns at least one match for it.**

That's the only authoritative test — InspireHEP curates HEP literature,
so presence is a strong positive signal. Absence is treated as a strong
negative signal even though it can produce occasional false negatives
(some collaboration notes or HEP-relevant ML papers are missing from
InspireHEP).

## Signal stack

The orchestrator applies signals in this order:

1. **`--hep` / `--no-hep` override** — explicit user intent always wins.
   Use these when the user has said something like "this is HEP", "이건
   ML 논문이야", "이거 천체물리 페이퍼", etc.
2. **arXiv category** (for arXiv-ID inputs only) — fetch
   `http://export.arxiv.org/api/query?id_list={id}` and look at
   `<category term="...">` tags. Any category starting with `hep-` or
   `nucl-` short-circuits to HEP.
3. **InspireHEP probe** — query InspireHEP with the raw input. If at
   least one match is returned, classify as HEP. Otherwise non-HEP.

The probe is the same call the HEP path would make anyway, so HEP queries
pay no extra cost — the orchestrator reuses the response.

## Why probe instead of using keyword heuristics?

Keyword-based heuristics ("title contains 'Higgs'", "abstract mentions
'supersymmetry'") are brittle:

- A particle-physics paper titled "Dark matter from neutrino interactions"
  has no obvious HEP cue.
- A neuroscience paper titled "Higgs Boson Search using neural networks" is
  classified incorrectly.
- The vocabulary of HEP overlaps with cosmology, AMO physics, and several
  ML/HEP cross-disciplinary subfields.

InspireHEP itself has already solved this classification problem
internally. Re-using its index by probing is more robust than reproducing
its taxonomy.

## False negatives

InspireHEP may not index:

- Very recent papers (1–2 day indexing lag for arXiv).
- HEP-adjacent ML / methodology papers that did not propagate to
  InspireHEP yet.
- Some conference proceedings.

If the user expected HEP but the skill picked Scholar / CrossRef, pass
`--hep` explicitly — that bypasses the probe and forces InspireHEP. If
InspireHEP still returns nothing, the orchestrator transparently falls
through to the non-HEP path with a `! InspireHEP returned no bibtex
despite HEP classification` note on stderr.

## False positives

InspireHEP occasionally indexes:

- Cosmology / astrophysics papers that intersect HEP topics.
- Some general-relativity papers.
- A small set of mathematical-physics papers.

Treating these as HEP is usually still correct — they will cite, and be
cited by, HEP papers. If the user dislikes a specific classification, the
`--no-hep` override is a one-liner.

## When to override

| Situation                                                       | Flag        |
|-----------------------------------------------------------------|-------------|
| User says "HEP papers" / "장 인용" / "particle physics"         | `--hep`     |
| User wants InspireHEP style on a borderline case                | `--hep`     |
| User says "ML paper" / "biology" / "non-HEP" / "출판사 bibtex"  | `--no-hep`  |
| Mixed batch — pass nothing, let auto-classification decide      | (no flag)   |

For mixed batches, the per-query reason is printed when `--verbose` is
on, so the user can audit the routing after the fact.
