#!/bin/bash
# workflow-mark.sh — Mark a workflow phase as complete.
# Called by SKILL.md after producing the expected artifact for a phase.
#
# Usage: workflow-mark.sh <phase_name> <artifact_path>
# Example: workflow-mark.sh blueprint /Users/mike/projects/landing-x/blueprint.md
#
# Behavior:
#   - Verifies artifact exists and meets min_bytes from contract
#   - Writes <phase>.done.json under ~/.memory/workflows/{plugin}/{session_id}/
#   - Moves phase from phases_remaining to phases_complete
#   - Exits non-zero if validation fails

set -euo pipefail

PHASE="${1:-}"
ARTIFACT="${2:-}"

if [ -z "$PHASE" ] || [ -z "$ARTIFACT" ]; then
  echo "Usage: workflow-mark.sh <phase_name> <artifact_path>" >&2
  exit 1
fi

WORKFLOWS_DIR="$HOME/.memory/workflows"
ACTIVE_FILE="$WORKFLOWS_DIR/active.json"

if [ ! -f "$ACTIVE_FILE" ]; then
  echo "ERROR: No active workflow. Run workflow-claim.sh first." >&2
  exit 1
fi

PLUGIN=$(jq -r '.plugin' "$ACTIVE_FILE")
SESSION_ID=$(jq -r '.session_id' "$ACTIVE_FILE")
CONTRACT_PATH=$(jq -r '.contract_path' "$ACTIVE_FILE")
SESSION_DIR="$WORKFLOWS_DIR/$PLUGIN/$SESSION_ID"

if [ ! -f "$CONTRACT_PATH" ]; then
  echo "ERROR: Contract file vanished: $CONTRACT_PATH" >&2
  exit 1
fi

# Verify phase exists in contract
PHASE_DEF=$(jq --arg p "$PHASE" '.phases[] | select(.name == $p)' "$CONTRACT_PATH")
if [ -z "$PHASE_DEF" ]; then
  echo "ERROR: Phase '$PHASE' not in contract. Valid phases:" >&2
  jq -r '.phases[].name' "$CONTRACT_PATH" >&2
  exit 1
fi

MIN_BYTES=$(echo "$PHASE_DEF" | jq -r '.min_bytes // 0')

# Verify artifact exists
if [ ! -f "$ARTIFACT" ]; then
  echo "ERROR: Artifact does not exist: $ARTIFACT" >&2
  exit 1
fi

# Get artifact size (macOS-compatible)
ARTIFACT_SIZE=$(stat -f%z "$ARTIFACT" 2>/dev/null || stat -c%s "$ARTIFACT")

if [ "$ARTIFACT_SIZE" -lt "$MIN_BYTES" ]; then
  echo "ERROR: Artifact too small ($ARTIFACT_SIZE bytes, min $MIN_BYTES): $ARTIFACT" >&2
  echo "Phase '$PHASE' requires substantive output." >&2
  exit 1
fi

# Write phase marker
MARKED_AT=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
mkdir -p "$SESSION_DIR"
jq -n \
  --arg phase "$PHASE" \
  --arg marked "$MARKED_AT" \
  --arg artifact "$ARTIFACT" \
  --argjson size "$ARTIFACT_SIZE" \
  '{
    phase: $phase,
    marked_at: $marked,
    artifact_path: $artifact,
    artifact_size_bytes: $size
  }' > "$SESSION_DIR/$PHASE.done.json"

# Update active.json: move phase from remaining -> complete
TMP=$(mktemp)
jq --arg p "$PHASE" '
  .phases_complete = (.phases_complete + [$p] | unique) |
  .phases_remaining = (.phases_remaining - [$p])
' "$ACTIVE_FILE" > "$TMP"
mv "$TMP" "$ACTIVE_FILE"

echo "✓ Marked phase '$PHASE' complete ($ARTIFACT_SIZE bytes)"
