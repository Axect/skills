# research-board schema

A **card** is one research question or attempt that can be started, paused, or closed
independently. Cards live in the same store as `research-log`:

```text
~/.research/projects/{slug}/cards/Q{n}-{kebab-title}.md      # YAML frontmatter + free prose body
~/.research/board/                                           # derived HTML (gitignored, regenerable)
```

Cards do not replace `compass.md` (direction), `journal.md` (why), `state.md` (session pointer)
or Morgen (schedule). The card owns **current work state and next action**; the journal owns the
reasoning behind a decision.

## Three axes (never merge them)

| Axis | Field | Values | Written by |
|---|---|---|---|
| Work state (board column) | `work` | `candidate` `active` `waiting` `parked` `closed` | approved research decision |
| Evidence verdict (card badge) | `verdict` | `unassessed` `supported` `refuted` `inconclusive` `conflicting` | approved judgement citing evidence |
| Run observation | `experiments[].runs[].state` | `queued` `running` `finished` `failed` `unknown` | observation, with `observed_at` |

`inconclusive` + `parked` is a legal, common combination ("undecided, work stopped"). `refuted` +
`active` is legal too ("headline refuted, re-measurement in progress"). Do not derive one axis from
another. `rboard show` prints a *derived hint* for `verdict` from valid assessments; a stated
verdict that differs from the hint needs `verdict_reason`.

## Card frontmatter

```yaml
id: neural-hamilton:Q3            # {slug}:Q{n}, project-qualified, unique, never reused
kind: hypothesis                  # hypothesis | exploration | engineering
title: 짧은 제목
claim: 반증 가능한 한 문장 (exploration/engineering은 목표 한 문장)
scope: 이 claim이 적용되는 설정 (데이터, 모델, 셀, 평가 조건). 범위를 바꾸면 덮어쓰지 말고 supersedes.
goal: G4.5                        # compass sub-goal, informational
work: active
work_reason: ""                   # required for waiting | parked
verdict: inconclusive
verdict_reason: ""                # required when verdict differs from the derived hint
verdict_basis: [E1, E2]           # experiment ids in this card (or {slug}:Q{n}/E{m})
falsifier:                        # hypothesis only
  text: "σ=1e-2에서 median MSE가 shooting보다 나쁨"
  provenance: prospective         # prospective | retrospective | unknown
  ref: "journal 2026-08-17"       # required when prospective
next_action: 다음 구체적 행동 한 줄
blocked_by: ""
supersedes: []                    # card ids this card replaces (claim or scope changed)
closure: ""                       # required when work=closed: resolved | superseded | deferred | unknown
source_refs: ["journal:2026-08-17 | 제목", "state.md", "compass:G4.5"]
needs_review: false               # true when journal/state/compass disagree and are unresolved
review_note: ""
last_verified_at: 2026-09-29      # last time this card was checked against sources
updated: 2026-09-29
experiments: []                   # see below; owner card holds the experiment
```

`falsifier.provenance: prospective` is a claim of pre-registration and needs a `ref` to a record
written before the run. Everything backfilled from journals is `retrospective`.

Body (markdown, free): the reasoning trail a human wants when resuming. Keep it short; long
reasoning stays in the journal.

## Experiments (owned by exactly one card)

```yaml
experiments:
  - id: E1                        # local; global ref is {slug}:Q{n}/E1
    title: ACO v0 vs FreeSpectral vs LP (synthetic + real_v2)
    date: 2026-09-27
    status: done                  # planned | running | analyzing | done | failed | invalid
    protocol: 비교 질문과 arm 정의
    assess:                       # per-card judgement; key = card id (own or another card)
      exmev:Q1: {effect: inconclusive, scope: "obs20, group=all", note: "합성 차이 큼, real 전체 비슷"}
    evaluation: {valid: true, version: "scores.csv 2026-09-27", note: ""}   # valid: true|false|unknown
    correction: ""                # what was invalidated/re-run and why (invalid or re-evaluated)
    runs_summary: "4 config x 3 seed, 12 checkpoints (provenance.json)"
    runs:                         # optional detail; arm/seed granularity
      - {arm: ACO obs20, seed: 117, state: finished, observed_at: 2026-09-27,
         ref: {path: runs/.../best.pt, wandb: "", pueue: "", commit: ""}}
    journal: "2026-09-27 | ..."   # pointer to the journal entry, not a copy
    results: {...}                # see below
```

- `effect`: `supports` `refutes` `inconclusive` `none`. One experiment may carry different
  effects for different questions, or for different scopes of the same question: use separate
  `assess` entries with their own `scope`.
- An experiment used by another card is **referenced**, not copied: that card lists
  `source_refs: ["exp:{slug}:Q{n}/E{m}"]`, and the owner experiment carries an `assess` entry keyed by
  the other card id.
- Infrastructure work is an experiment with `assess: {}`.
- `evaluation.valid: false` removes an experiment from verdict hints and from comparisons; it does
  not invalidate the runs.

## Results (headline numbers, tables, key plots)

```yaml
results:
  computed_at: 2026-09-29
  sources:                        # everything the numbers were derived from
    - {path: ~/Documents/Project/Research/ExMeV/outputs/20260927_aco_v0/scores.csv, sha256: 61e0bc32891e}
  metrics:                        # <= 6 per experiment; the comparison currency
    - name: median_abs_frac_err
      scope: {data: real_v2, band: 100-316MeV, group: all, model: ACO[obs20]}
      arm_key: model              # the scope key that names the arm
      dir: lower                  # lower | higher is better
      label: 'median $|\Delta\phi/\phi|$'   # optional display name; $...$ / $$...$$ / \(...\) render with KaTeX
      baseline: true              # optional: reference arm of arm comparisons (default: first listed)
      unit: frac
      value: 0.0553
      n: 3
      lo: 0.055                   # min over the n aggregated rows (absent if n=1)
      hi: 0.057
      extract:                    # how to recompute (rboard refresh); where defaults to scope
        file: ~/Documents/Project/Research/ExMeV/outputs/20260927_aco_v0/scores.csv
        column: median_abs_frac_err
        agg: median               # median | mean | min | max | sum | count | first
  tables:                         # small (<=12 rows), stored rows, not recomputed
    - {id: t1, title: "...", columns: [a, b], rows: [[1, 2]], note: ""}
  plots:
    - id: p1
      role: key                   # key | supporting
      title: "..."
      style: scienceplot          # scienceplot | legacy   (legacy = pre-existing figure, style unverified)
      out: ~/.../aco_v0_key_plot.png
      recipe: ~/.../aco_v0_key_plot.py     # scienceplot-py script that regenerates `out` (optional for legacy)
      data: [~/.../scores.csv]
      caption: ""
```

JSON sources use `extract: {file, path: [keys or indexes...], agg}`; the path selects a number or a
list of numbers. Values are **stored**; `rboard refresh` recomputes them and reports drift and
changed source hashes, and only `rboard refresh --accept` rewrites the card.

### Comparability

- **Within one experiment** two metrics are an *arm comparison* when `name`, `unit` and every scope
  key except `arm_key` are identical.
- **Across experiments** two metrics align only when `name`, `unit` and the *whole* scope (arm
  included) are identical. Otherwise the comparison is shown as `not comparable` with the scope-key
  difference; nothing is silently aligned by name. Different `evaluation.version` is flagged, not
  hidden. Any run condition that changes the number (training horizon, pinned vs Z2, split) belongs
  in `scope`.
- `lo`/`hi` are min/max over the aggregated rows, not confidence intervals. Overlapping ranges, or
  `n=1`, are flagged in every comparison.

## Linked agent sessions (resume where the work was)

An experiment (or, for work without an experiment, the card) lists the omp sessions that carry
it. `sessions` may sit on `experiments[]` entries or on the card frontmatter.

```yaml
sessions:
  - agent: omp
    id: 01a0ebf1-1a9e-763c-a72d-e89467b5cbd2      # uuid in the session file name
    path: ~/.omp/agent/sessions/<cwd-slug>/2026-09-29T06-54-01-886Z_01a0ebf1-....jsonl
    cwd: ~/Documents/Project/Research/ExMeV       # session launch dir; also the Orca worktree
    title: "Replicate TT Pilot Control Run"       # informational; the live title is read from the file
    linked_at: 2026-09-29
```

Commands (Linux, local Orca host):

- `rboard link <ref> --here` links the omp session that runs the command (walks up the process
  tree to the ancestor holding a session file). `--terminal <handle>` or `--session <path|id>`
  link another session; `--unlink <id-prefix>` removes one.
- `rboard open <ref>` picks the newest linked session (`--pick N` for others) and
  - **live in Orca** -> `orca terminal switch` to that terminal;
  - **not running** -> `orca terminal create --worktree path:<cwd> --command "omp --resume <path>"`
    in that project's worktree, then verifies an omp process holds the session;
  - **open outside Orca, or Orca no longer lists its terminal, or file missing** -> refuses with the
    reason (two writers on one session file corrupt it). `--dry-run` prints the action only.
- `rboard sessions` lists live omp sessions with their terminal handle and linked card, so an
  unlinked session can be found and linked.

Liveness is read from the OS, not guessed from titles: a running `omp` holds its session `.jsonl`
open once it has written, and every process in an Orca terminal carries `ORCA_TERMINAL_HANDLE`.
An idle resumed session has not opened its file yet, so the `--resume <path|id>` argument is used
as weaker evidence (it can be stale if the user switched session inside the process; that errs
toward refusing a resume). A fresh session with no message has no file and cannot be linked.
The Orca session-history index (`orca search`) is opt-in in Orca settings and is not used.

## Backfill rules

1. Reconcile `journal.md`, `state.md`, `compass.md` and the linked result files **by topic** before
   writing a card. When they disagree and the disagreement cannot be resolved from files, set
   `needs_review: true` with `review_note`; never pick a winner by file type or date.
2. `last_verified_at` is the date the card was checked against sources, not the source's date. A
   remembered `running` run becomes `state: unknown` when no observation is newer than the source.
3. Backfilled `falsifier.provenance` is `retrospective` unless a pre-run record exists.
4. The last 60 days are the *initial search scope* only. Also sweep `state.md` and `compass.md`
   next-actions and follow open items back in time. Older settled items get `closed` with
   `closure: resolved | superseded | deferred | unknown`; never close for age alone.
5. Never invent a hypothesis for work that was engineering or exploration; use `kind`.
6. Do not insert card ids into old journal entries. New entries carry
   `**Card**: {slug}:Q{n}/E{m}`; old ones are referenced from the card via `source_refs`.

## Lint rules (`rboard lint`)

Errors (schema): missing/invalid required fields, unknown enum values, duplicate ids, `waiting|parked`
without `work_reason`, `closed` without `closure`, `prospective` falsifier without `ref`,
`supersedes` to a missing card, `assess` pointing at a missing card or with an invalid `effect`,
metric without `dir`/`unit`/`scope` or with an `arm_key` outside `scope`, plot with invalid
`style`/`role`, session without `id` or `path`.

Warnings (state): `active` card not verified for more than 14 days; hypothesis without falsifier;
`done` experiment without an `assess` key (write `assess: {}` for infrastructure work);
`running`/`queued` run not observed for more than 3 days (reported as *last observed running,
currently unknown*); `running`/`analyzing` experiment in an `active` or `waiting` card with no linked
session; linked session file missing; verdict differs from the derived hint without
`verdict_reason`; `needs_review` set; source file changed since its stored hash; plot `out` missing on
disk. Metric drift is reported by `rboard refresh`, and `n=1` or overlapping ranges are flagged in
every comparison, not by lint.

`work: active` without a running experiment is **not** an error: analysis, proofs and literature work
have no run.
