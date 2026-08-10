#!/usr/bin/env bash
# Publish today's Indeed home-local run JSON onto branch automation-results
# so the 11 AM Notification Job can include applied/rejected/blocked/skipped.
#
# Usage (usually called from scripts/indeed-home-daily.sh):
#   bash scripts/publish-indeed-home-result.sh [path-to-report.json]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

REPORT_CANDIDATES=(
  "${1:-}"
  "${INDEED_DAILY_REPORT:-}"
  "/opt/cursor/artifacts/indeed-daily-run.json"
  "$ROOT/artifacts/indeed-daily-run.json"
  "$HOME/.cursor/indeed-home-logs/indeed-daily-run.json"
)

REPORT=""
for c in "${REPORT_CANDIDATES[@]}"; do
  [[ -n "$c" && -f "$c" ]] || continue
  REPORT="$c"
  break
done

if [[ -z "$REPORT" ]]; then
  echo "WARNING: no indeed-daily-run.json found — writing empty placeholder"
  mkdir -p "$ROOT/artifacts"
  REPORT="$ROOT/artifacts/indeed-daily-run.json"
  node "$ROOT/tools/indeed/daily_run_report.js" empty \
    --reason "home_run_json_missing" \
    --source home-local \
    --out "$REPORT"
fi

# Normalize schema (applied/rejected/blocked/skipped/…).
NORMALIZED="$ROOT/artifacts/indeed-daily-run.json"
mkdir -p "$(dirname "$NORMALIZED")"
node "$ROOT/tools/indeed/daily_run_report.js" write \
  --in "$REPORT" \
  --source home-local \
  --out "$NORMALIZED"
REPORT="$NORMALIZED"

DATE="$(node -e "const fs=require('fs'); const r=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); process.stdout.write(r.date || new Date().toISOString().slice(0,10));" "$REPORT")"
BRANCH="${INDEED_RESULTS_BRANCH:-automation-results}"
REMOTE="${INDEED_RESULTS_REMOTE:-origin}"
WT="$(mktemp -d "${TMPDIR:-/tmp}/indeed-results-XXXXXX")"
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
  # First publish: orphan branch so daily result commits stay off main history noise.
  git worktree add --detach "$WT" HEAD
  git -C "$WT" checkout --orphan "$BRANCH"
  git -C "$WT" rm -rf . >/dev/null 2>&1 || true
fi

DEST_DIR="$WT/automation-results/indeed"
mkdir -p "$DEST_DIR"
cp "$REPORT" "$DEST_DIR/$DATE.json"
cp "$REPORT" "$DEST_DIR/latest.json"

cat > "$WT/automation-results/README.md" <<'EOF'
# Automation results (machine-written)

Daily JSON summaries published by home/local runners for the Notification Job.

## Indeed home daily

- `indeed/YYYY-MM-DD.json` — dated snapshot
- `indeed/latest.json` — most recent home run

Schema counts: `applied`, `external`, `rejected`, `blocked`, `skipped`, `seen`.

Fetch from the Notification Job:

```bash
bash scripts/fetch-indeed-home-result.sh
```
EOF

git -C "$WT" add automation-results/indeed/"$DATE.json" \
  automation-results/indeed/latest.json \
  automation-results/README.md

if git -C "$WT" diff --cached --quiet; then
  echo "No Indeed result changes to publish for $DATE"
  node -e "const fs=require('fs'); const r=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); console.log(JSON.stringify(r.counts,null,2));" "$REPORT"
  exit 0
fi

git -C "$WT" -c user.email="${GIT_AUTHOR_EMAIL:-indeed-home@local}" \
  -c user.name="${GIT_AUTHOR_NAME:-Indeed Home Daily}" \
  commit -m "Indeed home daily results $DATE"

if ! git -C "$WT" push -u "$REMOTE" "$BRANCH"; then
  echo "ERROR: failed to push $BRANCH — Notification Job will not see today's Indeed home counts."
  echo "Fix: ensure this machine can push to $REMOTE ($BRANCH), then re-run:"
  echo "  bash scripts/publish-indeed-home-result.sh $REPORT"
  exit 1
fi

echo "Published Indeed home results → $REMOTE/$BRANCH automation-results/indeed/$DATE.json"
node -e "const fs=require('fs'); const r=JSON.parse(fs.readFileSync(process.argv[1],'utf8')); console.log(JSON.stringify({date:r.date, counts:r.counts, blockerSummary:r.blockerSummary}, null, 2));" "$REPORT"