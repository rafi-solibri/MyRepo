#!/usr/bin/env bash
# Open all portal login tabs on Windows system Chrome CDP and wait for sessions.
# Usage: bash scripts/home-headed-login-all.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export CHROME_CDP_MODE="${CHROME_CDP_MODE:-system}"
export CHROME_HEADLESS=0
export CDP_LIVE_LOGIN_CHECK=0

echo "Starting system Chrome with CDP (closes normal Chrome briefly)…"
bash scripts/launch-chrome-cdp.sh linkedin

open_tab() {
  local url="$1"
  curl -fsS -X PUT "http://127.0.0.1:9222/json/new?$(python -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$url" 2>/dev/null || echo "$url")" >/dev/null 2>&1 \
    || curl -fsS "http://127.0.0.1:9222/json/new?$url" >/dev/null 2>&1 \
    || true
}

echo "Opening portal login tabs — sign in to each in the Chrome window…"
open_tab "https://www.linkedin.com/feed/"
open_tab "https://www.naukri.com/mnjuser/homepage"
open_tab "https://www.foundit.in/profile"
open_tab "https://cutshort.io/profile/candidate-dashboard"
open_tab "https://www.instahyre.com/candidate/opportunities/"
open_tab "https://www.indeed.com/"

echo
echo "Sign in where needed (LinkedIn / Naukri / Foundit / Cutshort / Instahyre / Indeed)."
echo "Leave Chrome open. Waiting up to 20 minutes for LinkedIn li_at (strongest signal)…"
export NODE_PATH="$ROOT/tools/node_modules${NODE_PATH:+:$NODE_PATH}"
set +e
node "$ROOT/tools/linkedin/wait_for_cdp_login.js" --wait 1200
rc=$?
set -e

echo
echo "Quick portal cookie/live status:"
node -e "
const {hasAuth, PROFILES, useSystemChromeProfile}=require('./tools/chrome_session');
console.log({system: useSystemChromeProfile(), profile: PROFILES.linkedin});
for (const p of ['linkedin','naukri','foundit','cutshort','instahyre','indeed']) {
  console.log(p, hasAuth(p) ? 'cookie-name-ok' : 'cookie-name-missing-or-locked');
}
"

if [[ "$rc" -eq 0 ]]; then
  echo "OK: LinkedIn session live. Other portals: confirm each tab shows your dashboard, then evening runs can reuse this Chrome profile."
else
  echo "WARN: LinkedIn still not logged in after wait. Sign in on the LinkedIn tab and re-run: bash scripts/home-headed-login-all.sh" >&2
fi
exit "$rc"
