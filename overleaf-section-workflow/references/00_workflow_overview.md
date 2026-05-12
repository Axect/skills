# Workflow overview

The full per-section loop, with checkpoints. Each step has a "verify" sub-step that the agent should not skip.

## Pre-flight (once per project)

1. Confirm the three-directory contract exists:
   - `~/zbin/OverLeaf/<PROJECT>/` (sync)
   - `~/zbin/OverLeaf/<PROJECT>_draft/` (Korean drafts)
   - `~/zbin/OverLeaf/<PROJECT>_build/` (build)
   Create any missing one. Confirm the user agrees to the layout.
2. Ensure `<PROJECT>/figs/` exists. Plots will be deposited here.
3. Symlink figs into the draft directory for inline preview:
   ```bash
   ln -sf <PROJECT>/figs <PROJECT>_draft/figs_<short>
   ```
   This lets the Korean markdown reference `figs_<short>/foo.png` and the viewer (Obsidian, Typora, VSCode) can render the inline images.
4. Confirm `<PROJECT>_build/build_<jobname>.sh` exists; if not, copy from `templates/build_template.sh` and set `JOBNAME`.

## Per-section loop

### Step 1. Korean draft

Create `<PROJECT>_draft/section<N>_ko.md`. Structure:

```markdown
# §N. Section Title (English)

> Substrate: note.tex §X, lit-review at /tmp/X.md, prior conversation context.

## §N.1 Subsection Title (English)
`subsec:label`

**Paragraph lead.** Body text in Korean with inline math $X$ and display
$$
\text{equation}
\tag{N.1}
$$
and citations~\cite{key} preserved verbatim.

![caption](figs_<short>/foo.png)
```

Build narrative as: motivation → introduce families → unify → identify limitation → contribution. See `06_section_narrative.md`.

**Verify**: `grep -cP "[\x{2013}\x{2014}]" section<N>_ko.md` must return `0`.

### Step 2. Iterate with the user

The user will critique. Common issues to anticipate:

- "표준이다" → "표준으로 여겨진다" (soften absolute claims)
- "§\ref{...}" appearing in a background section → forward reference, remove
- "본 연구의 §X 에서 다루는 ..." → preview language, remove
- emoji / emdash / endash leaking in → AI style markers, scrub
- Novelty claim without hedging → add "우리가 아는 한"
- Citation that doesn't actually support the claim → re-verify with deep-research or by reading the cited paper
- Plot has legend on top of curves → move legend outside via `bbox_to_anchor`
- Plot has wasted space → tighten xlim/ylim

Do not silently apply user-suggested edits without judging validity. The user expects critical evaluation: if their proposed wording uses non-standard terminology (e.g., "biased solver" instead of "regularization"), say so before applying.

### Step 3. Citation verification

For each new `\cite{key}` introduced in the section:

1. **Generate the entry** via `bibtex-gen`. HEP papers route to InspireHEP, others to CrossRef/Scholar.
2. **Verify the texkey** matches InspireHEP canonical form (e.g., `Auffinger:2022dic` not `Auffinger:2022khh` — these are different papers).
3. **Verify the body claim** matches what the paper says. Don't trust an earlier reference-search subagent's summary; read the actual abstract.
4. For novelty claims, run `/deep-research` in fact-check mode.
5. Append confirmed entries to `<PROJECT>/ref.bib`.

See `02_citation_verification.md` for the full three-source protocol.

### Step 4. Plot creation

For each new figure:

1. Define data in `~/Documents/Project/Research/<PROJECT>/outputs/<topic>/<defs>.py` (reusable).
2. Write `plot_<name>.py` that imports the defs and produces both PNG and PDF.
3. Style mandates (see `03_plotting_conventions.md`):
   - `with plt.style.context(["science", "nature"]):`
   - `dpi=300, bbox_inches="tight"`
   - **No** title, **no** font-size override, **no** `usetex=False` / `no-latex` flag.
   - Legend outside the plot area via `bbox_to_anchor=(1.02, 0.5)` whenever data would overlap.
   - Tight `xlim`/`ylim` matched to data; avoid empty regions.
4. PNG embedded into Korean draft. PDF copied into `<PROJECT>/figs/`.
5. Per-family parameter sweeps → Appendix. Family overview / limit convergence → main body (if narrative-supporting).

### Step 5. User confirms Korean is paper-grade

Do not translate until the user explicitly confirms. Ask: "이 한글 초안으로 영어 번역 진행할까요?" before touching `.tex`.

### Step 6. Opus-direct English translation

**NEVER delegate to Sonnet subagents in this skill.** The user has explicitly forbidden Sonnet for translation because the output goes directly into the paper. Do the translation inline as Opus (you are already Opus when this skill is invoked).

Conversion rules in `05_translation_rules.md`. Brief summary:

- Markdown `**X.**` → `\paragraph{X.}`
- `## §N.X heading` → `\subsection{...}` (already in `main.tex` placeholder)
- `$$...$$` `\tag{X}` → `\begin{equation}...\label{eq:foo}\end{equation}` (drop `\tag`, let LaTeX number)
- Image embed → `\begin{figure}...\includegraphics{figs/foo.pdf}\caption{...}\label{fig:foo}\end{figure}`
- Markdown table → `\begin{tabular}{...}\toprule...\bottomrule\end{tabular}` (requires `\usepackage{booktabs}`)
- `\cite{key}` preserved verbatim
- Use `\eqref{eq:foo}` for equation cross-refs

Apply via `Edit` per subsection, replacing the empty subsection skeleton with the populated body.

### Step 7. Build verification

Run `bash <PROJECT>_build/build_<jobname>.sh`. The script:

- Compiles from sync dir, outputs to build dir
- 4-pass: pdflatex → bibtex → pdflatex → pdflatex
- Copies `.bst`, `.sty`, `ref.bib` to build dir for bibtex

Build must succeed AND produce zero `undefined` warnings (`grep -ci undefined <PROJECT>_build/main.3.log` must return `0`). Overfull / underfull hbox warnings are cosmetic and OK.

If build fails:
- Missing `\toprule`? Add `\usepackage{booktabs}` to preamble.
- Manual `\begin{thebibliography}` placeholder still present? Replace with `\bibliographystyle{JHEP}` + `\bibliography{ref}`.
- Undefined `\cite{}`? Either the texkey is wrong (re-verify via InspireHEP/bibtex-gen) or `ref.bib` isn't in build dir (build.sh should copy it).

### Step 8. Sync hygiene check

After build:
```bash
ls <PROJECT>/main.* 2>/dev/null
```
Should return only `main.tex` (and any other source .tex). If you see `main.aux`, `main.log`, etc. in the sync dir, the user accidentally ran `pdflatex` there or the build script has a bug — clean immediately.

### Step 9. Commit-triage

Use the `commit-triage` skill at session boundaries to produce clean commits.

## When to invoke this skill

- User says "§N 작성하자" / "section N drafting"
- User says "한글 초안 영어로 병합하자"
- User says "main.tex 에 영어로 옮기자"
- User asks about Overleaf paper workflow
- User wants to restart paper drafting after a long break

## When not to invoke

- One-shot full-paper writing (use `academic-paper` skill instead)
- Pure code / experiment work
- Non-paper writing (slides, reports, blog posts)
