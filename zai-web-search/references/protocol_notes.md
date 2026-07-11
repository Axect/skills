# Protocol notes — why this skill uses MCP and not the REST API

This documents the non-obvious mechanics behind `scripts/web_search.py`, so that
future maintenance (or porting to another client) does not have to rediscover
them.

## Two endpoints, one billing model

z.ai exposes web search two ways:

| Endpoint | Path | Billing | Status when this skill was written |
|---|---|---|---|
| **REST** | `POST https://api.z.ai/api/paas/v4/web_search` | Pay-as-you-go `paas` balance | Returns `429 {code:1113, "Insufficient balance or no resource package"}` unless the account is recharged separately |
| **MCP** | `POST https://api.z.ai/api/mcp/web_search_prime/mcp` | **Bundled with GLM Coding Plan** | Works with the same Coding Plan key pi already uses |

The skill uses the **MCP** endpoint exclusively. The wrapper retries transient
HTTP/TLS connection failures twice, restarting the complete MCP handshake for
each retry. The Coding Plan key in
`~/.pi/agent/auth.json` (`zai-coding-cn.key`) is authorized for MCP but the REST
endpoint reports insufficient balance — so calling REST would mislead the user
into thinking they need to recharge, when in fact their subscription already
covers web search via MCP.

## MCP streamable-HTTP handshake

The MCP server speaks the "streamable HTTP" transport, not plain request/response.
A working `tools/call` requires three round-trips:

1. `initialize` — send protocol version + client info. The response **header**
   `Mcp-Session-Id` must be captured; it is NOT in the JSON body.
2. `notifications/initialized` — a notification (no `id`, no response expected)
   that completes the capability handshake. Skipping this makes some servers
   reject the subsequent call.
3. `tools/call` with `name: "web_search_prime"` and `arguments: {search_query, ...}`.
   Must include the `Mcp-Session-Id` header captured in step 1.

Because the session id lives in the HTTP **response header** of step 1, the script
uses `http.client` directly (so it can read `resp.getheader("mcp-session-id")`)
rather than `urllib.request`, which discards headers on `urlopen`.

## Response shape: SSE + multiply-escaped JSON

The server answers steps 1 and 3 with `text/event-stream` (SSE):

```
id:1
event:message
data:{"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"\"[{\\\"title\\\":\\\"...\\\",...}]\""}]}}
```

Two traps:

1. **The payload is SSE, not JSON.** Parse lines matching `^data:\s*(\{.*\})$`
   and `json.loads` each; keep the one carrying `result` or `error`.
2. **The `content[].text` string is JSON-escaped multiple times.** The actual
   result list is buried under 2–3 layers of `json.dumps`. `_drill()` in the
   script keeps `json.loads`-ing until it reaches a Python `list`, up to 5 times.
   This is the single biggest source of "the script returned nothing" bugs if
   someone rewrites it naively.

Each item in the final list has roughly:
```
{ "title": "...", "link": "...", "content": "<short snippet>",
  "site_name": "...", "refer": "ref_N", ... }
```
The script normalizes to `{title, link, snippet, site}`.

## Optional arguments

`web_search_prime` accepts (from the server's `inputSchema`):

- `search_query` (required, ≤70 chars recommended)
- `search_domain_filter` (optional) — whitelist a single domain. The upstream
  service may still return off-domain results, so the wrapper applies a local
  hostname check after parsing the response; the requested domain and its
  subdomains are accepted.
- others may exist; the schema is the source of truth. The skill exposes only
  `search_query` and `search_domain_filter` (`--domain`).

## Why not add this as a pi MCP server instead of a skill?

You could register the MCP endpoint in pi config and let pi speak MCP natively.
That is a valid future option, but at the time this skill was written:

- pi's MCP integration surface was not the path of least resistance, and
- wrapping the handshake in a plain Python script keeps the capability usable
  from any tool (pi, a shell pipeline, another skill, cron) without depending
  on a particular client's MCP support.

If pi later gains first-class remote-MCP support and auto-injects the Coding
Plan key, this skill can thin out to a thin wrapper or be retired.
