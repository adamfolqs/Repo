#!/bin/bash
# Titan System installer — mirrors the package into ~/.claude/ and ~/.memory/.
# Non-destructive: existing destinations are backed up to ~/.titan-backup-<timestamp>/ first.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$HOME/.titan-backup-$TIMESTAMP"

# Destinations
PLUGIN_DST="$HOME/.claude/plugins/local/titan"
MEMORY_BASE="$HOME/.memory"
SKILLS_CP="$MEMORY_BASE/skills/copywriting"
SKILLS_DS="$MEMORY_BASE/skills/design"
SKILLS_OPS="$MEMORY_BASE/skills/ops"
SCRIPTS_DST="$MEMORY_BASE/scripts"

echo "Titan System installer"
echo "  source:  $SCRIPT_DIR"
echo "  backups: $BACKUP_DIR (created only if needed)"
echo

backup_if_exists() {
  local target="$1"
  if [ -e "$target" ]; then
    mkdir -p "$BACKUP_DIR"
    local rel="${target#$HOME/}"
    local dest="$BACKUP_DIR/$rel"
    mkdir -p "$(dirname "$dest")"
    mv "$target" "$dest"
    echo "  backed up: $target -> $dest"
  fi
}

install_dir() {
  local src="$1"
  local dst="$2"
  if [ ! -e "$src" ]; then
    echo "  SKIP (missing in package): $src"
    return
  fi
  backup_if_exists "$dst"
  mkdir -p "$(dirname "$dst")"
  cp -R "$src" "$dst"
  echo "  installed: $dst"
}

install_file() {
  local src="$1"
  local dst="$2"
  if [ ! -e "$src" ]; then
    echo "  SKIP (missing in package): $src"
    return
  fi
  backup_if_exists "$dst"
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  chmod +x "$dst" 2>/dev/null || true
  echo "  installed: $dst"
}

echo "Installing plugin..."
install_dir "$SCRIPT_DIR/plugin" "$PLUGIN_DST"

echo
echo "Installing copywriting skills..."
install_dir "$SCRIPT_DIR/skills/copywriting/titan-dr"             "$SKILLS_CP/titan-dr"
install_dir "$SCRIPT_DIR/skills/copywriting/titan-verify"         "$SKILLS_CP/titan-verify"
install_dir "$SCRIPT_DIR/skills/copywriting/titan-video-analyzer" "$SKILLS_CP/titan-video-analyzer"

echo
echo "Installing design skills..."
install_dir "$SCRIPT_DIR/skills/design/titan-ads"                "$SKILLS_DS/titan-ads"
install_dir "$SCRIPT_DIR/skills/design/titan-conversion-designer" "$SKILLS_DS/titan-conversion-designer"

echo
echo "Installing workflow enforcement..."
install_dir "$SCRIPT_DIR/workflow-enforcement" "$SKILLS_OPS/workflow-enforcement"

echo
echo "Installing workflow scripts..."
install_file "$SCRIPT_DIR/scripts/workflow-claim.sh" "$SCRIPTS_DST/workflow-claim.sh"
install_file "$SCRIPT_DIR/scripts/workflow-mark.sh"  "$SCRIPTS_DST/workflow-mark.sh"

echo
echo "Done."
if [ -d "$BACKUP_DIR" ]; then
  echo "Existing files were backed up to: $BACKUP_DIR"
fi
echo
echo "Next: restart Claude Code, then test with:"
echo "  /titan write 5 scroll-stop hooks for a beef organ supplement"
