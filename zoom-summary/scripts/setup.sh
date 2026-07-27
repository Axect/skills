#!/usr/bin/env bash
# zoom-summary setup: register Server-to-Server OAuth credentials and report
# which meeting-summary scopes the app actually got.
#
# Usage:
#   setup.sh              # interactive: prompts for the three values via TTY
#   setup.sh --stdin      # non-interactive: reads one JSON object from stdin
#   setup.sh --help
#
# The --stdin form exists so a skill orchestrator (e.g. Claude Code) can run
# setup without a terminal, once the user has pasted their credentials into
# chat. The JSON never appears in this process's argv:
#
#   bash setup.sh --stdin <<< '{"account_id":"...","client_id":"...","client_secret":"..."}'
#
# There is deliberately no --secret flag: a client secret on argv is visible in
# /proc/<pid>/cmdline for the life of the process.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=auth.sh
source "$SCRIPT_DIR/auth.sh"

write_creds() {
  local account_id="$1" client_id="$2" client_secret="$3"
  mkdir -p "$(dirname "$ZOOM_SKILL_CREDS")"
  local tmp
  tmp=$(mktemp "${ZOOM_SKILL_CREDS}.XXXXXX")
  if ! jq -n --arg a "$account_id" --arg i "$client_id" --arg s "$client_secret" \
        '{account_id:$a, client_id:$i, client_secret:$s}' > "$tmp"; then
    rm -f "$tmp"
    echo "zoom: failed to write credentials.json" >&2
    return 1
  fi
  chmod 600 "$tmp"
  if ! mv "$tmp" "$ZOOM_SKILL_CREDS"; then
    rm -f "$tmp"
    echo "zoom: failed to install credentials.json" >&2
    return 1
  fi
  chmod 600 "$ZOOM_SKILL_CREDS" || \
    echo "zoom: warning: chmod 600 failed on $ZOOM_SKILL_CREDS" >&2
  return 0
}

# has_scope <scope_string> <wanted>
has_scope() {
  local granted=" $1 " wanted="$2"
  [[ "$granted" == *" $wanted "* ]]
}

report_scopes() {
  local scope="$1"
  local list_ok=1 summary_ok=1

  if has_scope "$scope" "$ZOOM_SCOPE_LIST" || has_scope "$scope" "$ZOOM_SCOPE_CLASSIC"; then
    list_ok=0
  fi
  if has_scope "$scope" "$ZOOM_SCOPE_SUMMARY" || has_scope "$scope" "$ZOOM_SCOPE_CLASSIC"; then
    summary_ok=0
  fi

  if [[ $list_ok -eq 0 ]]; then
    echo "  list summaries : GRANTED"
  else
    echo "  list summaries : MISSING  ($ZOOM_SCOPE_LIST)"
  fi
  if [[ $summary_ok -eq 0 ]]; then
    echo "  read summary   : GRANTED"
  else
    echo "  read summary   : MISSING  ($ZOOM_SCOPE_SUMMARY)"
  fi

  if [[ $list_ok -ne 0 || $summary_ok -ne 0 ]]; then
    {
      echo
      echo "zoom: warning: at least one required scope is not on this app."
      echo "  Add it at https://marketplace.zoom.us -> your Server-to-Server OAuth app -> Scopes,"
      echo "  then Activate the app again and re-run this setup."
      echo "  If the granular scope is not offered in the picker, look for the classic"
      echo "  scope '$ZOOM_SCOPE_CLASSIC' instead, which covers both endpoints."
    } >&2
  fi
}

# Live check that the list endpoint really answers. The scope string is what
# Zoom says it granted; this is what the API actually does. Errors are NOT
# swallowed: a failing probe is the one moment the raw Zoom message matters.
probe_list() {
  local today from body
  today=$(date -u +%F)
  from=$(date -u -d '7 days ago' +%F 2>/dev/null) || from="$today"
  if body=$(zoom_api GET "/meetings/meeting_summaries?from=${from}&to=${today}&page_size=1"); then
    local n
    n=$(printf '%s' "$body" | jq -r '(.summaries // .meeting_summaries // []) | length')
    echo "  live probe     : OK (list endpoint answered, ${n} summary in the last 7 days)"
  else
    echo "  live probe     : FAILED (the Zoom error is printed above)" >&2
  fi
}

register() {
  local account_id="$1" client_id="$2" client_secret="$3"
  if [[ -z "$account_id" || -z "$client_id" || -z "$client_secret" ]]; then
    echo "zoom: account_id, client_id, and client_secret are all required." >&2
    return 1
  fi

  echo "Verifying credentials against ${ZOOM_OAUTH_URL} ..."
  local tok_json scope
  tok_json=$(zoom_mint_token "$account_id" "$client_id" "$client_secret") || {
    echo "zoom: credentials did not verify. Check Account ID / Client ID / Client Secret on the app's" >&2
    echo "      App Credentials page, and make sure the app is Activated." >&2
    return 1
  }
  scope=$(printf '%s' "$tok_json" | jq -r '.scope // ""')

  write_creds "$account_id" "$client_id" "$client_secret" || return 1

  # Reuse the verification token rather than minting a second one. Zoom can
  # reject a brand-new token for a moment when two are issued back to back,
  # which showed up as a spurious probe failure.
  zoom_load_creds && zoom_store_token "$tok_json" >/dev/null

  echo "Setup complete. Credentials saved to $ZOOM_SKILL_CREDS"
  report_scopes "$scope"
  probe_list
  return 0
}

run_interactive() {
  echo "=== zoom-summary setup ==="
  echo
  echo "1. Go to https://marketplace.zoom.us and sign in."
  echo "2. Develop -> Build App -> Server-to-Server OAuth."
  echo "3. On the Scopes tab add:"
  echo "     $ZOOM_SCOPE_LIST"
  echo "     $ZOOM_SCOPE_SUMMARY"
  echo "   (if the picker does not offer those, add the classic $ZOOM_SCOPE_CLASSIC)"
  echo "4. Activate the app, then copy the three values below from App Credentials."
  echo
  read -r -p "Account ID: " ACCOUNT_ID
  read -r -p "Client ID: " CLIENT_ID
  read -r -s -p "Client Secret (hidden): " CLIENT_SECRET; echo
  echo
  register "$ACCOUNT_ID" "$CLIENT_ID" "$CLIENT_SECRET" || exit 1
}

show_help() {
  sed -n '2,21p' "$0" | sed 's/^# \{0,1\}//'
}

main() {
  zoom_require_deps

  if [[ $# -eq 0 ]]; then
    if [[ ! -t 0 ]]; then
      echo "zoom: no TTY for interactive setup. Use: setup.sh --stdin <<< '<json>'" >&2
      exit 64
    fi
    run_interactive
    return 0
  fi

  case "${1:-}" in
    --stdin)
      local payload account_id client_id client_secret
      payload=$(cat)
      if ! printf '%s' "$payload" | jq -e . >/dev/null 2>&1; then
        echo "zoom: --stdin expects a JSON object with account_id, client_id, client_secret." >&2
        exit 1
      fi
      account_id=$(printf '%s' "$payload" | jq -r '.account_id // ""')
      client_id=$(printf '%s' "$payload" | jq -r '.client_id // ""')
      client_secret=$(printf '%s' "$payload" | jq -r '.client_secret // ""')
      register "$account_id" "$client_id" "$client_secret" || exit 1
      ;;
    --help|-h)
      show_help
      exit 0
      ;;
    *)
      echo "zoom: unknown flag: $1" >&2
      show_help >&2
      exit 64
      ;;
  esac
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
