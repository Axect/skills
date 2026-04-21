#!/usr/bin/env bash
# morgen events: list / create / update / delete calendar events.
#
# Usage:
#   events.sh list   <accountId> <calendarIds> <startISO> <endISO>
#   events.sh create <json_body>
#   events.sh update <json_body> [seriesUpdateMode]
#   events.sh delete <accountId> <calendarId> <eventId> [seriesUpdateMode]
#
# seriesUpdateMode (default: single): single | all | future
# <calendarIds> is comma-separated.
# <json_body> may be "-" to read from stdin.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=auth.sh
source "$SCRIPT_DIR/auth.sh"

morgen_require_deps

usage() {
  cat >&2 <<'EOF'
Usage:
  events.sh list   <accountId> <calendarIds> <startISO> <endISO>
  events.sh create <json_body|->
  events.sh update <json_body|-> [seriesUpdateMode]
  events.sh delete <accountId> <calendarId> <eventId> [seriesUpdateMode]
EOF
  exit 64
}

urlencode() {
  # Minimal URL encoder for query values.
  jq -rn --arg v "$1" '$v|@uri'
}

read_body() {
  local arg="$1"
  if [[ "$arg" == "-" ]]; then
    cat
  else
    printf '%s' "$arg"
  fi
}

cmd="${1:-}"
shift || true

case "$cmd" in
  list)
    if [[ $# -lt 4 ]]; then usage; fi
    account_id=$(urlencode "$1")
    calendar_ids=$(urlencode "$2")
    start=$(urlencode "$3")
    end=$(urlencode "$4")
    path="/events/list?accountId=${account_id}&calendarIds=${calendar_ids}&start=${start}&end=${end}"
    morgen_api_call GET "$path"
    ;;
  create)
    if [[ $# -lt 1 ]]; then usage; fi
    body=$(read_body "$1")
    if ! printf '%s' "$body" | jq empty >/dev/null 2>&1; then
      echo "morgen: request body is not valid JSON" >&2
      exit 1
    fi
    morgen_api_call POST "/events/create" "$body"
    ;;
  update)
    if [[ $# -lt 1 ]]; then usage; fi
    body=$(read_body "$1")
    mode="${2:-single}"
    if ! printf '%s' "$body" | jq empty >/dev/null 2>&1; then
      echo "morgen: request body is not valid JSON" >&2
      exit 1
    fi
    path="/events/update?seriesUpdateMode=$(urlencode "$mode")"
    morgen_api_call POST "$path" "$body"
    ;;
  delete)
    if [[ $# -lt 3 ]]; then usage; fi
    account_id="$1"; calendar_id="$2"; event_id="$3"
    mode="${4:-single}"
    body=$(jq -n \
      --arg a "$account_id" \
      --arg c "$calendar_id" \
      --arg i "$event_id" \
      '{accountId:$a, calendarId:$c, id:$i}')
    path="/events/delete?seriesUpdateMode=$(urlencode "$mode")"
    morgen_api_call POST "$path" "$body"
    ;;
  *)
    usage
    ;;
esac
