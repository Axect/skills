# Morgen skill: worked examples

All examples assume you are in the skill directory and `setup.sh` has been run. Output is pretty-printed with `jq` when useful.

## 1. List connected accounts and calendars

```bash
# Connected accounts (provider, accountId, auth status)
bash scripts/integrations.sh accounts | jq '.data.accounts[] | {id, providerId, email: .user.email}'

# Calendars across all accounts
bash scripts/calendars.sh list | jq '.data.calendars[] | {name, id, accountId, integrationId}'
```

Cache one `accountId` / `calendarId` pair for the rest of the session — do not call `list` in a loop (it costs 10 rate-limit points per call).

## 2. Show today's events on one calendar

```bash
ACC="640a62c9aa5b7e06cf420000"
CAL="WyI2NDBhNjJjOW..."
TODAY=$(date -u +%Y-%m-%d)
START="${TODAY}T00:00:00Z"
END="${TODAY}T23:59:59Z"

bash scripts/events.sh list "$ACC" "$CAL" "$START" "$END" \
  | jq '.data.events[] | {title, start, duration, timeZone}'
```

To query multiple calendars at once, pass a comma-separated string:

```bash
bash scripts/events.sh list "$ACC" "$CAL1,$CAL2" "$START" "$END"
```

## 3. Create a 1-hour meeting

```bash
cat > /tmp/event.json <<'JSON'
{
  "accountId": "640a62c9aa5b7e06cf420000",
  "calendarId": "WyI2NDBhNjJjOW...",
  "title": "Review: Q2 roadmap",
  "description": "See Confluence doc for agenda.",
  "start": "2026-04-21T14:00:00",
  "duration": "PT1H",
  "timeZone": "Europe/Berlin",
  "showWithoutTime": false
}
JSON

bash scripts/events.sh create "$(cat /tmp/event.json)"
```

Or stream via stdin:

```bash
bash scripts/events.sh create - < /tmp/event.json
```

## 4. Reschedule a recurring event (single occurrence only)

```bash
cat > /tmp/update.json <<'JSON'
{
  "accountId": "640a62c9aa5b7e06cf420000",
  "calendarId": "WyI2NDBhNjJjOW...",
  "masterEventId": "abc123...",
  "recurrenceId": "2026-04-28T14:00:00",
  "start": "2026-04-28T15:30:00",
  "duration": "PT1H",
  "timeZone": "Europe/Berlin",
  "showWithoutTime": false
}
JSON

bash scripts/events.sh update "$(cat /tmp/update.json)" single
```

Change `single` to `future` to reschedule that occurrence and every one after it, or `all` to edit the whole series.

**Important**: `start`, `duration`, `timeZone`, and `showWithoutTime` must be sent as a group — include all four whenever any one of them is in the update body, otherwise the API returns HTTP 400. Re-send the current values for the fields you're not changing.

## 5. TODO workflow with local cache (recommended)

`todos.sh` keeps a local mirror of your tasks at `~/.cache/morgen-skill/todos.json`, so filtered reads cost nothing and writes stay consistent with the API.

```bash
# Once per session (or whenever you suspect drift): 10 rate-limit points
bash scripts/todos.sh sync
# -> synced 47 tasks at 2026-04-21 09:14:02

# Zero-cost reads afterwards
bash scripts/todos.sh list
# · [!!!] aaaa1111  Review grant proposal  (due: 2026-04-25T17:00:00)
# · [ !!] bbbb2222  Reply to reviewer      (due: 2026-04-21T09:00:00)
# · [!!!] dddd4444  Write intro section    (due: 2026-04-21T15:00:00)

bash scripts/todos.sh today
bash scripts/todos.sh overdue
bash scripts/todos.sh list --priority 1
bash scripts/todos.sh list --tag research
bash scripts/todos.sh list --all                # include completed

# Add a new TODO (1 pt) — cache is patched in-place
bash scripts/todos.sh add "Proofread draft" \
  --due 2026-04-22T17:00:00 \
  --tz Asia/Seoul \
  --priority 2
# -> created: abcd1234efgh...

# Close a TODO by short-ID prefix (1 pt) — cache flipped to 'completed'
bash scripts/todos.sh done aaaa1111
# -> closed: aaaa1111bbbb...

# Reopen / delete work the same way
bash scripts/todos.sh reopen aaaa1111
bash scripts/todos.sh delete aaaa1111

# Detail view from cache
bash scripts/todos.sh show aaaa1111
```

Stale-cache notice appears automatically:

```
morgen: last sync 2h15m ago. Run 'todos.sh sync' to refresh.
```

You can silence it for a shell by setting `MORGEN_STALE_SECONDS=99999`, or change the cache dir with `MORGEN_CACHE_DIR`.

Rate-limit accounting for a typical research day: 1 `sync` (10 pts) + 30 mutations (30 pts) = **40 of 100 pts** used per 15 min window. The other 60 pts stay available for event queries or bulk edits.

## 6. Quick task triage (direct API, no cache)

```bash
# Pull up to 200 tasks updated in the last 24 hours
SINCE=$(date -u -d '-1 day' +%Y-%m-%dT%H:%M:%SZ)
bash scripts/tasks.sh list 200 "$SINCE" \
  | jq '.data.tasks[] | select(.progress != "completed") | {id, title, due, priority}'

# Close one
bash scripts/tasks.sh close "task_id_here"

# Reopen it
bash scripts/tasks.sh reopen "task_id_here"
```

## 7. Create a high-priority task

```bash
cat > /tmp/task.json <<'JSON'
{
  "title": "Review grant proposal before Friday",
  "description": "Focus on methodology section.",
  "due": "2026-04-25T17:00:00",
  "timeZone": "Europe/Berlin",
  "priority": 1
}
JSON

bash scripts/tasks.sh create "$(cat /tmp/task.json)"
# -> {"data":{"id":"<TASK_ID>"}}
```

## 8. Bulk tag cleanup

```bash
# List all tags
bash scripts/tags.sh list | jq '.data.tags[] | {id, name, color}'

# Rename one
bash scripts/tags.sh update "tag_id" "research" "#1E88E5"

# Soft-delete stale tags
for id in tag1 tag2 tag3; do
  bash scripts/tags.sh delete "$id"
done
```

## 9. Handling rate limits

```bash
out=$(bash scripts/events.sh list "$ACC" "$CAL" "$START" "$END" 2>&1)
rc=$?
if [[ $rc -eq 6 ]]; then
  # Parse Retry-After from the error line, or just wait 60s as a safe default.
  echo "Rate-limited. Sleeping 60s." >&2
  sleep 60
  out=$(bash scripts/events.sh list "$ACC" "$CAL" "$START" "$END")
fi
echo "$out"
```

## 10. Re-keying (API key rotated)

```bash
rm -f ~/.config/morgen-skill/credentials.json
bash scripts/setup.sh
```

## 11. Non-interactive setup (skill-orchestrated)

When Claude runs setup on your behalf (e.g. after you paste a key into chat), it uses `--stdin` so the key stays out of argv:

```bash
bash scripts/setup.sh --stdin <<< 'paste_your_key_here'
# Setup complete. Credentials saved to /home/you/.config/morgen-skill/credentials.json
```

Scripted bootstrap (e.g. from a password manager):

```bash
bash scripts/setup.sh --stdin <<< "$(pass show morgen/api-key)"
```

Avoid `--key` in shell history or multi-user machines; it exposes the key via `/proc/<pid>/cmdline` for the lifetime of the process.

