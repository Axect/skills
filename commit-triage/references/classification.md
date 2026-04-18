# Classification Heuristics

Use these heuristics to assign each changed path to **COMMIT**, **FAILURE**, or **ASK**. When in doubt, choose **ASK**.

## COMMIT — research-relevant changes that belong in history

Signals:

- Source code in tracked directories (`src/`, `lib/`, `<package>/`, `scripts/`).
- Tests in `tests/`, `test/`, or `*_test.py`/`*.test.ts` alongside source.
- Config files that the repo already tracks (`pyproject.toml`, `Cargo.toml`, `package.json`, `Makefile`, `.github/`, `.gitignore`).
- Reports the project archives (`report.md`, `report_v{N}.md`, `plots/plot_manifest.json`) when the run they describe is being kept.
- Documentation updates (`README.md`, `CHANGELOG.md`, `docs/`).
- Notes the repo tracks by convention (`notes/`, `decisions/`, `brainstorm/` if committed previously).
- Plot files under `plots/` when the matching `plot_manifest.json` entry is also being updated.

Signal that a path really is COMMIT:

- It matches the feature or fix the user described when they started the session.
- The commit still makes sense in a month.

## FAILURE — experiments that did not work out

Signals:

- Output directories from a crashed or aborted run (`outputs/run_*/` with partial logs, missing final metrics).
- Files whose names encode failure (`*_failed.*`, `*_broken.*`, `*_wip.*`).
- Training logs that ended in OOM, NaN, SSH disconnect, or manual kill.
- Checkpoints from a run the user already declared dead.
- Diagnostic CSVs or PNGs that only exist to show *why* a run failed.

Failure cases still belong in git history, just under `failure/`. Moving rather than deleting means the diagnosis is recoverable later.

Do **not** classify as FAILURE without at least one explicit signal. A run that simply has not been reviewed yet is **ASK**, not FAILURE.

## ASK — anything not obviously in the other two buckets

Always ASK when the path is any of:

- A new top-level directory that was not in the previous commit (`write/`, `scratch/`, `tmp/`, `_gen/`, `.cache/`, `.venv/`, new framework dirs).
- Anything inside a directory that looks user-scratch by name (`write/`, `scratch/`, `sandbox/`, `draft/`).
- Large binaries or generated artifacts (`*.pth`, `*.onnx`, `*.bin`, `*.parquet` over a few MB).
- Files outside the repo's known layout (a stray `.ipynb` at the root when notebooks usually live in `notebooks/`).
- Lock files that changed without a matching manifest change.
- Submodule pointer changes.
- Renames where the destination is in a directory that did not previously exist.
- Anything the user did not reference during the session.

For ASK items, show the path, a one-line reason, and wait for the user's decision. Do not guess.

## Ignore list (do not stage, do not archive, do not ask)

These are handled by git itself and should not appear in the triage table unless the user points at them:

- Paths already in `.gitignore` (they should not appear in `git status` anyway).
- `.DS_Store`, editor swap files, `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`.
- Build artifacts under `target/`, `dist/`, `build/`, `node_modules/` unless the project intentionally tracks them.

If one of these *does* show up in `git status`, propose a `.gitignore` update instead of staging or archiving.

## Tie-breakers

- **New file, no signal either way** → ASK.
- **Modified tracked file, no obvious reason** → COMMIT (assume the modification is intentional) but include the one-line reason so the user can reject.
- **Deleted tracked file** → always ASK. Deletions are destructive.
- **Rename** → classify by the destination path.
