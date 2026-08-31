#!/usr/bin/env bash
# One-time setup on the machine that will run the tracker.
#
# This has to run on YOUR machine, not in a cloud session: the whole point is a
# real Chrome, logged into your Seller Center, on a residential IP. Datacenter
# IPs get captcha-walled, which is measured and documented in the README.
#
#   ./scripts/setup.sh

set -uo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR" || exit 1

step() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }
warn() { printf '    \033[33m%s\033[0m\n' "$1"; }
ok()   { printf '    \033[32m%s\033[0m\n' "$1"; }

step "Checking Python"
PY="$(command -v python3 || true)"
[ -n "$PY" ] || { echo "python3 not found. Install Python 3.10+ and re-run."; exit 1; }
"$PY" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' || {
    echo "Python 3.10+ required; found $("$PY" --version)"; exit 1; }
ok "$("$PY" --version)"

step "Creating the virtualenv (.venv)"
[ -d .venv ] || "$PY" -m venv .venv
VENV_PY=".venv/bin/python"
ok "$($VENV_PY --version) in .venv"

step "Installing dependencies"
"$VENV_PY" -m pip install --quiet --upgrade pip
"$VENV_PY" -m pip install --quiet -r requirements.txt || {
    echo "pip install failed — see the output above."; exit 1; }
ok "installed"

step "Installing Chromium for Playwright"
if "$VENV_PY" -m playwright install chromium; then
    ok "browser ready"
else
    warn "Chromium install failed. Capture will not work until it succeeds:"
    warn "    .venv/bin/python -m playwright install chromium"
fi

step "Creating .env"
if [ -f .env ]; then
    ok ".env already exists — left alone"
else
    cp .env.example .env
    ok "copied .env.example -> .env"
fi

step "What is still needed"
missing=0
grep -q '^ANTHROPIC_API_KEY=.\+' .env || { warn "ANTHROPIC_API_KEY is empty in .env"; missing=1; }
[ -f service_account.json ] || {
    warn "service_account.json missing — and the two Sheets must be shared with"
    warn "its client_email as Editor, or writes 403"; missing=1; }
grep -q '^SMTP_HOST=.\+' .env || { warn "SMTP settings are empty in .env"; missing=1; }
grep -q '^TELEGRAM_BOT_TOKEN=.\+' .env || { warn "TELEGRAM_BOT_TOKEN is empty in .env"; missing=1; }
[ "$missing" -eq 0 ] && ok "credentials all present"

cat <<'NEXT'

Next, in order:

  .venv/bin/python -m folqs_tracker login       # a browser opens; log in (2FA and all)
  .venv/bin/python -m folqs_tracker calibrate   # visit each of the 6 screens, it records them
  .venv/bin/python -m folqs_tracker check       # confirms everything above is wired up
  .venv/bin/python -m folqs_tracker capture --headed --only shop_analytics
                                                # watch one screen get captured
  .venv/bin/python -m folqs_tracker run --capture --dry-run --print-report
                                                # full pipeline, writes nothing

Then, when that looks right:

  .venv/bin/python -m folqs_tracker backfill --capture --dry-run   # the 6 missing weeks
  ./scripts/install_schedule.sh                                    # Fridays 09:00

NEXT
