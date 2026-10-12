---
name: peer-agent-review
description: "Ask another AI agent to review or discuss your work and act on its answer: by default a live omp session running GPT-6-Astra in the same Orca worktree (\"Astra 확인\", \"Astra와 논의해봐\", \"Astra에게 검토\"), or any other live omp/Claude Code/Codex session, or a headless one-shot CLI (codex exec, claude -p, omp -p). Writes a durable brief, sends a one-line pointer, verifies delivery in the agent's session store, waits for the turn to finish, and reads the answer from the store. Encodes the accept loop (first line 수락/수정 필요 with replacement sentences, re-send until accepted) and the discussion mode (judgments, reasons, counterarguments, no verdict). Use adversarial-review for a parallel persona swarm inside your own session; use workshop-paper-review for OpenReview reports."
---

# peer-agent-review: get a second agent's verdict or discussion, then act on it

One helper, `scripts/peer_review.py`. A reviewer is a *target*. The default target
`astra` is the live omp session in the current worktree whose session model matches
`/astra/`. Other built-in targets: `sol`, `luna`, `opus` (live omp sessions by model),
`codex` and `claude` (headless one-shot). Any unknown target name is treated as a model
regex for a live omp session. Your own terminal (`$ORCA_TERMINAL_HANDLE`) is never chosen.

    P=<skill dir>/scripts/peer_review.py
    python3 $P targets                       # what each target resolves to here
    python3 $P ask --brief _guide/x.md --marker 'sec3 KO check'                # Astra, accept mode
    python3 $P ask -t sol --mode discuss --brief _guide/x.md --marker '구조 논의'
    python3 $P ask -t codex --brief notes/brief.md --marker 'second opinion' --out ans.md
    python3 $P send / wait / read ...        # split steps (e.g. send, keep working, wait later)

`ask` blocks until the answer is complete (default timeout 1 h, poll 30 s). Run it in the
background when the platform allows and keep working; a substantive review takes 1 to 10 min.
Exit codes: 2 resolution failure, 3 not delivered, 4 timeout, 5 the reviewer's composer
holds an unsubmitted user draft (never send over it without asking).

## Modes (the pointer line ends with the matching instruction)

| Mode | Use when | Reviewer is told |
|---|---|---|
| `accept` (default) | you changed a file and need sign-off | first line 수락 or 수정 필요; required fixes as replacement sentences; do not edit files |
| `discuss` | structure, framing, or a decision the user wants debated ("단순히 수락을 묻지 말고 논의") | judgments, reasons, counterarguments and its own best proposal per issue; no verdict |
| `free` | anything else | do not edit files |

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
- Another worktree's agent (e.g. the experiment repo's session for recipe facts):
  `--cwd <that worktree>` with `-t <model regex>` or `--handle`. Give it full context in the
  brief; it has not seen your conversation.
- Claude Code or Codex TUI sessions: pass `--handle`, or add a target with
  `"agent": "claude"` / `"codex"` and a `"title"` regex in the targets file.
- No live session: `--oneshot` (or a oneshot target) runs the configured CLI with the brief
  on stdin. Codex runs with `-s read-only`; Claude with `--permission-mode plan`.

Targets file (optional): `$PEER_REVIEW_TARGETS`, default
`~/.config/peer-agent-review/targets.json`, merged over the built-ins, e.g.

    {"astra": {"oneshot": ["omp", "-p", "--no-session", "--model", "gpt-6-astra", "--thinking", "high"]},
     "gemini": {"transport": "oneshot", "agent": "gemini", "oneshot": ["gemini", "-p"]}}

`PEER_REVIEW_DEFAULT` changes the default target; `ORCA_CLI` overrides the Orca binary
name (default `orca-ide`; a bare `orca` can be the GNOME screen reader on Linux).

## How it works and why (traps it handles)

- Resolution: for omp targets it scans the worktree's session store
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
