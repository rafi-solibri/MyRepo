#!/usr/bin/env bash
# In-session apply → auto-fix → merge → re-run loop (max 5) for one portal.
#
# Intended for cloud/home daily agents so "fix blockers and re-run up to 5 times"
# is mechanical, not prompt-only.
#
# Usage:
#   bash scripts/run-portal-with-autofix.sh <portal>
#   bash scripts/run-portal-with-autofix.sh naukri --max 5
#
# This script runs the durable apply helper each attempt. If the helper exits
# non-zero OR writes a report with codeFixable hint, the agent (caller) is
# expected to have already patched+merged; this script then pulls main and
# retries. For fully unattended loops inside an agent session, pair with
# AUTO_FIX.md: after each failed attempt, fix → append-issue-fix → auto-merge.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORTAL="$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
shift || true
MAX="${POST_FIX_RERUN_MAX:-5}"
TODAY="${POST_FIX_RERUN_DATE:-$(TZ=Asia/Kolkata date +%Y-%m-%d)}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --max) MAX="${2:-5}"; shift 2 ;;
    --help|-h)
      echo "Usage: bash scripts/run-portal-with-autofix.sh <portal> [--max N]"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

VALID=(linkedin foundit cutshort naukri instahyre indeed hitechcity)
ok=0
for p in "${VALID[@]}"; do [[ "$p" == "$PORTAL" ]] && ok=1 && break; done
if [[ "$ok" -ne 1 ]]; then
  echo "Usage: bash scripts/run-portal-with-autofix.sh <portal> [--max N]" >&2
  echo "Portals: ${VALID[*]}" >&2
  exit 2
fi

artifact_dir() {
  if [[ -d /opt/cursor/artifacts && -w /opt/cursor/artifacts ]]; then
    echo /opt/cursor/artifacts
  else
    mkdir -p "$ROOT/artifacts"
    echo "$ROOT/artifacts"
  fi
}

run_once() {
  local portal="$1"
  case "$portal" in
    linkedin)
      bash "$ROOT/scripts/preflight-portal-run.sh" linkedin || return $?
      bash "$ROOT/scripts/launch-chrome-cdp.sh" linkedin || return $?
      python3 "$ROOT/tools/linkedin/linkedin_easy_apply.py" || return $?
      python3 "$ROOT/tools/linkedin/linkedin_external_apply.py" || true
      ;;
    foundit)
      bash "$ROOT/scripts/preflight-portal-run.sh" foundit || return $?
      bash "$ROOT/scripts/launch-chrome-cdp.sh" foundit || return $?
      node "$ROOT/tools/foundit/daily_apply.js" || return $?
      ;;
    cutshort)
      bash "$ROOT/scripts/preflight-portal-run.sh" cutshort || return $?
      bash "$ROOT/scripts/launch-chrome-cdp.sh" cutshort || return $?
      node "$ROOT/tools/cutshort/daily_apply.js" || return $?
      ;;
    naukri)
      bash "$ROOT/scripts/preflight-portal-run.sh" naukri || return $?
      bash "$ROOT/scripts/launch-chrome-cdp.sh" naukri || return $?
      node "$ROOT/tools/naukri/daily_apply.js" || return $?
      ;;
    instahyre)
      bash "$ROOT/scripts/preflight-portal-run.sh" instahyre || return $?
      bash "$ROOT/scripts/launch-chrome-cdp.sh" instahyre || return $?
      node "$ROOT/tools/instahyre/daily_apply.js" || return $?
      ;;
    hirist)
      bash "$ROOT/scripts/preflight-portal-run.sh" hirist || return $?
      bash "$ROOT/scripts/launch-chrome-cdp.sh" hirist || return $?
      node "$ROOT/tools/hirist/daily_apply.js" || return $?
      ;;
    indeed)
      node "$ROOT/tools/indeed/preflight.js" || return $?
      bash "$ROOT/scripts/preflight-portal-run.sh" indeed || return $?
      node "$ROOT/tools/indeed/daily_apply.js" || return $?
      ;;
    hitechcity)
      bash "$ROOT/scripts/preflight-portal-run.sh" hitechcity || return $?
      bash "$ROOT/scripts/launch-chrome-cdp.sh" hitechcity || true
      export HITECHCITY_PARALLEL_TABS="${HITECHCITY_PARALLEL_TABS:-10}"
      python3 "$ROOT/tools/hitechcity/daily_apply.py" || return $?
      ;;
  esac
}

ADIR="$(artifact_dir)"
LOG="$ADIR/portal-autofix-loop-${PORTAL}-${TODAY}.json"
attempt=0
last_rc=0
launches='[]'

echo "portal-autofix-loop: portal=$PORTAL max=$MAX date=$TODAY"

while [[ "$attempt" -lt "$MAX" ]]; do
  attempt=$((attempt + 1))
  echo "=== attempt $attempt/$MAX for $PORTAL ==="
  # Always take latest main before a re-attempt (post-fix merges land here).
  git fetch origin main >/dev/null 2>&1 || true
  if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
    cur="$(git rev-parse --abbrev-ref HEAD)"
    if [[ "$cur" == "main" ]]; then
      git pull --ff-only origin main >/dev/null 2>&1 || true
    fi
  fi

  set +e
  run_once "$PORTAL"
  last_rc=$?
  set -e

  launches="$(python3 -c 'import json,sys,datetime; L=json.loads(sys.argv[1]); L.append({"attempt":int(sys.argv[2]),"rc":int(sys.argv[3]),"at":datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}); print(json.dumps(L))' "$launches" "$attempt" "$last_rc")"

  if [[ "$last_rc" -eq 0 ]]; then
    echo "OK: $PORTAL attempt $attempt succeeded"
    python3 - "$LOG" "$PORTAL" "$TODAY" "$attempt" "$last_rc" "$launches" <<'PY'
import json,sys
path,portal,day,attempt,rc,launches=sys.argv[1:7]
out={"portal":portal,"date":day,"attempts":int(attempt),"finalRc":int(rc),"ok":True,"launches":json.loads(launches)}
open(path,"w",encoding="utf-8").write(json.dumps(out,indent=2)+"\n")
print(path)
PY
    exit 0
  fi

  echo "attempt $attempt failed rc=$last_rc — if code-fixable, fix+append-issue-fix+auto-merge, then this loop retries"
  # Give the caller a chance: if a merge just landed on main, next iteration picks it up.
  # Sleep briefly so parallel merge scripts can finish.
  sleep 2
done

python3 - "$LOG" "$PORTAL" "$TODAY" "$attempt" "$last_rc" "$launches" <<'PY'
import json,sys
path,portal,day,attempt,rc,launches=sys.argv[1:7]
out={"portal":portal,"date":day,"attempts":int(attempt),"finalRc":int(rc),"ok":False,"launches":json.loads(launches)}
open(path,"w",encoding="utf-8").write(json.dumps(out,indent=2)+"\n")
print(path)
PY

echo "ERROR: $PORTAL exhausted $MAX attempts (last rc=$last_rc)" >&2
exit "$last_rc"
