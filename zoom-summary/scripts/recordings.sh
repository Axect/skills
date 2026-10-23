#!/usr/bin/env bash
# zoom-summary: list and delete Zoom cloud recordings.
#
# Usage:
#   recordings.sh list   [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--user <id|email>] [--json]
#   recordings.sh delete [--permanent] [--yes] <meetingUUID>... | -
#
# list    lists cloud recordings in a date range (default: the last 365 days),
#         querying Zoom one 30-day window at a time, as TSV:
#           start_time <TAB> topic <TAB> size_MB <TAB> files <TAB> uuid
#         A total line goes to stderr. --json emits the raw meetings array.
#         --user defaults to $ZOOM_RECORDING_USER, else "me".
# delete  deletes all recording files of each meeting UUID (read from stdin
#         with "-", one per line). Default moves them to the trash, which Zoom
#         keeps for 30 days; --permanent skips the trash. Without --yes it is a
#         dry run that only prints what would be deleted.
#
# Exit codes: 0 ok, 1 bad argument, 2 no credentials, 3 auth or missing scope,
# 4 not found, 5 other API error, 6 rate limited, 64 usage, 127 missing dependency.

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Recording scopes may live on a separate Server-to-Server app. Use its
# credentials (and a separate token cache) when that file exists.
ZOOM_RECORDING_CREDS="${ZOOM_RECORDING_CREDS:-$HOME/.config/zoom-skill/recordings-credentials.json}"
if [[ -z "${ZOOM_SKILL_CREDS:-}" && -f "$ZOOM_RECORDING_CREDS" ]]; then
  ZOOM_SKILL_CREDS="$ZOOM_RECORDING_CREDS"
  ZOOM_SKILL_CACHE="${ZOOM_SKILL_CACHE:-$HOME/.cache/zoom-skill}/recordings"
fi
# shellcheck source=auth.sh
source "$SCRIPT_DIR/auth.sh"

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
}

check_date() {
  if [[ ! "$1" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || ! date -u -d "$1" +%F >/dev/null 2>&1; then
    echo "zoom: dates must be YYYY-MM-DD (got '$1')" >&2
    exit 1
  fi
}

# ---------------------------------------------------------------- list

cmd_list() {
  local from="" to="" as_json=0 user="${ZOOM_RECORDING_USER:-me}"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --from) from="${2:-}"; shift 2 || { echo "zoom: --from requires a date" >&2; exit 64; } ;;
      --to)   to="${2:-}";   shift 2 || { echo "zoom: --to requires a date" >&2; exit 64; } ;;
      --user) user="${2:-}"; shift 2 || { echo "zoom: --user requires a value" >&2; exit 64; } ;;
      --json) as_json=1; shift ;;
      *) echo "zoom: unknown flag for list: $1" >&2; usage >&2; exit 64 ;;
    esac
  done

  [[ -z "$to" ]] && to=$(date -u +%F)
  [[ -z "$from" ]] && from=$(date -u -d "$to - 365 days" +%F)
  check_date "$from"; check_date "$to"
  if [[ "$from" > "$to" ]]; then
    echo "zoom: --from ($from) is after --to ($to)" >&2
    exit 1
  fi

  # The endpoint rejects ranges longer than one month, so walk 30-day windows.
  local user_enc pages="" all win_from="$from" win_to token body rc page
  user_enc=$(zoom_urlencode "$user")
  while [[ ! "$win_from" > "$to" ]]; do
    win_to=$(date -u -d "$win_from + 29 days" +%F)
    [[ "$win_to" > "$to" ]] && win_to="$to"
    token=""
    while :; do
      page="/users/${user_enc}/recordings?from=${win_from}&to=${win_to}&page_size=300&trash=false"
      [[ -n "$token" ]] && page="${page}&next_page_token=$(zoom_urlencode "$token")"
      body=$(zoom_api GET "$page")
      rc=$?
      [[ $rc -ne 0 ]] && exit $rc
      # Accumulate in a shell variable and feed jq on stdin: recording_files
      # carry long URLs, so passing the accumulator as an argument overflows ARG_MAX.
      pages+="$(printf '%s' "$body" | jq -c '.meetings // []')"$'\n'
      token=$(printf '%s' "$body" | jq -r '.next_page_token // ""')
      [[ -z "$token" ]] && break
    done
    win_from=$(date -u -d "$win_to + 1 day" +%F)
  done

  # A meeting can straddle two windows; keep one row per uuid.
  all=$(printf '%s' "$pages" | jq -s 'add // [] | unique_by(.uuid) | sort_by(.start_time // "")')

  if [[ $as_json -eq 1 ]]; then
    printf '%s\n' "$all"
    return 0
  fi

  local n
  n=$(printf '%s' "$all" | jq 'length')
  if [[ "$n" == "0" ]]; then
    echo "zoom: no cloud recordings between $from and $to." >&2
    return 0
  fi

  printf '%s' "$all" | jq -r '
    .[]
    | [ (.start_time // "-"),
        (.topic // "-"),
        ((.total_size // 0) / 1048576 | . * 10 | round / 10 | tostring),
        ((.recording_count // (.recording_files // [] | length)) | tostring),
        (.uuid // "-") ]
    | @tsv'
  printf '%s' "$all" | jq -r --arg f "$from" --arg t "$to" \
    '"zoom: \(length) meetings, \((map(.total_size // 0) | add) / 1073741824 | . * 100 | round / 100) GB between \($f) and \($t)."' >&2
}

# ---------------------------------------------------------------- delete

cmd_delete() {
  local action="trash" yes=0 uuids=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --permanent) action="delete"; shift ;;
      --yes) yes=1; shift ;;
      -) mapfile -t -O "${#uuids[@]}" uuids < <(grep -v '^[[:space:]]*$'); shift ;;
      --*) echo "zoom: unknown flag for delete: $1" >&2; usage >&2; exit 64 ;;
      *) uuids+=("$1"); shift ;;
    esac
  done
  [[ ${#uuids[@]} -eq 0 ]] && { echo "zoom: delete needs at least one meeting UUID" >&2; exit 64; }

  if [[ $yes -eq 0 ]]; then
    echo "zoom: dry run (add --yes to execute); action=$action for ${#uuids[@]} meeting(s):" >&2
    printf '%s\n' "${uuids[@]}"
    return 0
  fi

  local uuid rc failed=0 done_n=0
  for uuid in "${uuids[@]}"; do
    zoom_api DELETE "/meetings/$(zoom_encode_uuid "$uuid")/recordings?action=${action}" >/dev/null
    rc=$?
    if [[ $rc -eq 0 ]]; then
      printf 'deleted\t%s\n' "$uuid"
      done_n=$((done_n + 1))
    else
      printf 'failed\t%s\n' "$uuid"
      failed=$rc
      # Auth/scope errors will fail every remaining UUID the same way.
      [[ $rc -eq 3 ]] && break
    fi
  done
  echo "zoom: $done_n of ${#uuids[@]} meeting(s) processed (action=$action)." >&2
  return $failed
}

# ---------------------------------------------------------------- main

main() {
  zoom_require_deps
  [[ $# -eq 0 ]] && { usage >&2; exit 64; }

  local cmd="$1"; shift
  case "$cmd" in
    list)   cmd_list   "$@" ;;
    delete) cmd_delete "$@" ;;
    --help|-h|help) usage; exit 0 ;;
    *) echo "zoom: unknown command: $cmd" >&2; usage >&2; exit 64 ;;
  esac
}

main "$@"
