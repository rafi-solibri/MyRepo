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

# Windows system profile = real Chrome User Data (ABE-safe). Need Default profile dir flag.
profile_dir_args=()
system_profile=0
if node -e "const {useSystemChromeProfile}=require('./tools/chrome_session'); process.exit(useSystemChromeProfile()?0:1)"; then
  system_profile=1
  profile_dir_args=(--profile-directory="${CHROME_PROFILE_DIRECTORY:-Default}")
  echo "NOTE: CHROME_CDP_MODE=system — using Chrome User Data at $profile (ABE cookies decrypt)."
fi

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

# If CDP already up on :9222, reuse only when it matches our intended profile mode.
cdp_ready=0
if curl -fsS "http://127.0.0.1:9222/json/version" >/dev/null 2>&1; then
  if [[ "$system_profile" -eq 1 ]]; then
    # Ensure the listener is the system User Data Chrome, not a leftover empty CDP profile.
    if command -v powershell.exe >/dev/null 2>&1; then
      sys_match="$(
        powershell.exe -NoProfile -Command \
          "\$p='$profile' -replace '\\\\','\\\\'; Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | Where-Object { \$_.CommandLine -match 'remote-debugging-port=9222' -and \$_.CommandLine -like ('*' + \$p + '*') } | Select-Object -First 1 -ExpandProperty ProcessId" \
          2>/dev/null | tr -d '\r'
      )"
      if [[ -n "$sys_match" ]]; then
        cdp_ready=1
        echo "Chrome CDP already listening on :9222 with system profile — reusing."
      else
        echo "NOTE: :9222 is up but not system Chrome User Data — restarting with Default profile."
      fi
    else
      cdp_ready=1
      echo "Chrome CDP already listening on :9222 — reusing existing instance."
    fi
  else
    cdp_ready=1
    echo "Chrome CDP already listening on :9222 — reusing existing instance."
  fi
fi

if [[ "$cdp_ready" -eq 0 ]]; then
  # Daily automations use one portal per pod. Restarting avoids connecting to a
  # CDP process that was launched earlier with a different profile.
  if [[ "$system_profile" -eq 1 ]]; then
    # System profile is locked by any normal Chrome window — must close Chrome first.
    echo "Closing existing Chrome so Default profile can open with remote debugging…"
    if command -v taskkill.exe >/dev/null 2>&1; then
      taskkill.exe /F /IM chrome.exe >/dev/null 2>&1 || true
    else
      pkill -f "chrome" 2>/dev/null || true
    fi
  elif command -v taskkill.exe >/dev/null 2>&1; then
    # Only kill Chrome instances that expose CDP :9222 (leave normal browsing alone when possible).
    powershell.exe -NoProfile -Command \
      "Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | Where-Object { \$_.CommandLine -match 'remote-debugging-port=9222' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }" \
      >/dev/null 2>&1 || true
  else
    pkill -f "remote-debugging-port=9222" 2>/dev/null || true
  fi
  sleep 1
fi

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
# Home / residential Windows: skip WARP (INDEED_SKIP_WARP=1) — home IP is the bypass.
if [[ "$portal" == "indeed" ]]; then
  if [[ "${INDEED_SKIP_WARP:-}" == "1" ]]; then
    echo "NOTE: INDEED_SKIP_WARP=1 — launching Indeed Chrome without WARP (home/residential)."
  elif [[ -z "${INDEED_HTTP_PROXY:-}" || "${INDEED_HTTP_PROXY}" == *"127.0.0.1:40000"* ]]; then
    # shellcheck disable=SC1091
    if eval "$(bash "$ROOT/scripts/ensure-indeed-warp.sh")"; then
      :
    else
      if [[ "$is_win" -eq 1 ]]; then
        echo "WARNING: WARP SOCKS unavailable on Windows home — continuing without proxy (residential IP)." >&2
        unset INDEED_HTTP_PROXY || true
      else
        echo "ERROR: Could not start WARP SOCKS for Indeed CDP" >&2
        exit 1
      fi
    fi
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
if [[ "$cdp_ready" -eq 0 ]]; then
  if [[ "$is_win" -eq 1 ]] && command -v powershell.exe >/dev/null 2>&1; then
    # PowerShell Start-Process is more reliable than nohup for Windows Chrome + Default profile.
    arg_list="--no-sandbox --disable-gpu --disable-dev-shm-usage --disable-extensions --remote-debugging-address=127.0.0.1 --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=`"$profile`""
    if [[ "$system_profile" -eq 1 ]]; then
      arg_list+=" --profile-directory=${CHROME_PROFILE_DIRECTORY:-Default}"
    fi
    if [[ ${#proxy_args[@]} -gt 0 ]]; then
      arg_list+=" ${proxy_args[*]}"
    fi
    if [[ ${#headless[@]} -gt 0 ]]; then
      arg_list+=" ${headless[*]}"
    fi
    arg_list+=" about:blank"
    powershell.exe -NoProfile -Command \
      "Start-Process -FilePath '$chrome' -ArgumentList '$arg_list'" \
      >/dev/null 2>&1 || true
  else
    nohup "$chrome" \
      "${headless[@]}" \
      "${proxy_args[@]}" \
      --no-sandbox \
      --disable-gpu \
      --disable-dev-shm-usage \
      --disable-extensions \
      --remote-debugging-address=127.0.0.1 \
      --remote-debugging-port=9222 \
      --remote-allow-origins='*' \
      --user-data-dir="$profile" \
      "${profile_dir_args[@]}" \
      about:blank >"$log" 2>&1 &
  fi
fi

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
for _ in range(40):
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

# LinkedIn on Windows ABE: SQLite cookie names can lie. Live-probe CDP when asked.
if [[ "$portal" == "linkedin" || "$portal" == "hitechcity" ]]; then
  if [[ "${CDP_LIVE_LOGIN_CHECK:-1}" == "1" ]] && command -v node >/dev/null 2>&1; then
    export NODE_PATH="$ROOT/tools/node_modules${NODE_PATH:+:$NODE_PATH}"
    wait_sec="${LINKEDIN_LOGIN_WAIT_SEC:-0}"
    set +e
    if [[ "$wait_sec" -gt 0 ]]; then
      node "$ROOT/tools/linkedin/wait_for_cdp_login.js" --open-login --wait "$wait_sec"
      live_rc=$?
    else
      node "$ROOT/tools/linkedin/wait_for_cdp_login.js" --open-login
      live_rc=$?
    fi
    set -e
    if [[ "$live_rc" -ne 0 ]]; then
      echo "WARNING: LinkedIn CDP not logged in (live check exit $live_rc)." >&2
      echo "         Sign in once: bash scripts/home-headed-login.sh linkedin" >&2
      echo "         Or set LINKEDIN_LOGIN_WAIT_SEC=300 and re-launch while you sign in." >&2
    fi
  fi
fi
