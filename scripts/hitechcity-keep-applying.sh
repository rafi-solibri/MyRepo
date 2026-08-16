#!/usr/bin/env bash
# Keep Hitech City campus applies running across agent chat turns.
# Owner solves captchas only; this loop restarts daily_apply and focuses owner tabs.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG="${HITECHCITY_KEEP_LOG:-/tmp/hitechcity-headed-daily-cont.log}"
WATCH="${HITECHCITY_KEEP_WATCH:-/tmp/hitechcity-keepalive.log}"
export HOME_LOCAL="${HOME_LOCAL:-1}"
export CHROME_HEADLESS="${CHROME_HEADLESS:-0}"
export ATS_CAPTCHA_WAIT_SEC="${ATS_CAPTCHA_WAIT_SEC:-180}"
export ATS_CAPTCHA_POLL_SEC="${ATS_CAPTCHA_POLL_SEC:-0.4}"
export ATS_OWNER_FORM_WAIT_SEC="${ATS_OWNER_FORM_WAIT_SEC:-120}"
export ATS_OWNER_FOCUS_EVERY_SEC="${ATS_OWNER_FOCUS_EVERY_SEC:-2}"
export HITECHCITY_PARALLEL_TABS="${HITECHCITY_PARALLEL_TABS:-10}"
if [[ -f /tmp/hitechcity-owner-asleep ]]; then
  export HITECHCITY_OWNER_ASLEEP=1
  export ATS_CAPTCHA_WAIT_SEC="${ATS_CAPTCHA_WAIT_SEC:-12}"
  export ATS_OWNER_FORM_WAIT_SEC="${ATS_OWNER_FORM_WAIT_SEC:-12}"
fi
export HITECHCITY_CAREERS_ONLY="${HITECHCITY_CAREERS_ONLY:-0}"
export HITECHCITY_SKIP_LINKEDIN="${HITECHCITY_SKIP_LINKEDIN:-0}"
export HITECHCITY_DISCOVERY="${HITECHCITY_DISCOVERY:-0}"
export HITECHCITY_SKIP_UHG="${HITECHCITY_SKIP_UHG:-1}"
export HITECHCITY_SKIP_COMPANIES="${HITECHCITY_SKIP_COMPANIES:-Optum,UnitedHealth Group,Intel,Solera,AMD}"
export HITECHCITY_MAX_PER_COMPANY="${HITECHCITY_MAX_PER_COMPANY:-6}"
export HITECHCITY_MAX_COMPANIES="${HITECHCITY_MAX_COMPANIES:-60}"
export HITECHCITY_MAX_EXT_WALLS="${HITECHCITY_MAX_EXT_WALLS:-3}"
export HITECHCITY_MAX_EXT_ATTEMPTS="${HITECHCITY_MAX_EXT_ATTEMPTS:-12}"
export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

if [[ -f /tmp/hitechcity-restart.env ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    case "$line" in
      NAUKRI_WORKDAY_PASSWORD=*|LINKEDIN_PASSWORD=*|LINKEDIN_EMAIL=*|LINKEDIN_AUTO_LOGIN=*|LINKEDIN_LOGIN_WAIT_SEC=*)
        eval "$line" ;;
    esac
  done < /tmp/hitechcity-restart.env
fi

echo "=== keepalive start $(date -u +%H:%M:%SZ) tabs=${HITECHCITY_PARALLEL_TABS} ===" | tee -a "$WATCH"

focus_owner_tabs() {
  python3 - <<'PY' 2>/dev/null || true
import json, urllib.request
try:
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=3))
except Exception:
    raise SystemExit(0)
best = None
best_score = -1
for t in tabs:
    if t.get("type") != "page":
        continue
    u = (t.get("url") or "").lower()
    score = 0
    if any(x in u for x in ("hcaptcha", "checkpoint", "/challenge")):
        score = 100
    elif "myworkdayjobs" in u and any(x in u for x in ("apply", "jobapplication", "userhome")):
        score = 95
    elif "icims.com" in u and any(x in u for x in ("login", "form", "questions", "eeo")):
        score = 90
    elif "captcha" in u:
        score = 92
    if score > best_score:
        best_score = score
        best = t
if best and best_score >= 80:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:9222/json/activate/{best['id']}", timeout=3)
        print(
            f"keepalive_focus score={best_score} {(best.get('title') or '')[:50]}",
            flush=True,
        )
    except Exception:
        pass
PY
}

ensure_chrome() {
  if curl -sf http://127.0.0.1:9222/json/version >/dev/null; then
    return 0
  fi
  echo "launching chrome cdp" | tee -a "$WATCH"
  bash "$ROOT/scripts/launch-chrome-cdp.sh" hitechcity >>"$WATCH" 2>&1 || true
  sleep 3
}

ensure_run() {
  if pgrep -f 'tools/hitechcity/daily_apply.py' >/dev/null 2>&1; then
    return 0
  fi
  echo "=== keepalive RESTART daily_apply $(date -u +%H:%M:%SZ) ===" | tee -a "$WATCH" "$LOG"
  nohup python3 "$ROOT/tools/hitechcity/daily_apply.py" >>"$LOG" 2>&1 &
  echo "spawned pid=$!" | tee -a "$WATCH"
}

ensure_chrome
while true; do
  ensure_run
  focus_owner_tabs >>"$WATCH" 2>&1 || true
  if tail -40 "$LOG" 2>/dev/null | grep -qiE 'ASK_OWNER|hcaptcha=wait|owner_focus=|CAPTCHA'; then
    focus_owner_tabs >>"$WATCH" 2>&1 || true
  fi
  sleep 8
done
