#!/usr/bin/env bash
# Run all home-local portal automations sequentially, then notification.
# Portals share CDP :9222 — must not run in parallel.
# Agents may checkout fix branches; restore main between portals.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORTALS=(linkedin foundit cutshort naukri instahyre indeed hirist hitechcity)
LOG_DIR="${HOME_PORTAL_LOG_DIR:-$HOME/.cursor/portal-home-logs/_batch}"
mkdir -p "$LOG_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BATCH_LOG="$LOG_DIR/run-all-$STAMP.log"

exec > >(tee -a "$BATCH_LOG") 2>&1

echo "=== run-all-home-now @ $STAMP ==="
echo "root=$ROOT log=$BATCH_LOG"

restore_main() {
  cd "$ROOT" || return 1
  # Detach from agent fix-branches so scripts/ stay available; pick up merges.
  if git rev-parse --git-dir >/dev/null 2>&1; then
    git fetch origin main >/dev/null 2>&1 || true
    git checkout -f main >/dev/null 2>&1 || git checkout -f master >/dev/null 2>&1 || true
    git pull --ff-only origin main >/dev/null 2>&1 || true
  fi
  if [[ ! -f "$ROOT/scripts/portal-home-daily.sh" ]]; then
    echo "ERROR: missing $ROOT/scripts/portal-home-daily.sh after checkout"
    return 1
  fi
}

declare -a FAILED=()
for p in "${PORTALS[@]}"; do
  echo ""
  echo "######## START $p ########"
  restore_main || {
    FAILED+=("$p:restore")
    echo "######## END $p rc=restore ########"
    continue
  }
  set +e
  bash "$ROOT/scripts/portal-home-daily.sh" "$p"
  rc=$?
  set -e
  # Safety net: merge any leftover open fix PRs the agent pushed but did not merge.
  bash "$ROOT/scripts/merge-open-fix-prs.sh" || true
  restore_main || true
  echo "######## END $p rc=$rc ########"
  if [[ "$rc" -ne 0 ]]; then
    FAILED+=("$p:$rc")
  fi
done

echo ""
echo "######## START notification ########"
restore_main || true
set +e
bash "$ROOT/scripts/notification-home-daily.sh"
nrc=$?
set -e
restore_main || true
echo "######## END notification rc=$nrc ########"
if [[ "$nrc" -ne 0 ]]; then
  FAILED+=("notification:$nrc")
fi

echo ""
if [[ "${#FAILED[@]}" -gt 0 ]]; then
  echo "Completed with failures: ${FAILED[*]}"
  echo "Batch log: $BATCH_LOG"
  exit 1
fi

echo "All home automations finished OK"
echo "Batch log: $BATCH_LOG"
exit 0
