#!/usr/bin/env bash
# Free career-portal apply: headed Chrome, you click hCaptcha, the helper continues.
#
# No CapSolver / 2Captcha key required. Run this on your home PC (or any
# machine where you can see the Chrome window).
#
# Usage:
#   bash scripts/home-headed-careers-apply.sh
#   ATS_CAPTCHA_WAIT_SEC=300 bash scripts/home-headed-careers-apply.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# shellcheck disable=SC1091
source "$ROOT/scripts/load-job-secrets.sh" || true

export HOME_LOCAL="${HOME_LOCAL:-1}"
export CHROME_HEADLESS=0
export HITECHCITY_CAREERS_ONLY=1
export HITECHCITY_SKIP_LINKEDIN=1
export LINKEDIN_SKIP_WARP=1
export LINKEDIN_AUTO_LOGIN=0
export CDP_LIVE_LOGIN_CHECK=0
export ATS_CAPTCHA_WAIT_SEC="${ATS_CAPTCHA_WAIT_SEC:-300}"
# Every headed/daily run: parallel multi-tab careers (owner clicks captchas only).
export HITECHCITY_PARALLEL_TABS="${HITECHCITY_PARALLEL_TABS:-10}"
export HITECHCITY_MAX_PER_COMPANY="${HITECHCITY_MAX_PER_COMPANY:-6}"
export HITECHCITY_MAX_COMPANIES="${HITECHCITY_MAX_COMPANIES:-60}"
export HITECHCITY_MAX_EXT_WALLS="${HITECHCITY_MAX_EXT_WALLS:-3}"
export HITECHCITY_MAX_EXT_ATTEMPTS="${HITECHCITY_MAX_EXT_ATTEMPTS:-12}"
export ATS_CAPTCHA_POLL_SEC="${ATS_CAPTCHA_POLL_SEC:-0.4}"
export ATS_OWNER_FOCUS_EVERY_SEC="${ATS_OWNER_FOCUS_EVERY_SEC:-2}"

if [[ -z "${DISPLAY:-}" && "${OS:-}" != "Windows_NT" && -z "${MSYSTEM:-}" && "$(uname -s 2>/dev/null)" != MINGW* ]]; then
  echo "WARNING: no DISPLAY — headed Chrome may not be visible." >&2
  echo "Run this on your home PC (not a headless cloud VM)." >&2
fi

echo "Headed career-portal apply (free captcha path)."
echo "Parallel tabs: ${HITECHCITY_PARALLEL_TABS} (owner clicks captcha; other tabs keep applying)."
echo "Captcha/ASK_OWNER tab is re-focused every ${ATS_OWNER_FOCUS_EVERY_SEC}s until you finish."
echo "When Hyland/iCIMS shows hCaptcha, click it in the Chrome window."
echo "Wait budget: ${ATS_CAPTCHA_WAIT_SEC}s per captcha."
echo

bash "$ROOT/scripts/preflight-portal-run.sh" hitechcity
bash "$ROOT/scripts/launch-chrome-cdp.sh" hitechcity
PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}" python3 "$ROOT/tools/hitechcity/daily_apply.py"
