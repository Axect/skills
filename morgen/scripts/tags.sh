#!/usr/bin/env bash
# morgen tags: list / get / create / update / delete (soft-delete).
#
# Usage:
#   tags.sh list   [limit] [updatedAfterISO]
#   tags.sh get    <tagId>
#   tags.sh create <name> [hexColor]
#   tags.sh update <tagId> [name] [hexColor]
#   tags.sh delete <tagId>

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=auth.sh
source "$SCRIPT_DIR/auth.sh"

morgen_require_deps

usage() {
  cat >&2 <<'EOF'
Usage:
  tags.sh list   [limit] [updatedAfterISO]
  tags.sh get    <tagId>
  tags.sh create <name> [hexColor]
  tags.sh update <tagId> [name] [hexColor]
  tags.sh delete <tagId>
EOF
  exit 64
}

urlencode() { jq -rn --arg v "$1" '$v|@uri'; }

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
    path="/tags/list"
    [[ -n "$qs" ]] && path="${path}?${qs}"
    morgen_api_call GET "$path"
    ;;
  get)
    if [[ $# -lt 1 ]]; then usage; fi
    morgen_api_call GET "/tags?id=$(urlencode "$1")"
    ;;
  create)
    if [[ $# -lt 1 ]]; then usage; fi
    name="$1"; color="${2:-}"
    if [[ -n "$color" ]]; then
      body=$(jq -n --arg n "$name" --arg c "$color" '{name:$n, color:$c}')
    else
      body=$(jq -n --arg n "$name" '{name:$n}')
    fi
    morgen_api_call POST "/tags/create" "$body"
    ;;
  update)
    if [[ $# -lt 1 ]]; then usage; fi
    id="$1"; name="${2:-}"; color="${3:-}"
    body=$(jq -n --arg id "$id" '{id:$id}')
    if [[ -n "$name" ]]; then
      body=$(printf '%s' "$body" | jq --arg v "$name" '. + {name:$v}')
    fi
    if [[ -n "$color" ]]; then
      body=$(printf '%s' "$body" | jq --arg v "$color" '. + {color:$v}')
    fi
    morgen_api_call POST "/tags/update" "$body"
    ;;
  delete)
    if [[ $# -lt 1 ]]; then usage; fi
    body=$(jq -n --arg id "$1" '{id:$id}')
    morgen_api_call POST "/tags/delete" "$body"
    ;;
  *)
    usage
    ;;
esac
