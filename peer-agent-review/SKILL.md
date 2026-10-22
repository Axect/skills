---
name: peer-agent-review
description: "Ask another AI agent to review or discuss your work and act on its answer: by default a permanent live omp session running GPT-6-Astra in the same Orca worktree, launched automatically in a new Orca terminal when none exists and reused for every later brief (\"Astra 확인\", \"Astra와 논의해봐\", \"Astra에게 검토\"), or any other live omp/Claude Code/Codex session, or a headless one-shot CLI (codex exec, claude -p, omp -p). Writes a durable brief, sends a one-line pointer, verifies delivery in the agent's session store, waits for the turn to finish, and reads the answer from the store. Encodes the accept loop (first line 수락/수정 필요 with replacement sentences, re-send until accepted) and the discussion mode (judgments, reasons, counterarguments, no verdict). Use adversarial-review for a parallel persona swarm inside your own session; use workshop-paper-review for OpenReview reports."
---

# peer-agent-review: get a second agent's verdict or discussion, then act on it

One helper, `scripts/peer_review.py`. A reviewer is a *target*. The default target
`astra` is the live omp session in the current worktree whose session model matches
`/astra/`. Other built-in targets: `sol`, `luna`, `opus` (live omp sessions by model),
`codex` and `claude` (live Codex / Claude Code TUIs), and `argon` (Antigravity CLI `agy`,
Gemini 4 Argon; "Agy Argon Medium" = `-t argon --thinking medium`). Any unknown target name is
treated as a model regex for a live omp session. Your own terminal (`$ORCA_TERMINAL_HANDLE`) is never chosen.

**Reviews are hostile by default** (every mode except `propose`). Every pointer line tells the reviewer to read as the most
critical judge looking for reasons to reject: unsupported claims, overstatement, logical gaps,
source and number errors and missing counterexamples, each with a quotation, and no praise that
does not change the decision. Put any extra stance (e.g. "act as a selection committee member")
in the brief.

**The reviewer is permanent.** If no live reviewer exists in the worktree, `send`/`ask` launch
one in a new Orca terminal (`omp --model gpt-6-astra --thinking medium` for astra; override the
level with `--thinking`) and remember its handle in `~/.cache/peer-agent-review/reviewers.json`.
Every later brief goes to the same session, so the reviewer keeps its own earlier answers and
the loop below can run to agreement. Do not use a headless one-shot unless the user asks for
it (`--oneshot`): it forgets everything after one answer and cannot be argued with.

    P=<skill dir>/scripts/peer_review.py
    python3 $P targets                       # what each target resolves to here (never launches)
    python3 $P spawn [-t sol] [--thinking high]   # launch or reuse the permanent reviewer
    python3 $P close [-t sol]                # close the reviewer terminal when the work is done
    python3 $P ask --brief _guide/x.md --marker 'sec3 KO check'                # Astra, accept mode
    python3 $P ask -t argon --thinking medium --brief _guide/x.md --marker 'sec3 argon'   # agy Argon
    python3 $P ask -t sol --mode discuss --brief _guide/x.md --marker '구조 논의'
    python3 $P ask -t codex --brief notes/brief.md --marker 'second opinion' --out ans.md
    python3 $P send / wait / read ...        # split steps (e.g. send, keep working, wait later)

`ask` blocks until the answer is complete (default timeout 1 h, poll 30 s). Run it in the
background when the platform allows and keep working; a substantive review takes 1 to 10 min.
Exit codes: 2 resolution failure, 3 not delivered, 4 timeout, 5 the reviewer's composer
holds an unsubmitted user draft (never send over it without asking).

**argon (agy) answers through a file.** agy has no session store this helper can read, so the
pointer asks it to write its whole answer to
`~/.cache/peer-agent-review/answers/argon/<marker>.md` and to touch no other file; it runs in
`--mode accept-edits` so it can write that file. Delivery is the marker appearing in the
terminal tail; completion is the file non-empty, unchanged for `--settle` seconds, and no busy
token (`esc to`, `Thinking`, `Working`). A reused marker is refused (the answer file exists).
The `{level}` in the launch command becomes the model suffix (`gemini-4-argon-medium`).

## Modes (the pointer line ends with the matching instruction)

| Mode | Use when | Reviewer is told |
|---|---|---|
| `accept` (default) | you changed a file and need sign-off | first line 수락 or 수정 필요; required fixes as replacement sentences; do not edit files |
| `discuss` | structure, framing, or a decision the user wants debated ("단순히 수락을 묻지 말고 논의") | judgments, reasons, counterarguments and its own best proposal per issue; no verdict |
| `free` | anything else | do not edit files |
| `propose` | you want options rather than a verdict (the proposer role in `magi-research`, usually Argon) | not hostile: 2 to 3 distinct alternatives with specs, required reader knowledge, trade-offs, risks and one recommendation; mockups only in the folder the brief names; facts only from files |

## The brief (write it before sending)

- Put it in the project (`_guide/<topic>_brief_<date>.md`) or `~/.cache/<topic>/`, never `/tmp`
  (age-based cleaners delete it between sends). The tool sends only a one-line pointer
  `[marker] @<brief> …`; multi-line terminal text would submit at every newline.
- Contents: the user's instruction quoted verbatim (with the date), what you changed with
  file paths and a backup path of the previous version, exact new sentences or numbers,
  what you are unsure about as numbered questions, and the output contract.
- Apply your edits BEFORE sending and assert that each replacement happened; a failed
  script once sent the reviewer an unchanged file.
- Use a new unique marker per request; the marker is how delivery and the answer are found.
- If you and the reviewer read the same source, agreement is shared sourcing, not
  corroboration; say so in the brief and ask for falsifiable defects.

## The loop

1. `accept`: read the answer. For each required fix, verify the claim against the files
   (numbers, file:line, quotations) before applying. Apply replacement sentences as given
   unless you can show they are wrong; then say why in the next brief.
2. Re-send a short `vN 확인` brief listing exactly what changed. Repeat until 수락.
3. Optional suggestions: apply them or state why not.
4. When you disagree, do not ask for acceptance again. Switch to `discuss`, state the
   objection with evidence and let the reviewer answer it point by point. The user values
   real discussion over rubber-stamping.
5. Report to the user: verdict, what the reviewer corrected (including where it corrected
   itself), what changed, and anything unverified. Never forward a reviewer's numbers
   without re-deriving them.

## Choosing another reviewer

- Same live agent, different model: `-t sol`, `-t luna`, `-t <regex>`; or `--handle term_…`.
  Named targets are launched when missing; `--no-launch` makes a missing reviewer an error.
- Another worktree's agent (e.g. the experiment repo's session for recipe facts):
  `--cwd <that worktree>` with `-t <model regex>` or `--handle`. Give it full context in the
  brief; it has not seen your conversation.
- Claude Code or Codex TUI sessions: `-t codex` / `-t claude` launch them read-only
  (`codex -s read-only`, `claude --permission-mode plan`); an existing one needs `--handle` or
  a `"title"` regex in the targets file.
- Headless one-shot only when the user asks: `--oneshot` runs the target's `oneshot` CLI with
  the brief on stdin (no memory between briefs).

Targets file (optional): `$PEER_REVIEW_TARGETS`, default
`~/.config/peer-agent-review/targets.json`, merged over the built-ins, e.g.

    {"astra": {"thinking": "high"},
     "mylab": {"transport": "session", "agent": "omp", "model": "glm", "launch": ["omp", "--model", "glm-5"]},
     "gemini": {"transport": "oneshot", "agent": "gemini", "oneshot": ["gemini", "-p"]}}

`PEER_REVIEW_DEFAULT` changes the default target; `ORCA_CLI` overrides the Orca binary
name (default `orca-ide`; a bare `orca` can be the GNOME screen reader on Linux).

## How it works and why (traps it handles)

- Resolution order: `--handle`; the remembered permanent reviewer if its terminal still exists;
  a `"title"` regex; for omp targets the session store (below); otherwise launch. A stale
  handle is forgotten and the reviewer re-resolved or relaunched.
- Launch: `orca terminal create --worktree id:<this worktree> --command <launch>` then
  `terminal wait --for tui-idle` (must report `satisfied`) before the first send; a prompt typed
  into a TUI that is still starting is lost.
- Session-store resolution: for omp targets it scans the worktree's session store
  (`~/.omp/agent/sessions/-<cwd relative to $HOME, / → ->`), picks the newest session whose
  dominant `"model"` matches the regex, reads its title (first record), and finds the omp
  terminal in that worktree whose title contains it. Terminal titles and handles change
  after Orca restarts; resolution is redone on `terminal_handle_stale`.
- Delivery: Orca's `accepted: true` is not delivery. The tool waits for a user record
  containing the marker in the agent's session store and retries once after re-resolving.
- Completion: an assistant text record after the marker, no busy token in the terminal
  tail (`Working`, `⟨esc⟩`, `Completing` for omp; `esc to interrupt` for Claude/Codex), and
  the session file unchanged for `--settle` seconds. `orca terminal wait --for tui-idle`
  fires mid-turn and is not used.
- The answer is read from the session store, never scraped from the TUI (hard-wrapped,
  redraw noise). Orca JSON is parsed after replacing invalid UTF-8; never pipe it to `jq`.
- Composer hazard: if the reviewer's input box holds text, sending would submit the
  user's draft together with yours. The tool refuses (exit 5) unless `--force`.
- Slash-command prompts (`/skill:…`) create no user record; send plain text only.
