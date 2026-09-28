#!/usr/bin/env python3
"""Read pages from the user's logged-in Chrome through Playwright MCP --extension.

Every command opens its own tab in the agent's tab group, does its work there,
and closes that tab. The user's own tabs are never visible to it.

Usage:
  chrome_session.py text   URL              # page innerText
  chrome_session.py fetch  URL PATH [PATH…] # same-origin fetch() from inside the logged-in page
  chrome_session.py eval   URL JS_FUNCTION  # run an async arrow function in the page, print result
  chrome_session.py snapshot URL            # accessibility snapshot (Playwright YAML)

Token: PLAYWRIGHT_MCP_EXTENSION_TOKEN from the environment, else from
~/.config/playwright-mcp/token.env (KEY=VALUE, chmod 600).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

TOKEN_FILE = os.path.expanduser("~/.config/playwright-mcp/token.env")


def load_env():
    env = dict(os.environ)
    if "PLAYWRIGHT_MCP_EXTENSION_TOKEN" not in env and os.path.exists(TOKEN_FILE):
        for line in open(TOKEN_FILE):
            if "=" in line:
                k, v = line.strip().split("=", 1)
                env[k] = v
    if "PLAYWRIGHT_MCP_EXTENSION_TOKEN" not in env:
        sys.exit(f"no PLAYWRIGHT_MCP_EXTENSION_TOKEN (env or {TOKEN_FILE})")
    return env


class Session:
    def __init__(self):
        # The server writes .playwright-mcp/ (snapshots, console logs) into its cwd.
        self.workdir = tempfile.mkdtemp(prefix="chrome-session-")
        self.proc = subprocess.Popen(
            ["npx", "-y", "@playwright/mcp@latest", "--extension"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, env=load_env(), cwd=self.workdir)
        self.n = 0
        self._rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                 "clientInfo": {"name": "chrome-session", "version": "1"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _send(self, msg):
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

    def _rpc(self, method, params):
        self.n += 1
        self._send({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params})
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("playwright-mcp exited (is the Chrome extension installed and the token current?)")
            msg = json.loads(line)
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise RuntimeError(json.dumps(msg["error"]))
                return msg["result"]

    def call(self, tool, args):
        res = self._rpc("tools/call", {"name": tool, "arguments": args})
        text = "".join(c.get("text", "") for c in res.get("content", []))
        if res.get("isError"):
            raise RuntimeError(text)
        return text

    def evaluate(self, fn):
        out = self.call("browser_evaluate", {"function": fn})
        # Result block is "### Result\n<json>\n### Ran Playwright code…"
        body = out.split("### Result\n", 1)[1].split("\n### ", 1)[0].strip()
        return json.loads(body)

    def close(self):
        try:
            self.call("browser_close", {})
        finally:
            self.proc.terminate()
            shutil.rmtree(self.workdir, ignore_errors=True)


def main(argv):
    if len(argv) < 3 or argv[1] not in {"text", "fetch", "eval", "snapshot"}:
        sys.exit(__doc__)
    cmd, url = argv[1], argv[2]
    s = Session()
    try:
        nav = s.call("browser_navigate", {"url": url})
        if cmd == "snapshot":
            print(s.call("browser_snapshot", {}))
        elif cmd == "text":
            print(s.evaluate("() => document.body.innerText"))
        elif cmd == "eval":
            print(json.dumps(s.evaluate(argv[3]), ensure_ascii=False, indent=1))
        else:
            paths = json.dumps(argv[3:])
            fn = ("async () => { const out = {}; for (const p of %s) {"
                  " const r = await fetch(p, {credentials: 'include'});"
                  " const t = await r.text(); let b; try { b = JSON.parse(t); } catch { b = t; }"
                  " out[p] = {status: r.status, body: b}; } return out; }") % paths
            print(json.dumps(s.evaluate(fn), ensure_ascii=False, indent=1))
        final = [l for l in nav.splitlines() if l.startswith("- Page URL:")]
        if final:
            print(final[0].replace("- Page URL:", "# landed on:"), file=sys.stderr)
    finally:
        s.close()


if __name__ == "__main__":
    main(sys.argv)
