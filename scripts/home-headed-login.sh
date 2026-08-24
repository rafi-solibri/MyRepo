#!/usr/bin/env bash
# One-time headed login into a home CDP profile (Windows Chrome ABE workaround).
# Cookie sync from Desktop Default cannot decrypt v20 App-Bound cookies in a
# different --user-data-dir. Sign in once here; later daily runs reuse the profile.
#
# Usage:
#   bash scripts/home-headed-login.sh naukri
#   bash scripts/home-headed-login.sh linkedin
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORTAL="${1:-}"
# hitechcity reuses the LinkedIn CDP session for campus applies + referrals.
case "$PORTAL" in
  linkedin|hitechcity|foundit|cutshort|naukri|instahyre|indeed|hirist) ;;
  *)
    echo "Usage: bash scripts/home-headed-login.sh <linkedin|hitechcity|foundit|cutshort|naukri|instahyre|indeed|hirist>" >&2
    exit 2
    ;;
esac

LOGIN_URL="$(
  case "$PORTAL" in
    linkedin|hitechcity) echo "https://www.linkedin.com/login" ;;
    foundit) echo "https://www.foundit.in/rio/login" ;;
    cutshort) echo "https://cutshort.io/login" ;;
    naukri) echo "https://www.naukri.com/nlogin/login" ;;
    instahyre) echo "https://www.instahyre.com/login/" ;;
    indeed) echo "https://secure.indeed.com/auth" ;;
    hirist) echo "https://www.hirist.tech/login" ;;
  esac
)"

export CHROME_HEADLESS=0
# Launch may probe live login; do not abort here — this script waits for the owner next.
export CDP_REQUIRE_LIVE_LOGIN=0
export PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" && -x /c/Python314/python ]]; then
  export PYTHON_BIN=/c/Python314/python
fi

echo "Launching headed Chrome CDP for $PORTAL…"
echo "Sign in in the Chrome window that opens ($LOGIN_URL) if needed."
# Windows system Chrome profile: sessions already in Default — verify without blocking Enter.
SYSTEM_MODE=0
if node -e "const {useSystemChromeProfile}=require('./tools/chrome_session'); process.exit(useSystemChromeProfile()?0:1)" 2>/dev/null; then
  SYSTEM_MODE=1
  echo "NOTE: using system Chrome User Data (ABE-safe). If you are already logged in in normal Chrome, this should just work."
fi
bash scripts/launch-chrome-cdp.sh "$PORTAL"

# Open login tab via CDP HTTP
if command -v curl >/dev/null 2>&1; then
  curl -s -X PUT "http://127.0.0.1:9222/json/new?$(python -c "import urllib.parse; print(urllib.parse.quote('''$LOGIN_URL''', safe=''))" 2>/dev/null || echo "$LOGIN_URL")" >/dev/null 2>&1 \
    || curl -s "http://127.0.0.1:9222/json/new?$LOGIN_URL" >/dev/null 2>&1 \
    || true
fi

if [[ "$SYSTEM_MODE" -eq 0 ]]; then
  echo
  read -r -p "Press Enter after you have finished signing in…"
fi

# LinkedIn / HitechCity / Cutshort: prefer dedicated live CDP waiter (ABE-aware messaging).
if [[ "$PORTAL" == "linkedin" || "$PORTAL" == "hitechcity" ]] && [[ -f "$ROOT/tools/linkedin/wait_for_cdp_login.js" ]]; then
  export NODE_PATH="$ROOT/tools/node_modules${NODE_PATH:+:$NODE_PATH}"
  set +e
  node "$ROOT/tools/linkedin/wait_for_cdp_login.js"
  rc=$?
  set -e
  if [[ "$rc" -eq 0 ]]; then
    echo "OK: LinkedIn CDP session has li_at (also used by hitechcity). Future home dailies can reuse this profile."
    exit 0
  fi
  echo "WARN: LinkedIn still not logged in (exit $rc). Stay on the Chrome window and retry." >&2
  echo "Hint: bash scripts/home-headed-login.sh linkedin   # same session as hitechcity" >&2
  exit "$rc"
fi
if [[ "$PORTAL" == "cutshort" && -f "$ROOT/tools/cutshort/wait_for_cdp_login.js" ]]; then
  export NODE_PATH="$ROOT/tools/node_modules${NODE_PATH:+:$NODE_PATH}"
  set +e
  node "$ROOT/tools/cutshort/wait_for_cdp_login.js"
  rc=$?
  set -e
  if [[ "$rc" -eq 0 ]]; then
    echo "OK: Cutshort CDP session is live. Future home dailies can reuse this profile."
    exit 0
  fi
  echo "WARN: Cutshort still not logged in (exit $rc). Stay on the Chrome window and retry." >&2
  exit "$rc"
fi
if [[ "$PORTAL" == "instahyre" && -f "$ROOT/tools/instahyre/wait_for_cdp_login.js" ]]; then
  export NODE_PATH="$ROOT/tools/node_modules${NODE_PATH:+:$NODE_PATH}"
  set +e
  node "$ROOT/tools/instahyre/wait_for_cdp_login.js"
  rc=$?
  set -e
  if [[ "$rc" -eq 0 ]]; then
    echo "OK: Instahyre CDP session is live. Future home dailies can reuse this profile."
    exit 0
  fi
  echo "WARN: Instahyre still not logged in (exit $rc). Stay on the Chrome window and retry." >&2
  exit "$rc"
fi
if [[ "$PORTAL" == "foundit" && -f "$ROOT/tools/foundit/wait_for_cdp_login.js" ]]; then
  export NODE_PATH="$ROOT/tools/node_modules${NODE_PATH:+:$NODE_PATH}"
  set +e
  node "$ROOT/tools/foundit/wait_for_cdp_login.js" --open-login --wait "${FOUNDIT_LOGIN_WAIT_SEC:-180}"
  rc=$?
  set -e
  if [[ "$rc" -eq 0 ]]; then
    echo "OK: Foundit CDP session has MSSOAT. Future home dailies can reuse this profile."
    exit 0
  fi
  echo "WARN: Foundit still not logged in (exit $rc). Stay on the Chrome window and retry." >&2
  exit "$rc"
fi
if [[ "$PORTAL" == "naukri" && -f "$ROOT/tools/naukri/wait_for_cdp_login.js" ]]; then
  export NODE_PATH="$ROOT/tools/node_modules${NODE_PATH:+:$NODE_PATH}"
  set +e
  node "$ROOT/tools/naukri/wait_for_cdp_login.js" --wait "${NAUKRI_LOGIN_WAIT_SEC:-120}"
  rc=$?
  set -e
  if [[ "$rc" -eq 0 ]]; then
    echo "OK: Naukri CDP session has nauk_rt/nauk_at. Future home dailies can reuse this profile."
    exit 0
  fi
  echo "WARN: Naukri still not logged in (exit $rc). Stay on the Chrome window and retry." >&2
  exit "$rc"
fi
if [[ "$PORTAL" == "hirist" && -f "$ROOT/tools/hirist/wait_for_cdp_login.js" ]]; then
  export NODE_PATH="$ROOT/tools/node_modules${NODE_PATH:+:$NODE_PATH}"
  set +e
  node "$ROOT/tools/hirist/wait_for_cdp_login.js" --open-login --wait "${HIRIST_LOGIN_WAIT_SEC:-180}"
  rc=$?
  set -e
  if [[ "$rc" -eq 0 ]]; then
    echo "OK: Hirist CDP session is live. Future home dailies can reuse this profile."
    exit 0
  fi
  echo "WARN: Hirist still not logged in (exit $rc). Stay on the Chrome window and retry." >&2
  exit "$rc"
fi

# Portal-specific smoke check via Node + playwright when available
if [[ -d "$ROOT/tools/node_modules/playwright-core" ]]; then
  export NODE_PATH="$ROOT/tools/node_modules${NODE_PATH:+:$NODE_PATH}"
  node - "$PORTAL" "$LOGIN_URL" <<'NODE'
const { chromium } = require("playwright-core");
const portal = process.argv[2];
(async () => {
  const browser = await chromium.connectOverCDP("http://127.0.0.1:9222");
  const page = await browser.newPage();
  const checks = {
    naukri: "https://www.naukri.com/mnjuser/profile",
    linkedin: "https://www.linkedin.com/feed/",
    foundit: "https://www.foundit.in/profile",
    cutshort: "https://cutshort.io/profile/candidate-dashboard",
    instahyre: "https://www.instahyre.com/candidate/opportunities/",
    indeed: "https://www.indeed.com/",
    hirist: "https://www.hirist.tech/applied-jobs",
  };
  const url = checks[portal];
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
  await page.waitForTimeout(3000);
  const finalUrl = page.url();
  const text = await page.evaluate(() => (document.body && document.body.innerText || "").slice(0, 500));
  const loginish = /login|sign in|nlogin|authwall|session expired/i.test(finalUrl + "\n" + text);
  console.log(JSON.stringify({ portal, url: finalUrl, looksLoggedIn: !loginish, preview: text.slice(0, 200) }, null, 2));
  await page.close().catch(() => {});
  await browser.close().catch(() => {});
  process.exit(loginish ? 3 : 0);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
NODE
  rc=$?
  if [[ "$rc" -eq 0 ]]; then
    echo "OK: $PORTAL session looks logged in. Future home dailies can reuse this CDP profile."
  else
    echo "WARN: still looks logged out (exit $rc). Stay on the Chrome window and retry this script." >&2
    exit "$rc"
  fi
else
  echo "playwright-core not installed under tools/ — skipped automated verify."
  echo "Manually confirm you see your profile, then re-run the portal daily."
fi
