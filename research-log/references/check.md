# Workflow M1 (Explicit): Check a Planned Approach

Use when the user explicitly asks to vet a proposed action against past mistakes. This is
the manual twin of the always-active M1 guardrail defined in SKILL.md; same logic, invoked
on demand rather than automatically.

## Trigger examples

- "Check this plan against my past mistakes."
- "I'm going to use architecture X — any red flags?"
- "Research check: ..."
- "Have I made this mistake before?"
- "Validate this approach against lessons."

## Steps

### 1. Extract the proposed action

Identify the core action being considered: architecture, model, loss function, methodology,
experimental design, data pipeline choice, etc. Paraphrase it in one sentence if needed.

### 2. Match against rules.md

Read `~/.research/rules.md` (small; always loadable). For each Rule entry, check whether
the proposed action text overlaps with the Rule's trigger phrases or its one-line Check.

A match is positive if any trigger phrase appears in or is semantically close to the
proposed action. Do not require exact wording.

### 3. Semantically match against the broader lessons corpus

Run a QMD search over `~/.research/` targeted at `lessons/*.md`:

```
searches:
  - {type: 'vec',  query: '<proposed action paraphrase>'}
  - {type: 'hyde', query: '<a journal entry that describes making this exact mistake>'}
intent: 'find lessons relevant to the proposed action'
```

**Fallback (QMD unavailable):** grep `~/.research/lessons/*.md` on the `trigger:` fields
for terms from the proposed action.

### 4. Report matches

Return in two sections:

**Matched Rules** (from rules.md; highest confidence):
> You are about to {X}. This bit you in {projects} — {Check}.
> Evidence: {evidence field from the lesson}.

**Relevant Lessons** (from broader corpus; not yet promoted to rule):
> Lesson `{id}` ({confidence}): {Pattern}. Check: {Check}. ({projects})

List Rules first. Frame every match as advisory: present the risk and evidence, then let
the user decide. Do not block or refuse.

### 5. If nothing matches

State plainly: "No matching rules or lessons found for this action." Note that absence of
a match means no recorded precedent — not that the action is safe.

## Relationship to the automatic guardrail

The SKILL.md decision guardrail fires the same matching logic automatically whenever an
approach choice appears in conversation. This workflow is for when the user wants to invoke
the check explicitly, get a full listing of every relevant rule and lesson, and see the
evidence in detail.
