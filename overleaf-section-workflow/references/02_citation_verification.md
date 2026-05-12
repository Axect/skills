# Citation verification

For each `\cite{key}` introduced into the draft, verify three things:

1. **The BibTeX entry exists in `ref.bib`** with correct metadata.
2. **The texkey is canonical** (matches the database the paper actually lives in).
3. **The cited paper's content actually supports the body claim** — not just that the metadata is correct.

These three are independent. A correct metadata entry can still be cited for a claim the paper does not make. Catch this before submission.

## Three-source routing

Auto-route by source category:

| Source | What it covers | Endpoint |
|---|---|---|
| **InspireHEP** | HEP / astro-ph / nucl-th / gr-qc | `https://inspirehep.net/api/literature?q=...&format=bibtex` |
| **Google Scholar / openreview / PMLR** | ML / CS / NeurIPS / ICLR / ICML / COLM | `scholarly` Python lib or direct openreview/PMLR URLs |
| **CrossRef** | Older journals (Econometrica, Annals of Math Stat.), publisher textbooks (Springer, Cambridge, Yale UP) | `https://api.crossref.org/works/<DOI>/transform/application/x-bibtex` |

The `bibtex-gen` skill does this routing automatically. Use it for every new reference:

```bash
uv run ~/.claude/skills/bibtex-gen/scripts/bibtex_gen.py "<query>" [--hep | --no-hep]
```

## Common pitfalls

### Pitfall A: Texkey collision (different papers, same authors, same year)

InspireHEP uses keys like `Author:YYYYabc` where the suffix disambiguates papers from the same first author in the same year. Confusing two papers is a real risk.

Example encountered in a real session:
- `Auffinger:2022khh` = "Primordial black hole constraints with Hawking radiation — A review" (arXiv:2206.02672)
- `Auffinger:2022dic` = "Limits on primordial black holes detectability with Isatis" (arXiv:2201.01265)

Both are by Auffinger 2022, but they are different papers. Citing `:khh` for the Isatis paper is wrong.

**Fix**: query InspireHEP by arXiv ID, not by guessed texkey:
```bash
curl -sH "Accept: application/json" \
  "https://inspirehep.net/api/literature?q=arxiv:<id>&fields=control_number,texkeys" \
  | jq '.hits.hits[0].metadata.texkeys'
```

### Pitfall B: Author list mismatch

InspireHEP texkeys are deterministic from the original submission, but author lists can change between submission and publication (added authors, collaboration paper conversion).

Real example:
- `Carr:2017jsz` = arXiv:1705.05567. Locally cited as "Carr, Raccanelli, Riccardi, Rubin" (4 authors). InspireHEP shows the actual paper has authors "Carr, Raidal, Tenkanen, Vaskonen, Veermäe" (5). The 4-author attribution was a hallucination from an earlier reference-search.

**Fix**: re-fetch the bibtex by texkey directly:
```bash
curl -s "https://inspirehep.net/api/literature/<control_number>?format=bibtex"
```

Compare to the local entry. Replace author field if mismatch.

### Pitfall C: Collaboration-paper re-keying

Living Reviews, large GW analyses, and other collaboration papers may be re-keyed by InspireHEP from `FirstAuthor:YYYYxxx` to `Collaboration:YYYYxxx` after publication.

Real example:
- `Bagui:2023jfa` returns no hit. Actual texkey is `LISACosmologyWorkingGroup:2023njw` (arXiv:2310.19857). When citing, use the collaboration form with `author = "Bagui, Eleni and others"` + `collaboration = "LISA Cosmology Working Group"`.

**Fix**: if `texkey:` query returns 0 hits, fall back to `arxiv:<id>` query and update the local texkey.

### Pitfall D: BibTeX entry exists but content doesn't match

The most insidious failure: the entry is correct, but the paper does NOT say what the body claims.

Real example:
- Body claim: "Kühnel & Freese [Kuhnel:2017pwq] proposed QCD soft-EoS as a physical realization of the smooth-cutoff PL family."
- Actual paper: "Constraints on Primordial Black Holes with Extended Mass Functions" — a general constraint reevaluation paper, not specifically about QCD soft EoS.
- This was a hallucination from an earlier reference-search subagent that wrote a non-existent QCD-specific title.

**Fix**: read the actual abstract / introduction of every citation. If it doesn't say what you claim, either remove the citation, or replace with the correct paper (e.g., Jedamzik 1997 [astro-ph/9605152] for QCD soft-EoS).

### Pitfall E: Wrong arXiv ID on otherwise correct entry

Real example:
- `Crooks:2010amoroso` had `eprint = {1005.3310}` in local ref.bib. But the actual Amoroso paper is `arXiv:1005.3274`. `1005.3310` is a completely different paper.
- Caught by `bibtex-gen` round-trip: CrossRef returned an entry by Crooks 2015 with the correct eprint.

**Fix**: always run `bibtex-gen` on each entry as a sanity check. Source-canonical bibtex will reveal the correct eprint.

### Pitfall F: Foundational papers not on any database

Pre-arXiv papers (Hadamard 1902, Page 1976, MacGibbon 1991, etc.) often have no DOI and no InspireHEP/CrossRef entry. They are still citable; use the canonical form from Wikipedia or major secondary references.

For Hadamard 1902:
```bibtex
@article{Hadamard:1902,
  author    = {Hadamard, Jacques},
  title     = {{Sur les probl\`emes aux d\'eriv\'ees partielles et leur signification physique}},
  journal   = {Princeton Univ. Bull.},
  volume    = {13},
  pages     = {49--52},
  year      = {1902},
}
```

`bibtex-gen` will return a different paper (e.g., a 1907 paper) because CrossRef doesn't have the 1902 one. Override and use the canonical Wikipedia-style citation.

## Content verification protocol

For every new citation, after generating the BibTeX, do at least one of:

1. **Read the abstract** via InspireHEP/arXiv. Compare to the body claim.
2. **Read the introduction** of the cited paper if available.
3. **Cross-check with Wikipedia / secondary sources** if a textbook/historical reference.
4. For novelty claims, run `/deep-research` in fact-check mode.

Document the verification in the citation audit. If anything is unclear, surface it to the user before adding the citation.

## Novelty claim verification

For sentences of the form "to our knowledge, no prior work has X", run `/deep-research` in lit-review or fact-check mode against the strongest candidate prior-art papers.

Real example: GBP-as-PBH-MF novelty claim was verified by surveying 16 PBH papers (reviews + template-introducing works) and confirming none used GBP/GB2 as a closed-form four-parameter $\psi(M)$ template. Verdict was ⚠ (correct in strict sense but needs softening: BPL on $\mathcal{P}_\zeta(k)$ exists, must be acknowledged).

Always document the verdict (✓ / ⚠ / ✗) in a per-section audit file.

## Citation audit checklist (per section)

Before declaring a section done, run the following audit:

```text
[ ] Every \cite{key} resolves in ref.bib (no undefined warnings in build)
[ ] Every texkey matches InspireHEP / Scholar canonical form
[ ] Every author list matches the actual paper (no hallucinated authors)
[ ] Every claim matches the cited paper's actual content (not just metadata)
[ ] Novelty claims have been verified via deep-research and are properly hedged
[ ] No "soft attribution" (citation for a claim the paper doesn't make)
[ ] Foundational textbook citations are in canonical form
```
