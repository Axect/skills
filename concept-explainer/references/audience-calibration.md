# Audience Calibration

Goal: turn a free-form audience one-liner into a structured calibration that
shapes every subsequent decision (which terms to define, which derivation
steps to elide vs spell out, how dense to make the math, how many worked
examples to include).

## Inputs the one-liner usually carries

A useful audience description names at least two of:

- **Level**: high school / undergrad lower-division / undergrad upper-
  division / Master's / PhD / postdoc / faculty / engineer / hobbyist.
- **Field**: physics, math, ML, statistics, CS, biology, chemistry, …
- **What is known**: prerequisite courses or concepts the reader already
  has.
- **What is NOT known**: explicit gaps. (This is often the most useful
  field — "라그랑지안 모름" is more informative than "물리 학부생".)

If the one-liner has zero or one of the above, ask one targeted question
before proceeding. Examples:

| User said             | Ask                                                                     |
|-----------------------|-------------------------------------------------------------------------|
| "학생"                | "어느 학과의 몇 학년 정도이고, 이 개념에서 이미 알고 있는 게 무엇인가요?"  |
| "researcher"          | "Which field, and what is the closest concept they already know?"        |
| "초보자"              | "프로그래밍 / 미적분 / 선형대수 중 어디까지 익숙한 독자인가요?"           |

## Calibration table

Produce an internal dict (not visible to the reader) with these fields:

```text
prerequisite_knowledge:
  - <concept A>          # treat as known; do not redefine
  - <concept B>
needs_definition:
  - <concept C>          # define inline on first use
  - <concept D>
notation_conventions:
  - "physicist's index notation; Einstein summation by default"
  - "vectors bold-Roman, scalars italic"
math_density: low | moderate | high
worked_example_density: low | moderate | high
approximation_tolerance: strict | moderate | casual
schematic_appetite: none | only-when-structural | freely
prose_temperature: dry-technical | friendly-textbook | conversational
```

### Field meanings

- **math_density** — How much algebra per paragraph. `low`: ≤ 1 display
  equation per major section, derivations sketched and pointed at a
  reference. `high`: full derivations inline, with intermediate steps.
- **worked_example_density** — Numbers vs symbols. `high`: every major
  result followed by a numeric instance with a plot. `low`: pure-symbol
  treatment, examples deferred to exercises.
- **approximation_tolerance** — How carefully `≈` is qualified. `strict`:
  every approximation says the order ("to leading order in `ε`",
  "neglecting terms `O(α²)`"). `casual`: still mark `≈` vs `=`, but no
  order tags unless they change the conclusion.
- **schematic_appetite** — Whether to call `wide-slide-illustrator`. `none`:
  prose + matplotlib only. `only-when-structural`: schematic for pipelines /
  architectures / taxonomies. `freely`: schematic for any conceptual
  bottleneck the prose hits.

### Defaults by audience level (when the one-liner is sparse)

| Level                          | math_density | examples | tolerance | schematic   | temperature       |
|--------------------------------|--------------|----------|-----------|-------------|-------------------|
| High school                    | low          | high     | casual    | freely      | conversational    |
| Undergrad lower-div            | moderate     | high     | moderate  | only-struct | friendly-textbook |
| Undergrad upper-div / Master's | high         | moderate | strict    | only-struct | friendly-textbook |
| PhD / postdoc in same field    | high         | moderate | strict    | none        | dry-technical     |
| PhD / postdoc cross-field      | high         | high     | strict    | freely      | friendly-textbook |
| Engineer (applied)             | moderate     | high     | moderate  | freely      | friendly-textbook |

These are starting points — override from the one-liner. A PhD whose
one-liner says "first time touching this measure-theoretic stuff" should
get the "cross-field" row regardless of nominal level.

## Applying the calibration

While drafting, the calibration controls:

1. **Glossary discipline.** Every term in `needs_definition` gets an inline
   definition on first use, with the form "<term> (intuitive gloss; formal
   definition)". Terms in `prerequisite_knowledge` are used without
   apology.
2. **Derivation granularity.** With `math_density: high`, show every step
   in a chain of equations and name the rule. With `low`, show endpoint
   and one anchoring middle step, then point at a reference for the rest.
3. **Example density.** With `worked_example_density: high`, each major
   formula is followed by a 5–10 line numeric instance (often with a plot).
   With `low`, examples live in §6 only.
4. **Hedge audit.** With `approximation_tolerance: strict`, grep the
   document for `≈` and confirm each one names its order. With `casual`,
   `≈` without order tag is fine when the omitted terms don't change the
   conclusion.
5. **Voice.** `prose_temperature: dry-technical` ⇒ third person, declarative.
   `friendly-textbook` ⇒ second person OK ("you can verify by substituting…"),
   short anchoring sentences allowed. `conversational` ⇒ rhetorical
   questions, occasional informal asides, but never at the cost of rigor.

## Anti-patterns to refuse

- Calibrating to a vague audience ("smart person") — ask first.
- Calibrating *up* to match a more sophisticated reader than the user
  asked for. If the user says "고등학생", the document is for a high
  schooler even if the explainer would prefer to write for a grad
  student.
- Calibrating *down* to insult the audience. Adding extra hand-holding
  beyond what the level needs is itself a form of disrespect.
- Treating "knows X" as transitive. "Knows linear algebra" does not
  imply "fluent with tensor index notation"; ask if uncertain.
