# Running `overleap sync` for long sessions

`overleap sync` is a daemon: it connects via Socket.IO and runs until interrupted. Pick a host process that matches how long you want sync to live and how visible the log should be.

## Decision matrix

| Want | Use |
|---|---|
| Watch the log live, single Overleaf session, easy Ctrl+C | **`tmux` / separate terminal** (recommended default) |
| Survives shell exit, queueable, scriptable, lives across Claude sessions | **`pueue`** (matches the user's global rule) |
| Tied to current Claude session, no setup | **`run_in_background` Bash call** |
| Always-on at boot | **`systemd --user` service** (advanced) |

Whichever you pick, **only one sync daemon per `(project, dir)` pair**. Two daemons watching the same directory will fight over OT versions and cause noisy "version mismatch → resync" loops.

## Pattern A — `tmux` / separate terminal

Simplest, most observable. The user opens a fresh pane and runs:

```bash
cd <dir>
overleap sync -p <id-or-num>
```

The log scrolls in the pane. Ctrl+C stops cleanly (SIGINT triggers the graceful shutdown path in `src/daemon.js:stop`).

Inside `tmux`, a useful pattern is a dedicated window:

```bash
tmux new-window -n overleap "cd <dir> && overleap sync -p <id-or-num>; bash"
```

The trailing `bash` keeps the pane alive after Ctrl+C so the user can re-run without losing scrollback.

## Pattern B — `pueue`

Matches the user's `CLAUDE.md` rule: *"For long-running tasks, use pueue so they persist beyond the Claude session."*

```bash
# One-time, per project
pueue group add overleap-<shortname>

# Queue the daemon
pueue add -g overleap-<shortname> -- bash -c 'cd <dir> && overleap sync -p <id-or-num>'
# → prints something like: Created task with ID 42

# Watch the log live
pueue log 42 -f

# Inspect status
pueue status -g overleap-<shortname>

# Stop cleanly
pueue kill -s SIGINT 42

# Restart later
pueue add -g overleap-<shortname> -- bash -c 'cd <dir> && overleap sync -p <id-or-num>'
```

Notes:

- `pueue log -f` follows the live stdout/stderr stream — use this to confirm the daemon connected, see disconnect/reconnect cycles, and watch OT acks.
- The `bash -c '...'` wrapper is required because `pueue add -- ...` runs the command directly without a shell, and we need `cd` semantics.
- **Per the global rule**, never `pueue kill` a task in another project's group, and ask the user before killing any pueue task.

### Why a per-project `pueue` group?

If you queue overleap into a shared group (say, `default`), it competes with other long-running tasks for parallelism slots. Per-project groups isolate it and make `pueue status` readable.

## Pattern C — `run_in_background` from Claude

Acceptable for a short demo within a single Claude session. The daemon dies when the Claude session ends.

```text
Bash tool call:
  command: cd <dir> && overleap sync -p <id-or-num>
  run_in_background: true
```

Then poll the background shell for output as needed. Stop with `KillBash`.

**Always tell the user**: "This daemon will exit when this Claude session ends. If you want it to outlive the session, switch to pueue or a tmux pane."

## Pattern D — `systemd --user` service

For users who want overleap to start at login and never need to think about it again.

`~/.config/systemd/user/overleap@.service`:

```ini
[Unit]
Description=overleap sync for %i
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/Papers/%i
EnvironmentFile=%h/Papers/%i/.env
ExecStart=/usr/bin/env overleap sync
Restart=on-failure
RestartSec=10
# Optional: cap log noise
StandardOutput=append:%h/.local/state/overleap/%i.log
StandardError=append:%h/.local/state/overleap/%i.log

[Install]
WantedBy=default.target
```

```bash
mkdir -p ~/.local/state/overleap
systemctl --user daemon-reload
systemctl --user enable --now overleap@quantum-draft.service
journalctl --user -u overleap@quantum-draft.service -f
```

Caveats:

- `EnvironmentFile` parses `KEY=VALUE` lines without quote-stripping. If your cookie value contains `#`, escape it or use a wrapper.
- The `overleap` binary must be on `PATH` for the user's systemd environment. If `nvm` is involved, `which overleap` and use the absolute path in `ExecStart`.
- This is the only pattern that survives reboots. For most users, Pattern A or B is plenty.

## Stopping cleanly — why SIGINT, not SIGKILL

`src/daemon.js:stop` does three things on SIGINT/SIGTERM:

1. Calls `syncEngine.cleanup()` — sends `leaveDoc` for every joined doc and clears all pending debounce timers. **It does not force-flush in-flight edits**: any local change still inside the 150 ms debounce window at shutdown time is dropped (the timer is cancelled before the OT op is computed). If you want every keystroke synced, save the file and wait ~200 ms before hitting Ctrl+C.
2. Stops the chokidar watcher cleanly (otherwise inotify handles can leak).
3. Disconnects the socket so the server marks you offline immediately rather than waiting for the connection to time out.

`SIGKILL` (`kill -9`, `pueue kill -s SIGKILL`) skips all three: no `leaveDoc` notifications, leaked inotify watches, and the socket lingers as half-open on the server until its own timeout. Don't use it unless the process is genuinely stuck. If the 2-second exit safety net in `daemon.js` (`setTimeout(() => process.exit(0), 2000).unref()`) doesn't fire, that's a bug worth reporting upstream.

## Diagnosing "the daemon won't stay connected"

Symptoms in the log:

```
[daemon] Disconnected: <reason>
[daemon] Reconnecting in 1s...
[daemon] Reconnect failed: <message>
[daemon] Reconnecting in 2s...
[daemon] Reconnect failed: <message>
[daemon] Reconnecting in 4s...
...
```

The exponential backoff caps at 30 s (see `_reconnect` in `src/daemon.js`). Causes, in order of likelihood:

1. **Cookie expired**: re-extract and re-run setup with `--force`.
2. **Network**: laptop sleep, VPN flap, captive portal. Wait or fix the network.
3. **Overleaf maintenance**: rare; check status.overleaf.com in the browser.
4. **Server-side rate limiting**: very rare for personal use; if hit, wait a few minutes.

If reconnect *succeeds* but immediately disconnects again, that's almost always cookie expiry — Overleaf accepts the WebSocket upgrade but the join-project handshake fails.

## One more guard rail

Before starting a new sync daemon for a directory, check whether one is already running. A quick check:

```bash
pgrep -af 'overleap sync.*<dir-or-project>'
# or, if you used pueue:
pueue status | grep overleap
```

Two daemons on the same project will both try to be authoritative and produce a stream of OT version-mismatch resyncs in the logs. Stop the old one before starting the new one.
