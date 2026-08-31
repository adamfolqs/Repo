#!/bin/bash
# workflow-claim.sh — Claim a workflow at the start of a multi-phase plugin run.
# Called by SKILL.md (e.g., cro/SKILL.md) when the workflow begins.
#
# Usage: workflow-claim.sh <plugin> <mode> [workspace_path]
# Example: workflow-claim.sh cro build /Users/mike/projects/landing-x
#
# Behavior:
#   - If active.json exists and matches same plugin → no-op (handles nested calls)
#   - Otherwise: generate session_id, copy contract, write active.json
#   - Echo session_id to stdout

set -euo pipefail

PLUGIN="${1:-}"
MODE="${2:-}"
WORKSPACE="${3:-$PWD}"

if [ -z "$PLUGIN" ] || [ -z "$MODE" ]; then
  echo "Usage: workflow-claim.sh <plugin> <mode> [workspace_path]" >&2
  exit 1
fi

WORKFLOWS_DIR="$HOME/.memory/workflows"
ACTIVE_FILE="$WORKFLOWS_DIR/active.json"
CONTRACTS_DIR="$HOME/.memory/skills/ops/workflow-enforcement/contracts"
CONTRACT_FILE="$CONTRACTS_DIR/${PLUGIN}-${MODE}.json"

mkdir -p "$WORKFLOWS_DIR/_archive"

# Verify contract exists
if [ ! -f "$CONTRACT_FILE" ]; then
  echo "ERROR: No contract found at $CONTRACT_FILE" >&2
  echo "Available contracts:" >&2
  ls "$CONTRACTS_DIR" 2>/dev/null >&2 || echo "  (none)" >&2
  exit 1
fi

# Idempotent claim — if same plugin already active, return its session_id
if [ -f "$ACTIVE_FILE" ]; then
  EXISTING_PLUGIN=$(jq -r '.plugin // empty' "$ACTIVE_FILE")
  EXISTING_MODE=$(jq -r '.mode // empty' "$ACTIVE_FILE")
  EXISTING_SESSION=$(jq -r '.session_id // empty' "$ACTIVE_FILE")

  if [ "$EXISTING_PLUGIN" = "$PLUGIN" ] && [ "$EXISTING_MODE" = "$MODE" ]; then
    echo "$EXISTING_SESSION"
    exit 0
  fi

  # Different active workflow — block
  echo "ERROR: Workflow already active: $EXISTING_PLUGIN/$EXISTING_MODE (session $EXISTING_SESSION)" >&2
  echo "Finish it or run /cancel-workflow first." >&2
  exit 2
fi

# Generate session_id: YYYY-MM-DD-HHMM-<random6>
# Use openssl to avoid SIGPIPE from `tr | head` under pipefail
RAND6=$(openssl rand -hex 3 2>/dev/null || printf '%06x' $RANDOM)
SESSION_ID="$(date '+%Y-%m-%d-%H%M')-${RAND6}"
STARTED_AT=$(date -u '+%Y-%m-%dT%H:%M:%SZ')

# Extract phases from contract
PHASES_REMAINING=$(jq -c '[.phases[].name]' "$CONTRACT_FILE")

# Write active.json
jq -n \
  --arg plugin "$PLUGIN" \
  --arg mode "$MODE" \
  --arg session "$SESSION_ID" \
  --arg started "$STARTED_AT" \
  --arg workspace "$WORKSPACE" \
  --arg contract "$CONTRACT_FILE" \
  --argjson remaining "$PHASES_REMAINING" \
  '{
    plugin: $plugin,
    mode: $mode,
    session_id: $session,
    started_at: $started,
    workspace: $workspace,
    contract_path: $contract,
    phases_complete: [],
    phases_remaining: $remaining,
    stop_hook_fires: 0
  }' > "$ACTIVE_FILE"

# Create session phase-marker directory
mkdir -p "$WORKFLOWS_DIR/$PLUGIN/$SESSION_ID"

echo "$SESSION_ID"
