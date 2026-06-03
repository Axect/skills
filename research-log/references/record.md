# Workflow: Record a Decision Log Entry

Use after an experiment, debugging session, design choice, or failed attempt.

## Trigger examples

- "Record this experiment"
- "Log this decision with failure analysis"
- "Add a decision log entry for what just happened"
- "Document why this approach failed"

## Steps

1. Read `~/.research/dashboard.md`; match CWD against Project Registry.
   If no match, ask which project this entry belongs to.

2. Read `~/.research/projects/{slug}/compass.md`; identify the relevant sub-goal and note which
   item carries `← current focus`.

3. Gather context from available sources:
   - Recent `git log --oneline` and diffs
   - Changed config files
   - Logs, metrics, experiment outputs
   - Current conversation context
   - Optional topic hint from the user

4. Draft a journal.md Decision Log entry using the exact format from `conventions.md`:
   Context / Tried / Expected / Got / Why analysis / Conclusion / Lesson.

5. Present the full draft. Wait for user approval before writing.

6. After approval: acquire `~/.research/.locks/{slug}.lock`; insert the entry at the **top** of
   `~/.research/projects/{slug}/journal.md` (newest-first, verbatim).

---

## LESSON EXTRACTION

After the journal entry is written, ask: does this yield a generalizable lesson?

**Dedup step** — search `~/.research/lessons/` for an existing lesson with the same pattern:
- If QMD is available: query with lex + vec sub-queries using key terms from the lesson.
- Fallback: `grep -r` over `~/.research/lessons/` for trigger phrases.

Two outcomes:
- **Match found**: append this project's slug to that lesson's `projects:` list; refresh its
  `Evidence` field with the new entry pointer. Do NOT create a duplicate lesson file.
- **No match**: create `~/.research/lessons/{id}.md` using the Lesson schema in `conventions.md`
  with `status: lesson`. Choose a stable kebab-case `id`; assign `trigger` phrases as the kinds
  of things a user would say when about to make the same choice.

**Trigger phrase rules**: write them in first-person present tense as a user would say them
("I'm going to use X", "let me pick architecture Y before checking the data"). These are the
hook phrases matched at decision time (M1) and during recall (M3).

**Lesson body rules**:
- `Pattern` — describe the situation, not the outcome.
- `Why it bites` — root-cause / domain reasoning, not just "it failed".
- `Check` — one question to ask before committing to the matching action.
- `Evidence` — `{project} {section/date}` pointers so the lesson is traceable.

---

## RULE PROMOTION

After any lesson create-or-update, check the lesson's `projects:` list length.

If `len(projects) >= 2` and `status` is still `lesson`:
- Propose promoting to `status: rule`.
- After user approval: update the lesson file's frontmatter; regenerate
  `~/.research/rules.md` as the compact projection (one line per promoted lesson:
  `**{id}** — {Check}. ({projects})`).

---

## CORE DOCUMENTS ASSESSMENT

After the Compass / drift check, read the `## Core Documents` section of
`~/.research/projects/{slug}/compass.md` (if it exists) and assess whether the recorded
decision implies any of the following changes:

- **New canonical artifact created** — a new `outputs/<dir>/` (or comparable path) was
  produced that supersedes or extends the current frontier. → propose adding as ★★★ Core.
- **Existing canonical artifact superseded** — a previously listed ★★★ entry is now
  superseded by a newer one. → propose demoting to ★★ Foundational, or adding a
  `component → <new-path>` status if it remains a valid component.
- **Status or role changed** — an artifact gained a deprecation header, was renamed, split,
  or its `last YYYY-MM-DD` touch date should advance. → propose the status / date update.
- **New foundational reference identified** — an architecture / training-data / paper-substrate
  document the project will keep referencing. → propose adding as ★★ Foundational.

If **none** of these apply, skip this step silently — most decisions do not change Core
Documents.

When proposing, present a concrete diff:

> "Core Documents update proposal:
> - **Add (★★★)** `outputs/<new-dir>/` — <role> · active canonical · {today}
> - **Demote (★★★ → ★★)** `outputs/<old-dir>/` — status: `superseded by <new-dir>` · {today}
> - **Touch** `outputs/<existing-dir>/` last date → {today}
>
> Apply these changes?"

Apply only after user approval. Use `flock ~/.research/.locks/{slug}.lock` for the write.
Cap at ≤ 15 entries; if the list would exceed the cap, propose pruning a stale ★★ entry
first. The section is **user-curated** — never auto-edit without explicit approval.

---

## DRIFT CHECK (M4)

Compare the journal entry's target sub-goal against the `← current focus` marker in
`compass.md`. If the work falls under a different sub-goal than the current focus, emit a
one-line flag inline:

> Drift: this work targets G?.? but current focus is G?.?

Do not block the write — flag only.

---

## Why analysis rules

- Point 1 — mandatory: trace the root-cause chain.
- Point 2 — mandatory: provide the domain-specific explanation.
- Point 3 — encouraged: cite literature, precedent, or prior experiment evidence.
- If the cause is genuinely unknown, state that explicitly.
