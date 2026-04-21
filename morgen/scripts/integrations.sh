#!/usr/bin/env bash
# morgen integrations: list connected accounts or available providers.
#
# Usage:
#   integrations.sh accounts    # requires API key
#   integrations.sh providers   # no auth required

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=auth.sh
source "$SCRIPT_DIR/auth.sh"

morgen_require_deps

usage() {
  cat >&2 <<'EOF'
Usage:
  integrations.sh accounts
  integrations.sh providers
EOF
  exit 64
}

cmd="${1:-}"

case "$cmd" in
  accounts)
    morgen_api_call GET "/integrations/accounts/list"
    ;;
  providers)
    # No auth required for this endpoint, but the helper still sends the key
    # if it's available — Morgen accepts authenticated calls to unauth endpoints.
    # If credentials are missing, fall back to a plain curl.
    if [[ -f "$MORGEN_SKILL_CREDS" ]]; then
      morgen_api_call GET "/integrations/list"
    else
      curl -sS -X GET "${MORGEN_API_BASE}/integrations/list" \
        -H "Accept: application/json"
    fi
    ;;
  *)
    usage
    ;;
esac
