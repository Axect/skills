#!/usr/bin/env python3
"""Read pages from the user's logged-in Chrome through Playwright MCP --extension.

All commands share ONE tab in the agent's tab group. The first command starts a
background daemon that owns the Playwright MCP session (and its tab); later
commands reuse it over a Unix socket. The daemon closes the tab and exits after
CHROME_SESSION_IDLE seconds without a command (default 600) or on `stop`.
The user's own tabs are never visible to it.

Usage:
  chrome_session.py text     URL|-             # page innerText
  chrome_session.py fetch    URL|- PATH [PATH…] # same-origin fetch() from inside the logged-in page
  chrome_session.py eval     URL|- JS_FUNCTION  # run an async arrow function in the page, print result
  chrome_session.py snapshot URL|-              # accessibility snapshot (Playwright YAML)
  chrome_session.py nav      URL                # navigate only
  chrome_session.py tool     URL|- NAME JSON    # raw Playwright MCP tool call, e.g. browser_click {"element":..,"ref":..}
  chrome_session.py status                      # is the daemon/tab alive, and where is it
  chrome_session.py stop                        # close the tab and stop the daemon

URL `-` stays on the current page (no navigation).

Token: PLAYWRIGHT_MCP_EXTENSION_TOKEN from the environment, else from
~/.config/playwright-mcp/token.env (KEY=VALUE, chmod 600).
"""
import fcntl
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

TOKEN_FILE = os.path.expanduser("~/.config/playwright-mcp/token.env")
RUNTIME_DIR = os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir()
SOCK = os.path.join(RUNTIME_DIR, f"chrome-session-{os.getuid()}.sock")
LOCK = SOCK + ".lock"
LOG = SOCK + ".log"
IDLE = float(os.environ.get("CHROME_SESSION_IDLE", "600"))
COMMANDS = {"text", "fetch", "eval", "snapshot", "nav", "tool"}


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
                                 "clientInfo": {"name": "chrome-session", "version": "2"}})
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
                raise EOFError("playwright-mcp exited (is the Chrome extension installed and the token current?)")
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
        except Exception:
            pass
        finally:
            self.proc.terminate()
            shutil.rmtree(self.workdir, ignore_errors=True)


def page_url(text):
    lines = [l for l in text.splitlines() if l.startswith("- Page URL:")]
    return lines[0].split(":", 1)[1].strip() if lines else None


def run(s, cmd, url, args):
    """Execute one command in the shared tab; return (stdout, landed_url)."""
    landed = None
    if url != "-":
        landed = page_url(s.call("browser_navigate", {"url": url}))
    if cmd == "nav":
        out = ""
    elif cmd == "snapshot":
        out = s.call("browser_snapshot", {})
    elif cmd == "text":
        out = s.evaluate("() => document.body.innerText")
        out = out if isinstance(out, str) else json.dumps(out, ensure_ascii=False)
    elif cmd == "eval":
        out = json.dumps(s.evaluate(args[0]), ensure_ascii=False, indent=1)
    elif cmd == "tool":
        out = s.call(args[0], json.loads(args[1]))
    else:  # fetch
        fn = ("async () => { const out = {}; for (const p of %s) {"
              " const r = await fetch(p, {credentials: 'include'});"
              " const t = await r.text(); let b; try { b = JSON.parse(t); } catch { b = t; }"
              " out[p] = {status: r.status, body: b}; } return out; }") % json.dumps(args)
        out = json.dumps(s.evaluate(fn), ensure_ascii=False, indent=1)
    if landed is None:
        landed = s.evaluate("() => location.href")
    return out, landed


def recv_all(conn):
    chunks = []
    while True:
        b = conn.recv(65536)
        if not b:
            return b"".join(chunks)
        chunks.append(b)


def serve():
    s = Session()  # bind only once the MCP session is up: a live socket means ready
    srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    if os.path.exists(SOCK):
        os.unlink(SOCK)
    srv.bind(SOCK)
    os.chmod(SOCK, 0o600)
    srv.listen(8)
    srv.settimeout(IDLE)
    try:
        while True:
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                return  # idle: close the tab
            with conn:
                conn.settimeout(None)
                raw = recv_all(conn)  # client half-closes after sending
                if not raw:
                    continue  # liveness probe from ensure_daemon()
                req = json.loads(raw.decode())
                if req["cmd"] == "stop":
                    reply(conn, {"ok": True, "out": "stopped", "landed": None})
                    return
                try:
                    if req["cmd"] == "status":
                        out, landed = "alive", s.evaluate("() => location.href")
                    else:
                        out, landed = run(s, req["cmd"], req["url"], req["args"])
                    resp = {"ok": True, "out": out, "landed": landed}
                except EOFError as e:
                    reply(conn, {"ok": False, "err": str(e)})
                    return  # MCP server died: nothing left to reuse
                except Exception as e:
                    resp = {"ok": False, "err": str(e)}
                reply(conn, resp)
    finally:
        s.close()
        srv.close()
        if os.path.exists(SOCK):
            os.unlink(SOCK)


def reply(conn, resp):
    # A client killed mid-request (timeout, Ctrl-C) must not take the daemon and its tab down.
    try:
        conn.sendall(json.dumps(resp).encode())
    except OSError:
        pass


def connect():
    c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    c.connect(SOCK)
    return c


def ensure_daemon():
    try:
        connect().close()
        return
    except OSError:
        pass
    with open(LOCK, "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)  # one starter at a time
        try:
            connect().close()
            return
        except OSError:
            pass
        proc = subprocess.Popen([sys.executable, os.path.abspath(__file__), "serve"],
                                stdin=subprocess.DEVNULL, stdout=open(LOG, "a"), stderr=subprocess.STDOUT,
                                start_new_session=True)
        deadline = time.time() + 120  # first run downloads @playwright/mcp
        while time.time() < deadline and proc.poll() is None:
            try:
                connect().close()
                return
            except OSError:
                time.sleep(0.3)
        sys.exit(f"chrome-session daemon did not start; see {LOG}")


def request(req):
    c = connect()
    with c:
        c.sendall(json.dumps(req).encode())
        c.shutdown(socket.SHUT_WR)
        return json.loads(recv_all(c).decode())


def main(argv):
    cmd = argv[1] if len(argv) > 1 else None
    if cmd == "serve":
        return serve()
    if cmd in {"stop", "status"}:
        if not os.path.exists(SOCK):
            print("not running")
            return
        try:
            resp = request({"cmd": cmd})
        except OSError:
            print("not running")
            return
    else:
        if cmd not in COMMANDS or len(argv) < 3 or (cmd in {"eval", "fetch"} and len(argv) < 4) \
                or (cmd == "tool" and len(argv) < 5) \
                or (cmd == "nav" and argv[2] == "-"):
            sys.exit(__doc__)
        ensure_daemon()
        resp = request({"cmd": cmd, "url": argv[2], "args": argv[3:]})
    if not resp["ok"]:
        sys.exit(resp["err"])
    if resp["out"]:
        print(resp["out"])
    if resp.get("landed"):
        print(f"# landed on: {resp['landed']}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv)
