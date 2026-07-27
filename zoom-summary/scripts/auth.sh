# shellcheck shell=bash
# Sourceable library for the zoom-summary skill. Provides:
#   zoom_require_deps
#   zoom_mint_token      <account_id> <client_id> <client_secret>   -> raw token JSON on stdout
#   zoom_get_token                                                  -> access_token on stdout (cached)
#   zoom_token_scope                                                -> granted scope string on stdout
#   zoom_api             <METHOD> <path_with_query>                 -> response body on stdout
#   zoom_encode_uuid     <meeting_uuid>                             -> path-safe uuid on stdout
#
# Nothing here is executed directly; summaries.sh and setup.sh source it.

ZOOM_SKILL_CREDS="${ZOOM_SKILL_CREDS:-$HOME/.config/zoom-skill/credentials.json}"
ZOOM_SKILL_CACHE="${ZOOM_SKILL_CACHE:-$HOME/.cache/zoom-skill}"
ZOOM_API_BASE="${ZOOM_API_BASE:-https://api.zoom.us/v2}"
ZOOM_OAUTH_URL="${ZOOM_OAUTH_URL:-https://zoom.us/oauth/token}"

# Granular scopes needed by this skill. Classic equivalents are accepted too:
# an account still on classic scopes reports meeting_summary:read:admin, which
# covers both endpoints.
ZOOM_SCOPE_LIST="meeting:read:list_summaries:admin"
ZOOM_SCOPE_SUMMARY="meeting:read:summary:admin"
ZOOM_SCOPE_CLASSIC="meeting_summary:read:admin"

zoom_require_deps() {
  for cmd in curl jq base64; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      echo "zoom: '$cmd' is required but not found." >&2
      exit 127
    fi
  done
}

# Reads credentials.json and exports ZOOM_ACCOUNT_ID / ZOOM_CLIENT_ID / ZOOM_CLIENT_SECRET.
zoom_load_creds() {
  if [[ ! -f "$ZOOM_SKILL_CREDS" ]]; then
    echo "zoom: no credentials at $ZOOM_SKILL_CREDS. Run setup.sh first." >&2
    return 2
  fi
  ZOOM_ACCOUNT_ID=$(jq -r '.account_id // ""' "$ZOOM_SKILL_CREDS")
  ZOOM_CLIENT_ID=$(jq -r '.client_id // ""' "$ZOOM_SKILL_CREDS")
  ZOOM_CLIENT_SECRET=$(jq -r '.client_secret // ""' "$ZOOM_SKILL_CREDS")
  if [[ -z "$ZOOM_ACCOUNT_ID" || -z "$ZOOM_CLIENT_ID" || -z "$ZOOM_CLIENT_SECRET" ]]; then
    echo "zoom: credentials.json is missing account_id, client_id, or client_secret. Re-run setup.sh." >&2
    return 2
  fi
  return 0
}

# zoom_mint_token <account_id> <client_id> <client_secret>
#
# Prints the raw OAuth response JSON (access_token, expires_in, scope, ...) on
# success. On failure prints the error body to stderr and returns 3.
zoom_mint_token() {
  local account_id="$1" client_id="$2" client_secret="$3"
  local basic response http_code body
  basic=$(printf '%s:%s' "$client_id" "$client_secret" | base64 | tr -d '\n')

  response=$(curl -sS -w $'\n%{http_code}' \
    -X POST "$ZOOM_OAUTH_URL" \
    -H "Authorization: Basic $basic" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "grant_type=account_credentials" \
    --data-urlencode "account_id=$account_id") || {
      echo "zoom: could not reach $ZOOM_OAUTH_URL" >&2
      return 5
    }
  http_code=$(printf '%s' "$response" | tail -n1)
  body=$(printf '%s' "$response" | sed '$d')

  if [[ ! "$http_code" =~ ^2 ]]; then
    echo "zoom: token request failed (HTTP $http_code): $body" >&2
    return 3
  fi
  printf '%s' "$body"
  return 0
}

# Fingerprint of the active credentials, so a cached token minted from a
# different app is never reused.
zoom_cred_fingerprint() {
  printf '%s|%s' "$ZOOM_ACCOUNT_ID" "$ZOOM_CLIENT_ID" | sha256sum | cut -d' ' -f1
}

# zoom_store_token <token_json>
#
# Writes an already-minted token response into the cache. Callers must have run
# zoom_load_creds first. setup.sh uses this to reuse its verification token
# instead of minting a second one, which Zoom sometimes rejects for a moment.
zoom_store_token() {
  local tok_json="$1"
  local token expires_in scope now cache tmp
  token=$(printf '%s' "$tok_json" | jq -r '.access_token // ""')
  expires_in=$(printf '%s' "$tok_json" | jq -r '.expires_in // 3600')
  scope=$(printf '%s' "$tok_json" | jq -r '.scope // ""')
  if [[ -z "$token" ]]; then
    echo "zoom: token response contained no access_token." >&2
    return 3
  fi
  now=$(date +%s)
  cache="$ZOOM_SKILL_CACHE/token.json"
  mkdir -p "$ZOOM_SKILL_CACHE"
  tmp=$(mktemp "${cache}.XXXXXX")
  jq -n --arg t "$token" --arg s "$scope" --arg f "$(zoom_cred_fingerprint)" \
        --argjson e "$((now + expires_in))" \
        '{access_token:$t, expires_at:$e, scope:$s, fingerprint:$f}' > "$tmp" \
    && mv "$tmp" "$cache" \
    && chmod 600 "$cache" \
    || { rm -f "$tmp"; echo "zoom: warning: could not write token cache" >&2; }
  printf '%s' "$token"
  return 0
}

# Mints a token if the cache is missing, expiring within 60s, or from other creds.
# Writes the cache and prints the access token.
zoom_get_token() {
  zoom_load_creds || return $?

  local cache="$ZOOM_SKILL_CACHE/token.json"
  local fp now
  fp=$(zoom_cred_fingerprint)
  now=$(date +%s)

  if [[ -f "$cache" ]]; then
    local c_token c_exp c_fp
    c_token=$(jq -r '.access_token // ""' "$cache" 2>/dev/null)
    c_exp=$(jq -r '.expires_at // 0' "$cache" 2>/dev/null)
    c_fp=$(jq -r '.fingerprint // ""' "$cache" 2>/dev/null)
    if [[ -n "$c_token" && "$c_fp" == "$fp" && "$c_exp" =~ ^[0-9]+$ && $((c_exp - 60)) -gt "$now" ]]; then
      printf '%s' "$c_token"
      return 0
    fi
  fi

  local tok_json
  tok_json=$(zoom_mint_token "$ZOOM_ACCOUNT_ID" "$ZOOM_CLIENT_ID" "$ZOOM_CLIENT_SECRET") || return $?
  zoom_store_token "$tok_json"
}

# Prints the scope string attached to the current (possibly freshly minted) token.
zoom_token_scope() {
  zoom_get_token >/dev/null || return $?
  jq -r '.scope // ""' "$ZOOM_SKILL_CACHE/token.json" 2>/dev/null
}

# zoom_api <METHOD> <path_with_query>
#
# <path_with_query> must start with "/" and is appended to ZOOM_API_BASE.
# 2xx bodies go to stdout. Otherwise the body goes to stderr and the return is:
#   3 on 401/403 (auth or missing scope), 4 on 404, 6 on 429, 5 otherwise.
zoom_api() {
  local method="$1" path="$2"
  local token
  token=$(zoom_get_token) || return $?

  local response http_code body
  response=$(curl -sS -w $'\n%{http_code}' \
    -X "$method" "${ZOOM_API_BASE}${path}" \
    -H "Authorization: Bearer $token" \
    -H "Accept: application/json") || {
      echo "zoom: could not reach ${ZOOM_API_BASE}${path}" >&2
      return 5
    }
  http_code=$(printf '%s' "$response" | tail -n1)
  body=$(printf '%s' "$response" | sed '$d')

  if [[ "$http_code" =~ ^2 ]]; then
    printf '%s' "$body"
    return 0
  fi

  echo "zoom: API error (HTTP $http_code) on $path: $body" >&2
  case "$http_code" in
    401|403) return 3 ;;
    404)     return 4 ;;
    429)     return 6 ;;
    *)       return 5 ;;
  esac
}

# Percent-encodes a string for use in a URL path segment.
zoom_urlencode() {
  jq -rn --arg s "$1" '$s|@uri'
}

# Zoom's rule: a meeting UUID that starts with "/" or contains "//" must be
# double URL encoded before it goes into the path. Every other UUID is passed
# through untouched. Getting this wrong returns 404, not a helpful error.
zoom_encode_uuid() {
  local uuid="$1"
  if [[ "$uuid" == /* || "$uuid" == *//* ]]; then
    zoom_urlencode "$(zoom_urlencode "$uuid")"
  else
    printf '%s' "$uuid"
  fi
}
