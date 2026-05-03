#!/usr/bin/env bash
# init_env.sh — Initialize an overleap project directory with a .env file.
#
# Reads the Overleaf session cookie from stdin (so it never appears in argv or
# shell history), writes <dir>/.env with mode 600, and ensures `.env` is in
# <dir>/.gitignore.
#
# Usage:
#   bash init_env.sh <dir> [--force]
#   # Then pipe / heredoc the cookie:
#   bash init_env.sh <dir> <<< 'overleaf_session2=...; ...'
#
# Exit codes:
#   0  success
#   1  bad argument / I/O error
#   2  refused (existing .env without --force)
#   64 usage error

set -euo pipefail

usage() {
    cat >&2 <<'EOF'
Usage: init_env.sh <dir> [--force]

Reads the Overleaf cookie from stdin and writes <dir>/.env (mode 600).
Refuses to overwrite an existing .env unless --force is given.

The cookie is whatever the user copied from browser DevTools — typically the
full Cookie header value, or just the `overleaf_session2=...` segment.
EOF
    exit 64
}

DIR=""
FORCE=0

for arg in "$@"; do
    case "$arg" in
        -h|--help) usage ;;
        --force)   FORCE=1 ;;
        -*)        echo "Unknown flag: $arg" >&2; usage ;;
        *)
            if [ -z "$DIR" ]; then
                DIR="$arg"
            else
                echo "Unexpected positional: $arg" >&2
                usage
            fi
            ;;
    esac
done

if [ -z "$DIR" ]; then
    usage
fi

if [ ! -d "$DIR" ]; then
    # Create the directory only if the parent exists; never auto-create deep paths.
    PARENT="$(dirname -- "$DIR")"
    if [ ! -d "$PARENT" ]; then
        echo "init_env.sh: parent directory does not exist: $PARENT" >&2
        exit 1
    fi
    mkdir -- "$DIR"
fi

ENV_FILE="$DIR/.env"
GITIGNORE="$DIR/.gitignore"

if [ -e "$ENV_FILE" ] && [ "$FORCE" -ne 1 ]; then
    echo "init_env.sh: $ENV_FILE already exists. Re-run with --force to overwrite." >&2
    exit 2
fi

# Read cookie from stdin. Do not echo, do not pass via argv.
if [ -t 0 ]; then
    cat >&2 <<'EOF'
init_env.sh: stdin is a TTY. Pipe or heredoc the cookie instead, e.g.:

  bash init_env.sh <dir> <<< 'overleaf_session2=...'

This keeps the cookie out of your shell history.
EOF
    exit 64
fi

COOKIE="$(cat)"
COOKIE="${COOKIE%$'\n'}"  # strip a single trailing newline if present

if [ -z "$COOKIE" ]; then
    echo "init_env.sh: empty cookie on stdin" >&2
    exit 1
fi

# Write .env with mode 600. Use printf to avoid echo's flag-parsing quirks.
umask 077
{
    printf 'OVERLEAF_COOKIE=%s\n' "$COOKIE"
} > "$ENV_FILE"
chmod 600 "$ENV_FILE"

# Ensure .gitignore exists and contains .env (exact match on its own line).
if [ ! -e "$GITIGNORE" ] || ! grep -qxF '.env' "$GITIGNORE"; then
    printf '.env\n' >> "$GITIGNORE"
fi

echo "init_env.sh: wrote $ENV_FILE (mode 600) and ensured .env is in .gitignore"
echo "init_env.sh: smoke-test with: cd \"$DIR\" && overleap projects"
