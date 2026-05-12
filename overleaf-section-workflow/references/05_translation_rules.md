# Korean → English LaTeX translation rules

This is the hardest step of the workflow because it goes directly into the paper. The user has explicitly required that translation be performed by Opus (not delegated to Sonnet subagents) for this very reason.

## Non-negotiable: Opus only

Even though the lab convention (in `~/.claude/CLAUDE.md`) says to delegate translation to Sonnet subagents, **this skill overrides that convention**. Reason: the output is direct paper text. Sonnet's translation discipline is statistically lower for technical physics writing than Opus's.

Do the translation **inline**, as the main agent (which is Opus when this skill is active). Do not spawn `Agent(subagent_type=..., model="sonnet")`.

If the translation is extremely long (>500 lines), the agent may spawn an Opus subagent (`Agent(model="opus")`) to handle the volume — but never Sonnet.

## Source → target mapping

### Headings

| Markdown source | LaTeX target |
|---|---|
| `## §N.M Subsection Title` | `\subsection{Subsection Title}` (header already present in main.tex skeleton) |
| `### E.X Subsubsection` | `\subsection{Subsubsection}` (in appendix context) |
| `**Paragraph lead.**` | `\paragraph{Paragraph lead.}` |

### Math

| Markdown source | LaTeX target |
|---|---|
| `$X$` | `$X$` (unchanged) |
| `$$ ... \tag{N.M} $$` | `\begin{equation} ... \label{eq:foo} \end{equation}` (drop `\tag`, add `\label`) |
| `식 (2.X)` cross-ref | `eq.~\eqref{eq:foo}` |
| `그림 \ref{fig:foo}` | `figure~\ref{fig:foo}` |

The Korean draft uses `\tag{X}` for math labels because markdown doesn't auto-number. In LaTeX, drop `\tag` and let `\begin{equation}` auto-number with `\label`.

### Citations

`\cite{key}` is preserved verbatim. Korean and English both use the same syntax. Double-check that the citation key appears in `ref.bib`.

### Lists

| Markdown source | LaTeX target |
|---|---|
| `(a) **Primary**: text` followed by linebreak | `\begin{description} \item[(a)] \textbf{Primary}: text ... \end{description}` |
| `- bullet` | `\begin{itemize} \item bullet ... \end{itemize}` |
| `(i) text. (ii) text.` inline | inline `(i)~text. (ii)~text.` (use non-breaking space `~`) |

### Figures

Markdown:
```markdown
![Caption text. `fig:label`](figs_<short>/foo.png)
```

LaTeX:
```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=0.75\textwidth]{figs/foo.pdf}
  \caption{Caption text in English, including parameter values.}
  \label{fig:label}
\end{figure}
```

Note:
- PNG in markdown, **PDF in LaTeX** (vector graphics).
- Path: markdown is `figs_<short>/...` (symlink in draft dir), LaTeX is `figs/...` (real dir in sync folder).
- Width default: `0.75\textwidth` for normal figures, `\textwidth` for wide overview, smaller for inline.

### Tables

Markdown:
```markdown
| Col1 | Col2 |
|---|---|
| a | b |
| c | d |
```

LaTeX (with booktabs):
```latex
\begin{center}
\begin{tabular}{ll}
  \toprule
  Col1 & Col2 \\
  \midrule
  a & b \\
  c & d \\
  \bottomrule
\end{tabular}
\end{center}
```

Requires `\usepackage{booktabs}` in preamble.

### Code-style snippets

The Korean draft uses backticks for code names (`\textsc{BlackHawk}`-style). In LaTeX, use `\textsc{BlackHawk}` for software names, `\texttt{module.function}` for code references.

| Markdown | LaTeX |
|---|---|
| `\textsc{BlackHawk}` (already TeX) | `\textsc{BlackHawk}` (unchanged) |
| code `module.function` | `\texttt{module.function}` |
| `*italic*` | `\emph{italic}` |
| `**bold**` (mid-sentence) | `\textbf{bold}` |
| `**Paragraph lead.**` (line start) | `\paragraph{Paragraph lead.}` |

## Korean idiom → English style

Korean and English physics writing differ stylistically. Apply these conversions:

| Korean idiom | English equivalent |
|---|---|
| "본 절은 ... 를 정리한다" | "This section reviews ..." |
| "본 연구는 ... 를 채택한다" | "We adopt ...", "In this work we adopt ..." |
| "우리가 아는 한 ... 없다" | "to our knowledge, ... has not been ..." |
| "표준으로 여겨진다" | "is the conventional choice", "is the standard tool" |
| "다음과 같다" | "is as follows", "are summarised below" |
| "이는 ... 때문이다" | "This is because ...", "The reason is that ..." |
| "정확히 일치한다" | "matches exactly", "is recovered exactly" |
| "극한이다" | "is the limit of", "follows in the ... limit" |

Avoid Korean-literal English. The English text must read as if written natively, not translated.

## Notation consistency

After translation, confirm:

- All equations have `\label{eq:foo}`.
- All figures have `\label{fig:foo}` and `\caption{...}`.
- All `\subsection{...}` have `\label{subsec:foo}`.
- Cross-references use `\eqref{eq:foo}`, `\ref{fig:foo}`, `\ref{subsec:foo}`.
- Inline citations use `\cite{key}` with key matching `ref.bib`.
- `\textsc{...}` for code names, `\emph{...}` for emphasis, `\textbf{...}` for bold.

## Verification after translation

1. Build via `bash <PROJECT>_build/build_<jobname>.sh`.
2. Check `grep -ci undefined <PROJECT>_build/<JOBNAME>.3.log` returns `0`.
3. Inspect the rendered PDF for layout issues (table breaks, oversized figures, line breaks).
4. If any `\ref{}` is undefined in the build log, find the missing `\label{}` in the LaTeX source.

## Worked example (from real session)

**Korean source** (section2_ko.md fragment):
```markdown
**Hawking 복사 (primary spectrum).** 질량 $M$ 인 PBH 로부터 입자 종 $i$ 가 방출되는 미분 방출률은~\cite{Hawking:1975vcx}
$$
\frac{d^2 N_i}{dt\,dE}
= \frac{g_i}{2\pi}\,
  \frac{\Gamma(E,M)}{e^{E/T_H} - (-1)^{2s_i}},
\tag{2.1}
$$
이며, $T_H = 1/(8\pi G M)$ 은 Hawking 온도, $g_i$ 는 내부 자유도, $s_i$ 는 스핀, $\Gamma(E,M)$ 은 시공간 곡률에 의한 투과 확률을 나타내는 *greybody factor* 이다.
```

**English target** (main.tex fragment):
```latex
\paragraph{Hawking radiation (primary spectrum).}
The differential emission rate of particle species $i$ from a PBH of mass $M$ is~\cite{Hawking:1975vcx}
\begin{equation}
  \frac{d^{2} N_i}{dt\,dE}
  = \frac{g_i}{2\pi}\,
    \frac{\Gamma(E,M)}{e^{E/T_H} - (-1)^{2 s_i}},
  \label{eq:primary}
\end{equation}
where $T_H = 1/(8\pi G M)$ is the Hawking temperature, $g_i$ counts the internal degrees of freedom, $s_i$ is the spin, and $\Gamma(E,M)$ is the \emph{greybody factor} encoding the transmission probability through the spacetime curvature surrounding the black hole.
```

Note the changes:
- `**Hawking 복사 (primary spectrum).**` → `\paragraph{Hawking radiation (primary spectrum).}`
- `$$ ... \tag{2.1} $$` → `\begin{equation} ... \label{eq:primary} \end{equation}`
- `이며, $T_H = ...$ 은 Hawking 온도 ...` → `where $T_H = ...$ is the Hawking temperature, ...`
- `*greybody factor*` → `\emph{greybody factor}`
- Korean syntactic patterns ("...은 ... 이다") collapse into English declarative ("X is Y, Z is W").

## What NOT to do

- Do NOT preserve Korean punctuation (`、`, `「」`, etc.) — replace with English equivalents.
- Do NOT preserve em-dashes or en-dashes (Rule 1 in writing-style ref).
- Do NOT add or remove citations during translation. The English should cite *exactly the same papers* as the Korean.
- Do NOT change the technical content. Translation is not the place to "improve" claims; that happens in the Korean iteration phase.
- Do NOT use Sonnet subagents (covered above, but worth repeating).
