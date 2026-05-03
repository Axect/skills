# Sync internals (what happens on the wire)

Background reading for diagnosing weird sync behavior. Not required for normal use — `SKILL.md` is enough for the common workflows.

References point at `~/Documents/Project/AI_Project/overleap/src/...` (the upstream source the user has locally). Line numbers may drift across versions; current as of overleap **0.2.5**.

## Architecture in one paragraph

`overleap` connects to Overleaf with the same Socket.IO v0.9 + Operational Transform protocol the browser editor uses. On startup it joins the project, downloads all files, and starts a chokidar file watcher in the local directory. Local text edits are diffed against the last server-confirmed content (`fast-diff` → OT `i`/`d` ops) and sent as ShareJS-style ops with a monotonic version. Local binary changes are uploaded via the multipart REST endpoint. Remote ops are applied to disk through atomic writes (write to `.tmp.NNN` → rename), and remote file/doc creates trigger fresh downloads.

## The OT loop (`src/sync-engine.js`)

Per-doc state machine:

```
idle ──(local edit)──> debouncing ──(150 ms quiet + content stable)──> sending
  ▲                                                                       │
  │                                                                       ▼
  └────────────────────(self-update ack)────────────────────────────── waiting-ack
                                                                          │
  remote update lands while sending → mark needsResync → on ack: full resync
```

Key invariants the engine maintains:

1. **One in-flight op per doc.** While a doc is `sending`, additional local edits queue up; when the ack lands, the engine diffs the *current* file against the *server-confirmed* content (now including the sent op) and sends a new op if needed.
2. **Version monotonicity.** `docState.version` is bumped only on confirmed ack. Self-update acks with no matching pending entry are silently ignored (defensive: prevents corrupted state from stray duplicates).
3. **Send epoch.** A monotonic counter (`_sendEpoch`) tags every send. Acks for stale epochs (after a resync) are dropped instead of clearing pending state.
4. **Pre-send fence.** Right before sending, the engine re-checks the content hash and the doc version. If either drifted (remote update arrived during the 50 ms stability window), it aborts the send and re-debounces.

These guards exist because rapid edits from AI agents (or fast typers) used to corrupt content — see `CHANGELOG.md` 0.2.0 / 0.2.1 / 0.2.5.

## Debouncing & content stability

Local writes trigger a 150 ms flush debounce per doc. Inside the flush:

1. Read the current file content.
2. Wait 50 ms.
3. Re-read. If content changed, defer (still being written).
4. Diff against last server-confirmed content. Emit `i`/`d` ops. Send.

Net effect: a flurry of `Edit` calls that touch the same file across, say, 80 ms collapses into a single OT op. This is the single biggest reason `overleap` works well for AI-driven editing.

`awaitWriteFinish` on the chokidar watcher uses 500 ms stability + 100 ms poll (raised in 0.2.3) to handle copy-paste of large files. Smaller than that, and partial reads were uploading 0-byte content.

## Watcher suppression

After overleap writes a remote update to disk, it suppresses its own watcher event for that path. Two suppression strategies:

- **Text files**: hash-based — the suppression entry is the SHA of the content just written. Watcher events with the same hash are ignored. Hash-based avoids timing-dependent races.
- **Binary files**: path-based for *all* event types including `unlink` (added in 0.2.4 to fix a delete/re-upload loop).

The `IGNORE_PATTERNS` (in `src/constants.js`) skip dotfiles (including `.env`!), `node_modules`, `.git`, editor swap files, and overleap's own `.tmp.NNN` atomic-write temp files. **Don't put files you want synced inside dotted directories.**

## Binary files

Detected by extension (anything not in the `TEXT_EXTENSIONS` set in `src/sync-engine.js:10`). Uploaded via Overleaf's multipart endpoint (`/Project/{id}/upload`), which requires:

- a `name` form field with the display filename (added in 0.2.2 — its absence caused all binary uploads to 422)
- the file payload
- the standard CSRF token in headers
- sanitized filename (control chars and quotes stripped — 0.2.4)

Concurrent binary uploads are throttled to 3 (`Semaphore(3)`) to prevent overloading the server, with a single retry after 1 s on transient HTTP errors. 0-byte reads (still being written) trigger up to 2 retries with increasing delay.

## Reconnection

`src/daemon.js:_reconnect` does exponential backoff `1s → 2s → 4s → ... → 30s` cap. Each attempt:

1. Refreshes the GCLB / load-balancer cookies via `updateCookies()`.
2. Cleans up the old `SyncEngine` (sends `leaveDoc` for every joined doc, clears debounce timers, removes watcher listeners). Pending debounced edits at this point are dropped, not force-flushed.
3. Disconnects the old socket.
4. Re-fetches CSRF token via `fetchProjectPage`.
5. Builds a new `SocketManager`, joins the project, re-runs `initialSync`.

The disconnect handler is rebound with `.once()` to avoid listener accumulation across reconnects (fixed in an earlier release as the H2/H3 pair).

If the auth callback (`onAuthExpired`) is wired up, the engine will try one auto-refresh on HTTP 403 from REST calls. After that, it surfaces the failure — at which point the cookie genuinely needs to be re-extracted.

## Initial sync

On `joinProject`:

1. The server returns a project tree with all docs and file refs.
2. `initialSync` flattens it (`src/tree.js:flattenTree`) into a list of `{ relativePath, docId|fileId, type }`.
3. For each text doc: emit `joinDoc` to fetch full content + version, then write to disk (suppress own write).
4. For each binary file: skip if already on disk with matching size; otherwise download.
5. **Then**: walk the local directory, find files that exist locally but not on the server (excluding `IGNORE_PATTERNS`), and upload them. This is how a fresh `overleap sync` in a non-empty directory ingests local-only files.

This last step is intentional but can be surprising. **If you point `--dir` at a directory full of unrelated files, they all get uploaded.** Always sync into a directory dedicated to one project.

## Edge cases worth knowing

- **Local create + remote echo race**: when you create a new text file locally, overleap POSTs to create the doc, then `joinDoc`s it. The server echoes a `reciveNewDoc` event for that doc. The `_creatingFiles` guard plus a `_locallyInitiated` content stash (added in 0.2.5) prevent the echo from overwriting your local content even if `joinDoc` throws mid-flight.
- **Two writers on the same line**: handled by OT — both ops are transformed and applied in order. No data loss, but the resulting text may not be what either writer intended. Same as collaborative editing in the browser.
- **Collaborator deletes a file you just created**: the server delete wins. Restore from git or Overleaf history.
- **`joinLeaveEpoch mismatch`**: an older bug, now recovered automatically by the `_locallyInitiated` map. If you still see this in logs, check you're on 0.2.5+.

## Where the protocol details live

- Auth & CSRF: `src/auth.js`
- Project page scraping (cookie warmup, project list extraction): `src/auth.js:fetchProjectPage`
- Socket.IO setup, join handshake: `src/socket.js`
- File diff → OT ops: `src/diff.js:computeOps`
- Project tree flattening: `src/tree.js:flattenTree`
- Atomic file writes, ignore patterns: `src/watcher.js`, `src/constants.js`

When something looks wrong, start with `src/sync-engine.js` — every per-doc decision lives there.
