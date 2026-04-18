# Meta-Editor Synthesis

After every persona returns its critique, run the meta-editor pass described here. The meta-editor's output (`summary.md`) is the single file the author reads first — the persona files are evidence, not reading material.

## Inputs

- Every persona's output markdown (severity-classified findings + suggested defense + confidence).
- The context packet (for venue-specific tailoring).
- The draft itself (for pointer verification only — do **not** re-open the critique).

## Output: `summary.md`

### Structure

```markdown
# Adversarial Review — <draft title or filename>

**Run**: <YYYY-MM-DD HH:MM>  
**Venue**: <venue>  
**Personas run**: <list>  
**Personas skipped**: <list, with one-line reasons — empty if none>

## Findings by severity

### Desk-reject risk (N)
1. <finding, deduplicated across personas>
   - Raised by: <persona, persona>
   - Evidence: <section / figure / citation pointer>
   - Proposed defense: <action>

### Major (N)
...

### Minor (N)
...

## Top-3 actions
1. <the single most important fix>
2. ...
3. ...

## Coverage notes
- <anything the swarm could not evaluate — e.g. "no supplementary material was provided, so ablation completeness is inferred from the main text only">
- <any persona flagged as unreliable and why>
```

### Top-3 actions

The top-3 list is the only part of `summary.md` the author is guaranteed to read. Pick the three highest-leverage fixes, which usually means:

1. the highest-severity DESK-REJECT finding (if any), else the most-cited MAJOR finding,
2. the finding whose defense is cheapest relative to its severity,
3. the finding that would most change the paper's framing if acted on.

Do not pad to three if there are genuinely fewer than three. An honest "only two actions matter" beats a filler third item.

## Deduplication rules

Personas will overlap. When two or more findings are about the same issue:

- Merge into one bullet.
- List all persona names that raised it under `Raised by:` (co-signature strengthens severity).
- Take the **highest** severity among the contributors.
- Take the **most specific** evidence pointer.
- Take the defense from whichever persona's defense is most concrete (not whichever wrote the most words).

Two findings are the same issue when they point at the same section/figure/citation *and* make the same structural claim. Two findings about the same figure for different reasons (e.g. caption vs. axis units) stay separate.

## Severity ranking

Within each severity bucket, rank by:

1. Number of personas that co-signed (more = higher rank).
2. Concreteness of evidence pointer (section+line > section > chapter > "somewhere in the draft").
3. Cost of the proposed defense (cheaper fixes rise, because they are the ones the author should do first).

## Defense experiment / fix authoring

Every DESK-REJECT and MAJOR finding must have a proposed defense. Keep defenses concrete and acted-on in ≤ 2 sentences. A defense is one of:

- a **textual fix** — specific sentence or paragraph to rewrite, with the correction direction (not a full rewrite);
- an **ablation or control** — the exact experiment to run, with the metric that would settle the finding;
- a **citation fix** — the paper to cite or remove, with a one-line reason;
- a **figure fix** — the specific panel and the change (axis, caption, cutoff, path).

If the meta-editor cannot author a defense for a MAJOR finding, leave `Proposed defense: author-to-decide` rather than inventing one. That itself is signal.

## Low-confidence handling

A finding marked by its persona as `Confidence: low` is dropped from `summary.md` **unless** at least one other persona corroborates it. Dropped findings stay in their persona file for traceability.

A persona whose findings are predominantly low-confidence is noted under `Coverage notes` as potentially unreliable — the author can decide whether to re-run it with tighter instructions.

## Never

- Never rewrite the draft or sketch replacement prose. The review surfaces problems; the author writes the fix.
- Never soften a DESK-REJECT finding into a MAJOR one because the overall review "feels too harsh." Severity is set by the persona that surfaced it, not by the meta-editor's taste.
- Never invent a co-signature. `Raised by:` must list only personas whose output actually contained the finding.
- Never produce a review with zero DESK-REJECT / MAJOR findings without saying so explicitly. A clean review is possible but should be called out in `Coverage notes` so the author knows the swarm genuinely found nothing, rather than silently skipped.
