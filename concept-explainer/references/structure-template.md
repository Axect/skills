# Structure Template

Drop the template below into `<concept-slug>/explanation.md` and fill the
braces. Translate section headings to match the requested language; keep
the section *order* and the section *purpose*.

```markdown
# {Concept title}

**Audience**: {one-line audience description}
**Reading level / 분량**: {short | standard | long}
**Prerequisites**: {comma-separated list, or "none beyond high-school calculus"}

---

## 1. {Why this matters}

{1–2 paragraphs. State the question the concept answers. State the
historical or applied stake. Do NOT define anything yet — pure motivation.
A reader who stops here should know why the rest exists.}

## 2. {Setup}

{The simplest non-trivial case that still exhibits the phenomenon. One
diagram of the system if helpful. State coordinates and units. This is
the "throat of the bottle" through which all later generalizations pass.}

## 3. {Definitions and assumptions}

### 3.1 {Definitions}

{Every symbol that the document will use. Group them; do not dump a flat
glossary. Define operators alongside the objects they act on.}

### 3.2 {Assumptions}

> **A1.** {first regime / smoothness / boundary condition}
> **A2.** {second}
> **A3.** {third}

{When a later section drops or generalizes one of these, it will say so
explicitly.}

## 4. {Intuition}

{Verbal picture. Analogy if it carries weight (analogies that don't survive
contact with the math get dropped). Optional schematic figure here — if
the concept has structure (a pipeline, a hierarchy, a "what's happening
under the hood"), this is where the schematic earns its keep.}

![<schematic caption — what to look at + the takeaway>](schematics/<name>.png)

## 5. {Step-by-step derivation}

{Each step names its rule. Each intermediate equation appears on its own
line. Symbols defined on first use. Approximations marked. The derivation
ends with the headline result on its own line, boxed if visually useful.}

Start from {starting equation}:

$$
{\text{starting eq}}
$$

with {symbol-definition line}.

**Step 1.** {Name of the rule applied.}

$$
{\text{intermediate eq 1}}
$$

**Step 2.** {Name of the rule applied.}

$$
{\text{intermediate eq 2}}
$$

…

**Result.** {Final form.}

$$
\boxed{ {\text{headline result}} }
$$

## 6. {Worked example}

{A concrete instance with numbers. State the inputs, walk through the
arithmetic, show the answer. Anchor it with a plot — at minimum
`function_plot.py` showing the relevant curve at the chosen parameter
values.}

![<example caption — what is plotted, what to look at, what it means>](plots/<name>.png)

## 7. {Visualizations}

{The figures that build intuition you can't reach with prose: parameter
sweeps, fields, limits, edge cases. One figure per intuition. Each one's
caption interprets the figure for this audience.}

![<sweep caption>](plots/<name>.png)

![<heatmap caption>](plots/<name>.png)

## 8. {Generalization}

{How the result extends. Which assumptions can be released and what
happens to the conclusion. Pointers to the more general theorem. If
generalization is genuinely a different concept, point at it and stop —
do not silently grow this document into a survey.}

## 9. {Limitations and common misconceptions}

### 9.1 {Failure modes}

{Where the formula breaks: singularities, divergences, regimes where
assumptions fail, numerical hazards.}

### 9.2 {Common misconceptions}

> **오개념 1.** *<the wrong statement, in italics>*
>
> **수정.** {The correction.}
>
> **출처.** {Where this wrong intuition typically comes from.}

> **오개념 2.** *<…>*
>
> **수정.** …
>
> **출처.** …

(English equivalent: `Misconception N` / `Correction` / `Source`.)

## 10. {Where to go next}

### 10.1 {Follow-up concepts}

- {Concept X — one line on what it adds}
- {Concept Y}

### 10.2 {References}

1. {Author, *Title*, Publisher, Year, §section} — used in §{N} for {claim}.
2. {…}

### 10.3 {Exercises (optional)}

1. {Short problem that tests symbol fluency.}
2. {Slightly harder problem that tests derivation fluency.}
3. {An open-ended question that points at §10.1.}
```

## Adapting the skeleton

- **Drop sections** only when the concept genuinely does not need them. A
  pure-definition note may not need §5 (no derivation) or §6 (no example).
  A method explanation may not need §8 (generalization is the next paper).
- **Merge sections** when boundaries are forced. §6 and §7 can merge if
  the worked example *is* the parametric sweep.
- **Add sections** freely. A "Connection to {related concept}" section
  before §10 is a common useful addition.
- **Re-order** only if the dependency graph forces it. The default order
  matches the reader's path: motivation → setup → tools → derivation →
  example → intuition → extension → caveats → exit ramp.

## Headings in Korean

When the document is Korean, the default heading translations:

| English                          | Korean                              |
|----------------------------------|-------------------------------------|
| Why this matters                 | 왜 이걸 알아야 하는가               |
| Setup                            | 시작점                              |
| Definitions and assumptions      | 정의와 가정                          |
| Definitions                      | 정의                                 |
| Assumptions                      | 가정                                 |
| Intuition                        | 직관                                 |
| Step-by-step derivation          | 단계별 유도                          |
| Worked example                   | 구체적인 예제                        |
| Visualizations                   | 시각화                               |
| Generalization                   | 일반화                               |
| Limitations and common misconceptions | 한계와 흔한 오개념              |
| Failure modes                    | 실패 모드 / 깨지는 경우              |
| Common misconceptions            | 흔한 오개념                          |
| Where to go next                 | 다음 단계                            |
| Follow-up concepts               | 다음에 볼 개념                       |
| References                       | 참고문헌                             |
| Exercises (optional)             | 연습 문제 (선택)                     |

Use these consistently within one document. Pick one column and hold it.
