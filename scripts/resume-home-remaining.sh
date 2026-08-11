#!/usr/bin/env bash
# Resume remaining portals after a partial batch (naukri → notification).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORTALS=(naukri instahyre indeed)
FAILED=()

restore_main() {
  cd "$ROOT"
  git checkout -f main >/dev/null 2>&1 || true
}

for p in "${PORTALS[@]}"; do
  echo "######## START $p ########"
  restore_main
  set +e
  bash "$ROOT/scripts/portal-home-daily.sh" "$p"
  rc=$?
  set -e
  bash "$ROOT/scripts/merge-open-fix-prs.sh" || true
  restore_main
  echo "######## END $p rc=$rc ########"
  [[ "$rc" -eq 0 ]] || FAILED+=("$p:$rc")
done

echo "######## START notification ########"
restore_main
set +e
bash "$ROOT/scripts/notification-home-daily.sh"
nrc=$?
set -e
bash "$ROOT/scripts/merge-open-fix-prs.sh" || true
restore_main
echo "######## END notification rc=$nrc ########"
[[ "$nrc" -eq 0 ]] || FAILED+=("notification:$nrc")

if [[ "${#FAILED[@]}" -gt 0 ]]; then
  echo "Completed with failures: ${FAILED[*]}"
  exit 1
fi
echo "Resume batch finished OK"
