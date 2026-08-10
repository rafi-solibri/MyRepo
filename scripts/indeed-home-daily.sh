#!/usr/bin/env bash
# Run Indeed daily apply on THIS machine (must be home/residential network).
# Intended for cron / Task Scheduler / launchd — not for Cursor public-cloud VMs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG_DIR="${INDEED_HOME_LOG_DIR:-$HOME/.cursor/indeed-home-logs}"
mkdir -p "$LOG_DIR" "$ROOT/artifacts"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$LOG_DIR/indeed-$STAMP.log"
REPORT_CLOUD="/opt/cursor/artifacts/indeed-daily-run.json"
REPORT_LOCAL="$ROOT/artifacts/indeed-daily-run.json"
REPORT_HOME="$LOG_DIR/indeed-daily-run.json"

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
    node tools/indeed/daily_run_report.js empty \
      --reason "indeed_cloudflare_private_worker_required" \
      --source home-local \
      --log "$LOG" \
      --out "$REPORT_LOCAL" || true
    cp "$REPORT_LOCAL" "$REPORT_HOME" 2>/dev/null || true
    bash scripts/publish-indeed-home-result.sh "$REPORT_LOCAL" || true
    exit 5
  fi
  if [[ "$pf" -ne 0 ]]; then
    echo "WARNING: preflight exit $pf — continuing to agent (login may still work in browser)."
  fi
fi

PROMPT="$(cat <<EOF
You are the Indeed Daily apply runner on a HOME / residential machine.
Read and OBEY the full fenced instructions in automation-prompts/06-indeed.md.
1) node tools/indeed/preflight.js — if exit 5, STOP and report Cloudflare (wrong network).
2) bash scripts/preflight-portal-run.sh indeed
3) bash scripts/launch-chrome-cdp.sh indeed
4) Execute the daily Indeed apply job for Mohammed Abdul Rafi Ahmed.
Use resumes/Rafi_Resume.docx. Hyd/Telangana OR Remote only. Expected CTC 65 LPA.
Report submitted/skipped/blocked/rejected. Do not invent applies.

HARD — write a JSON summary the daily mail can ingest:
- Prefer writable path: $REPORT_CLOUD
- Else: $REPORT_LOCAL
- Also copy/symlink-equivalent write to: $REPORT_HOME
Required JSON fields:
{
  "portal": "indeed",
  "source": "home-local",
  "date": "YYYY-MM-DD",
  "finishedAt": "ISO-8601",
  "counts": {
    "applied": 0,
    "external": 0,
    "rejected": 0,
    "blocked": 0,
    "skipped": 0,
    "seen": 0
  },
  "applied": [],
  "external": [],
  "rejected": [],
  "blocked": [],
  "skipped": [],
  "blockerSummary": null
}
After writing raw JSON, run:
  node tools/indeed/daily_run_report.js write --in <that-file> --source home-local --out <same-file>
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
  node tools/indeed/daily_run_report.js empty \
    --reason "cursor_agent_cli_missing" \
    --source home-local \
    --log "$LOG" \
    --out "$REPORT_LOCAL" || true
  bash scripts/publish-indeed-home-result.sh "$REPORT_LOCAL" || true
  exit 127
fi

# Prefer API key for unattended cron; otherwise rely on prior `agent login`.
if [[ -z "${CURSOR_API_KEY:-}" ]]; then
  echo "NOTE: CURSOR_API_KEY unset — using interactive login session from 'agent login'."
fi

echo "Using agent: $AGENT_BIN"
set +e
# --force/--yolo allows shell + browser tools without prompts (home automation).
"$AGENT_BIN" -p --force --trust --workspace "$ROOT" "$PROMPT"
agent_rc=$?
set -e

# Ensure a report exists even if the agent forgot to write one.
if [[ ! -f "$REPORT_CLOUD" && ! -f "$REPORT_LOCAL" && ! -f "$REPORT_HOME" ]]; then
  echo "WARNING: agent did not write indeed-daily-run.json — recording empty/blocked stub"
  node tools/indeed/daily_run_report.js empty \
    --reason "agent_finished_without_report_exit_${agent_rc}" \
    --source home-local \
    --log "$LOG" \
    --out "$REPORT_LOCAL" || true
fi

# Prefer cloud artifacts path when present, else local.
FINAL_REPORT="$REPORT_LOCAL"
[[ -f "$REPORT_CLOUD" ]] && FINAL_REPORT="$REPORT_CLOUD"
[[ -f "$REPORT_HOME" && ! -f "$REPORT_CLOUD" && ! -f "$REPORT_LOCAL" ]] && FINAL_REPORT="$REPORT_HOME"

# Normalize + copy into standard locations for publish.
node tools/indeed/daily_run_report.js write \
  --in "$FINAL_REPORT" \
  --source home-local \
  --log "$LOG" \
  --out "$REPORT_LOCAL"
cp "$REPORT_LOCAL" "$REPORT_HOME" 2>/dev/null || true
if [[ -d /opt/cursor/artifacts ]]; then
  cp "$REPORT_LOCAL" "$REPORT_CLOUD" 2>/dev/null || true
fi

echo "Publishing Indeed home results for daily mail…"
bash scripts/publish-indeed-home-result.sh "$REPORT_LOCAL"

echo "=== done; log=$LOG report=$REPORT_LOCAL agent_rc=$agent_rc ==="
exit "$agent_rc"
