#!/usr/bin/env bash
# morgen todos: local-cached TODO management via the Morgen Tasks API.
#
# Design: manual sync, cache-first reads, mutations hit the API and then
# patch the local cache. No automatic sync, no conflict resolution — if the
# mobile app diverges, the next `sync` wins.
#
# Cache: $MORGEN_CACHE_DIR/todos.json  (default: ~/.cache/morgen-skill/todos.json)
#   Format: {"synced_at": <unix_ts>, "tasks": [...]}
#
# Usage:
#   todos.sh sync
#   todos.sh list [--all] [--tag <id>] [--priority <n>]
#   todos.sh today
#   todos.sh overdue
#   todos.sh show <taskIdOrPrefix>
#   todos.sh add <title> [--due <ISO>] [--priority <n>] [--tz <IANA>] [--description <text>]
#   todos.sh done <taskIdOrPrefix>
#   todos.sh reopen <taskIdOrPrefix>
#   todos.sh delete <taskIdOrPrefix>
#
# Environment:
#   MORGEN_CACHE_DIR       cache directory (default: ~/.cache/morgen-skill)
#   MORGEN_STALE_SECONDS   age threshold for stale warning (default: 3600)

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=auth.sh
source "$SCRIPT_DIR/auth.sh"

morgen_require_deps

MORGEN_CACHE_DIR="${MORGEN_CACHE_DIR:-$HOME/.cache/morgen-skill}"
MORGEN_TODOS_CACHE="$MORGEN_CACHE_DIR/todos.json"
STALE_SECONDS="${MORGEN_STALE_SECONDS:-3600}"

usage() {
  cat >&2 <<'EOF'
Usage:
  todos.sh sync
  todos.sh list [--all] [--tag <id>] [--priority <n>]
  todos.sh today
  todos.sh overdue
  todos.sh show <taskIdOrPrefix>
  todos.sh add <title> [--due <ISO>] [--priority <n>] [--tz <IANA>] [--description <text>]
  todos.sh done <taskIdOrPrefix>
  todos.sh reopen <taskIdOrPrefix>
  todos.sh delete <taskIdOrPrefix>
EOF
  exit 64
}

ensure_cache() {
  if [[ ! -f "$MORGEN_TODOS_CACHE" ]]; then
    echo "morgen: no todo cache yet. Run: todos.sh sync" >&2
    return 2
  fi
}

check_stale() {
  local synced_at now age mins
  synced_at=$(jq -r '.synced_at // 0' "$MORGEN_TODOS_CACHE")
  now=$(date +%s)
  age=$(( now - synced_at ))
  if (( age > STALE_SECONDS )); then
    mins=$(( age / 60 ))
    if (( mins < 60 )); then
      echo "morgen: last sync ${mins}m ago. Run 'todos.sh sync' to refresh." >&2
    else
      echo "morgen: last sync $(( mins / 60 ))h$(( mins % 60 ))m ago. Run 'todos.sh sync' to refresh." >&2
    fi
  fi
}

write_cache_atomic() {
  local content="$1"
  local tmp
  tmp=$(mktemp "${MORGEN_TODOS_CACHE}.XXXXXX")
  printf '%s' "$content" > "$tmp"
  mv "$tmp" "$MORGEN_TODOS_CACHE"
  chmod 600 "$MORGEN_TODOS_CACHE" 2>/dev/null || true
}

patch_cache() {
  # patch_cache <jq_filter>
  [[ -f "$MORGEN_TODOS_CACHE" ]] || return 0
  local patched
  patched=$(jq "$1" "$MORGEN_TODOS_CACHE") || return 1
  write_cache_atomic "$patched"
}

format_tasks() {
  # Reads a JSON array of tasks from stdin and emits one line per task.
  # Priority symbol: 1 -> !!!, 2 -> !!, 3 -> !, else space.
  # Status symbol: completed -> ✓, else ·
  jq -r '
    def prio: if . == 1 then "!!!" elif . == 2 then " !!" elif . == 3 then "  !" else "   " end;
    def stat: if . == "completed" then "✓" else "·" end;
    def due_str: if . == null or . == "" then "" else "  (due: \(.))" end;
    .[]
    | "\(.progress // "needs-action" | stat) [\(.priority // 0 | prio)] \(.id[0:8])  \(.title)\(.due | due_str)"
  '
}

resolve_id() {
  # Resolve a full or prefix ID to a full ID using the cache. Prints the full
  # ID on stdout if found, or the original input as a fallback.
  local input="$1"
  if [[ -f "$MORGEN_TODOS_CACHE" ]]; then
    local matches
    matches=$(jq -r --arg s "$input" '
      .tasks[]
      | select(.id == $s or (.id | startswith($s)))
      | .id
    ' "$MORGEN_TODOS_CACHE")
    local n
    n=$(printf '%s' "$matches" | grep -c . || true)
    if [[ "$n" == "1" ]]; then
      printf '%s' "$matches"
      return 0
    elif [[ "$n" -gt 1 ]]; then
      echo "morgen: id prefix '$input' matches $n tasks:" >&2
      printf '%s\n' "$matches" >&2
      return 1
    fi
  fi
  printf '%s' "$input"
}

cmd_sync() {
  mkdir -p "$MORGEN_CACHE_DIR"
  local resp rc
  resp=$(morgen_api_call GET "/tasks/list?limit=1000")
  rc=$?
  if [[ $rc -ne 0 ]]; then
    return $rc
  fi
  local now count content
  now=$(date +%s)
  count=$(printf '%s' "$resp" | jq '.data.tasks | length')
  content=$(printf '%s' "$resp" | jq --argjson t "$now" \
    '{synced_at: $t, tasks: .data.tasks}')
  write_cache_atomic "$content"
  echo "synced $count tasks at $(date -d "@$now" '+%Y-%m-%d %H:%M:%S')"
}

cmd_list() {
  ensure_cache || return $?
  check_stale
  local include_done=false tag="" priority=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --all) include_done=true; shift ;;
      --tag) tag="${2:-}"; shift 2 ;;
      --priority)
        priority="${2:-}"
        [[ "$priority" =~ ^[0-9]+$ ]] || { echo "morgen: --priority must be a non-negative integer" >&2; return 1; }
        shift 2
        ;;
      *) echo "morgen: unknown flag: $1" >&2; return 1 ;;
    esac
  done

  jq --argjson include_done "$include_done" \
     --arg tag "$tag" \
     --arg priority "$priority" '
    .tasks
    | map(select($include_done or (.progress // "needs-action") != "completed"))
    | map(select($tag == "" or (.tags // [] | index($tag))))
    | map(select($priority == "" or (.priority|tostring) == $priority))
  ' "$MORGEN_TODOS_CACHE" | format_tasks
}

cmd_today() {
  ensure_cache || return $?
  check_stale
  local today
  today=$(date +%Y-%m-%d)
  jq --arg d "$today" '
    .tasks
    | map(select(
        (.progress // "needs-action") != "completed"
        and (.due // "" | startswith($d))
      ))
  ' "$MORGEN_TODOS_CACHE" | format_tasks
}

cmd_overdue() {
  ensure_cache || return $?
  check_stale
  local now_iso
  now_iso=$(date +%Y-%m-%dT%H:%M:%S)
  jq --arg n "$now_iso" '
    .tasks
    | map(select(
        (.progress // "needs-action") != "completed"
        and (.due // "") != ""
        and (.due < $n)
      ))
  ' "$MORGEN_TODOS_CACHE" | format_tasks
}

cmd_show() {
  [[ $# -lt 1 ]] && usage
  ensure_cache || return $?
  check_stale
  local id
  id=$(resolve_id "$1") || return $?
  jq --arg id "$id" '.tasks[] | select(.id == $id)' "$MORGEN_TODOS_CACHE"
}

cmd_add() {
  [[ $# -lt 1 ]] && usage
  local title="$1"; shift
  local due="" priority="" tz="" description=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --due)         due="${2:-}"; shift 2 ;;
      --priority)
        priority="${2:-}"
        [[ "$priority" =~ ^[0-9]+$ ]] || { echo "morgen: --priority must be a non-negative integer" >&2; return 1; }
        shift 2
        ;;
      --tz)          tz="${2:-}"; shift 2 ;;
      --description) description="${2:-}"; shift 2 ;;
      *) echo "morgen: unknown flag: $1" >&2; return 1 ;;
    esac
  done

  local body
  body=$(jq -n --arg t "$title" '{title: $t}')
  [[ -n "$due" ]]         && body=$(printf '%s' "$body" | jq --arg v "$due" '. + {due: $v}')
  [[ -n "$priority" ]]    && body=$(printf '%s' "$body" | jq --argjson v "$priority" '. + {priority: $v}')
  [[ -n "$tz" ]]          && body=$(printf '%s' "$body" | jq --arg v "$tz" '. + {timeZone: $v}')
  [[ -n "$description" ]] && body=$(printf '%s' "$body" | jq --arg v "$description" '. + {description: $v}')

  local resp new_id
  resp=$(morgen_api_call POST "/tasks/create" "$body") || return $?
  new_id=$(printf '%s' "$resp" | jq -r '.data.id')
  if [[ -z "$new_id" || "$new_id" == "null" ]]; then
    echo "morgen: create response did not contain an id: $resp" >&2
    return 5
  fi
  echo "created: $new_id"

  # Patch local cache with a stub built from what we sent.
  if [[ -f "$MORGEN_TODOS_CACHE" ]]; then
    local stub
    stub=$(printf '%s' "$body" | jq --arg id "$new_id" '. + {id: $id, progress: "needs-action"}')
    patch_cache ".tasks += [$stub]"
  fi
}

cmd_done() {
  [[ $# -lt 1 ]] && usage
  local id
  id=$(resolve_id "$1") || return $?
  local body
  body=$(jq -n --arg id "$id" '{id: $id}')
  morgen_api_call POST "/tasks/close" "$body" >/dev/null || return $?
  patch_cache ".tasks |= map(if .id == \"$id\" then .progress = \"completed\" else . end)"
  echo "closed: $id"
}

cmd_reopen() {
  [[ $# -lt 1 ]] && usage
  local id
  id=$(resolve_id "$1") || return $?
  local body
  body=$(jq -n --arg id "$id" '{id: $id}')
  morgen_api_call POST "/tasks/reopen" "$body" >/dev/null || return $?
  patch_cache ".tasks |= map(if .id == \"$id\" then .progress = \"needs-action\" else . end)"
  echo "reopened: $id"
}

cmd_delete() {
  [[ $# -lt 1 ]] && usage
  local id
  id=$(resolve_id "$1") || return $?
  local body
  body=$(jq -n --arg id "$id" '{id: $id}')
  morgen_api_call POST "/tasks/delete" "$body" >/dev/null || return $?
  patch_cache ".tasks |= map(select(.id != \"$id\"))"
  echo "deleted: $id"
}

cmd="${1:-}"
shift || true

case "$cmd" in
  sync)    cmd_sync "$@" ;;
  list)    cmd_list "$@" ;;
  today)   cmd_today "$@" ;;
  overdue) cmd_overdue "$@" ;;
  show)    cmd_show "$@" ;;
  add)     cmd_add "$@" ;;
  done)    cmd_done "$@" ;;
  reopen)  cmd_reopen "$@" ;;
  delete)  cmd_delete "$@" ;;
  *)       usage ;;
esac
