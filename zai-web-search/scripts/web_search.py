#!/usr/bin/env python3
"""z.ai web search via the web_search_prime MCP server.

Uses the GLM Coding Plan's bundled MCP endpoint (not the separately-billed
REST /paas/v4/web_search). Reads the key from pi's single source of truth,
~/.pi/agent/auth.json (zai-coding-cn.key), so there is no second credential file.

Exit codes: 0 ok, 1 bad arg, 2 no auth, 3 auth rejected, 4 search error,
5 network/parse, 64 usage. See SKILL.md.
"""
import argparse
import http.client
import json
import os
import re
import sys
import time
from urllib.parse import urlsplit

DEFAULT_AUTH = os.path.expanduser("~/.pi/agent/auth.json")
MCP_HOST = "api.z.ai"
MCP_PATH = "/api/mcp/web_search_prime/mcp"
PROTO = "2024-11-05"
TOOL = "web_search_prime"
NETWORK_RETRIES = 2
RETRY_DELAYS = (1.0, 3.0)


def die(code, msg):
    print(f"[web_search] {msg}", file=sys.stderr)
    sys.exit(code)


def load_key(path):
    try:
        with open(path) as f:
            d = json.load(f)
    except FileNotFoundError:
        die(2, f"auth file not found: {path}")
    except json.JSONDecodeError as e:
        die(2, f"auth file unreadable ({path}): {e}")
    entry = d.get("zai-coding-cn") or {}
    key = entry.get("key")
    if not key:
        die(2, f"no 'zai-coding-cn.key' in {path}")
    return key


def mcp_post(key, body, sid=None):
    """POST one JSONRPC message; return (text, session_id, http_status)."""
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if sid:
        headers["Mcp-Session-Id"] = sid
    conn = http.client.HTTPSConnection(MCP_HOST, timeout=70)
    try:
        conn.request("POST", MCP_PATH, body=json.dumps(body), headers=headers)
        resp = conn.getresponse()
        sid_back = resp.getheader("mcp-session-id")
        data = resp.read().decode("utf-8", "replace")
        status = resp.status
    finally:
        conn.close()
    return data, sid_back, status


def parse_sse_result(data):
    """Return the jsonrpc object that carries 'result' or 'error', else None."""
    best = None
    for m in re.finditer(r"^data:\s*(\{.*\})\s*$", data, re.M):
        try:
            o = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(o, dict) and ("result" in o or "error" in o):
            best = o
    return best


def _drill(t):
    """web_search_prime returns content[].text as a multiply JSON-escaped string.
    Keep json.loads-ing until we hit a list (or give up)."""
    for _ in range(5):
        try:
            t = json.loads(t)
        except (json.JSONDecodeError, TypeError):
            return None
        if isinstance(t, list):
            return t
        if not isinstance(t, str):
            return None
    return None


def unpack_items(result_obj):
    items = []
    for c in result_obj.get("content", []):
        if c.get("type") != "text":
            continue
        lst = _drill(c.get("text", ""))
        if isinstance(lst, list):
            for it in lst:
                if isinstance(it, dict):
                    items.append(it)
    return items


def domain_matches(link, domain):
    """Return whether link belongs to domain or one of its subdomains."""
    if not domain:
        return True

    wanted = domain.strip().lower()
    if "://" in wanted:
        wanted = urlsplit(wanted).hostname or ""
    else:
        wanted = wanted.split("/", 1)[0]
    wanted = wanted.rstrip(".")
    if wanted.startswith("*."):
        wanted = wanted[2:]
    if not wanted:
        return False

    try:
        host = urlsplit(link).hostname
    except ValueError:
        return False
    if not host:
        return False
    host = host.lower().rstrip(".")
    return host == wanted or host.endswith("." + wanted)


def search(key, query, limit, domain=None):
    # 1) initialize -> capture session id from response header
    _, sid, status = mcp_post(
        key,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTO,
                "capabilities": {},
                "clientInfo": {"name": "zai-web-search", "version": "1.0"},
            },
        },
    )
    if status == 401:
        die(3, "auth rejected (401) at initialize — key invalid or expired")
    if status != 200 or not sid:
        die(4, f"initialize failed (HTTP {status})")
    # 2) initialized notification (server sends no response)
    mcp_post(
        key,
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        sid=sid,
    )
    # 3) tools/call
    args = {"search_query": query}
    if domain:
        args["search_domain_filter"] = domain
    data, _, status = mcp_post(
        key,
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": TOOL, "arguments": args},
        },
        sid=sid,
    )
    obj = parse_sse_result(data)
    if obj is None:
        die(5, f"could not parse SSE response (HTTP {status}); head:\n{data[:300]}")
    if "error" in obj:
        ecode = obj["error"].get("code")
        emsg = obj["error"].get("message", "")
        if ecode == -401 or status == 401:
            die(3, f"auth rejected (MCP {ecode}): {emsg}")
        die(4, f"MCP error {ecode}: {emsg}")
    items = unpack_items(obj["result"])
    if domain:
        # The MCP server may return off-domain results despite accepting the
        # search_domain_filter argument, so enforce the whitelist locally too.
        items = [it for it in items if domain_matches(normalize(it)["link"], domain)]
    return items[:limit]


def normalize(it):
    return {
        "title": (it.get("title") or "").strip(),
        "link": it.get("link") or it.get("url") or "",
        "snippet": (it.get("content") or it.get("snippet") or "").strip(),
        "site": it.get("site_name") or it.get("site") or "",
    }


def main():
    ap = argparse.ArgumentParser(
        prog="web_search.py",
        description="z.ai web search via web_search_prime MCP (reads key from pi auth.json)",
    )
    ap.add_argument("query", nargs="?", help="search query (or use --query/-q)")
    ap.add_argument("-q", "--query", dest="qopt", help="search query (alternative to positional)")
    ap.add_argument("-n", "--limit", type=int, default=8, help="max results (default 8)")
    ap.add_argument("--domain", help="restrict to a domain, e.g. arxiv.org")
    ap.add_argument("--json", action="store_true", help="emit JSON for piping")
    ap.add_argument(
        "--auth",
        default=DEFAULT_AUTH,
        help=f"auth.json path (default {DEFAULT_AUTH})",
    )
    args = ap.parse_args()

    query = (args.qopt or args.query or "").strip()
    if not query:
        die(64, "no query given (positional or --query/-q)")
    if len(query) > 200:
        die(64, "query too long (>200 chars); MCP recommends <=70")

    key = load_key(args.auth)
    try:
        items = search(key, query, args.limit, args.domain)
    except (http.client.HTTPException, OSError) as first_error:
        # TLS connections to the MCP endpoint can fail transiently with EOF.
        # Retry the complete MCP handshake, but never retry auth/search errors
        # that are converted to exit codes inside search().
        last_error = first_error
        for attempt, delay in enumerate(RETRY_DELAYS, start=1):
            print(
                f"[web_search] transient network error; retrying "
                f"({attempt}/{NETWORK_RETRIES}) in {delay:g}s: {last_error}",
                file=sys.stderr,
            )
            time.sleep(delay)
            try:
                items = search(key, query, args.limit, args.domain)
                break
            except (http.client.HTTPException, OSError) as retry_error:
                last_error = retry_error
        else:
            die(
                5,
                f"network error after {NETWORK_RETRIES + 1} attempts: {last_error}",
            )

    rows = [normalize(it) for it in items]
    if args.json:
        json.dump(
            {"query": query, "count": len(rows), "results": rows},
            sys.stdout,
            ensure_ascii=False,
            indent=1,
        )
        sys.stdout.write("\n")
    else:
        if not rows:
            print("(no results)", file=sys.stderr)
        for i, r in enumerate(rows, 1):
            print(f"[{i}] {r['title']}")
            if r["link"]:
                print(f"    {r['link']}")
            if r["snippet"]:
                print(f"    {r['snippet'][:220]}")


if __name__ == "__main__":
    main()
