#!/usr/bin/env bash
# Install a daily home cron for Indeed (macOS/Linux/WSL).
# Usage:
#   bash scripts/install-indeed-home-cron.sh [HH:MM]
# Default time: 09:00 local.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIME="${1:-09:00}"
HOUR="${TIME%%:*}"
MIN="${TIME##*:}"
SCRIPT="$ROOT/scripts/indeed-home-daily.sh"
chmod +x "$SCRIPT" "$ROOT/scripts/indeed-home-daily.sh"

MARKER="# indeed-home-daily cursor"
LINE="$MIN $HOUR * * * cd $ROOT && /usr/bin/env bash $SCRIPT $MARKER"

# Ensure agent is on PATH for cron (often minimal env).
CRON_PATH_LINE="PATH=$HOME/.cursor/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"

existing="$(crontab -l 2>/dev/null || true)"
filtered="$(printf '%s\n' "$existing" | grep -v 'indeed-home-daily cursor' || true)"

{
  printf '%s\n' "$filtered"
  echo "$CRON_PATH_LINE"
  echo "$LINE"
} | grep -v '^$' | crontab -

echo "Installed cron entry for Indeed home daily at $TIME local:"
crontab -l | grep -A1 'indeed-home-daily' || crontab -l | tail -5
echo
echo "Prereqs (once):"
echo "  curl https://cursor.com/install -fsS | bash"
echo "  agent login"
echo "  # optional for headless cron:"
echo "  export CURSOR_API_KEY=...   # from https://cursor.com/dashboard/api → put in ~/.bashrc or cron env"
echo
echo "Test now: bash $SCRIPT"
echo "Remove: crontab -l | grep -v indeed-home-daily | crontab -"
