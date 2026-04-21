#!/usr/bin/env bash
# morgen setup: register API key (interactive or non-interactive).
#
# Usage:
#   setup.sh                      # interactive: prompts for key via TTY
#   setup.sh --stdin              # non-interactive: reads one line from stdin
#   setup.sh --key <API_KEY>      # non-interactive: key on argv (see security note)
#   setup.sh --help
#
# Non-interactive modes exist so a skill orchestrator (e.g. Claude Code) can
# run setup without a terminal, once the user has pasted their key into chat.
#
# Security note: `--key` exposes the API key in /proc/<pid>/cmdline for the
# lifetime of this process (milliseconds). On a personal single-user machine
# this is acceptable. On shared machines, prefer `--stdin` with a here-string:
#   bash setup.sh --stdin <<< "your_api_key"
# The herestring content never appears as argv of setup.sh itself.

set -uo pipefail

MORGEN_SKILL_CREDS="${MORGEN_SKILL_CREDS:-$HOME/.config/morgen-skill/credentials.json}"
MORGEN_API_BASE="${MORGEN_API_BASE:-https://api.morgen.so/v3}"

require_deps() {
  for cmd in curl jq; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      echo "morgen: '$cmd' is required but not found." >&2
      exit 127
    fi
  done
}

write_creds() {
  local api_key="$1"
  mkdir -p "$(dirname "$MORGEN_SKILL_CREDS")"
  local tmp
  tmp=$(mktemp "${MORGEN_SKILL_CREDS}.XXXXXX")
  if ! jq -n --arg k "$api_key" '{api_key:$k}' > "$tmp"; then
    rm -f "$tmp"
    echo "morgen: failed to write credentials.json" >&2
    return 1
  fi
  if ! mv "$tmp" "$MORGEN_SKILL_CREDS"; then
    rm -f "$tmp"
    echo "morgen: failed to install credentials.json" >&2
    return 1
  fi
  chmod 600 "$MORGEN_SKILL_CREDS" || \
    echo "morgen: warning: chmod 600 failed on $MORGEN_SKILL_CREDS" >&2
  return 0
}

verify_key() {
  local api_key="$1"
  local response http_code
  response=$(curl -sS -w $'\n%{http_code}' \
    -X GET "${MORGEN_API_BASE}/calendars/list" \
    -H "Authorization: ApiKey $api_key" \
    -H "Accept: application/json")
  http_code=$(printf '%s' "$response" | tail -n1)
  if [[ "$http_code" =~ ^2 ]]; then
    return 0
  fi
  local body
  body=$(printf '%s' "$response" | sed '$d')
  echo "morgen: key verification failed (HTTP $http_code): $body" >&2
  return 1
}

register_key() {
  # Verify + save. Shared by all modes.
  local api_key="$1"
  if [[ -z "$api_key" ]]; then
    echo "morgen: API key is empty" >&2
    return 1
  fi
  if ! verify_key "$api_key"; then
    echo "morgen: key did not verify. Get a valid key at https://platform.morgen.so → Developers API." >&2
    return 1
  fi
  if ! write_creds "$api_key"; then
    return 1
  fi
  echo "Setup complete. Credentials saved to $MORGEN_SKILL_CREDS"
  return 0
}

run_interactive() {
  echo "=== morgen setup ==="
  echo
  echo "1. Go to https://platform.morgen.so and sign in."
  echo "2. Open the 'Developers API' page and copy your API key."
  echo "   (If you don't have one yet, generate it there.)"
  echo
  read -r -s -p "Paste your Morgen API key (hidden): " API_KEY; echo
  echo
  echo "Verifying key against ${MORGEN_API_BASE}/calendars/list ..."
  register_key "$API_KEY" || exit 1
}

show_help() {
  sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'
}

main() {
  require_deps

  if [[ $# -eq 0 ]]; then
    run_interactive
    return 0
  fi

  local mode="" api_key=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --key)
        mode="flag"
        api_key="${2:-}"
        shift 2 || { echo "morgen: --key requires a value" >&2; exit 64; }
        ;;
      --stdin)
        mode="stdin"
        shift
        ;;
      --help|-h)
        show_help
        exit 0
        ;;
      *)
        echo "morgen: unknown flag: $1" >&2
        show_help >&2
        exit 64
        ;;
    esac
  done

  case "$mode" in
    flag)
      register_key "$api_key" || exit 1
      ;;
    stdin)
      IFS= read -r api_key || true
      register_key "$api_key" || exit 1
      ;;
    *)
      echo "morgen: no mode selected" >&2
      exit 64
      ;;
  esac
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
