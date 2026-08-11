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
case "$PORTAL" in
  linkedin|foundit|cutshort|naukri|instahyre|indeed) ;;
  *)
    echo "Usage: bash scripts/home-headed-login.sh <linkedin|foundit|cutshort|naukri|instahyre|indeed>" >&2
    exit 2
    ;;
esac

LOGIN_URL="$(
  case "$PORTAL" in
    linkedin) echo "https://www.linkedin.com/login" ;;
    foundit) echo "https://www.foundit.in/rio/login" ;;
    cutshort) echo "https://cutshort.io/login" ;;
    naukri) echo "https://www.naukri.com/nlogin/login" ;;
    instahyre) echo "https://www.instahyre.com/login/" ;;
    indeed) echo "https://secure.indeed.com/auth" ;;
  esac
)"

export CHROME_HEADLESS=0
export PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" && -x /c/Python314/python ]]; then
  export PYTHON_BIN=/c/Python314/python
fi

echo "Launching headed Chrome CDP for $PORTAL…"
echo "Sign in in the Chrome window that opens ($LOGIN_URL)."
echo "When done, leave the window open and press Enter here to verify."
bash scripts/launch-chrome-cdp.sh "$PORTAL"

# Open login tab via CDP HTTP
if command -v curl >/dev/null 2>&1; then
  curl -s -X PUT "http://127.0.0.1:9222/json/new?$(python -c "import urllib.parse; print(urllib.parse.quote('''$LOGIN_URL''', safe=''))" 2>/dev/null || echo "$LOGIN_URL")" >/dev/null 2>&1 \
    || curl -s "http://127.0.0.1:9222/json/new?$LOGIN_URL" >/dev/null 2>&1 \
    || true
fi

echo
read -r -p "Press Enter after you have finished signing in…"

# LinkedIn: prefer dedicated live CDP waiter (ABE-aware messaging).
if [[ "$PORTAL" == "linkedin" && -f "$ROOT/tools/linkedin/wait_for_cdp_login.js" ]]; then
  export NODE_PATH="$ROOT/tools/node_modules${NODE_PATH:+:$NODE_PATH}"
  set +e
  node "$ROOT/tools/linkedin/wait_for_cdp_login.js"
  rc=$?
  set -e
  if [[ "$rc" -eq 0 ]]; then
    echo "OK: LinkedIn CDP session has li_at. Future home dailies can reuse this profile."
    exit 0
  fi
  echo "WARN: LinkedIn still not logged in (exit $rc). Stay on the Chrome window and retry." >&2
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
