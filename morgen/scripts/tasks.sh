#!/usr/bin/env bash
# morgen tasks: list / get / create / update / move / close / reopen / delete.
#
# Usage:
#   tasks.sh list   [limit] [updatedAfterISO]
#   tasks.sh get    <taskId>
#   tasks.sh create <json_body|->
#   tasks.sh update <json_body|->
#   tasks.sh move   <taskId> [previousId] [parentId]
#   tasks.sh close  <taskId> [occurrenceStart]
#   tasks.sh reopen <taskId> [occurrenceStart]
#   tasks.sh delete <taskId>

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=auth.sh
source "$SCRIPT_DIR/auth.sh"

morgen_require_deps

usage() {
  cat >&2 <<'EOF'
Usage:
  tasks.sh list   [limit] [updatedAfterISO]
  tasks.sh get    <taskId>
  tasks.sh create <json_body|->
  tasks.sh update <json_body|->
  tasks.sh move   <taskId> [previousId] [parentId]
  tasks.sh close  <taskId> [occurrenceStart]
  tasks.sh reopen <taskId> [occurrenceStart]
  tasks.sh delete <taskId>
EOF
  exit 64
}

urlencode() { jq -rn --arg v "$1" '$v|@uri'; }

read_body() {
  local arg="$1"
  if [[ "$arg" == "-" ]]; then cat; else printf '%s' "$arg"; fi
}

post_with_id() {
  # post_with_id <path> <taskId> [key=value ...]
  local path="$1"; local id="$2"; shift 2
  local body
  body=$(jq -n --arg id "$id" '{id:$id}')
  local k v
  for pair in "$@"; do
    k="${pair%%=*}"; v="${pair#*=}"
    if [[ -n "$v" ]]; then
      body=$(printf '%s' "$body" | jq --arg k "$k" --arg v "$v" '. + {($k):$v}')
    fi
  done
  morgen_api_call POST "$path" "$body"
}

cmd="${1:-}"
shift || true

case "$cmd" in
  list)
    limit="${1:-}"; updated_after="${2:-}"
    qs=""
    if [[ -n "$limit" ]]; then qs="limit=$(urlencode "$limit")"; fi
    if [[ -n "$updated_after" ]]; then
      [[ -n "$qs" ]] && qs="$qs&"
      qs="${qs}updatedAfter=$(urlencode "$updated_after")"
    fi
    path="/tasks/list"
    [[ -n "$qs" ]] && path="${path}?${qs}"
    morgen_api_call GET "$path"
    ;;
  get)
    if [[ $# -lt 1 ]]; then usage; fi
    path="/tasks?id=$(urlencode "$1")"
    morgen_api_call GET "$path"
    ;;
  create)
    if [[ $# -lt 1 ]]; then usage; fi
    body=$(read_body "$1")
    if ! printf '%s' "$body" | jq empty >/dev/null 2>&1; then
      echo "morgen: request body is not valid JSON" >&2; exit 1
    fi
    if ! printf '%s' "$body" | jq -e 'has("title")' >/dev/null; then
      echo "morgen: task create requires a 'title' field" >&2; exit 1
    fi
    morgen_api_call POST "/tasks/create" "$body"
    ;;
  update)
    if [[ $# -lt 1 ]]; then usage; fi
    body=$(read_body "$1")
    if ! printf '%s' "$body" | jq empty >/dev/null 2>&1; then
      echo "morgen: request body is not valid JSON" >&2; exit 1
    fi
    if ! printf '%s' "$body" | jq -e 'has("id")' >/dev/null; then
      echo "morgen: task update requires an 'id' field" >&2; exit 1
    fi
    morgen_api_call POST "/tasks/update" "$body"
    ;;
  move)
    if [[ $# -lt 1 ]]; then usage; fi
    task_id="$1"; previous_id="${2:-}"; parent_id="${3:-}"
    post_with_id "/tasks/move" "$task_id" \
      "previousId=$previous_id" "parentId=$parent_id"
    ;;
  close)
    if [[ $# -lt 1 ]]; then usage; fi
    post_with_id "/tasks/close" "$1" "occurrenceStart=${2:-}"
    ;;
  reopen)
    if [[ $# -lt 1 ]]; then usage; fi
    post_with_id "/tasks/reopen" "$1" "occurrenceStart=${2:-}"
    ;;
  delete)
    if [[ $# -lt 1 ]]; then usage; fi
    body=$(jq -n --arg id "$1" '{id:$id}')
    morgen_api_call POST "/tasks/delete" "$body"
    ;;
  *)
    usage
    ;;
esac
