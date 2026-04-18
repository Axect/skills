# Integration Notes

How `adversarial-review` wires into the rest of the skills collection and the standing Korean-translation convention.

## With `reference-search`

`reference-search` is the backbone for two personas:

### Hostile Theorist — prior art search

For each central claim the draft makes, run one `background` or `method` search:

```bash
python reference-search/scripts/openalex_search.py \
  "<claim-as-query>" --mode background --limit 10 --format md
```

Use the returned paper list to find prior art the draft failed to cite. A directly anticipating paper missing from the draft's references is a **MAJOR** or **DESK-REJECT** finding depending on how central the claim is.

### Citation Auditor — citation verification

For every non-trivial citation in the draft, verify it exists:

- **By DOI**: if the draft provides a DOI, fetch it directly (the script accepts a title query; a DOI query also works as a filter).
- **By title + first author**: run `openalex_search.py "<title>" --limit 5 --format json` and inspect the `results` array for a matching DOI/year/authorship.

Flag as **not found via OpenAlex — manual verification required** when nothing matches. Do **not** escalate to a fabrication finding on absence alone — some legitimate papers (older physics preprints, certain books) are not indexed. Escalate to **MAJOR** (misrepresentation) or **DESK-REJECT** (fabrication) only when you have positive counter-evidence.

### Rate limiting

OpenAlex is lenient but not infinite. When auditing a dense bibliography, batch queries and pass `--email` to hit the polite pool. Prefer 1 query per citation rather than a broad sweep.

## With `research-report`

Drafts produced by `research-report` are the cleanest inputs for this skill:

- `report.md` at the report root — the draft.
- `plots/` next to it — the figures the Figure Critic audits.
- `plots/plot_manifest.json` — ground truth for "which figures are referenced, with which captions."
- `report_versions.json` — the version history, if the review is being done on a specific tagged version.

When both skills are in play, `outputs/review/<timestamp>/` lives inside the same report root as `report.md`, so the review and the artifact it reviews stay together.

If the draft is **not** a `research-report` artifact (e.g. a Typst source, a paper under `paper/`, a standalone memo), the same workflow applies — the Figure Critic just has to locate figures manually rather than via `plot_manifest.json`.

## With the Korean-translation convention

The user's standing convention: any English `report*.md` / `synthesis*.md` / `explanation*.md` automatically gets a `*_ko.md` sibling via a Sonnet subagent.

For this skill, when the user asks for Korean output (or has a project-level standing rule):

- Translate **`summary.md` only**, not the per-persona files. The per-persona files are evidence; the author reads `summary.md`.
- Output path: `outputs/review/<YYYY-MM-DD-HHMM>/summary_ko.md`.
- Delegate the translation to a Sonnet subagent rather than doing it inline, so the main context stays free for any follow-up review work.
- Do **not** translate technical terms that the draft itself uses in English (optimizer names, architecture names, metric names) — the translation should preserve those as-is.

If the project already runs `/md2pdf-typora` on Korean markdown, trigger that on `summary_ko.md` after translation completes and copy the PDF to the appropriate Dropbox mirror.

## With `commit-triage`

After a review is run, the `outputs/review/<timestamp>/` directory is a new set of files in the working tree. When the user commits next, `commit-triage` should:

- classify review outputs as **COMMIT** only if the project already tracks `outputs/` historically;
- otherwise propose adding `outputs/review/` to `.gitignore`, since review artifacts are typically local-only decision aids;
- never archive a review to `failure/` — reviews document the draft, not failed experiments.

## With standing user instructions

- Never modify the draft during a review. This skill is read-only w.r.t. the manuscript.
- Never `git add` review outputs automatically. Leave that to `commit-triage` or an explicit user request.
- Never push or share review outputs without explicit user approval — they may contain unpublished claims.
