#!/usr/bin/env bash
# Run Indeed daily apply on THIS machine (must be home/residential network).
# Intended for cron / Task Scheduler / launchd — not for Cursor public-cloud VMs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG_DIR="${INDEED_HOME_LOG_DIR:-$HOME/.cursor/indeed-home-logs}"
mkdir -p "$LOG_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$LOG_DIR/indeed-$STAMP.log"

exec > >(tee -a "$LOG") 2>&1

echo "=== Indeed home daily @ $STAMP ==="
echo "cwd=$ROOT host=$(hostname) "

# Fail fast if this looks like a blocked public-cloud path (optional check).
if command -v node >/dev/null 2>&1 && [[ -f tools/indeed/preflight.js ]]; then
  set +e
  node tools/indeed/preflight.js
  pf=$?
  set -e
  if [[ "$pf" -eq 5 ]]; then
    echo "ERROR: Indeed Cloudflare block on this IP. Run this script on home Wi‑Fi, not a datacenter VPN/cloud."
    exit 5
  fi
  if [[ "$pf" -ne 0 ]]; then
    echo "WARNING: preflight exit $pf — continuing to agent (login may still work in browser)."
  fi
fi

PROMPT="$(cat <<'EOF'
You are the Indeed Daily apply runner on a HOME / residential machine.
Read and OBEY the full fenced instructions in automation-prompts/06-indeed.md.
1) node tools/indeed/preflight.js — if exit 5, STOP and report Cloudflare (wrong network).
2) bash scripts/preflight-portal-run.sh indeed
3) bash scripts/launch-chrome-cdp.sh indeed
4) Execute the daily Indeed apply job for Mohammed Abdul Rafi Ahmed.
Use resumes/Rafi_Resume.docx. Hyd/Telangana OR Remote only. Expected CTC 65 LPA.
Report submitted/skipped/blocked. Do not invent applies.
Write JSON summary to /opt/cursor/artifacts/indeed-daily-run.json if writable, else ./artifacts/indeed-daily-run.json.
EOF
)"

AGENT_BIN="${CURSOR_AGENT_BIN:-}"
if [[ -z "$AGENT_BIN" ]]; then
  AGENT_BIN="$(command -v agent || true)"
fi
if [[ -z "$AGENT_BIN" && -x "$HOME/.cursor/bin/agent" ]]; then
  AGENT_BIN="$HOME/.cursor/bin/agent"
fi
if [[ -z "$AGENT_BIN" && -x "$HOME/.local/bin/agent" ]]; then
  AGENT_BIN="$HOME/.local/bin/agent"
fi

if [[ -z "$AGENT_BIN" ]]; then
  echo "ERROR: Cursor CLI 'agent' not found. Install once:"
  echo "  curl https://cursor.com/install -fsS | bash"
  echo "  agent login"
  exit 127
fi

# Prefer API key for unattended cron; otherwise rely on prior `agent login`.
if [[ -z "${CURSOR_API_KEY:-}" ]]; then
  echo "NOTE: CURSOR_API_KEY unset — using interactive login session from 'agent login'."
fi

echo "Using agent: $AGENT_BIN"
# --force/--yolo allows shell + browser tools without prompts (home automation).
"$AGENT_BIN" -p --force --trust --workspace "$ROOT" "$PROMPT"
echo "=== done; log=$LOG ==="
