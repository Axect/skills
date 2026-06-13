#!/usr/bin/env bash
# research-backup backup: mirror registered report directories into
# BACKUP_ROOT with rsync. Additive only; deletions are never propagated.
# Usage: backup.sh [--dry-run|-n] (--all | <filter>...)
set -uo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=./common.sh
source "$SCRIPT_DIR/common.sh"
load_config

command -v rsync >/dev/null 2>&1 || { echo "research-backup: rsync is required" >&2; exit 127; }

usage() {
  echo "Usage: backup.sh [--dry-run|-n] (--all | <filter>...)" >&2
  exit 64
}

DRY=0
ALL=0
FILTERS=()
for arg in "$@"; do
  case "$arg" in
    --dry-run|-n) DRY=1 ;;
    --all) ALL=1 ;;
    -*) usage ;;
    *) FILTERS+=("$arg") ;;
  esac
done
[[ $ALL -eq 1 || ${#FILTERS[@]} -gt 0 ]] || usage

matches() {
  local entry="$1" f
  [[ $ALL -eq 1 ]] && return 0
  for f in "${FILTERS[@]}"; do
    [[ "${entry,,}" == *"${f,,}"* ]] && return 0
  done
  return 1
}

excl=()
for p in $RSYNC_EXCLUDES; do
  excl+=(--exclude "$p")
done

rsync_flags=(-a --itemize-changes)
[[ $DRY -eq 1 ]] && rsync_flags+=(-n)

n_matched=0 n_missing=0 n_failed=0 total_items=0

while IFS= read -r src; do
  matches "$src" || continue
  n_matched=$((n_matched + 1))

  if [[ ! -d "$src" ]]; then
    echo "WARN  missing source, skipped: $src" >&2
    n_missing=$((n_missing + 1))
    continue
  fi

  if ! dest=$(dest_for "$src"); then
    echo "WARN  not under \$HOME, skipped: $src" >&2
    n_missing=$((n_missing + 1))
    continue
  fi

  [[ $DRY -eq 1 ]] || mkdir -p "$dest"

  out=$(rsync "${rsync_flags[@]}" "${excl[@]}" "$src/" "$dest/" 2>&1)
  rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "FAIL  rsync exited $rc: $src" >&2
    printf '%s\n' "$out" >&2
    n_failed=$((n_failed + 1))
    continue
  fi

  changed=$(printf '%s\n' "$out" | grep -c '[^[:space:]]')
  total_items=$((total_items + changed))
  rel="${src#"$SCAN_ROOT"/}"
  if [[ $changed -eq 0 ]]; then
    printf 'OK    %-60s up to date\n' "$rel"
  elif [[ $DRY -eq 1 ]]; then
    printf 'PEND  %-60s %d item(s) would sync\n' "$rel" "$changed"
  else
    printf 'OK    %-60s %d item(s) synced -> %s\n' "$rel" "$changed" "$dest"
  fi
done < <(read_registry)

if [[ $n_matched -eq 0 ]]; then
  echo "research-backup: no registry entry matched. Run discover.sh first or check the filter." >&2
  exit 3
fi

mode=$([[ $DRY -eq 1 ]] && echo "dry-run" || echo "synced")
echo "research-backup: $n_matched matched, $total_items item(s) $mode, $n_missing skipped, $n_failed failed" >&2
[[ $n_failed -gt 0 ]] && exit 5
exit 0
