# Lessons log

Concrete incidents from the JCAP §2 drafting session that motivated each skill rule. Use this as a reference when explaining to the user why a rule exists.

## Writing-style incidents

### Incident: Emdashes everywhere

Symptom: Initial Korean drafts contained em-dashes (`—`) as paragraph-internal punctuation, used like "Z — Y" or "(a)—(c)".

Diagnosis: Em-dashes are a well-known AI-writing-style marker. Native Korean physics writing uses periods and commas; native English physics writing rarely uses em-dashes in body text.

Fix: scan with `grep -cP "[\x{2013}\x{2014}]"` after every edit. Use periods, commas, parens.

### Incident: Forward references in background section

Symptom: §2.3 closing paragraph said "본 연구의 §\ref{sec:inverse} 에서 다루는 DeCLA 사후분포 구성은, 결정론적 역연산자가 아닌, 학습된 decoder-conditional Laplace 근사 위에 anchored TTR refinement 를 얹어 이 불안정성을 정량적으로 통제한다."

Diagnosis: This is a §2 paragraph previewing §5 content. Background sections must stand alone.

Fix: Remove the preview. Replace with a single declarative sentence: "Regularisation is required to obtain a usable solution."

### Incident: "표준이다" absolute claim

Symptom: §2.1 said "HAZMA 가 표준이다" / "HDMSpectra 가 표준이다".

Diagnosis: Physics writing prefers hedged claims; "is the standard" is too absolute.

Fix: "표준으로 여겨진다" / "is the conventional choice".

### Incident: Tutorial-tone closing

Symptom: §2.3 closing originally said "이러한 불안정성이 *왜 단순한 직접 역산이 통하지 않으며* 어떤 형태의 정규화가 본질적으로 필요한지의 근원이다."

Diagnosis: Tutorial / rhetorical-question tone, inappropriate for paper body.

Fix: Replace with declarative statement: "Stability requires accepting bias (regularisation)."

### Incident: Non-standard ML jargon import

Symptom: User suggested replacement: "biased solver 가 필요하다" instead of "정규화가 필요하다".

Evaluation: "Biased solver" is operationally accurate (bias-variance tradeoff) but NOT a standard term in inverse-problem literature. Standard term is "regularization" (Tikhonov, Engl, Kress).

Fix: combine both — "stability 를 얻는 대신 bias 를 받아들이는 정규화 (regularisation)". User's operational framing preserved; standard term added for referee-defensibility.

Meta-lesson: do not silently apply user-suggested wording. Evaluate first.

## Citation incidents

### Incident: Hallucinated author list

Symptom: `Carr:2017jsz` locally cited as "Carr, Raccanelli, Riccardi, Rubin" (4 authors).

Diagnosis: Reference-search subagent (earlier in session) hallucinated the author list. Actual paper has 5 authors: Carr, Raidal, Tenkanen, Vaskonen, Veermäe.

Fix: re-verify via InspireHEP API with arXiv ID:
```bash
curl -sH "Accept: application/json" "https://inspirehep.net/api/literature?q=arxiv:1705.05567" \
  | jq '.hits.hits[0].metadata.authors[].full_name'
```

Meta-lesson: never trust an earlier subagent's metadata summary. Verify directly.

### Incident: Wrong texkey (collision)

Symptom: `Auffinger:2022khh` cited locally as "Isatis paper". Actually `:khh` is the *review* paper (arXiv:2206.02672), not the Isatis tool paper (arXiv:2201.01265, texkey `Auffinger:2022dic`).

Diagnosis: same first author, same year, different paper. The reference-search subagent guessed the texkey without verification.

Fix: query by arXiv ID, get the canonical texkey, replace local key.

### Incident: Re-keyed collaboration paper

Symptom: `Bagui:2023jfa` returns 0 hits on InspireHEP. Actual texkey is `LISACosmologyWorkingGroup:2023njw` (arXiv:2310.19857), with author = "Bagui, Eleni and others" + collaboration tag.

Diagnosis: Living Reviews paper was re-keyed by InspireHEP after publication as a collaboration paper.

Fix: re-fetch via arXiv ID, update key and entry format.

### Incident: arXiv ID typo

Symptom: `Crooks:2010amoroso` had `eprint = {1005.3310}`. Actual Amoroso paper is `arXiv:1005.3274` (Crooks 2010, "The Amoroso distribution"). `1005.3310` is a different paper entirely.

Diagnosis: Single-character typo introduced when manually constructing the BibTeX.

Fix: run `bibtex-gen` on each entry as a sanity check. CrossRef round-trip will reveal the correct eprint.

### Incident: Citation for a claim the paper doesn't make

Symptom: `Kuhnel:2017pwq` cited for "QCD soft-EoS as a physical realisation of smooth-cutoff PL".

Diagnosis: The actual paper title is "Constraints on Primordial Black Holes with Extended Mass Functions" — a general constraint methodology paper, not specifically about QCD soft-EoS. The "QCD soft-EoS" attribution was a hallucination from the earlier reference-search subagent.

Fix: read the actual abstract, then remove the misattribution. The correct reference for QCD soft-EoS → PBH is Jedamzik 1997 (astro-ph/9605152).

### Incident: Pre-arXiv paper not on CrossRef

Symptom: `Hadamard:1902` (Princeton Univ. Bull. 13, 49). CrossRef returns a *different* Hadamard paper (1907 in Journal de Physique).

Diagnosis: 1902 paper predates CrossRef indexing.

Fix: keep the canonical Wikipedia-style BibTeX entry, do not let `bibtex-gen` override.

## Plot incidents

### Incident: Legend overlapping data

Symptom: `family_overview.png` had legend at upper right (`loc="best"`), overlapping with curves.

Diagnosis: All 5 distributions peak in the same region; "best" location ends up among the data.

Fix: explicit outside placement:
```python
ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5))
```

### Incident: Wasted plot area

Symptom: `family_overview` with `xlim=(1e13, 1e22)` showed distributions squeezed into leftmost 30% of plot. Right 70% empty.

Diagnosis: xlim ranges across 9 decades but distributions only span ~3 decades.

Fix: tighten `xlim=(1e13, 1e18)`. Smooth-PL tail extends slightly beyond but gets clipped — acceptable.

### Incident: Title on plot

Symptom: Initial plot scripts included `ax.set_title(...)`.

Diagnosis: User mandate: no titles on data plots (titles go in figure captions).

Fix: remove all `set_title` calls. Information goes in caption only.

### Incident: Per-family parameter sweeps in main text

Symptom: Five per-family parameter-sweep plots (LogN with $\sigma$ variations, Pareto with $\alpha$ variations, etc.) included in main §2.2.

Diagnosis: These are reference figures, not narrative-load-bearing. They duplicate the family_overview content but at higher detail.

Fix: move all per-family parameter sweeps to Appendix E (Dataset Generation Details). Keep only the family_overview in main body.

## Section-narrative incidents

### Incident: Forgotten contribution claim

Symptom: GBP introduced in §2.2 as if it were a standard PBH-MF family.

Diagnosis: User pointed out: "Generalized Beta Prime은 우리가 발견한 기여인데?" — GBP-as-PBH-MF is the paper's contribution.

Fix: rewrite §2.2 to frame three families (LogN, PL, CC) as "canonical PBH literature", then unify via Stacy, then identify Stacy's limitation, then introduce GBP as the contribution.

Meta-lesson: contribution claims must be explicitly marked. Don't let a contribution slide into the section as if it were prior work.

### Incident: Misattributed motivation

Symptom: §2.2 attributed Gow et al. CC3 as "Smooth Power-Law unconstraining" motivation.

Diagnosis: Wrong paper cited (`Gow:2020bzo` is constraint methodology; CC3 is in `Gow:2020cou`). Also wrong motivation (CC3 was for fast analytic approximation of numerical $\psi(M)$, not Smooth-PL unconstraining).

Fix: correct paper + correct motivation:
> "Gow, Byrnes & Hall~\cite{Gow:2020cou} ... 표준 log-normal template 으로 정확히 적합되지 않는다는 점을 지적하며, ... CC3 를 MCMC inference 용 수치 ψ(M) 의 해석적 근사로 제안했다."

### Incident: Abrupt subsection appearance

Symptom: "다봉 분포의 본질적 한계" paragraph appeared as a bold-headed section at the end of §2.2, after a figure, disconnected from the GBP narrative.

Diagnosis: Bold-headed paragraphs should support the section narrative. This one was tacked on.

Fix: absorb the multimodal acknowledgement into the GBP closing sentence: "단 GBP 도 단봉 family 이므로 다봉 $\psi(M)$ 은 직접 표현하지 못한다."

## Build incidents

### Incident: Built in sync folder

Symptom: Ran `pdflatex main.tex` inside `~/zbin/OverLeaf/OSPREY/JCAP/`. Created main.aux, main.log, main.pdf, etc. inside the Overleaf sync folder.

Diagnosis: Cardinal rule violation. Build artefacts would sync to Overleaf and pollute the remote.

Fix: clean up the artefacts in the sync folder immediately:
```bash
cd ~/zbin/OverLeaf/OSPREY/JCAP
rm -f main.aux main.bbl main.blg main.log main.out main.pdf main.toc
```
Then build via `bash <PROJECT>_build/build_main.sh` (out-of-tree).

User reaction: "build를 여기서 하면 어떻게해! 여긴 동기화 폴더야!" Lesson learned the hard way.

### Incident: Placeholder bibliography

Symptom: All `\cite{}` undefined despite ref.bib being correct.

Diagnosis: `main.tex` had placeholder `\begin{thebibliography}{99} \bibitem{a} ... \end{thebibliography}` instead of `\bibliography{ref}`.

Fix: replace with `\bibliographystyle{JHEP}` + `\bibliography{ref}`.

### Incident: `\toprule` undefined

Symptom: First successful build attempt failed with "Undefined control sequence \toprule".

Diagnosis: booktabs not loaded.

Fix: add `\usepackage{booktabs}` to preamble.

## Workflow incidents

### Incident: Sonnet subagent attempt

Symptom: Standard lab convention (in `~/.claude/CLAUDE.md`) says "translate via Sonnet subagent". User overrode for this paper.

Diagnosis: Paper text quality matters more than translation cost. User explicit: "sonnet subagent를 쓰지말고 반드시 opus를 이용하도록 해줘."

Fix: do translation inline as Opus. Document this override in the skill so future invocations respect it.

### Incident: Long bibliography verification batch

Symptom: 38+ refs to verify across InspireHEP / CrossRef / Scholar. Doing sequentially would bloat context.

Diagnosis: Verification can be parallelised across 2-3 subagents (`general-purpose`, `run_in_background=true`).

Fix: split ref.bib by source category (HEP / non-HEP / textbook), dispatch in parallel, merge audit reports.

Important: subagent reports are *interpretations*. Always cross-check critical claims (e.g., novelty verification) by reading the actual paper, not just the subagent summary.

### Incident: User confirms then asks for restructure

Symptom: After user confirms Korean draft, they propose alternative structure ("EMF → PL discontinuity → Smooth PL → Stacy unification → ..."). Now need to re-translate.

Diagnosis: User confirmation is not final. Be ready to revise even after "confirm".

Fix: keep Korean and English drafts in sync. When re-translating, treat the English version as scratchwork until the user confirms the English too.
