#!/usr/bin/env bash
# Canonical Cloud Agent bootstrap for the job-apply automation repo.
#
# Idempotent: safe to re-run. Prepares everything the daily portal automations
# and their helper scripts rely on:
#   1. Python tooling  (Playwright + scraping/HTTP libs + pytest) and Chromium
#   2. Resume assets    (Rafi_Resume.docx materialized in every expected dir)
#   3. Node tooling     (playwright-core for the JS portal helpers)
#   4. Chrome CDP dirs  (per-portal profiles the cron agents launch)
#   5. Session sync     (copy authenticated Desktop Chrome logins into CDP dirs)
set -euo pipefail
cd "$(dirname "$0")/.."

# --- 1. Python tooling ------------------------------------------------------
# The linkedin/*.py helpers and any pytest checks import Playwright plus
# scraping/HTTP libraries. Install into the user site and drive a Chromium
# build. Debian/Ubuntu ship a PEP 668 "externally managed" interpreter, so
# allow --break-system-packages when the local pip supports it.
PY=python3
export PIP_DISABLE_PIP_VERSION_CHECK=1
PIP_INSTALL=("$PY" -m pip install --user --upgrade)
if "$PY" -m pip install --help 2>/dev/null | grep -q -- '--break-system-packages'; then
  PIP_INSTALL+=(--break-system-packages)
fi
"${PIP_INSTALL[@]}" playwright beautifulsoup4 lxml requests pytest seleniumbase PyAutoGUI pysocks

# install-deps shells out to apt (escalating with sudo itself) and is
# best-effort: if sudo/apt are unavailable the base image already ships the
# needed libraries.
"$PY" -m playwright install-deps chromium || true
"$PY" -m playwright install chromium

# Indeed Cloudflare bypass on public cloud: WARP SOCKS + SeleniumBase UC.
# Best-effort — pods without apt/sudo still work once the package is snapshotted.
if ! command -v warp-cli >/dev/null 2>&1; then
  curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg \
    | sudo gpg --yes --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" \
      | sudo tee /etc/apt/sources.list.d/cloudflare-client.list >/dev/null \
    && sudo apt-get update -qq \
    && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y cloudflare-warp python3-tk \
    || echo "WARNING: cloudflare-warp install failed; Indeed cloud bypass needs it."
else
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-tk >/dev/null 2>&1 || true
fi

# --- 2. Resume assets -------------------------------------------------------
bash scripts/bootstrap-job-assets.sh

# --- 3. Node tooling --------------------------------------------------------
if [[ -f tools/package.json ]]; then
  (cd tools && npm ci --no-fund --no-audit || npm install --no-fund --no-audit)
fi

# --- 4. Chrome CDP profile directories --------------------------------------
mkdir -p \
  /home/ubuntu/resumes \
  /home/ubuntu/Documents \
  /home/ubuntu/.naukri-chrome-profile \
  /home/ubuntu/.config/chrome-foundit \
  /home/ubuntu/chrome-instahyre-profile \
  /home/ubuntu/chrome-indeed-profile \
  /home/ubuntu/chrome-cdp-profile \
  /home/ubuntu/chrome-linkedin-profile \
  /home/ubuntu/chrome-cutshort-profile \
  /opt/cursor/artifacts

# --- 5. Session restore + sync ----------------------------------------------
# Environment builds often boot from a base disk that lacks Desktop logins.
# Restore the private .portal-sessions seed first (if present), then sync
# Default Chrome into each CDP profile. Sync is non-destructive.
bash scripts/restore-portal-sessions.sh || echo "WARNING: portal session restore failed; continuing install."
if [[ -f /home/ubuntu/.config/google-chrome/Default/Cookies ]]; then
  bash scripts/sync-chrome-sessions.sh || echo "WARNING: Chrome session sync reported missing auth; continuing install."
fi
node tools/chrome_session.js status || true
bash scripts/verify-portal-logins.sh --no-sync || true

echo "Job-apply assets ready."
ls -la resumes/Rafi_Resume.docx /home/ubuntu/resumes/Rafi_Resume.docx 2>/dev/null || true
