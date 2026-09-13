#!/usr/bin/env bash
# install.sh - install the reMarkable Cloud toolchain without sudo.
#
#   1. ddvk/rmapi release binary  -> $PREFIX/rmapi        (default ~/.local/bin)
#   2. rmrl in its own venv       -> $RMRL_VENV           (default ~/.venvs/rmrl)
#   3. rmrender / rmsync symlinks -> $PREFIX
#
# rmrl pins reportlab==3.6.13, which no longer compiles on GCC 14+ (C23 makes
# `bool` a keyword and reportlab's gt1-parset1.c uses it as an identifier), so
# the venv MUST use a Python version with a prebuilt wheel: cp37-cp311 only.
# Hence --python 3.11. rmrl also needs pkg_resources, removed in setuptools 81.
set -Eeuo pipefail

PREFIX="${PREFIX:-$HOME/.local/bin}"
RMRL_VENV="${RMRL_VENV:-$HOME/.venvs/rmrl}"
RMRL_PYTHON="${RMRL_PYTHON:-3.11}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

die() { echo "error: $*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

mkdir -p "$PREFIX"

case "$(uname -m)" in
  x86_64|amd64) RMAPI_ARCH=amd64 ;;
  aarch64|arm64) RMAPI_ARCH=arm64 ;;
  *) die "unsupported architecture $(uname -m)" ;;
esac

# ---------------------------------------------------------------- rmapi ------
if [[ -x "$PREFIX/rmapi" && "${FORCE:-0}" != 1 ]]; then
  echo "rmapi already installed: $("$PREFIX/rmapi" version)"
else
  have curl || die "curl is required"
  tag="$(curl -fsSL https://api.github.com/repos/ddvk/rmapi/releases/latest \
    | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -1)"
  [[ -n "$tag" ]] || die "could not resolve the latest ddvk/rmapi release"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  url="https://github.com/ddvk/rmapi/releases/download/$tag/rmapi-linux-$RMAPI_ARCH.tar.gz"
  echo "downloading rmapi $tag ($RMAPI_ARCH)"
  curl -fsSL -o "$tmp/rmapi.tar.gz" "$url"
  tar xzf "$tmp/rmapi.tar.gz" -C "$tmp"
  install -m 755 "$tmp/rmapi" "$PREFIX/rmapi"
  echo "installed $PREFIX/rmapi ($("$PREFIX/rmapi" version))"
fi

# ----------------------------------------------------------------- rmrl ------
if [[ -x "$RMRL_VENV/bin/python" && "${FORCE:-0}" != 1 ]]; then
  echo "rmrl venv already present: $RMRL_VENV"
else
  if have uv; then
    uv venv "$RMRL_VENV" --python "$RMRL_PYTHON"
    uv pip install --python "$RMRL_VENV/bin/python" rmrl 'setuptools<81'
  else
    have "python$RMRL_PYTHON" || die "need uv, or python$RMRL_PYTHON on PATH"
    "python$RMRL_PYTHON" -m venv "$RMRL_VENV"
    "$RMRL_VENV/bin/pip" install --quiet --upgrade pip
    "$RMRL_VENV/bin/pip" install rmrl 'setuptools<81'
  fi
fi

"$RMRL_VENV/bin/python" - <<'PY'
import rmrl, sys
print(f"rmrl {rmrl.__name__} import OK on {sys.version.split()[0]}")
PY

# ------------------------------------------------------------- front ends ----
ln -sf "$SCRIPT_DIR/rmrender" "$PREFIX/rmrender"
ln -sf "$SCRIPT_DIR/rmsync" "$PREFIX/rmsync"
echo "linked $PREFIX/{rmrender,rmsync} -> $SCRIPT_DIR"

case ":$PATH:" in
  *":$PREFIX:"*) ;;
  *) echo "note: $PREFIX is not on PATH" ;;
esac

if [[ -s "${XDG_CONFIG_HOME:-$HOME/.config}/rmapi/rmapi.conf" ]]; then
  echo "rmapi already authenticated"
else
  cat <<'MSG'

Next: authenticate once.
  1. open https://my.remarkable.com/device/browser/connect and copy the 8-char code
  2. printf 'CODE\n' | rmapi auth
  3. rmapi ls /          # should list the cloud root
Then: rmsync             # mirror + render into $RM_MIRROR (default ~/Documents/Remarkable)
MSG
fi
