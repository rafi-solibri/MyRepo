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
bash scripts/sync-chrome-sessions.sh
python3 tools/resume_paths.py
node tools/chrome_session.js check "$portal"
