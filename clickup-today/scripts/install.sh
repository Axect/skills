#!/usr/bin/env bash
set -euo pipefail

source=$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/clickup-today
target_dir=${PREFIX:-$HOME/.local/bin}
mkdir -p -- "$target_dir"
target=$target_dir/clickup-today
if [[ -L "$target" ]] && [[ $(readlink -- "$target") == "$source" ]]; then
    printf 'Already installed: %s\n' "$target"
elif [[ -e "$target" || -L "$target" ]]; then
    printf 'Refusing to replace existing command: %s\n' "$target" >&2
    exit 1
else
    ln -s -- "$source" "$target"
    printf 'Installed: %s\n' "$target"
fi
