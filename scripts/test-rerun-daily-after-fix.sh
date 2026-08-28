#!/usr/bin/env bash
# Smoke tests for post-fix portal detection (no network, no apply exec).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT/scripts/rerun-daily-after-fix.sh"
fail=0

expect() {
  local got="$1" want="$2" label="$3"
  if [[ "$got" != "$want" ]]; then
    echo "FAIL $label"
    echo "  want: $(printf %q "$want")"
    echo "  got:  $(printf %q "$got")"
    fail=1
  else
    echo "OK   $label"
  fi
}

got="$(bash "$SCRIPT" --detect-from-title "fix(naukri): Workday consent")"
expect "$got" "naukri" "title naukri"

got="$(bash "$SCRIPT" --detect-from-title "fix(hitechcity): recover Oracle scrapers")"
expect "$got" "hitechcity" "title hitechcity"

got="$(bash "$SCRIPT" --detect-from-title "fix(notification): retry Resend TLS")"
expect "$got" "notification" "title notification"

got="$(bash "$SCRIPT" --detect-from-title "docs(linkedin): WARP auto-login")"
expect "$got" "linkedin" "title docs(linkedin)"

got="$(bash "$SCRIPT" --detect-from-files tools/naukri/workday_apply.js automation-prompts/issues/naukri.md)"
expect "$got" "naukri" "files naukri helper"

got="$(bash "$SCRIPT" --detect-from-files tools/chrome_session.js)"
want="$(printf '%s\n' linkedin foundit cutshort naukri instahyre indeed hirist hitechcity)"
expect "$got" "$want" "shared chrome_session → all apply portals"

got="$(bash "$SCRIPT" --detect-from-files tools/ats/complete.py)"
expect "$got" "$want" "shared tools/ats → all apply portals"

got="$(bash "$SCRIPT" --detect-from-files scripts/rerun-daily-after-fix.sh automation-prompts/AUTO_FIX.md)"
expect "$got" "" "rerun/AUTO_FIX docs do not trigger apply jobs"

got="$(bash "$SCRIPT" --detect-from-files tools/hotels/automation.py scripts/send-job-status-email.mjs)"
want="$(printf '%s\n' notification hotels)"
expect "$got" "$want" "hotels + notification files"

got="$(bash "$SCRIPT" --detect-from-files automation-prompts/01-linkedin.md automation-prompts/02-foundit.md)"
expect "$got" "" "prompt-only edits do not fan out to apply jobs"

got="$(bash "$SCRIPT" --dry-run --portal naukri)"
if echo "$got" | grep -q "DRY-RUN would re-run naukri"; then
  echo "OK   dry-run naukri"
else
  echo "FAIL dry-run naukri"
  echo "$got"
  fail=1
fi

# Explicit --portal must not also pick up tip-of-main portals (e.g. fix(linkedin) HEAD).
got="$(bash "$SCRIPT" --dry-run --portal foundit)"
if echo "$got" | grep -q "portals=foundit " || echo "$got" | grep -q "portals=foundit$"; then
  if echo "$got" | grep -qE "portals=.*linkedin|-------- linkedin --------"; then
    echo "FAIL dry-run foundit must be exclusive (got linkedin too)"
    echo "$got"
    fail=1
  else
    echo "OK   dry-run foundit exclusive"
  fi
else
  echo "FAIL dry-run foundit portal line"
  echo "$got"
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  echo "test-rerun-daily-after-fix: FAILED"
  exit 1
fi
echo "test-rerun-daily-after-fix: PASSED"
exit 0
