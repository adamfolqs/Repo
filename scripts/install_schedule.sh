#!/usr/bin/env bash
# Install (or remove) the weekly schedule: launchd on macOS, cron on Linux.
#
#   ./scripts/install_schedule.sh            # install, Friday 09:00
#   ./scripts/install_schedule.sh --at 17:30 # install at a different time
#   ./scripts/install_schedule.sh --uninstall
#   ./scripts/install_schedule.sh --status

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.folqs.weekly-tracker"
PLIST_TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"
RUNNER="$REPO_DIR/scripts/run_weekly_tracker.sh"
CRON_TAG="# folqs-weekly-tracker"
ACTION="install"
AT="09:00"

while [ $# -gt 0 ]; do
    case "$1" in
        --uninstall) ACTION="uninstall"; shift ;;
        --status)    ACTION="status";    shift ;;
        --at)        AT="${2:?--at needs HH:MM}"; shift 2 ;;
        *) echo "unknown option: $1" >&2; exit 2 ;;
    esac
done

HOUR="${AT%%:*}"
MINUTE="${AT##*:}"
HOUR="$((10#$HOUR))"
MINUTE="$((10#$MINUTE))"

install_launchd() {
    mkdir -p "$HOME/Library/LaunchAgents" "$REPO_DIR/data/tracking/logs"
    sed -e "s|__REPO_DIR__|$REPO_DIR|g" \
        -e "s|<key>Hour</key><integer>9</integer>|<key>Hour</key><integer>$HOUR</integer>|" \
        -e "s|<key>Minute</key><integer>0</integer>|<key>Minute</key><integer>$MINUTE</integer>|" \
        "$REPO_DIR/scripts/$LABEL.plist" > "$PLIST_TARGET"
    launchctl unload "$PLIST_TARGET" 2>/dev/null || true
    launchctl load "$PLIST_TARGET"
    echo "Installed launchd job '$LABEL' — Fridays at $AT."
    echo "  plist: $PLIST_TARGET"
    echo "  Note: grant your terminal Full Disk Access if the job cannot read the repo."
}

install_cron() {
    mkdir -p "$REPO_DIR/data/tracking/logs"
    local line="$MINUTE $HOUR * * 5 $RUNNER $CRON_TAG"
    local current
    current="$(crontab -l 2>/dev/null | grep -v -F "$CRON_TAG" || true)"
    printf '%s\n%s\n' "$current" "$line" | sed '/^$/d' | crontab -
    echo "Installed cron job — Fridays at $AT."
    echo "  $line"
    echo "  Note: cron does NOT catch up a run missed while the machine was off."
}

case "$ACTION" in
install)
    [ -x "$RUNNER" ] || chmod +x "$RUNNER"
    if [ "$(uname -s)" = "Darwin" ]; then install_launchd; else install_cron; fi
    echo
    echo "Next: verify the job's dependencies with"
    echo "  python -m folqs_tracker check"
    ;;
uninstall)
    if [ "$(uname -s)" = "Darwin" ]; then
        launchctl unload "$PLIST_TARGET" 2>/dev/null || true
        rm -f "$PLIST_TARGET"
        echo "Removed launchd job '$LABEL'."
    else
        crontab -l 2>/dev/null | grep -v -F "$CRON_TAG" | crontab - || true
        echo "Removed cron job."
    fi
    ;;
status)
    if [ "$(uname -s)" = "Darwin" ]; then
        launchctl list | grep -F "$LABEL" || echo "launchd job not loaded."
    else
        crontab -l 2>/dev/null | grep -F "$CRON_TAG" || echo "cron job not installed."
    fi
    ;;
esac
