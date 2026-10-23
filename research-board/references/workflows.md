# research-board workflows

Set `RB="uv run <skill dir>/scripts/rboard.py"` (or use `rboard` if the symlink exists).

## 1. Where was I? (resume)

1. `rboard -p <slug>` — active and waiting cards first; `!` marks an active card not verified for
   more than 14 days; `session:` shows `live`, `resumable`, `missing`, `live-outside-orca`.
2. `rboard show <slug:Qn>` — read NEXT, BLOCKED BY, VERDICT BASIS (hint is scope-blind: read each
   assessment's scope), CORRECTIONS, then the experiments. A `needs_review` banner means the sources
   disagree; resolve that before acting.
3. `rboard open <slug:Qn>` (or `…/En`) — jump to the live Orca terminal, or resume the session there.
   `--dry-run` shows the action.
4. The card can be stale: check its `last_verified_at` against `git log`, `pueue status`, W&B and the
   output directories named in the experiments before trusting `running`.

## 2. After a work session (update cards)

1. Read the project's cards (`rboard -p <slug>`, then `show` for those touched).
2. Decide, per touched card: new experiment? status change? new `assess`, `evaluation`, `correction`?
   verdict or work-state change (needs reason)? new `next_action`/`blocked_by`? Set
   `last_verified_at` to today only for what was actually checked against sources.
3. When the work also produced a journal-worthy decision, draft both together (research-log `record`
   flow); the new journal entry carries `**Card**: {slug}:Q{n}/E{m}`. Do not edit old entries.
4. Present the delta, wait for approval, write the card file(s) under the project lock, then
   `rboard lint -p <slug>` and fix errors.
5. For each experiment that is `running` or `analyzing`: `rboard link <ref> --here`.

## 3. Attach results (headline numbers, table, key plot)

1. Read the result file(s) named by the experiment. Pick at most six headline metrics that answer the
   card's question. For each: `name`, `unit`, `dir`, `arm_key`, and a `scope` containing **every**
   condition that changes the number. Write the `extract` spec (`file`, `column`, `agg`, and `where`
   when the scope has non-column keys; JSON: `path`).
2. List every source file under `results.sources` (path only). Leave `value/n/lo/hi` and `sha256`
   empty and run `rboard refresh <ref>` to see the numbers, then `--accept` after the user has seen
   them. Cross-check one value by hand against the raw file.
3. Key plot: write and run a `scienceplot-py` script from the project root (PNG + PDF, 300 dpi, output
   in the run's `outputs/YYYYMMDD_<topic>/`). Record it as `style: scienceplot` with `recipe`, `out`
   and `data`. The recipe must aggregate from the data files itself so it can be re-run after a
   source change (`rboard render <ref/plot>`).
4. Show the plot: check for clipped points, empty axes, wrong units, `n` visible in the caption or
   table. Existing figures: attach with `style: legacy`.
5. `rboard html` (or keep `rboard serve` running), open the card page, check the picture and table. In
   Orca open `http://127.0.0.1:8765/` (`orca tab create --url …`), never the `file://` path: Orca's
   embedded browser ignores link clicks that start on a `file://` page.

## 4. Compare experiments

`rboard compare <slug:Qn>` (all experiments of a card) or several `…/En` refs, optionally
`--html file`. Read `NOT COMPARABLE` lines as findings: they name the scope keys or values that
differ. `ranges overlap` / `n=1` mean the difference is not established by that comparison. Never
edit a scope to make numbers line up.

## 5. Backfill a project

1. Stage in `~/.cache/research-board/staging/` with the same layout (`projects/{slug}/cards/`); write
   nothing to `~/.research` before approval.
2. Sources, in this order, compared **by topic**: the project's `state.md`, `compass.md` next-actions
   and open items, `journal.md` + `journal-archive.md`, and the result files the entries name. The
   last 60 days are the initial scope; follow open items further back. Age alone never closes a card.
3. One card per independently stoppable question (not per journal entry); one experiment per
   comparison question and protocol, with arm/seed runs as `runs` or `runs_summary`. Journal entries
   become `source_refs`, not copies.
4. Run `rboard --root <staging> lint` until no errors, `rboard --root <staging> html -o …` and read the
   pages. Present the cards for approval.
5. After approval copy into `~/.research/projects/{slug}/cards/` under the project lock; add
   `board/` to `~/.research/.gitignore` once.

## 6. Link and reopen sessions

- Link: `rboard link <ref> --here` inside the session doing the work; `rboard sessions` lists live
  sessions when another one must be linked (`--terminal <handle>`); `--unlink <id-prefix>` to remove.
- Reopen: `rboard open <ref>`. Refusals are deliberate: a session held open outside Orca, a handle Orca
  no longer lists, or a missing file each mean resuming could put two writers on one session file.
- Linux and the local Orca host only. Remote (SSH) Orca terminals are not visible to `/proc` scanning.
