#!/usr/bin/env bash
# morgen calendars: list and update calendar metadata.
#
# Usage:
#   calendars.sh list
#   calendars.sh update <accountId> <calendarId> <metadata_json>

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=auth.sh
source "$SCRIPT_DIR/auth.sh"

morgen_require_deps

usage() {
  cat >&2 <<'EOF'
Usage:
  calendars.sh list
  calendars.sh update <accountId> <calendarId> <metadata_json>

  <metadata_json> is the "morgen.so:metadata" object as raw JSON, e.g.
    '{"busy":true,"overrideColor":"#FF0000","overrideName":"Work"}'
EOF
  exit 64
}

cmd="${1:-}"
shift || true

case "$cmd" in
  list)
    morgen_api_call GET "/calendars/list"
    ;;
  update)
    if [[ $# -lt 3 ]]; then usage; fi
    account_id="$1"; calendar_id="$2"; metadata="$3"
    if ! printf '%s' "$metadata" | jq empty >/dev/null 2>&1; then
      echo "morgen: <metadata_json> is not valid JSON" >&2
      exit 1
    fi
    body=$(jq -n \
      --arg a "$account_id" \
      --arg c "$calendar_id" \
      --argjson m "$metadata" \
      '{accountId:$a, id:$c, "morgen.so:metadata":$m}')
    morgen_api_call POST "/calendars/update" "$body"
    ;;
  *)
    usage
    ;;
esac
