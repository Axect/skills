#!/usr/bin/env bash
# research-backup shared helpers: config and registry loading.
# Sourced by discover.sh and backup.sh; not meant to be executed directly.

CONFIG_DIR="${RESEARCH_BACKUP_CONFIG_DIR:-$HOME/.config/research-backup}"
CONFIG_FILE="$CONFIG_DIR/config"
REGISTRY_FILE="$CONFIG_DIR/registry"

ensure_config() {
  mkdir -p "$CONFIG_DIR"
  if [[ ! -f "$CONFIG_FILE" ]]; then
    cat > "$CONFIG_FILE" <<'EOF'
# research-backup configuration. This file is sourced as shell, so keep
# KEY="value" lines only. $HOME is expanded at load time.

# Root under which research projects live. Registry paths inside this root
# are mirrored relative to it, so the Dropbox side keeps the
# <category>/<project>/<dir> layout and same-named projects in different
# categories never collide.
SCAN_ROOT="$HOME/Documents/Project"

# Destination root inside the locally synced Dropbox folder. The Dropbox
# daemon picks up anything written here; no API calls are made.
BACKUP_ROOT="$HOME/Dropbox/ResearchBackup"

# Directory basenames discover.sh looks for.
DIR_NAMES="outputs results report reports"

# Optional rsync exclude patterns, space separated (e.g. "*.ckpt wandb").
RSYNC_EXCLUDES=""
EOF
    echo "research-backup: created default config at $CONFIG_FILE" >&2
  fi
  [[ -f "$REGISTRY_FILE" ]] || : > "$REGISTRY_FILE"
}

load_config() {
  ensure_config
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
  : "${SCAN_ROOT:?research-backup: SCAN_ROOT missing in $CONFIG_FILE}"
  : "${BACKUP_ROOT:?research-backup: BACKUP_ROOT missing in $CONFIG_FILE}"
  DIR_NAMES="${DIR_NAMES:-outputs results report reports}"
  RSYNC_EXCLUDES="${RSYNC_EXCLUDES:-}"
  if [[ ! -d "$SCAN_ROOT" ]]; then
    echo "research-backup: SCAN_ROOT does not exist: $SCAN_ROOT" >&2
    exit 2
  fi
  if [[ ! -d "$(dirname "$BACKUP_ROOT")" ]]; then
    echo "research-backup: parent of BACKUP_ROOT does not exist: $(dirname "$BACKUP_ROOT"). Is the Dropbox client syncing this machine?" >&2
    exit 2
  fi
}

# Map a source directory to its destination under BACKUP_ROOT.
# Inside SCAN_ROOT the relative layout is preserved; anything else under
# $HOME goes to _external/<rel-to-home>. Paths outside $HOME are rejected.
dest_for() {
  local src="$1"
  case "$src" in
    "$SCAN_ROOT"/*) printf '%s\n' "$BACKUP_ROOT/${src#"$SCAN_ROOT"/}" ;;
    "$HOME"/*)      printf '%s\n' "$BACKUP_ROOT/_external/${src#"$HOME"/}" ;;
    *)              return 1 ;;
  esac
}

# Emit registry entries, skipping blank lines and # comments.
read_registry() {
  grep -vE '^[[:space:]]*(#|$)' "$REGISTRY_FILE" 2>/dev/null || true
}
