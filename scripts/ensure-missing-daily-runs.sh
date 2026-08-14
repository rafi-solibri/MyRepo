#!/usr/bin/env bash
# Detect which daily apply portals have no usable same-day result and launch them.
#
# Prefer launching a fresh Cursor cloud agent (needs CURSOR_API_KEY). Otherwise
# re-exec the durable apply helper in this session (same path as post-fix re-run).
#
# A report that only records login_required / ok:false / 0-seen failure does NOT
# count as coverage — those portals are still launched.
#
# Usage:
#   bash scripts/ensure-missing-daily-runs.sh
#   bash scripts/ensure-missing-daily-runs.sh --dry-run
#   bash scripts/ensure-missing-daily-runs.sh --portal linkedin,indeed
#   bash scripts/ensure-missing-daily-runs.sh --force-all
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DRY_RUN=0
FORCE_ALL=0
PORTAL_ARG=""
TODAY="${ENSURE_DAILY_DATE:-$(TZ=Asia/Kolkata date +%Y-%m-%d)}"
APPLY_PORTALS=(linkedin foundit cutshort naukri instahyre indeed hitechcity)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --force-all) FORCE_ALL=1; shift ;;
    --portal) PORTAL_ARG="${2:-}"; shift 2 ;;
    --help|-h)
      echo "Usage: bash scripts/ensure-missing-daily-runs.sh [--dry-run] [--force-all] [--portal a,b]"
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

# Returns 0 when the report proves a usable same-day apply attempt (not just a login wall).
report_is_usable() {
  local portal="$1"
  local f="$2"
  [[ -f "$f" ]] || return 1
  case "$f" in
    *.md)
      if grep -qiE 'login_required|did not fire|anonymous session|0 seen|linkedin_login|indeed_login_required' "$f" \
        && ! grep -qiE 'Applied: \*\*[1-9]|applied\": [1-9]|\+ *[1-9]+ *applies|First pass Applied|Qualifying:|Scanned:' "$f"; then
        return 1
      fi
      if grep -qiE 'Applied: \*\*[1-9]|\+ *[1-9]|intentionalApplies|appliedCount|Qualifying:|Scanned:|scanned=' "$f"; then
        return 0
      fi
      return 1
      ;;
  esac
  REPORT_PORTAL="$portal" python3 - "$f" <<'PY'
import json, os, sys
path = sys.argv[1]
try:
    d = json.load(open(path, encoding="utf-8"))
except Exception:
    raise SystemExit(1)
if isinstance(d, list):
    d = d[0] if d and isinstance(d[0], dict) else {}
if not isinstance(d, dict):
    raise SystemExit(1)

def blocked_login(obj):
    blob = json.dumps(obj).lower()
    return any(
        x in blob
        for x in (
            "login_required",
            "indeed_login_required",
            "linkedin_login_required",
            "still_blocked_after_uc",
            "indeed_cloudflare_still_blocked",
        )
    )

def as_int(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def applied_from(obj):
    if obj is None:
        return 0
    if isinstance(obj, list):
        return len(obj)
    return as_int(obj, 0)


counts = d.get("counts") or {}
if not isinstance(counts, dict):
    counts = {}
applied = applied_from(counts.get("applied"))
seen = as_int(counts.get("seen") or 0)
# list-shaped top-level applied / submitted (Instahyre / Naukri / LinkedIn)
applied = max(applied, applied_from(d.get("applied")), applied_from(d.get("submitted")))
ok = d.get("ok")
if isinstance(d.get("ucApply"), dict):
    uc = d["ucApply"]
    counts = uc.get("counts") or counts
    if not isinstance(counts, dict):
        counts = {}
    applied = max(applied, applied_from(counts.get("applied")))
    seen = as_int(counts.get("seen") or seen)
    if uc.get("ok") is False and applied == 0 and seen == 0:
        raise SystemExit(1)
if isinstance(d.get("summary"), dict):
    applied = max(applied, applied_from(d["summary"].get("applied")))
# HitechCity orchestrator: totals + nested phases (no top-level counts/ok historically)
if isinstance(d.get("totals"), dict):
    applied = max(applied, applied_from(d["totals"].get("applied")))
    seen = max(seen, as_int(d["totals"].get("skipped") or 0), as_int(d["totals"].get("blocked") or 0))
for phase in ("linkedin", "careers", "boards"):
    part = d.get(phase)
    if isinstance(part, dict):
        applied = max(applied, applied_from(part.get("applied")))

if blocked_login(d) and applied == 0:
    raise SystemExit(1)
if ok is False and applied == 0 and seen == 0:
    raise SystemExit(1)
if applied > 0 or seen > 0 or ok is True:
    raise SystemExit(0)
# Completed orchestrator run (finishedAt) counts even when inventory yielded 0 applies
if d.get("finishedAt") and isinstance(d.get("totals"), dict):
    raise SystemExit(0)
if d.get("loggedIn") and (d.get("applied") is not None or d.get("submitted") is not None):
    raise SystemExit(0)
raise SystemExit(1)
PY
}

has_usable_same_day() {
  local portal="$1"
  local adir f
  adir="$(artifact_dir)"
  local -a candidates=()
  case "$portal" in
    linkedin) candidates=("$adir/linkedin-apply-report.json" "$adir/apply-report.json" "$ROOT/reports/$TODAY/linkedin-daily.md") ;;
    foundit) candidates=("$adir/foundit-apply-report.json" "$ROOT/reports/$TODAY/foundit-daily.md") ;;
    cutshort) candidates=("$adir/cutshort-daily-run.json" "$adir/cutshort-daily-apply.json" "$ROOT/reports/$TODAY/cutshort-daily.md") ;;
    naukri) candidates=("$adir/naukri-daily-apply.json" "$ROOT/reports/$TODAY/naukri-daily.md") ;;
    instahyre) candidates=("$adir/instahyre-apply-report.json" "$adir/instahyre-daily-apply.json" "$ROOT/reports/$TODAY/instahyre-daily.md") ;;
    indeed) candidates=("$adir/indeed-daily-run.json" "$adir/indeed-apply-report.json" "$ROOT/reports/$TODAY/indeed-daily.md") ;;
    hitechcity) candidates=("$adir/hitechcity-daily.json" "$ROOT/reports/$TODAY/hitechcity-daily.md") ;;
  esac
  for f in "${candidates[@]}"; do
    if report_is_usable "$portal" "$f"; then
      return 0
    fi
  done
  if git -C "$ROOT" cat-file -e "origin/automation-results:automation-results/${portal}/${TODAY}.json" 2>/dev/null; then
    local tmp
    tmp="$(mktemp)"
    git -C "$ROOT" show "origin/automation-results:automation-results/${portal}/${TODAY}.json" >"$tmp" 2>/dev/null || true
    if report_is_usable "$portal" "$tmp"; then
      rm -f "$tmp"
      return 0
    fi
    rm -f "$tmp"
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
elif [[ "$FORCE_ALL" -eq 1 ]]; then
  missing=("${APPLY_PORTALS[@]}")
else
  for p in "${APPLY_PORTALS[@]}"; do
    if has_usable_same_day "$p"; then
      echo "OK: $p has usable same-day coverage for $TODAY"
    else
      echo "MISSING/FAILED: $p needs a same-day apply run for $TODAY"
      missing+=("$p")
    fi
  done
fi

if [[ ${#missing[@]} -eq 0 ]]; then
  echo "All apply portals have usable same-day coverage for $TODAY"
  exit 0
fi

echo "Will launch portals: ${missing[*]}"
if [[ "$DRY_RUN" -eq 1 ]]; then
  exit 0
fi

# Restore seeded sessions before launching (helps Indeed/LinkedIn when dest was wiped).
if [[ -x "$ROOT/scripts/restore-portal-sessions.sh" ]]; then
  FORCE_RESTORE_SESSIONS="${FORCE_RESTORE_SESSIONS:-0}" bash "$ROOT/scripts/restore-portal-sessions.sh" \
    || echo "WARNING: restore-portal-sessions failed (continuing)"
fi

export POST_FIX_RERUN_REASON="${POST_FIX_RERUN_REASON:-ensure-missing-daily}"
for p in "${missing[@]}"; do
  echo "=== ensure-missing: $p ==="
  bash "$ROOT/scripts/rerun-daily-after-fix.sh" --portal "$p" \
    || echo "WARNING: ensure-missing launch failed for $p"
done
