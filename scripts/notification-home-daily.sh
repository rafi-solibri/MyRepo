#!/usr/bin/env bash
# Home/local Notification Job — email daily status from all portal home runs.
# Intended for Task Scheduler after portal jobs finish (default 11:30).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG_DIR="${HOME_PORTAL_LOG_DIR:-$HOME/.cursor/portal-home-logs/notification}"
mkdir -p "$LOG_DIR" "$ROOT/artifacts"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$LOG_DIR/notification-$STAMP.log"

exec > >(tee -a "$LOG") 2>&1

echo "=== notification home daily @ $STAMP ==="

PORTALS=(linkedin foundit cutshort naukri instahyre indeed)
for p in "${PORTALS[@]}"; do
  echo "--- fetch $p ---"
  bash scripts/fetch-home-result.sh "$p" --today || true
done

PROMPT="$(cat <<'EOF'
You are the Notification Job runner on a HOME / residential machine.
Read and OBEY the full fenced instructions in automation-prompts/07-notification.md.

IMPORTANT — all apply portals now run HOME-LOCAL (not cloud). For EACH portal below,
run and parse the JSON before composing the email:

  bash scripts/fetch-home-result.sh linkedin --today
  bash scripts/fetch-home-result.sh foundit --today
  bash scripts/fetch-home-result.sh cutshort --today
  bash scripts/fetch-home-result.sh naukri --today
  bash scripts/fetch-home-result.sh instahyre --today
  bash scripts/fetch-home-result.sh indeed --today

Also still support the legacy Indeed helper if needed:
  bash scripts/fetch-indeed-home-result.sh --today

For each portal include: applied, external, rejected, blocked, skipped, blockerSummary,
and note source home-local. Do not invent applies. Prefer same-day JSON.

Email delivery:
- Prefer Resend MCP → rafi.success@gmail.com
- From: RESEND_FROM_EMAIL when set; else Job Status <onboarding@resend.dev>
- Subject: Job status — YYYY-MM-DD
- If Resend MCP unavailable but RESEND_API_KEY is set, use scripts/send-job-status-email.mjs
- Always write the full report to automation memory / artifacts/job-status-YYYY-MM-DD.md
EOF
)"

resolve_agent() {
  if [[ -n "${CURSOR_AGENT_BIN:-}" ]]; then
    echo "$CURSOR_AGENT_BIN"
    return
  fi
  if command -v agent >/dev/null 2>&1; then
    command -v agent
    return
  fi
  local candidates=()
  if [[ -n "${LOCALAPPDATA:-}" ]]; then
    candidates+=("$LOCALAPPDATA/cursor-agent/agent.cmd")
  fi
  candidates+=(
    "$HOME/.cursor/bin/agent"
    "$HOME/.local/bin/agent"
    "/mnt/c/Users/MohammedAhmed/AppData/Local/cursor-agent/agent.cmd"
  )
  for c in "${candidates[@]}"; do
    if [[ -x "$c" || -f "$c" ]]; then
      echo "$c"
      return
    fi
  done
  echo ""
}

AGENT_BIN="$(resolve_agent)"
if [[ -z "$AGENT_BIN" ]]; then
  echo "ERROR: Cursor CLI 'agent' not found."
  exit 127
fi

echo "Using agent: $AGENT_BIN"
set +e
"$AGENT_BIN" -p --force --trust --workspace "$ROOT" "$PROMPT"
agent_rc=$?
set -e

echo "=== done; log=$LOG agent_rc=$agent_rc ==="
exit "$agent_rc"
