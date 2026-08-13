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

# If CDP already up on :9222, reuse only when it matches our intended user-data-dir.
cdp_ready=0
if curl -fsS "http://127.0.0.1:9222/json/version" >/dev/null 2>&1; then
  profile_match=0
  # Prefer /proc exe+cmdline so we never confuse agent shells with Chrome.
  for pid in /proc/[0-9]*; do
    pid="${pid#/proc/}"
    [[ "$pid" =~ ^[0-9]+$ ]] || continue
    exe="$(readlink -f "/proc/$pid/exe" 2>/dev/null || true)"
    case "$exe" in
      */chrome|*/google-chrome*|*/chromium*) ;;
      *) continue ;;
    esac
    cmd="$(tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null || true)"
    [[ "$cmd" == *remote-debugging-port=9222* ]] || continue
    [[ "$cmd" == *"--user-data-dir=$profile"* || "$cmd" == *"--user-data-dir=$profile "* ]] || continue
    profile_match=1
    break
  done
  if [[ "$profile_match" -eq 1 ]]; then
    cdp_ready=1
    echo "Chrome CDP already listening on :9222 with $profile — reusing."
  else
    echo "NOTE: :9222 is up but not user-data-dir=$profile — restarting."
  fi
fi

if [[ "$cdp_ready" -eq 0 ]]; then
  # Daily automations use one portal per pod. Restarting avoids connecting to a
  # CDP process that was launched earlier with a different profile.
  # NEVER use `pkill -f chrome` / `pkill -f remote-debugging-port=9222` — those
  # patterns match the agent shell's own command line and abort the launcher.
  if [[ "$system_profile" -eq 1 ]]; then
    # System profile is locked by any normal Chrome window — must close Chrome first.
    echo "Closing existing Chrome so Default profile can open with remote debugging…"
    if command -v taskkill.exe >/dev/null 2>&1; then
      taskkill.exe /F /IM chrome.exe >/dev/null 2>&1 || true
    else
      bash "$ROOT/scripts/kill-chrome-cdp.sh" all || true
    fi
  elif command -v taskkill.exe >/dev/null 2>&1; then
    # Only kill Chrome instances that expose CDP :9222 (leave normal browsing alone when possible).
    powershell.exe -NoProfile -Command \
      "Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | Where-Object { \$_.CommandLine -match 'remote-debugging-port=9222' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }" \
      >/dev/null 2>&1 || true
  else
    bash "$ROOT/scripts/kill-chrome-cdp.sh" cdp || true
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
# LinkedIn/HitechCity (cloud): same WARP path — AWS IPs trigger LinkedIn checkpoint/CAPTCHA.
# Home / residential Windows: skip WARP (*_SKIP_WARP=1) — home IP is the bypass.
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
elif [[ "$portal" == "linkedin" || "$portal" == "hitechcity" ]]; then
  if [[ "${LINKEDIN_SKIP_WARP:-}" == "1" ]]; then
    echo "NOTE: LINKEDIN_SKIP_WARP=1 — launching LinkedIn Chrome without WARP."
  elif [[ "$is_win" -eq 1 ]]; then
    echo "NOTE: Windows home LinkedIn — skipping WARP (residential IP)."
  elif [[ -n "${LINKEDIN_HTTP_PROXY:-}" ]]; then
    proxy_args=(--proxy-server="${LINKEDIN_HTTP_PROXY}")
    echo "Using LINKEDIN_HTTP_PROXY for Chrome CDP (${LINKEDIN_HTTP_PROXY})"
  elif [[ -n "${CHROME_HTTP_PROXY:-}" ]]; then
    proxy_args=(--proxy-server="${CHROME_HTTP_PROXY}")
    echo "Using CHROME_HTTP_PROXY for Chrome CDP"
  else
    # shellcheck disable=SC1091
    if eval "$(bash "$ROOT/scripts/ensure-linkedin-warp.sh")"; then
      if [[ -n "${LINKEDIN_HTTP_PROXY:-}" ]]; then
        proxy_args=(--proxy-server="${LINKEDIN_HTTP_PROXY}")
        echo "Using WARP SOCKS for LinkedIn CDP (${LINKEDIN_HTTP_PROXY})"
      fi
    else
      echo "WARNING: WARP SOCKS unavailable for LinkedIn — continuing without proxy (CAPTCHA more likely)." >&2
    fi
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
    ps_file="$(mktemp /tmp/chrome-cdp-launch-XXXXXX.ps1 2>/dev/null || echo "$ROOT/artifacts/_chrome_cdp_launch.ps1")"
    mkdir -p "$(dirname "$ps_file")" 2>/dev/null || true
    profile_dir="${CHROME_PROFILE_DIRECTORY:-Default}"
    {
      echo "\$chrome = @'"
      echo "$chrome"
      echo "'@"
      echo "\$ud = @'"
      echo "$profile"
      echo "'@"
      echo "\$args = @("
      echo "  '--no-sandbox',"
      echo "  '--disable-gpu',"
      echo "  '--disable-dev-shm-usage',"
      echo "  '--disable-extensions',"
      echo "  '--remote-debugging-address=127.0.0.1',"
      echo "  '--remote-debugging-port=9222',"
      echo "  '--remote-allow-origins=*',"
      echo "  \"--user-data-dir=\$ud\""
      if [[ "$system_profile" -eq 1 ]]; then
        echo "  ,'--profile-directory=$profile_dir'"
      fi
      if [[ ${#proxy_args[@]} -gt 0 ]]; then
        echo "  ,'${proxy_args[0]}'"
      fi
      if [[ ${#headless[@]} -gt 0 ]]; then
        echo "  ,'${headless[0]}'"
      fi
      echo "  ,'about:blank'"
      echo ")"
      echo "Start-Process -FilePath \$chrome -ArgumentList \$args"
    } > "$ps_file"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$ps_file" >/dev/null 2>&1 || true
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
      # Unattended recovery: Google SSO / LINKEDIN_PASSWORD, then refresh seed on success.
      if [[ "${LINKEDIN_AUTO_LOGIN:-1}" == "1" && -f "$ROOT/tools/linkedin/auto_login.py" ]]; then
        echo "Attempting unattended LinkedIn auto-login…"
        PY="$(bash "$ROOT/scripts/resolve-python.sh")"
        set +e
        if [[ "$PY" == "py" ]]; then
          py -3 "$ROOT/tools/linkedin/auto_login.py"
          auto_rc=$?
        else
          "$PY" "$ROOT/tools/linkedin/auto_login.py"
          auto_rc=$?
        fi
        set -e
        if [[ "$auto_rc" -eq 0 ]]; then
          node "$ROOT/tools/linkedin/wait_for_cdp_login.js"
          live_rc=$?
          if [[ "$live_rc" -eq 0 ]]; then
            echo "LinkedIn auto-login OK — refreshing .portal-sessions seed."
            bash "$ROOT/scripts/refresh-portal-session-seed.sh" linkedin || true
          fi
        else
          echo "NOTE: auto-login exit $auto_rc (5=login required, 6=CAPTCHA/checkpoint)." >&2
        fi
      fi
    fi
    if [[ "$live_rc" -eq 0 ]]; then
      # Keep seed fresh whenever live session is good (survives next environment boot).
      if [[ "${LINKEDIN_REFRESH_SEED:-1}" == "1" ]]; then
        bash "$ROOT/scripts/refresh-portal-session-seed.sh" linkedin || true
      fi
    elif [[ "$live_rc" -ne 0 ]]; then
      echo "WARNING: LinkedIn CDP still not logged in (live check exit $live_rc)." >&2
      echo "         Sign in once: bash scripts/home-headed-login.sh linkedin" >&2
      echo "         Or set secrets LINKEDIN_EMAIL + LINKEDIN_PASSWORD for password fallback." >&2
      echo "         Or set LINKEDIN_LOGIN_WAIT_SEC=300 and re-launch while you sign in." >&2
      # Cron/cloud: hard-fail so apply helpers do not burn inventory on login walls.
      # Headed login scripts set CDP_REQUIRE_LIVE_LOGIN=0 (they wait separately).
      if [[ "${CDP_REQUIRE_LIVE_LOGIN:-1}" == "1" ]]; then
        echo "ERROR: CDP_REQUIRE_LIVE_LOGIN=1 — refusing to continue without a live LinkedIn session." >&2
        echo "       After a successful login, seed refresh is automatic; push .portal-sessions if needed." >&2
        exit "$live_rc"
      fi
    fi
  fi
fi
