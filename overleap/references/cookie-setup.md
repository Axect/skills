# Cookie setup & refresh

`overleap` authenticates with Overleaf using the same browser session cookie the editor uses. There is no OAuth, no API key — the cookie *is* the credential. Treat it like a password.

## Which cookie value matters

When you copy the full `Cookie:` header from DevTools, you get something like:

```
overleaf_session2=s%3A...; GCLB="..."; gke-route=...; sharelatex.sid=...; ...
```

`overleap` only strictly needs `overleaf_session2`. The other values (`GCLB`, `gke-route`) are load-balancer stickiness cookies — overleap refreshes them itself on every connection via `updateCookies()` (see `src/auth.js`), so it's fine if they're stale or missing.

You can therefore store either:

1. **The full cookie string** (simplest, most robust). Just paste the whole `Cookie:` header value.
2. **Just `overleaf_session2=...`** (minimal). Works as long as that segment is current.

The setup helper accepts either form unchanged.

## Step-by-step extraction (Chromium / Chrome / Edge / Brave / Arc)

1. Sign in to <https://www.overleaf.com> in the browser.
2. Open DevTools (`F12` or right-click → *Inspect*).
3. Go to **Application** → **Storage** → **Cookies** → `https://www.overleaf.com`.
4. Find the row whose name is `overleaf_session2`. Copy the full **Value** column (it starts with `s%3A`).
5. (Optional, for the full-string form) Switch to the **Network** tab, reload the page, click any request to overleaf.com, and copy the `Cookie:` request header verbatim.

## Step-by-step extraction (Firefox)

1. Sign in to <https://www.overleaf.com>.
2. Open DevTools (`F12`).
3. **Storage** tab → **Cookies** → `https://www.overleaf.com`.
4. Right-click the `overleaf_session2` row → *Copy Value*. Paste that.
5. (Optional, for the full-string form) **Network** tab → reload → click any request → *Headers* → *Request Headers* → copy the `Cookie:` line minus the `Cookie: ` prefix.

## Storing the cookie

The skill's `scripts/init_env.sh` writes `<dir>/.env` with mode `0600` and ensures `.env` is in `.gitignore`. Always prefer this over `--cookie` on the command line — `--cookie` shows up in `ps`, shell history, and journald.

The `.env` line looks like:

```env
OVERLEAF_COOKIE=overleaf_session2=s%3A...whatever-you-copied...
```

No quoting is needed; `overleap`'s `.env` parser strips at most one pair of surrounding quotes, but bare values are fine because the cookie has no whitespace.

## When to refresh

Overleaf sessions are long-lived (months) but expire when:

- You explicitly log out in the browser.
- You change your password.
- Overleaf rotates session IDs (rare, but happens after security incidents).
- You stay logged out of the browser for a long enough period that the session is invalidated server-side.

Symptoms in `overleap`:

- `overleap projects` returns `HTTP 401` or `HTTP 403`.
- `overleap sync` connects briefly, then disconnects with a 401 / 403 reason and the auto-reconnect backoff keeps failing.
- The OT engine reports `auth expired` in logs (the `_refreshAuthIfNeeded` path in `src/sync-engine.js` will try once, then surface the failure).

To refresh:

1. Open the browser, sign back in to Overleaf.
2. Re-extract `overleaf_session2` (steps above).
3. Re-run setup with `--force`:
   ```bash
   bash scripts/init_env.sh <dir> --force <<< 'overleaf_session2=...'
   ```
4. If sync was running, restart it (Pattern 1 / 2 / 3 in `SKILL.md`).

## Multi-account / shared machines

- The cookie is per-user. Do **not** share `.env` files across users.
- On a shared machine, prefer environment variables in your shell rcfile (sourced only for your user) over `.env` files in shared directories.
- Mode `0600` is mandatory; verify with `stat -c '%a' .env` (should print `600`).

## What `overleap` does *not* do with the cookie

- It does not send the cookie anywhere except `https://www.overleaf.com` (or the URL passed via `--url` / `OVERLEAF_URL`).
- It does not log the cookie. Stack traces from unhandled rejections are scrubbed in `bin/overleap.js`.
- It does not write the cookie to any file other than the one you put it in.

If you ever suspect the cookie was leaked (committed to git, posted in a chat, etc.), revoke it immediately by signing out of *all* Overleaf sessions in the web UI (Account Settings → Sessions → "Log out other sessions").
