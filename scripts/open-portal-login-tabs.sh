#!/usr/bin/env bash
# Open Default Desktop Chrome with the 6 portal home pages so you can sign in.
# Use Cloud Agent Desktop (VNC). Do NOT use CDP profiles for this step.
set -euo pipefail

DISPLAY="${DISPLAY:-:1}"
export DISPLAY
export CHROME_SOURCE_PROFILE="${CHROME_SOURCE_PROFILE:-/home/ubuntu/.config/google-chrome}"

# Stale locks from a previous snapshot crash block Chrome from starting.
rm -f \
  "$CHROME_SOURCE_PROFILE/SingletonLock" \
  "$CHROME_SOURCE_PROFILE/SingletonCookie" \
  "$CHROME_SOURCE_PROFILE/SingletonSocket" \
  "$CHROME_SOURCE_PROFILE/Default/SingletonLock" \
  "$CHROME_SOURCE_PROFILE/Default/lockfile" 2>/dev/null || true

URLS=(
  "https://www.linkedin.com/feed/"
  "https://www.naukri.com/mnjuser/homepage"
  "https://www.foundit.in/seeker/dashboard"
  "https://cutshort.io/profile"
  "https://www.instahyre.com/candidate/opportunities/"
  "https://www.indeed.com/"
  "https://www.hirist.tech/login"
  "file:///workspace/scripts/portal-login-checklist.html"
)

CHROME_BIN=""
for c in google-chrome google-chrome-stable /opt/google/chrome/chrome chromium-browser chromium; do
  if command -v "$c" >/dev/null 2>&1 || [[ -x "$c" ]]; then
    CHROME_BIN="$c"
    break
  fi
done
if [[ -z "$CHROME_BIN" ]]; then
  echo "ERROR: Chrome binary not found" >&2
  exit 1
fi

# If Chrome is already running on Default, just open tabs via a second process.
echo "Launching Default Chrome on DISPLAY=$DISPLAY"
echo "Sign into every portal that shows a login page (home/feed must load)."
echo "When done: fully quit Chrome, then run:"
echo "  bash scripts/verify-portal-logins.sh --strict"
echo "Then Save / Update snapshot on the environment dashboard."

nohup "$CHROME_BIN" \
  --user-data-dir="$CHROME_SOURCE_PROFILE" \
  --profile-directory=Default \
  --no-first-run \
  --no-default-browser-check \
  --disable-session-crashed-bubble \
  --hide-crash-restore-bubble \
  "${URLS[@]}" \
  >/tmp/portal-login-chrome.log 2>&1 &

echo "Chrome PID $!  (log: /tmp/portal-login-chrome.log)"
echo "Open Cloud Agent Desktop to complete the logins."
