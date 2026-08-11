#!/usr/bin/env bash
# Run all home-local portal automations sequentially, then notification.
# Portals share CDP :9222 — must not run in parallel.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORTALS=(linkedin foundit cutshort naukri instahyre indeed)
LOG_DIR="${HOME_PORTAL_LOG_DIR:-$HOME/.cursor/portal-home-logs/_batch}"
mkdir -p "$LOG_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BATCH_LOG="$LOG_DIR/run-all-$STAMP.log"

exec > >(tee -a "$BATCH_LOG") 2>&1

echo "=== run-all-home-now @ $STAMP ==="
echo "log=$BATCH_LOG"

declare -a FAILED=()
for p in "${PORTALS[@]}"; do
  echo ""
  echo "######## START $p ########"
  set +e
  bash scripts/portal-home-daily.sh "$p"
  rc=$?
  set -e
  echo "######## END $p rc=$rc ########"
  if [[ "$rc" -ne 0 ]]; then
    FAILED+=("$p:$rc")
  fi
done

echo ""
echo "######## START notification ########"
set +e
bash scripts/notification-home-daily.sh
nrc=$?
set -e
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
