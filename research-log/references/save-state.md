# Workflow: Save Current Session State

Use when the user asks to save working context, or at the end of a work session.

## Trigger examples

- "Save current state"
- "Update research-log state"
- "Save session context before I stop"
- "Checkpoint my progress"

## Steps

1. Read `~/.research/dashboard.md`; match CWD against Project Registry.
   If no match, say briefly: "Current directory is not a registered project."
   Stop — do not write anything.

2. Acquire `~/.research/.locks/{slug}.lock`.

3. Read `~/.research/projects/{slug}/state.md`; copy the current `Session` value into
   `Last session`.

4. Generate a concise new State from recent work. Populate all fields per the State schema in
   `conventions.md`:
   - `Session` — current datetime (YYYY-MM-DDTHH:MM)
   - `Last session` — previous Session value (from step 3)
   - `Location` — compass sub-goal reference (G?.?)
   - `Working on` — what was being worked on
   - `Current status` — brief status phrase
   - `Blocker` — current blocker, or "None"
   - `Next step` — the next concrete action
   - `Compass link` — one sentence connecting this to the focused sub-goal

5. **Overwrite** `state.md` with the new snapshot. Do not append; do not preserve previous
   snapshots inside the file.

---

## DRIFT CHECK (M4)

After writing state.md, compare the `Working on` field against the `← current focus` marker
in `~/.research/projects/{slug}/compass.md`.

If the recent work does not serve the focused sub-goal, emit one line:

> Drift: working on G?.? ({topic}) but current focus is G?.?

This is informational only. Do not alter compass.md or block the save.

---

## Notes

- Keep each field 1–2 sentences.
- `state.md` is a quick context-recovery summary — not a history. A single snapshot only.
- **Auto-save mode** (invoked by session-end hook, no interactive approval): perform steps 1–5
  and the drift check silently. Write only `state.md`. Skip lesson extraction, journal writes,
  and any prompts.
