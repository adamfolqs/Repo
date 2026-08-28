#!/usr/bin/env bash
# Wrapper for the scheduled weekly run.
#
# cron and launchd start with a near-empty environment and a working directory
# you did not choose, so this script pins both before doing anything, and logs
# every run. Without that, the usual failure is a job that "runs" every Friday
# and silently does nothing.

set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR" || exit 1

LOG_DIR="${TRACKER_LOG_DIR:-$REPO_DIR/data/tracking/logs}"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/weekly-$(date +%Y-%m-%d).log"

# Prefer the project venv; fall back to whatever python3 is on PATH.
if [ -x "$REPO_DIR/.venv/bin/python" ]; then
    PYTHON="$REPO_DIR/.venv/bin/python"
else
    PYTHON="$(command -v python3)"
fi

{
    echo "=== $(date '+%Y-%m-%d %H:%M:%S %Z') — folqs weekly tracker ==="
    echo "repo:   $REPO_DIR"
    echo "python: $PYTHON"
    "$PYTHON" -m folqs_tracker run "$@"
    status=$?
    echo "=== exit $status ==="
    exit $status
} >>"$LOG_FILE" 2>&1
