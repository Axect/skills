#!/usr/bin/env bash
# zoom-summary: read Zoom AI Companion meeting summaries.
#
# Usage:
#   summaries.sh list [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--json]
#   summaries.sh get  <meetingUUID> [--json]
#   summaries.sh save <meetingUUID> [--dir <path>] [--force]
#
# list  lists summaries in a date range (default: the last 30 days) as TSV:
#         start_time <TAB> topic <TAB> meeting_id <TAB> uuid
#       --json emits the raw summaries array instead.
# get   prints one summary rendered as markdown; --json prints the raw body.
# save  writes that markdown to $ZOOM_SUMMARY_DIR (default ~/Documents/ZoomSummaries)
#       and prints the saved path.
#
# Exit codes: 0 ok, 1 bad argument or refused overwrite, 2 no credentials,
# 3 auth or missing scope, 4 not found, 5 other API error, 6 rate limited,
# 64 usage, 127 missing dependency.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=auth.sh
source "$SCRIPT_DIR/auth.sh"

ZOOM_SUMMARY_DIR="${ZOOM_SUMMARY_DIR:-$HOME/Documents/ZoomSummaries}"

read -r -d '' RENDER_MD <<'JQ' || true
def blank(v): ((v // "") | tostring) | if . == "" then "-" else . end;
[
  "# " + blank(.summary_title),
  "",
  "- 미팅: " + blank(.meeting_topic),
  "- 일시: " + blank(.summary_start_time) + " ~ " + blank(.summary_end_time),
  "- Meeting ID: " + blank(.meeting_id) + " / UUID: " + blank(.meeting_uuid),
  "- 호스트: " + blank(.meeting_host_email),
  "- 요약 생성: " + blank(.summary_created_time),
  "",
  "## 개요",
  "",
  blank(.summary_overview),
  ""
]
+ (if ((.summary_details // []) | length) > 0
   then ["## 세부 내용", ""]
        + [.summary_details[] | ("### " + blank(.label)), "", blank(.summary), ""]
   else [] end)
+ (if ((.next_steps // []) | length) > 0
   then ["## Next steps", ""] + [.next_steps[] | "- " + (. | tostring)] + [""]
   else [] end)
| join("\n")
JQ

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
}

# ---------------------------------------------------------------- list

cmd_list() {
  local from="" to="" as_json=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --from) from="${2:-}"; shift 2 || { echo "zoom: --from requires a date" >&2; exit 64; } ;;
      --to)   to="${2:-}";   shift 2 || { echo "zoom: --to requires a date" >&2; exit 64; } ;;
      --json) as_json=1; shift ;;
      *) echo "zoom: unknown flag for list: $1" >&2; usage >&2; exit 64 ;;
    esac
  done

  [[ -z "$to" ]] && to=$(date -u +%F)
  [[ -z "$from" ]] && from=$(date -u -d '30 days ago' +%F)

  for d in "$from" "$to"; do
    if [[ ! "$d" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
      echo "zoom: dates must be YYYY-MM-DD (got '$d')" >&2
      exit 1
    fi
  done

  local token="" all="[]" body rc page
  while :; do
    page="/meetings/meeting_summaries?from=${from}&to=${to}&page_size=30"
    [[ -n "$token" ]] && page="${page}&next_page_token=$(zoom_urlencode "$token")"

    body=$(zoom_api GET "$page")
    rc=$?
    [[ $rc -ne 0 ]] && exit $rc

    all=$(jq -n --argjson acc "$all" --argjson b "$body" \
      '$acc + ($b.summaries // $b.meeting_summaries // [])')
    token=$(printf '%s' "$body" | jq -r '.next_page_token // ""')
    [[ -z "$token" ]] && break
  done

  if [[ $as_json -eq 1 ]]; then
    printf '%s\n' "$all"
    return 0
  fi

  local n
  n=$(printf '%s' "$all" | jq 'length')
  if [[ "$n" == "0" ]]; then
    echo "zoom: no summaries between $from and $to." >&2
    return 0
  fi

  printf '%s' "$all" | jq -r '
    sort_by(.meeting_start_time // .summary_start_time // "")
    | .[]
    | [ (.meeting_start_time // .summary_start_time // "-"),
        (.meeting_topic // .summary_title // "-"),
        ((.meeting_id // "-") | tostring),
        (.meeting_uuid // "-") ]
    | @tsv'
}

# ---------------------------------------------------------------- get

fetch_summary() {
  local uuid="$1" enc
  enc=$(zoom_encode_uuid "$uuid")
  zoom_api GET "/meetings/${enc}/meeting_summary"
}

cmd_get() {
  local uuid="" as_json=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --json) as_json=1; shift ;;
      -*) echo "zoom: unknown flag for get: $1" >&2; usage >&2; exit 64 ;;
      *) if [[ -z "$uuid" ]]; then uuid="$1"; shift; else echo "zoom: too many arguments" >&2; exit 64; fi ;;
    esac
  done
  [[ -z "$uuid" ]] && { echo "zoom: get requires a meeting UUID" >&2; usage >&2; exit 64; }

  local body rc
  body=$(fetch_summary "$uuid")
  rc=$?
  [[ $rc -ne 0 ]] && exit $rc

  if [[ $as_json -eq 1 ]]; then
    printf '%s\n' "$body"
  else
    printf '%s' "$body" | jq -r "$RENDER_MD"
  fi
}

# ---------------------------------------------------------------- save

slugify() {
  local s
  s=$(printf '%s' "$1" \
    | tr -d '\000-\037' \
    | sed -e 's#[/\\:*?"<>|]#-#g' \
          -e 's/[[:space:]]\{1,\}/-/g' \
          -e 's/-\{2,\}/-/g' \
          -e 's/^-//' -e 's/-$//')
  s="${s:0:60}"
  s="${s%-}"
  [[ -z "$s" ]] && s="meeting"
  printf '%s' "$s"
}

cmd_save() {
  local uuid="" dir="$ZOOM_SUMMARY_DIR" force=0
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dir)   dir="${2:-}"; shift 2 || { echo "zoom: --dir requires a path" >&2; exit 64; } ;;
      --force) force=1; shift ;;
      -*) echo "zoom: unknown flag for save: $1" >&2; usage >&2; exit 64 ;;
      *) if [[ -z "$uuid" ]]; then uuid="$1"; shift; else echo "zoom: too many arguments" >&2; exit 64; fi ;;
    esac
  done
  [[ -z "$uuid" ]] && { echo "zoom: save requires a meeting UUID" >&2; usage >&2; exit 64; }

  local body rc
  body=$(fetch_summary "$uuid")
  rc=$?
  [[ $rc -ne 0 ]] && exit $rc

  local topic date_part slug out
  topic=$(printf '%s' "$body" | jq -r '.meeting_topic // .summary_title // ""')
  date_part=$(printf '%s' "$body" | jq -r '(.meeting_start_time // .summary_start_time // "")[0:10]')
  [[ -z "$date_part" ]] && date_part=$(date -u +%F)
  slug=$(slugify "$topic")
  out="${dir%/}/${date_part}_${slug}.md"

  if [[ -e "$out" && $force -ne 1 ]]; then
    echo "zoom: $out already exists. Pass --force to overwrite." >&2
    exit 1
  fi

  mkdir -p "$dir" || { echo "zoom: cannot create $dir" >&2; exit 1; }
  if ! printf '%s' "$body" | jq -r "$RENDER_MD" > "$out"; then
    echo "zoom: failed to write $out" >&2
    exit 1
  fi
  printf '%s\n' "$out"
}

# ---------------------------------------------------------------- main

main() {
  zoom_require_deps
  [[ $# -eq 0 ]] && { usage >&2; exit 64; }

  local cmd="$1"; shift
  case "$cmd" in
    list) cmd_list "$@" ;;
    get)  cmd_get  "$@" ;;
    save) cmd_save "$@" ;;
    --help|-h|help) usage; exit 0 ;;
    *) echo "zoom: unknown command: $cmd" >&2; usage >&2; exit 64 ;;
  esac
}

main "$@"
