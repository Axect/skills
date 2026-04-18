# Failure Archive Layout

Failed experiments are archived under `failure/` rather than deleted. This keeps the diagnosis recoverable and keeps the main tree focused on the live narrative.

## Directory layout

```text
failure/
  <YYYY-MM-DD>-<short-slug>/
    NOTES.md               # required: what / why / lesson
    <moved files...>       # moved with `git mv`, preserving relative layout
```

- `<YYYY-MM-DD>` is the date the archive is created, not the date the run started.
- `<short-slug>` is 2–4 lowercase words joined with `-`, summarizing the failure. Examples:
  - `oom-psi-run`
  - `glibc-mismatch-vastai`
  - `adamw-vs-splus-pixelcnn`
  - `normalization-binary-drift`

Keep the internal directory structure of the moved files intact when it is meaningful (e.g. `outputs/run_2026-04-15_psi/metrics.csv` → `failure/<slug>/outputs/run_2026-04-15_psi/metrics.csv`). If the structure is noisy, flatten into the slug directory.

## `NOTES.md` template

Every failure archive must include a short `NOTES.md`. Keep it skimmable — the goal is "does this look like something I should revisit in two months?".

```markdown
# <short-slug>

**Archived**: <YYYY-MM-DD>  
**Source run(s)**: <original paths, e.g. outputs/run_2026-04-15_psi/>

## What was attempted
<1–3 sentences: the hypothesis, the config, the setting. No prose padding.>

## What failed
<1–3 sentences: concrete failure mode — OOM at epoch N, NaN loss, SSH drop,
wrong optimizer, wrong baseline version, etc. Include the earliest clear symptom.>

## What was learned
<1–3 sentences: the takeaway that should influence the next attempt. If nothing
was learned beyond "this path is dead," say so explicitly.>

## Revisit if
<Conditions under which this is worth another look: a new optimizer lands,
the cluster gets a newer GLIBC, the baseline is bumped, etc. Leave empty if
the experiment is not worth revisiting.>
```

## Movement rules

- Always use `git mv`. Never `rm` followed by re-`add`.
- Move whole run directories rather than individual files — the internal layout is usually the clearest diagnosis.
- If the failed run produced a valuable artifact (a plot that shows *why* it failed), keep it inside the archive. Do not extract individual files back to the live tree.
- Do not compress or tar the archive. Plain directories stay greppable and diffable.

## When not to archive

Skip the archive and just drop the change when the path is trivially regenerable noise:

- Editor swap files, `__pycache__/`, `.pytest_cache/`.
- Log files that duplicate information already in `wandb/` or a run database.
- Binary artifacts that are cheap to regenerate and never contained useful diagnosis.

In these cases, propose a `.gitignore` addition rather than an archive.

## Cross-links

- When the failure corresponds to a decision that is recorded elsewhere (e.g. a `research-log` Decision Log entry), reference its ID from `NOTES.md` so the two stay discoverable together.
- When a later successful run replaces a failed one, add a one-line pointer in the successful run's own notes: "Previous attempt archived in `failure/<slug>/`."
