#!/usr/bin/env bash
# research-backup discover: scan SCAN_ROOT for report-like directories that
# git does not track and compare them against the registry.
# Usage: discover.sh [--register]
set -uo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=./common.sh
source "$SCRIPT_DIR/common.sh"
load_config

REGISTER=0
case "${1:-}" in
  "") ;;
  --register) REGISTER=1 ;;
  *) echo "Usage: discover.sh [--register]" >&2; exit 64 ;;
esac

# Classify a directory's relationship to git:
#   no-git    : not inside any git repository
#   ignored   : inside a repo and matched by .gitignore
#   untracked : inside a repo, not ignored, but contains no tracked files
#   tracked   : contains files git already tracks (no backup needed)
git_state() {
  local d="$1" repo
  repo=$(git -C "$d" rev-parse --show-toplevel 2>/dev/null) || { echo "no-git"; return; }
  if git -C "$repo" check-ignore -q "$d" 2>/dev/null; then
    echo "ignored"
    return
  fi
  if [[ -z "$(git -C "$repo" ls-files -- "$d" 2>/dev/null | head -n1)" ]]; then
    echo "untracked"
  else
    echo "tracked"
  fi
}

# Build the find name expression from DIR_NAMES.
name_expr=()
for n in $DIR_NAMES; do
  name_expr+=(-name "$n" -o)
done
unset 'name_expr[${#name_expr[@]}-1]'

mapfile -t candidates < <(
  find "$SCAN_ROOT" -mindepth 2 \
    \( -type d \( -name .git -o -name node_modules -o -name .venv -o -name venv \
       -o -name __pycache__ -o -name target -o -name .cache -o -name .ipynb_checkpoints \) -prune \) -o \
    \( -type d \( "${name_expr[@]}" \) -print -prune \) | sort
)

declare -A registered=()
while IFS= read -r line; do
  registered["$line"]=1
done < <(read_registry)

new_paths=()
n_new=0 n_reg=0 n_tracked=0

printf '%-12s %-10s %s\n' "STATE" "GIT" "PATH"
for d in "${candidates[@]}"; do
  state=$(git_state "$d")
  if [[ -n "${registered[$d]:-}" ]]; then
    printf '%-12s %-10s %s\n' "REGISTERED" "$state" "$d"
    n_reg=$((n_reg + 1))
  elif [[ "$state" == "tracked" ]]; then
    printf '%-12s %-10s %s\n' "TRACKED" "$state" "$d"
    n_tracked=$((n_tracked + 1))
  else
    printf '%-12s %-10s %s\n' "NEW" "$state" "$d"
    new_paths+=("$d")
    n_new=$((n_new + 1))
  fi
done

# Registry entries whose directory no longer exists.
n_missing=0
while IFS= read -r entry; do
  if [[ ! -d "$entry" ]]; then
    printf '%-12s %-10s %s\n' "MISSING" "-" "$entry"
    n_missing=$((n_missing + 1))
  fi
done < <(read_registry)

if [[ $REGISTER -eq 1 && $n_new -gt 0 ]]; then
  for d in "${new_paths[@]}"; do
    printf '%s\n' "$d" >> "$REGISTRY_FILE"
  done
  echo "research-backup: registered $n_new new director$([[ $n_new -eq 1 ]] && echo y || echo ies) in $REGISTRY_FILE" >&2
fi

echo "research-backup: $n_new new, $n_reg registered, $n_tracked tracked (skipped), $n_missing missing" >&2
