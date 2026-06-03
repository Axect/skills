# Workflow M3: Recall Past Lessons

Use when the user asks how a blocker was solved before, wants cross-project patterns, or
needs to surface any prior lesson relevant to a current problem.

## Trigger examples

- "How did I solve X before?"
- "Any lessons about inverse problems?"
- "What did I do last month on project Y?"
- "Have I hit this blocker before?"
- "Did I ever run into convergence failures with this kind of loss?"
- "What do I know about architecture X across my projects?"

## Steps

### 1. Parse question type

Classify the query into one of:
- **project-specific** — scoped to a named project
- **cross-project** — pattern or lesson spanning multiple projects
- **timeline** — what happened in a date range
- **why/decision** — rationale for a past choice
- **status** — current project state (redirect to state.md + compass.md)
- **blocker-precedent** — have I been stuck here before?

### 2. Search via QMD

Query QMD over the `~/.research/` collection (pattern `**/*.md`) with a multi-subquery call:

```
searches:
  - {type: 'lex',  query: '<exact terms from the user's question>'}
  - {type: 'vec',  query: '<paraphrased meaning of the question>'}
  - {type: 'hyde', query: '<hypothetical journal entry that would answer this>'}
intent: '<one-sentence description of what the user wants to find>'
```

**Fallback (QMD unavailable):** grep over `~/.research/lessons/*.md` (all fields) and
`~/.research/projects/*/journal.md` for the key terms from the question.

### 3. Read Core Documents (if present)

For each project file consulted, read the `## Core Documents` section of
`~/.research/projects/{slug}/compass.md` if it exists.

- The Core Documents list (★★★ Core / ★★ Foundational) is **user-curated** — treat it as
  authoritative for "what matters now" in that project.
- When composing a forward-looking answer, prefer pinned `outputs/` paths from ★★★ Core
  entries over searching the broader output directory. Example: "Continue §4 using
  `outputs/<dir>/` as the substrate ({slug}, {date} ★★★ active canonical)."
- If the answer hinges on an artifact that is **not** pinned in Core Documents, flag it:
  "This depends on `<path>` which is not pinned in Core Documents — consider promoting it
  via the record workflow."

### 4. Merge hits with direct reads

- For each matched `lessons/{id}.md`, read the full Lesson object (schema in conventions.md).
- For each matched journal region, read the relevant `### YYYY-MM-DD` entry block verbatim.
- Deduplicate overlapping hits; rank Lessons above journal evidence.

### 5. Compose the answer

**Lead with matched Lessons** — they are the distilled, reusable asset. Then support with
journal evidence.

Answer format by question type:

| Type | Format |
|---|---|
| why/decision | Quote the journal entry's **Why analysis** + **Conclusion**; cite `({project}, {date})` |
| status | Show `state.md` fields + compass sub-goal progress |
| timeline | Chronological table: Date / Project / Decision or Event |
| cross-project pattern | Compare matching entries across projects; cite each; note shared root cause |
| blocker-precedent | "Project {Y} had a similar blocker ({date}) — here is how it was resolved." |

Citation style throughout: `({project}, {date})`.

## Follow-up

If a cross-project pattern emerges from the hits and no corresponding Lesson yet exists,
suggest recording one (via the record workflow) or flag it for promotion at the next review.
