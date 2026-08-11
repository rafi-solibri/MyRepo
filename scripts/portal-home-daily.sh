#!/usr/bin/env bash
# Run one portal's daily apply on THIS machine (home / residential).
# Usage:
#   bash scripts/portal-home-daily.sh <portal>
# Portals: linkedin | foundit | cutshort | naukri | instahyre | indeed
set -euo pipefail

PORTAL="${1:-}"
case "$PORTAL" in
  linkedin|foundit|cutshort|naukri|instahyre|indeed) ;;
  *)
    echo "Usage: bash scripts/portal-home-daily.sh <linkedin|foundit|cutshort|naukri|instahyre|indeed>"
    exit 2
    ;;
esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

prompt_file_for() {
  case "$1" in
    linkedin) echo "automation-prompts/01-linkedin.md" ;;
    foundit) echo "automation-prompts/02-foundit.md" ;;
    cutshort) echo "automation-prompts/03-cutshort.md" ;;
    naukri) echo "automation-prompts/04-naukri-general.md" ;;
    instahyre) echo "automation-prompts/05-instahyre.md" ;;
    indeed) echo "automation-prompts/06-indeed.md" ;;
  esac
}
PROMPT_MD="$(prompt_file_for "$PORTAL")"

LOG_DIR="${HOME_PORTAL_LOG_DIR:-$HOME/.cursor/portal-home-logs/$PORTAL}"
mkdir -p "$LOG_DIR" "$ROOT/artifacts"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="$LOG_DIR/$PORTAL-$STAMP.log"
REPORT_CLOUD="/opt/cursor/artifacts/${PORTAL}-daily-run.json"
REPORT_LOCAL="$ROOT/artifacts/${PORTAL}-daily-run.json"
REPORT_HOME="$LOG_DIR/${PORTAL}-daily-run.json"
REPORT_TOOL="$ROOT/tools/home_run_report.js"

# Indeed keeps its specialized normalizer for backward compatibility.
if [[ "$PORTAL" == "indeed" && -f "$ROOT/tools/indeed/daily_run_report.js" ]]; then
  REPORT_TOOL="$ROOT/tools/indeed/daily_run_report.js"
fi

exec > >(tee -a "$LOG") 2>&1

echo "=== $PORTAL home daily @ $STAMP ==="
echo "cwd=$ROOT host=$(hostname)"

write_empty() {
  local reason="$1"
  local out="$2"
  if [[ "$REPORT_TOOL" == *home_run_report.js ]]; then
    node "$REPORT_TOOL" empty --portal "$PORTAL" --reason "$reason" --source home-local --log "$LOG" --out "$out"
  else
    node "$REPORT_TOOL" empty --reason "$reason" --source home-local --log "$LOG" --out "$out"
  fi
}

normalize_report() {
  local inn="$1"
  local out="$2"
  if [[ "$REPORT_TOOL" == *home_run_report.js ]]; then
    node "$REPORT_TOOL" write --portal "$PORTAL" --in "$inn" --source home-local --log "$LOG" --out "$out"
  else
    node "$REPORT_TOOL" write --in "$inn" --source home-local --log "$LOG" --out "$out"
  fi
}

# Indeed Cloudflare gate (residential IP required).
# Home Windows: skip WARP — residential IP is the Cloudflare bypass.
if [[ "$PORTAL" == "indeed" ]]; then
  is_win=0
  [[ "${OS:-}" == "Windows_NT" || -n "${MSYSTEM:-}" || "$(uname -s 2>/dev/null)" == MINGW* ]] && is_win=1
  if [[ "$is_win" -eq 1 ]]; then
    export INDEED_SKIP_WARP="${INDEED_SKIP_WARP:-1}"
    echo "NOTE: Windows home Indeed — INDEED_SKIP_WARP=${INDEED_SKIP_WARP}"
  fi
fi
if [[ "$PORTAL" == "indeed" ]] && command -v node >/dev/null 2>&1 && [[ -f tools/indeed/preflight.js ]]; then
  set +e
  node tools/indeed/preflight.js
  pf=$?
  set -e
  if [[ "$pf" -eq 5 ]]; then
    echo "ERROR: Indeed Cloudflare block on this IP. Use home Wi‑Fi, not datacenter VPN/cloud."
    write_empty "indeed_cloudflare_private_worker_required" "$REPORT_LOCAL" || true
    cp "$REPORT_LOCAL" "$REPORT_HOME" 2>/dev/null || true
    bash scripts/publish-home-result.sh indeed "$REPORT_LOCAL" || true
    exit 5
  fi
  if [[ "$pf" -ne 0 ]]; then
    echo "WARNING: indeed preflight exit $pf — continuing to agent."
  fi
fi

EXTRA_STEPS=""
case "$PORTAL" in
  linkedin|naukri|indeed)
    EXTRA_STEPS="Then: bash scripts/launch-chrome-cdp.sh $PORTAL"
    ;;
esac
if [[ "$PORTAL" == "naukri" ]]; then
  EXTRA_STEPS="$EXTRA_STEPS
CRITICAL STEP 0 before applies: node tools/naukri/update_profile_resume.js (profileUpdated: true)."
fi

PROMPT="$(cat <<EOF
You are the ${PORTAL} Daily apply runner on a HOME / residential machine.
Read and OBEY the full fenced instructions in ${PROMPT_MD}.
Also OBEY automation-prompts/AUTO_FIX.md for every code-fixable blocker.
1) bash scripts/preflight-portal-run.sh ${PORTAL}
${EXTRA_STEPS}
2) Execute the daily ${PORTAL} apply job for Mohammed Abdul Rafi Ahmed.
Use resumes/Rafi_Resume.docx. Hyd/Telangana OR Remote only. Expected CTC 65 LPA.
Report submitted/skipped/blocked/rejected. Do not invent applies.

AUTO-FIX / PUSH / MERGE (MANDATORY when code-fixable):
- Patch durable helpers under tools/ or scripts/ or automation-prompts/
- Append automation-prompts/ISSUES_AND_FIXES.md
- Feature branch (never commit straight to main), git push
- Open a READY (non-draft) PR to main, then run: bash scripts/auto-merge-fix-pr.sh
- If merge conflicts: rebase onto origin/main, push, re-run auto-merge-fix-pr.sh
- After merge: git fetch origin main && git checkout main && git pull --ff-only
- Owner-only blockers (login/CAPTCHA/OTP): report + headed login helper if present; still ship any code helpers that make the next login smoother

HARD — write a JSON summary the daily mail can ingest:
- Prefer writable path: ${REPORT_CLOUD}
- Else: ${REPORT_LOCAL}
- Also copy to: ${REPORT_HOME}
Required JSON fields:
{
  "portal": "${PORTAL}",
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
After writing raw JSON, normalize with:
  node tools/home_run_report.js write --portal ${PORTAL} --in <that-file> --source home-local --out <same-file>
(For indeed you may use tools/indeed/daily_run_report.js instead.)
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
  local candidates=(
    "$HOME/.cursor/bin/agent"
    "$HOME/.local/bin/agent"
    "/mnt/c/Users/MohammedAhmed/AppData/Local/cursor-agent/agent.cmd"
  )
  # Git Bash on Windows: LOCALAPPDATA path
  if [[ -n "${LOCALAPPDATA:-}" ]]; then
    candidates+=("$LOCALAPPDATA/cursor-agent/agent.cmd")
  fi
  if [[ -n "${USERPROFILE:-}" ]]; then
    candidates+=("$USERPROFILE/AppData/Local/cursor-agent/agent.cmd")
  fi
  # WSL path when USER is set
  if [[ -n "${USER:-}" ]]; then
    candidates+=("/mnt/c/Users/${USER}/AppData/Local/cursor-agent/agent.cmd")
  fi
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
  echo "ERROR: Cursor CLI 'agent' not found. Install once:"
  echo "  irm 'https://cursor.com/install?win32=true' | iex"
  echo "  agent login"
  write_empty "cursor_agent_cli_missing" "$REPORT_LOCAL" || true
  bash scripts/publish-home-result.sh "$PORTAL" "$REPORT_LOCAL" || true
  exit 127
fi

if [[ -z "${CURSOR_API_KEY:-}" ]]; then
  echo "NOTE: CURSOR_API_KEY unset — using interactive login session from 'agent login'."
fi

echo "Using agent: $AGENT_BIN"
set +e
"$AGENT_BIN" -p --force --trust --workspace "$ROOT" "$PROMPT"
agent_rc=$?
set -e

# Safety net: merge leftover open fix PRs, then return to main for publish.
bash "$ROOT/scripts/merge-open-fix-prs.sh" || true
cd "$ROOT"
git fetch origin main >/dev/null 2>&1 || true
git checkout -f main >/dev/null 2>&1 || true
git pull --ff-only origin main >/dev/null 2>&1 || true

if [[ ! -f "$REPORT_CLOUD" && ! -f "$REPORT_LOCAL" && ! -f "$REPORT_HOME" ]]; then
  echo "WARNING: agent did not write ${PORTAL}-daily-run.json — recording empty/blocked stub"
  write_empty "agent_finished_without_report_exit_${agent_rc}" "$REPORT_LOCAL" || true
fi

FINAL_REPORT="$REPORT_LOCAL"
[[ -f "$REPORT_CLOUD" ]] && FINAL_REPORT="$REPORT_CLOUD"
[[ -f "$REPORT_HOME" && ! -f "$REPORT_CLOUD" && ! -f "$REPORT_LOCAL" ]] && FINAL_REPORT="$REPORT_HOME"

normalize_report "$FINAL_REPORT" "$REPORT_LOCAL"
cp "$REPORT_LOCAL" "$REPORT_HOME" 2>/dev/null || true
if [[ -d /opt/cursor/artifacts ]]; then
  cp "$REPORT_LOCAL" "$REPORT_CLOUD" 2>/dev/null || true
fi

echo "Publishing ${PORTAL} home results for daily mail…"
bash scripts/publish-home-result.sh "$PORTAL" "$REPORT_LOCAL"

echo "=== done; log=$LOG report=$REPORT_LOCAL agent_rc=$agent_rc ==="
exit "$agent_rc"
