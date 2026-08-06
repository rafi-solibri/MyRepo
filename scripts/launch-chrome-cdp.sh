#!/usr/bin/env bash
# Launch Chrome CDP on :9222 with the synced per-portal profile.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

portal="${1:-}"
if [[ -z "$portal" ]]; then
  echo "Usage: bash scripts/launch-chrome-cdp.sh <linkedin|naukri|foundit|cutshort|instahyre|indeed>" >&2
  exit 2
fi

profile="$(
  node - "$portal" <<'NODE'
const { PROFILES } = require("./tools/chrome_session");
const portal = process.argv[2];
if (!PROFILES[portal]) process.exit(2);
process.stdout.write(PROFILES[portal]);
NODE
)" || {
  echo "Unknown portal: $portal" >&2
  exit 2
}

chrome="${CHROME_BIN:-}"
if [[ -z "$chrome" ]]; then
  chrome="$(command -v google-chrome || command -v chromium || command -v chromium-browser || command -v google-chrome-stable || true)"
fi
if [[ -z "$chrome" ]]; then
  echo "ERROR: Chrome/Chromium executable not found" >&2
  exit 1
fi

mkdir -p "$profile" /opt/cursor/artifacts /tmp/cursor

# Daily automations use one portal per pod. Restarting avoids connecting to a
# CDP process that was launched earlier with a different profile.
pkill -f "remote-debugging-port=9222" 2>/dev/null || true

headless=()
if [[ "${CHROME_HEADLESS:-auto}" == "1" || ( "${CHROME_HEADLESS:-auto}" == "auto" && -z "${DISPLAY:-}" ) ]]; then
  headless=(--headless=new)
fi

log="/tmp/cursor/chrome-cdp-${portal}.log"
nohup "$chrome" \
  "${headless[@]}" \
  --no-sandbox \
  --disable-gpu \
  --disable-dev-shm-usage \
  --disable-extensions \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=9222 \
  --user-data-dir="$profile" \
  about:blank >"$log" 2>&1 &

python3 - <<'PY'
import sys, time, urllib.request

url = "http://127.0.0.1:9222/json/version"
last = None
for _ in range(30):
    try:
        print(urllib.request.urlopen(url, timeout=1).read().decode())
        raise SystemExit(0)
    except Exception as exc:
        last = exc
        time.sleep(0.5)
print(f"ERROR: Chrome CDP did not become ready: {last}", file=sys.stderr)
raise SystemExit(1)
PY

echo "Chrome CDP ready for $portal using $profile (log: $log)"
