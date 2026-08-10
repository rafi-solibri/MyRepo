#!/usr/bin/env bash
# Fetch the latest (or today's) Indeed home-local daily run JSON for the
# Notification Job. Prefers branch automation-results over cloud Cloudflare runs.
#
# Usage:
#   bash scripts/fetch-indeed-home-result.sh           # print latest JSON
#   bash scripts/fetch-indeed-home-result.sh --today    # require today's date
#   bash scripts/fetch-indeed-home-result.sh --path     # print local cache path only
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BRANCH="${INDEED_RESULTS_BRANCH:-automation-results}"
REMOTE="${INDEED_RESULTS_REMOTE:-origin}"
TODAY="$(date -u +%Y-%m-%d)"
WANT_TODAY=0
PATH_ONLY=0

for arg in "$@"; do
  case "$arg" in
    --today) WANT_TODAY=1 ;;
    --path) PATH_ONLY=1 ;;
    --help|-h)
      echo "Usage: bash scripts/fetch-indeed-home-result.sh [--today] [--path]"
      exit 0
      ;;
  esac
done

OUT_DIR="${INDEED_HOME_RESULT_CACHE:-/opt/cursor/artifacts}"
if [[ ! -d "$OUT_DIR" ]]; then
  OUT_DIR="$ROOT/artifacts"
fi
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/indeed-home-result.json"

set +e
git fetch "$REMOTE" "$BRANCH" 2>/dev/null
fetch_ok=$?
set -e

if [[ "$fetch_ok" -ne 0 ]]; then
  echo "ERROR: could not fetch $REMOTE/$BRANCH (Indeed home results not published yet?)" >&2
  echo '{"portal":"indeed","source":"home-local","ok":false,"blockerSummary":"indeed_home_results_branch_missing","counts":{"applied":0,"external":0,"rejected":0,"blocked":0,"skipped":0,"seen":0}}' > "$OUT"
  if [[ "$PATH_ONLY" -eq 1 ]]; then
    echo "$OUT"
  else
    cat "$OUT"
  fi
  exit 2
fi

TARGET_BLOB="automation-results/indeed/latest.json"
if [[ "$WANT_TODAY" -eq 1 ]]; then
  TARGET_BLOB="automation-results/indeed/$TODAY.json"
fi

set +e
git show "$REMOTE/$BRANCH:$TARGET_BLOB" > "$OUT" 2>/dev/null
show_ok=$?
set -e

if [[ "$show_ok" -ne 0 && "$WANT_TODAY" -eq 1 ]]; then
  # Fall back to latest but annotate missing today.
  if git show "$REMOTE/$BRANCH:automation-results/indeed/latest.json" > "$OUT" 2>/dev/null; then
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
    echo "ERROR: no Indeed home result on $REMOTE/$BRANCH" >&2
    echo '{"portal":"indeed","source":"home-local","ok":false,"blockerSummary":"indeed_home_result_missing","counts":{"applied":0,"external":0,"rejected":0,"blocked":0,"skipped":0,"seen":0}}' > "$OUT"
    if [[ "$PATH_ONLY" -eq 1 ]]; then echo "$OUT"; else cat "$OUT"; fi
    exit 3
  fi
elif [[ "$show_ok" -ne 0 ]]; then
  echo "ERROR: missing $TARGET_BLOB on $REMOTE/$BRANCH" >&2
  echo '{"portal":"indeed","source":"home-local","ok":false,"blockerSummary":"indeed_home_result_missing","counts":{"applied":0,"external":0,"rejected":0,"blocked":0,"skipped":0,"seen":0}}' > "$OUT"
  if [[ "$PATH_ONLY" -eq 1 ]]; then echo "$OUT"; else cat "$OUT"; fi
  exit 3
fi

# Mark same-day when possible.
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
