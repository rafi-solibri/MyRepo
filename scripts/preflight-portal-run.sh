#!/usr/bin/env bash
# Canonical preflight for daily portal automations.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

portal="${1:-}"
if [[ -z "$portal" ]]; then
  echo "Usage: bash scripts/preflight-portal-run.sh <linkedin|hitechcity|naukri|foundit|cutshort|instahyre|indeed>" >&2
  exit 2
fi

bash scripts/bootstrap-job-assets.sh
# Node portal helpers (foundit/cutshort/…) need playwright-core under tools/.
if [[ -f tools/package.json ]]; then
  if [[ ! -d tools/node_modules/playwright-core ]]; then
    echo "Installing tools/ npm deps (playwright-core)…"
    (cd tools && npm ci --no-fund --no-audit 2>/dev/null || npm install --no-fund --no-audit)
  fi
fi
bash scripts/sync-chrome-sessions.sh
python3 tools/resume_paths.py
node tools/chrome_session.js check "$portal"
