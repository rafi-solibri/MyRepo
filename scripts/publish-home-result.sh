#!/usr/bin/env bash
# Publish today's home-local run JSON onto branch automation-results.
# Usage:
#   bash scripts/publish-home-result.sh <portal> [path-to-report.json]
set -euo pipefail

PORTAL="${1:-}"
case "$PORTAL" in
  linkedin|foundit|cutshort|naukri|instahyre|indeed|hitechcity) ;;
  *)
    echo "Usage: bash scripts/publish-home-result.sh <portal> [report.json]"
    exit 2
    ;;
esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

REPORT_TOOL="$ROOT/tools/home_run_report.js"
if [[ "$PORTAL" == "indeed" && -f "$ROOT/tools/indeed/daily_run_report.js" ]]; then
  REPORT_TOOL="$ROOT/tools/indeed/daily_run_report.js"
fi

REPORT_CANDIDATES=(
  "${2:-}"
  "${HOME_DAILY_REPORT:-}"
  "/opt/cursor/artifacts/${PORTAL}-daily-run.json"
  "$ROOT/artifacts/${PORTAL}-daily-run.json"
  "$HOME/.cursor/portal-home-logs/${PORTAL}/${PORTAL}-daily-run.json"
  "$HOME/.cursor/indeed-home-logs/indeed-daily-run.json"
)

REPORT=""
for c in "${REPORT_CANDIDATES[@]}"; do
  [[ -n "$c" && -f "$c" ]] || continue
  REPORT="$c"
  break
done

if [[ -z "$REPORT" ]]; then
  echo "WARNING: no ${PORTAL}-daily-run.json found — writing empty placeholder"
  mkdir -p "$ROOT/artifacts"
  REPORT="$ROOT/artifacts/${PORTAL}-daily-run.json"
  if [[ "$REPORT_TOOL" == *home_run_report.js ]]; then
    node "$REPORT_TOOL" empty --portal "$PORTAL" --reason "home_run_json_missing" --source home-local --out "$REPORT"
  else
    node "$REPORT_TOOL" empty --reason "home_run_json_missing" --source home-local --out "$REPORT"
  fi
fi

NORMALIZED="$ROOT/artifacts/${PORTAL}-daily-run.json"
mkdir -p "$(dirname "$NORMALIZED")"
if [[ "$REPORT_TOOL" == *home_run_report.js ]]; then
  node "$REPORT_TOOL" write --portal "$PORTAL" --in "$REPORT" --source home-local --out "$NORMALIZED"
else
  node "$REPORT_TOOL" write --in "$REPORT" --source home-local --out "$NORMALIZED"
fi
REPORT="$NORMALIZED"

DATE="$(node -e "const fs=require('fs'); const r=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); process.stdout.write(r.date || new Date().toISOString().slice(0,10));" "$REPORT")"
TODAY_UTC="$(date -u +%Y-%m-%d)"
# Never overwrite today's good result (or latest.json) with a prior-day stale report.
# Set HOME_PUBLISH_ALLOW_STALE=1 only for intentional historical backfills.
if [[ "$DATE" != "$TODAY_UTC" && "${HOME_PUBLISH_ALLOW_STALE:-}" != "1" ]]; then
  echo "ERROR: refusing to publish stale $PORTAL report date=$DATE (today UTC=$TODAY_UTC)."
  echo "Fix: write a same-day artifacts/${PORTAL}-daily-run.json, or set HOME_PUBLISH_ALLOW_STALE=1 to override."
  node -e "const fs=require('fs'); const r=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); console.log(JSON.stringify({date:r.date, counts:r.counts, blockerSummary:r.blockerSummary}, null, 2));" "$REPORT"
  exit 4
fi

BRANCH="${HOME_RESULTS_BRANCH:-automation-results}"
REMOTE="${HOME_RESULTS_REMOTE:-origin}"
WT="$(mktemp -d "${TMPDIR:-/tmp}/${PORTAL}-results-XXXXXX")"
cleanup() {
  git worktree remove --force "$WT" 2>/dev/null || true
  rm -rf "$WT"
}
trap cleanup EXIT

git fetch "$REMOTE" "$BRANCH" 2>/dev/null || git fetch "$REMOTE" main 2>/dev/null || true

if git show-ref --verify --quiet "refs/remotes/$REMOTE/$BRANCH"; then
  git worktree add --detach "$WT" "$REMOTE/$BRANCH"
  git -C "$WT" checkout -B "$BRANCH"
elif git show-ref --verify --quiet "refs/heads/$BRANCH"; then
  git worktree add "$WT" "$BRANCH"
else
  git worktree add --detach "$WT" HEAD
  git -C "$WT" checkout --orphan "$BRANCH"
  git -C "$WT" rm -rf . >/dev/null 2>&1 || true
fi

DEST_DIR="$WT/automation-results/$PORTAL"
mkdir -p "$DEST_DIR"
cp "$REPORT" "$DEST_DIR/$DATE.json"
cp "$REPORT" "$DEST_DIR/latest.json"

cat > "$WT/automation-results/README.md" <<'EOF'
# Automation results (machine-written)

Daily JSON summaries published by home/local runners for the Notification Job.

Per portal: `<portal>/YYYY-MM-DD.json` and `<portal>/latest.json`.

Schema counts: `applied`, `external`, `rejected`, `blocked`, `skipped`, `seen`.

```bash
bash scripts/fetch-home-result.sh <portal> --today
```
EOF

git -C "$WT" add "automation-results/$PORTAL/$DATE.json" \
  "automation-results/$PORTAL/latest.json" \
  automation-results/README.md

if git -C "$WT" diff --cached --quiet; then
  echo "No $PORTAL result changes to publish for $DATE"
  node -e "const fs=require('fs'); const r=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); console.log(JSON.stringify(r.counts,null,2));" "$REPORT"
  exit 0
fi

git -C "$WT" -c user.email="${GIT_AUTHOR_EMAIL:-portal-home@local}" \
  -c user.name="${GIT_AUTHOR_NAME:-Portal Home Daily}" \
  commit -m "$PORTAL home daily results $DATE"

if ! git -C "$WT" push -u "$REMOTE" "$BRANCH"; then
  echo "ERROR: failed to push $BRANCH — Notification Job will not see today's $PORTAL home counts."
  echo "Fix: ensure this machine can push to $REMOTE ($BRANCH), then re-run:"
  echo "  bash scripts/publish-home-result.sh $PORTAL $REPORT"
  exit 1
fi

echo "Published $PORTAL home results → $REMOTE/$BRANCH automation-results/$PORTAL/$DATE.json"
node -e "const fs=require('fs'); const r=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); console.log(JSON.stringify({date:r.date, counts:r.counts, blockerSummary:r.blockerSummary}, null, 2));" "$REPORT"
