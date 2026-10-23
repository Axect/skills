# ClickUp Today

Portable daily Markdown sheets for Typora, backed by the Python standard library and an already installed and authenticated `clickup-cli`. Configure the ClickUp lists privately; the repository does not ship list IDs, task data, or credentials.

From the repository root, create `clickup-today/config.json` with your own list IDs (find them with `clickup-cli --output json list list --space SPACE_ID` or `--folder FOLDER_ID`):

```json
{"lists": ["LIST_ID_A", "LIST_ID_B"]}
```

`config.json` and `days/` are ignored by Git. Keep both local, and never commit your private list IDs or sheets. Without a valid nonempty list configuration, commands exit with an error. Existing `clickup-cli` authentication is reused; `CLICKUP_CLI=/path/to/clickup-cli` selects another CLI executable.

Install the user command without sudo:

```sh
bash clickup-today/scripts/install.sh
```

This links `clickup-today` into `${PREFIX:-$HOME/.local/bin}`. Run the installer again safely; it leaves an unrelated existing command untouched. Ensure that directory is on `PATH`, or invoke `clickup-today/scripts/clickup-today` directly. The original `today.py` remains directly runnable with `python3 clickup-today/today.py`.

```sh
clickup-today refresh
clickup-today refresh --date YYYY-MM-DD
clickup-today refresh --focus TASK_ID        # repeat --focus for more IDs
clickup-today publish --date YYYY-MM-DD
clickup-today push --date YYYY-MM-DD
```

Dates default to the computer's local day; `--focus` only works with `refresh` and saves a chosen undated task for that day's sheet. `refresh` reads the configured lists and writes `days/YYYY-MM-DD.md` with incomplete due or overdue tasks and unfinished descendants of due parents. An unfinished task's completed or future parent may appear only as non-actionable context. It preserves local checkbox states, handwritten nested items, and text under `## 메모`; saving Typora edits before running it is essential. Do not remove ClickUp task links: their IDs maintain the parent association.

Add an unlinked checkbox under a linked parent to draft a subtask. `publish` finds a same-named direct child under that parent, including completed children, or creates and verifies one before linking it in the sheet. Nested handwritten items can then be published under that child. A checked local item is **not** completed remotely by `publish`; neither `refresh` nor `publish` pushes completion.

Only run `push` when you intend to change ClickUp: it completes explicitly checked, linked tasks using each list's completion status, verifies the saved result, and refreshes the sheet. It never completes unlinked items or reopens unchecked tasks. A local sheet remains readable without network access; syncing requires ClickUp connectivity.
