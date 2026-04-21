# Morgen API Reference (v3)

Companion reference for the `morgen` skill. Authoritative source: https://docs.morgen.so/

- **Base URL**: `https://api.morgen.so/v3`
- **Auth header**: `Authorization: ApiKey <API_KEY>`
- **Content-Type**: `application/json` for all write endpoints
- **Rate limit**: 100 points / 15 min (list = 10 pts, others = 1 pt)

## Calendars

| Method | Path | Purpose |
|---|---|---|
| GET | `/calendars/list` | List all calendars across connected accounts |
| POST | `/calendars/update` | Patch `morgen.so:metadata` (busy, overrideColor, overrideName) |

Calendar object (selected fields):
- `id`, `accountId`, `integrationId`
- `name`, `color`, `sortOrder`
- `myRights` — permissions object
- `defaultAlertsWithTime`, `defaultAlertsWithoutTime`
- `morgen.so:metadata` — user-level overrides

## Events

| Method | Path | Purpose |
|---|---|---|
| GET | `/events/list` | List events in a window |
| POST | `/events/create` | Create event |
| POST | `/events/update?seriesUpdateMode=...` | Update event (or series) |
| POST | `/events/delete?seriesUpdateMode=...` | Delete event (or series) |

### /events/list query parameters

| Param | Required | Notes |
|---|---|---|
| `accountId` | yes | Account of the target calendars |
| `calendarIds` | yes | Comma-separated calendar IDs |
| `start` | yes | ISO 8601 UTC, e.g. `2026-04-21T00:00:00Z` |
| `end` | yes | ISO 8601 UTC; max 6-month window from `start` |

### /events/create body

Required: `accountId`, `calendarId`, `title`, `start`, `duration`, `timeZone`, `showWithoutTime`.

Optional: `description`, `locations`, `participants`, `alerts`, `privacy`, `recurrenceRules`, `google.com:colorId`.

- `start`: **local** ISO 8601 without timezone suffix, e.g. `2026-04-21T14:00:00`
- `duration`: ISO 8601 duration, e.g. `PT25M`, `PT1H`, `PT1H30M`
- `timeZone`: IANA, e.g. `Europe/Berlin`
- `showWithoutTime`: boolean (all-day flag)

### /events/update body

Required: `accountId`, `calendarId`, AND either `id` OR (`masterEventId` + `recurrenceId`).

Any other field patches the event, with one exception:

**Atomic group** — `start`, `duration`, `timeZone`, and `showWithoutTime` must be sent **together** whenever any of them is included. Sending only a subset returns HTTP 400 `MRG_ERR_VALIDATION_FAILED: "Properties start, duration, timeZone and showWithoutTime must be provided together. timeZone can be null to indicate floating events."` To patch just one of these (e.g. extend a meeting's `duration`), re-send the existing values for the other three. `timeZone: null` marks the event as floating.

`seriesUpdateMode` ∈ {`single`, `all`, `future`}. Default `single`.

### /events/delete body

Required: `accountId`, `calendarId`, `id`. Same `seriesUpdateMode` query param.

## Tasks

| Method | Path | Purpose |
|---|---|---|
| GET | `/tasks/list` | List tasks (paginated by `limit`, filter by `updatedAfter`) |
| GET | `/tasks?id=…` | Get one task |
| POST | `/tasks/create` | Create task (requires `title`) |
| POST | `/tasks/update` | Patch task (requires `id`) |
| POST | `/tasks/move` | Reorder / reparent task |
| POST | `/tasks/close` | Mark done (optional `occurrenceStart` for recurring) |
| POST | `/tasks/reopen` | Reopen a closed task |
| POST | `/tasks/delete` | Delete task |

Task fields: `id`, `title`, `description`, `due`, `timeZone`, `priority`, `progress`, `tags`, `relatedTo`, plus subtask hierarchy via `parentId` / ordering via `previousId`.

All mutating task endpoints return HTTP 204 on success.

## Integrations

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/integrations/accounts/list` | yes | List user's connected accounts |
| GET | `/integrations/list` | no | List available providers and capabilities |

Connect/disconnect must happen in the Morgen app — no API endpoint exists for it.

Supported providers:
- **Calendars**: Google Calendar, Office 365, iCloud, Fastmail, CalDAV, calendar feeds
- **Video**: Zoom, Webex (plus Google Meet / MS Teams via the underlying calendar)
- **Tasks / Automation**: see `/integrations/list` response for the current set

## Tags

| Method | Path | Purpose |
|---|---|---|
| GET | `/tags/list` | List tags (optional `limit`, `updatedAfter`) |
| GET | `/tags?id=…` | Get one tag |
| POST | `/tags/create` | Create tag (`name` required, `color` optional hex) |
| POST | `/tags/update` | Patch tag (`id` required) |
| POST | `/tags/delete` | Soft-delete; tag returns with `deleted: true` on sync |

## Rate-limit headers

Every response includes:
- `RateLimit-Limit` — points allowed in the current window
- `RateLimit-Remaining` — points left
- `RateLimit-Reset` — seconds until the window resets
- `Retry-After` — only on 429, seconds to wait before retrying

The `auth.sh` helper does not surface these headers by default. If rate-limit tracking matters, call `curl -D -` directly and parse the header lines.

## Errors to expect

| HTTP | Meaning | Handler |
|---|---|---|
| 400 | Bad request (missing field, malformed JSON) | Fix payload; exit 5 |
| 401/403 | API key missing / rejected | Re-run `setup.sh`; exit 3 |
| 404 | Resource not found | Verify IDs; exit 4 |
| 409 | Conflict (stale state, duplicate) | Refresh and retry; exit 5 |
| 429 | Rate-limited | Sleep `Retry-After` seconds; exit 6 |
| 5xx | Server issue | Retry with backoff; exit 5 |
