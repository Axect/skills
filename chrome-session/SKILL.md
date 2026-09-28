---
name: chrome-session
description: "Read auth-walled pages from the user's own logged-in Chrome (Overleaf comments/threads JSON, Google Scholar, university-VPN resources, any site that CAPTCHAs or login-walls agent browsers) through Playwright MCP's Chrome extension. Use when a page needs the user's existing login and the agent's own browser is blocked or signed out. Opens and closes its own tab in a separate tab group; never touches the user's tabs; no per-connection approval dialog once the token is saved."
---

# chrome-session: the user's logged-in Chrome, via Playwright extension

One helper, `scripts/chrome_session.py`, starts `@playwright/mcp --extension`
for a single command, opens a new tab in the agent's own tab group, does the
read, closes the tab, and exits. The user's tabs are invisible to it.

## Why this tool (checked 2026-09-28, Linux, Chrome 153)

| Option | Verdict |
|---|---|
| Playwright MCP `--extension` (this skill) | Uses the default profile's logins; agent sees only its tab group; token skips the approval dialog |
| Chrome DevTools MCP `--autoConnect` | Works, but Chrome shows an Allow dialog on every new server connection, and the agent sees every open window |
| `--remote-debugging-port` (Stagehand `connect`, browser-use, DevTools `--browser-url`) | Chrome ≥136 ignores it on the default profile: needs a separate profile and a second login |
| ego-lite | macOS only; Linux is roadmap |
| Copying the Cookies DB | Encrypted with the OS keyring key; sites re-challenge anyway. Do not |

## Prerequisites (check first)

1. Chrome has the **Playwright Extension** (Chrome Web Store id `mmlmfjhmonkocbjadbfplnigmagldckm`).
2. Token file `~/.config/playwright-mcp/token.env`, mode 600:

       PLAYWRIGHT_MCP_EXTENSION_TOKEN=<value shown in the extension's status page>

   Or export the variable. The token is per Chrome profile; never print it.
3. Node/`npx` on PATH (first run downloads `@playwright/mcp`, ~30 s).

If the helper says `playwright-mcp exited`, the extension is missing or the
token is stale: ask the user to open the extension and copy the current token.

## Usage

    S=<skill dir>/scripts/chrome_session.py
    python3 $S text     https://scholar.google.com/citations?user=XXXX
    python3 $S fetch    https://www.overleaf.com/project/<id> /project/<id>/threads /project/<id>/ranges
    python3 $S eval     https://example.com "async () => document.title"
    python3 $S snapshot https://example.com

- `fetch` runs same-origin `fetch()` inside the logged-in page, so cookies and
  CSRF context apply. Prints `{path: {status, body}}` JSON. Best choice for sites
  with JSON APIs.
- The final URL goes to stderr as `# landed on:`; a login URL there means the
  user is not signed in to that site.
- One command = one tab. Run commands sequentially per site; several helpers can
  run at once (each MCP client gets its own tab group).

## Recipe: Overleaf review comments

    python3 $S fetch https://www.overleaf.com/project/<id> \
        /project/<id>/threads /project/<id>/ranges /Project/<id>/doc/<docid>/download

- `threads`: `{threadId: {messages: [{content, timestamp, user: {first_name, last_name}}], resolved}}`.
- `ranges`: `[{id: docid, ranges: {comments: [{op: {p, c, t}}]}}]`; `p` is a
  character offset, `c` the anchored text, `t` the thread id.
- Doc download returns raw text; line number = count of `\n` before `p`. Check
  `text[p:p+len(c)] == c` before trusting the mapping.

## Rules

- Read-only by default. Never click, type, or submit in the user's accounts
  unless the user asked for that exact action.
- Do not navigate to URLs that trigger actions (logout, delete, confirm links).
- The helper deletes the `.playwright-mcp/` output directory it runs in; if you
  drive the MCP server another way, delete that directory yourself.
- OMP note: OMP silently drops MCP servers whose args contain `@playwright/mcp`
  while `browser.enabled` is true, so use the helper instead of registering it.
