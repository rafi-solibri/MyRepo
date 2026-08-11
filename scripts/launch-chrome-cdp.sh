#!/usr/bin/env bash
# Launch Chrome CDP on :9222 with the synced per-portal profile.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

portal="${1:-}"
if [[ -z "$portal" ]]; then
  echo "Usage: bash scripts/launch-chrome-cdp.sh <linkedin|hitechcity|naukri|foundit|cutshort|instahyre|indeed>" >&2
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
  for cand in \
    "/c/Program Files/Google/Chrome/Application/chrome.exe" \
    "/c/Program Files (x86)/Google/Chrome/Application/chrome.exe" \
    "$(command -v google-chrome 2>/dev/null || true)" \
    "$(command -v google-chrome-stable 2>/dev/null || true)" \
    "$(command -v chromium 2>/dev/null || true)" \
    "$(command -v chromium-browser 2>/dev/null || true)"; do
    if [[ -n "$cand" && -f "$cand" ]]; then
      chrome="$cand"
      break
    fi
  done
fi
if [[ -z "$chrome" ]]; then
  echo "ERROR: Chrome/Chromium executable not found" >&2
  exit 1
fi

mkdir -p "$profile" /tmp/cursor
mkdir -p /opt/cursor/artifacts 2>/dev/null || mkdir -p "$ROOT/artifacts"

# Daily automations use one portal per pod. Restarting avoids connecting to a
# CDP process that was launched earlier with a different profile.
if command -v taskkill.exe >/dev/null 2>&1; then
  # Only kill Chrome instances that expose CDP :9222 (leave normal browsing alone when possible).
  powershell.exe -NoProfile -Command \
    "Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | Where-Object { \$_.CommandLine -match 'remote-debugging-port=9222' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }" \
    >/dev/null 2>&1 || true
else
  pkill -f "remote-debugging-port=9222" 2>/dev/null || true
fi
sleep 1

headless=()
# On Windows home (Git Bash), DISPLAY is unset but headed Chrome is preferred.
is_win=0
[[ "${OS:-}" == "Windows_NT" || -n "${MSYSTEM:-}" || "$(uname -s 2>/dev/null)" == MINGW* ]] && is_win=1
if [[ "${CHROME_HEADLESS:-auto}" == "1" ]]; then
  headless=(--headless=new)
elif [[ "${CHROME_HEADLESS:-auto}" == "auto" && "$is_win" -eq 0 && -z "${DISPLAY:-}" ]]; then
  headless=(--headless=new)
fi

proxy_args=()
# Indeed: WARP SOCKS (auto) or residential INDEED_HTTP_PROXY bypasses datacenter Cloudflare.
if [[ "$portal" == "indeed" ]]; then
  if [[ -z "${INDEED_HTTP_PROXY:-}" || "${INDEED_HTTP_PROXY}" == *"127.0.0.1:40000"* ]]; then
    # shellcheck disable=SC1091
    eval "$(bash "$ROOT/scripts/ensure-indeed-warp.sh")" || {
      echo "ERROR: Could not start WARP SOCKS for Indeed CDP" >&2
      exit 1
    }
  fi
  if [[ -n "${INDEED_HTTP_PROXY:-}" ]]; then
    proxy_args=(--proxy-server="${INDEED_HTTP_PROXY}")
    echo "Using INDEED_HTTP_PROXY for Chrome CDP (${INDEED_HTTP_PROXY})"
  fi
elif [[ -n "${CHROME_HTTP_PROXY:-}" ]]; then
  proxy_args=(--proxy-server="${CHROME_HTTP_PROXY}")
  echo "Using CHROME_HTTP_PROXY for Chrome CDP"
fi

# Indeed Turnstile / applies need a headed display when possible.
if [[ "$portal" == "indeed" && "${CHROME_HEADLESS:-auto}" == "auto" && -n "${DISPLAY:-}" ]]; then
  headless=()
fi

log="/tmp/cursor/chrome-cdp-${portal}.log"
nohup "$chrome" \
  "${headless[@]}" \
  "${proxy_args[@]}" \
  --no-sandbox \
  --disable-gpu \
  --disable-dev-shm-usage \
  --disable-extensions \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=9222 \
  --user-data-dir="$profile" \
  about:blank >"$log" 2>&1 &

PY="$(bash "$ROOT/scripts/resolve-python.sh")"
run_py() {
  if [[ "$PY" == "py" ]]; then
    py -3 "$@"
  else
    "$PY" "$@"
  fi
}
run_py - <<'PY'
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
