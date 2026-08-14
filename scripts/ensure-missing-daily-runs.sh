#!/usr/bin/env bash
# Detect which daily apply portals have no same-day cloud/home result and launch them.
#
# Prefer launching a fresh Cursor cloud agent (needs CURSOR_API_KEY). Otherwise
# re-exec the durable apply helper in this session (same path as post-fix re-run).
#
# Usage:
#   bash scripts/ensure-missing-daily-runs.sh
#   bash scripts/ensure-missing-daily-runs.sh --dry-run
#   bash scripts/ensure-missing-daily-runs.sh --portal linkedin,indeed
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DRY_RUN=0
PORTAL_ARG=""
TODAY="${ENSURE_DAILY_DATE:-$(TZ=Asia/Kolkata date +%Y-%m-%d)}"
APPLY_PORTALS=(linkedin foundit cutshort naukri instahyre indeed hitechcity)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --portal) PORTAL_ARG="${2:-}"; shift 2 ;;
    --help|-h)
      echo "Usage: bash scripts/ensure-missing-daily-runs.sh [--dry-run] [--portal a,b]"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

artifact_dir() {
  if [[ -d /opt/cursor/artifacts && -w /opt/cursor/artifacts ]]; then
    echo /opt/cursor/artifacts
  else
    mkdir -p "$ROOT/artifacts"
    echo "$ROOT/artifacts"
  fi
}

has_same_day_artifact() {
  local portal="$1"
  local adir
  adir="$(artifact_dir)"
  case "$portal" in
    linkedin)
      [[ -f "$adir/linkedin-apply-report.json" ]] || [[ -f "$ROOT/reports/$TODAY/linkedin-daily.md" ]] && return 0
      ;;
    foundit)
      [[ -f "$adir/foundit-apply-report.json" ]] || [[ -f "$ROOT/reports/$TODAY/foundit-daily.md" ]] && return 0
      ;;
    cutshort)
      [[ -f "$adir/cutshort-daily-apply.json" ]] || [[ -f "$ROOT/reports/$TODAY/cutshort-daily.md" ]] && return 0
      ;;
    naukri)
      [[ -f "$adir/naukri-daily-apply.json" ]] || [[ -f "$ROOT/reports/$TODAY/naukri-daily.md" ]] && return 0
      ;;
    instahyre)
      [[ -f "$adir/instahyre-daily-apply.json" ]] || [[ -f "$ROOT/reports/$TODAY/instahyre-daily.md" ]] && return 0
      ;;
    indeed)
      [[ -f "$adir/indeed-daily-run.json" ]] || [[ -f "$ROOT/reports/$TODAY/indeed-daily.md" ]] && return 0
      ;;
    hitechcity)
      [[ -f "$adir/hitechcity-daily.json" ]] || [[ -f "$ROOT/reports/$TODAY/hitechcity-daily.md" ]] && return 0
      ;;
  esac
  # Home published results branch (best-effort)
  if git -C "$ROOT" cat-file -e "origin/automation-results:automation-results/${portal}/${TODAY}.json" 2>/dev/null; then
    return 0
  fi
  return 1
}

missing=()
if [[ -n "$PORTAL_ARG" ]]; then
  IFS=',' read -r -a want <<< "$PORTAL_ARG" || true
  for p in "${want[@]}"; do
    p="$(printf '%s' "$p" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
    [[ -n "$p" ]] || continue
    missing+=("$p")
  done
else
  for p in "${APPLY_PORTALS[@]}"; do
    if has_same_day_artifact "$p"; then
      echo "OK: $p has same-day artifact/report for $TODAY"
    else
      echo "MISSING: $p has no same-day artifact/report for $TODAY"
      missing+=("$p")
    fi
  done
fi

if [[ ${#missing[@]} -eq 0 ]]; then
  echo "All apply portals have same-day coverage for $TODAY"
  exit 0
fi

echo "Will launch missing portals: ${missing[*]}"
if [[ "$DRY_RUN" -eq 1 ]]; then
  exit 0
fi

# Reuse post-fix re-run launcher (cloud agent or in-session exec).
# Cap still applies (POST_FIX_RERUN_MAX, default 5).
export POST_FIX_RERUN_REASON="${POST_FIX_RERUN_REASON:-ensure-missing-daily}"
for p in "${missing[@]}"; do
  echo "=== ensure-missing: $p ==="
  bash "$ROOT/scripts/rerun-daily-after-fix.sh" --portal "$p" \
    || echo "WARNING: ensure-missing launch failed for $p"
done
