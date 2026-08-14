#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
tmp="$ROOT/automation-prompts/issues/notification.md"
cp "$tmp" /tmp/notification.md.bak
ISSUE_FIX_DATE=2099-01-01 ISSUE_FIX_SOURCE=cloud \
  bash scripts/append-issue-fix.sh notification "unit-test-issue" "unit-test-fix"
grep -q 'unit-test-issue' "$tmp"
grep -q '2099-01-01 (cloud)' "$tmp"
mv /tmp/notification.md.bak "$tmp"
bash scripts/assert-no-conflict-markers.sh automation-prompts/ISSUES_AND_FIXES.md >/dev/null
echo "OK: append-issue-fix + assert-no-conflict-markers"
