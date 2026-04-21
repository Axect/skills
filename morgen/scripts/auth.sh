# shellcheck shell=bash
# Sourceable library. Provides:
#   morgen_require_deps
#   morgen_get_api_key
#   morgen_api_call   <METHOD> <path_with_query> [json_body]

MORGEN_SKILL_CREDS="${MORGEN_SKILL_CREDS:-$HOME/.config/morgen-skill/credentials.json}"
MORGEN_API_BASE="${MORGEN_API_BASE:-https://api.morgen.so/v3}"

morgen_require_deps() {
  for cmd in curl jq; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      echo "morgen: '$cmd' is required but not found." >&2
      exit 127
    fi
  done
}

morgen_get_api_key() {
  if [[ ! -f "$MORGEN_SKILL_CREDS" ]]; then
    echo "morgen: no credentials at $MORGEN_SKILL_CREDS. Run setup.sh first." >&2
    return 2
  fi
  local key
  key=$(jq -r '.api_key // ""' "$MORGEN_SKILL_CREDS")
  if [[ -z "$key" || "$key" == "null" ]]; then
    echo "morgen: credentials.json is missing 'api_key'. Re-run setup.sh." >&2
    return 2
  fi
  printf '%s' "$key"
}

# morgen_api_call <METHOD> <path_with_query> [json_body]
#
# Emits the response body on stdout for 2xx responses (204 -> '{"ok":true}').
# Non-2xx responses go to stderr with the HTTP code, and the function returns:
#   3  on 401/403 (auth)
#   4  on 404
#   6  on 429
#   5  otherwise
#
# <path_with_query> must start with "/" and is appended to MORGEN_API_BASE.
morgen_api_call() {
  local method="$1"
  local path="$2"
  local body="${3:-}"

  local key
  key=$(morgen_get_api_key) || return $?

  local url="${MORGEN_API_BASE}${path}"
  local response http_code resp_body
  if [[ -n "$body" ]]; then
    response=$(curl -sS -w $'\n%{http_code}' \
      -X "$method" "$url" \
      -H "Authorization: ApiKey $key" \
      -H "Accept: application/json" \
      -H "Content-Type: application/json" \
      --data "$body")
  else
    response=$(curl -sS -w $'\n%{http_code}' \
      -X "$method" "$url" \
      -H "Authorization: ApiKey $key" \
      -H "Accept: application/json")
  fi
  http_code=$(printf '%s' "$response" | tail -n1)
  resp_body=$(printf '%s' "$response" | sed '$d')

  if [[ "$http_code" == "204" ]]; then
    printf '{"ok":true}\n'
    return 0
  fi
  if [[ "$http_code" =~ ^2 ]]; then
    printf '%s' "$resp_body"
    return 0
  fi

  echo "morgen: API error (HTTP $http_code): $resp_body" >&2
  case "$http_code" in
    401|403) return 3 ;;
    404)     return 4 ;;
    429)     return 6 ;;
    *)       return 5 ;;
  esac
}
