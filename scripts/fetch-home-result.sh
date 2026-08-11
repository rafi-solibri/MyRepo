#!/usr/bin/env bash
# Fetch home-local daily run JSON for Notification Job.
# Usage:
#   bash scripts/fetch-home-result.sh <portal> [--today] [--path]
set -euo pipefail

PORTAL="${1:-}"
case "$PORTAL" in
  linkedin|foundit|cutshort|naukri|instahyre|indeed) ;;
  *)
    echo "Usage: bash scripts/fetch-home-result.sh <portal> [--today] [--path]"
    exit 2
    ;;
esac
shift || true

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BRANCH="${HOME_RESULTS_BRANCH:-automation-results}"
REMOTE="${HOME_RESULTS_REMOTE:-origin}"
TODAY="$(date -u +%Y-%m-%d)"
WANT_TODAY=0
PATH_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --today) WANT_TODAY=1 ;;
    --path) PATH_ONLY=1 ;;
    --help|-h)
      echo "Usage: bash scripts/fetch-home-result.sh <portal> [--today] [--path]"
      exit 0
      ;;
  esac
done

OUT_DIR="${HOME_RESULT_CACHE:-/opt/cursor/artifacts}"
if [[ ! -d "$OUT_DIR" ]]; then
  OUT_DIR="$ROOT/artifacts"
fi
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/${PORTAL}-home-result.json"

empty_json() {
  local reason="$1"
  echo "{\"portal\":\"$PORTAL\",\"source\":\"home-local\",\"ok\":false,\"blockerSummary\":\"$reason\",\"counts\":{\"applied\":0,\"external\":0,\"rejected\":0,\"blocked\":0,\"skipped\":0,\"seen\":0}}"
}

set +e
git fetch "$REMOTE" "$BRANCH" 2>/dev/null
fetch_ok=$?
set -e

if [[ "$fetch_ok" -ne 0 ]]; then
  echo "ERROR: could not fetch $REMOTE/$BRANCH (${PORTAL} home results not published yet?)" >&2
  empty_json "${PORTAL}_home_results_branch_missing" > "$OUT"
  if [[ "$PATH_ONLY" -eq 1 ]]; then echo "$OUT"; else cat "$OUT"; fi
  exit 2
fi

TARGET_BLOB="automation-results/$PORTAL/latest.json"
if [[ "$WANT_TODAY" -eq 1 ]]; then
  TARGET_BLOB="automation-results/$PORTAL/$TODAY.json"
fi

set +e
git show "$REMOTE/$BRANCH:$TARGET_BLOB" > "$OUT" 2>/dev/null
show_ok=$?
set -e

if [[ "$show_ok" -ne 0 && "$WANT_TODAY" -eq 1 ]]; then
  if git show "$REMOTE/$BRANCH:automation-results/$PORTAL/latest.json" > "$OUT" 2>/dev/null; then
    node -e "
      const fs=require('fs');
      const p='$OUT';
      const r=JSON.parse(fs.readFileSync(p,'utf8'));
      r.notes = Array.isArray(r.notes) ? r.notes : [];
      r.notes.push('no_same_day_home_result_for_$TODAY');
      r.sameDay = false;
      r.requestedDate = '$TODAY';
      fs.writeFileSync(p, JSON.stringify(r, null, 2) + '\n');
    "
  else
    echo "ERROR: no $PORTAL home result on $REMOTE/$BRANCH" >&2
    empty_json "${PORTAL}_home_result_missing" > "$OUT"
    if [[ "$PATH_ONLY" -eq 1 ]]; then echo "$OUT"; else cat "$OUT"; fi
    exit 3
  fi
elif [[ "$show_ok" -ne 0 ]]; then
  echo "ERROR: missing $TARGET_BLOB on $REMOTE/$BRANCH" >&2
  empty_json "${PORTAL}_home_result_missing" > "$OUT"
  if [[ "$PATH_ONLY" -eq 1 ]]; then echo "$OUT"; else cat "$OUT"; fi
  exit 3
fi

node -e "
  const fs=require('fs');
  const p='$OUT';
  const r=JSON.parse(fs.readFileSync(p,'utf8'));
  r.sameDay = r.date === '$TODAY';
  r.fetchedAt = new Date().toISOString();
  fs.writeFileSync(p, JSON.stringify(r, null, 2) + '\n');
"

if [[ "$PATH_ONLY" -eq 1 ]]; then
  echo "$OUT"
else
  cat "$OUT"
fi
