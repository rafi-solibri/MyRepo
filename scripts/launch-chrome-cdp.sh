#!/usr/bin/env bash
# Launch Chrome CDP on :9222 with the synced per-portal profile.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
# Optional local secrets (LINKEDIN_PASSWORD etc.) — never committed.
# shellcheck disable=SC1091
source "$ROOT/scripts/load-job-secrets.sh" || true

portal="${1:-}"
if [[ -z "$portal" ]]; then
  echo "Usage: bash scripts/launch-chrome-cdp.sh <linkedin|hitechcity|naukri|foundit|cutshort|instahyre|indeed|hirist>" >&2
  exit 2
fi

# Skip LinkedIn login/apply CDP when a known temporary restriction is still active.
# Careers-only hitechcity may continue without LI; pure linkedin portal exits 7.
if [[ "$portal" == "linkedin" || "$portal" == "hitechcity" ]]; then
  if [[ "${LINKEDIN_IGNORE_RESTRICTION_FLAG:-}" != "1" ]]; then
    PY_RESTR="$(bash "$ROOT/scripts/resolve-python.sh" 2>/dev/null || echo python3)"
    set +e
    if [[ "$PY_RESTR" == "py" ]]; then
      restr_out="$(py -3 -c "from tools.linkedin.restriction import should_skip_linkedin_for_restriction; import json; s=should_skip_linkedin_for_restriction(); print(json.dumps(s) if s else '')" 2>/dev/null)"
      restr_rc=$?
    else
      restr_out="$("$PY_RESTR" -c "from tools.linkedin.restriction import should_skip_linkedin_for_restriction; import json; s=should_skip_linkedin_for_restriction(); print(json.dumps(s) if s else '')" 2>/dev/null)"
      restr_rc=$?
    fi
    set -e
    if [[ "$restr_rc" -eq 0 && -n "${restr_out:-}" ]]; then
      echo "NOTE: LinkedIn temporary restriction still active — $restr_out" >&2
      if [[ "$portal" == "linkedin" ]]; then
        echo "ERROR: refusing LinkedIn CDP launch until lift (exit 7). Careers can use: HITECHCITY_CAREERS_ONLY=1" >&2
        exit 7
      fi
      # hitechcity: allow careers CDP without LI auto-login / WARP thrash
      export LINKEDIN_AUTO_LOGIN=0
      export CDP_LIVE_LOGIN_CHECK=0
      export LINKEDIN_SKIP_WARP="${LINKEDIN_SKIP_WARP:-1}"
      echo "NOTE: hitechcity continuing careers-only (LinkedIn auto-login/WARP disabled until lift)." >&2
    fi
  fi
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
  is_win_cdp=0
  [[ "${OS:-}" == "Windows_NT" || -n "${MSYSTEM:-}" || "$(uname -s 2>/dev/null)" == MINGW* ]] && is_win_cdp=1

  if [[ "$is_win_cdp" -eq 1 ]] && command -v powershell.exe >/dev/null 2>&1; then
    # Git Bash /proc does not expose real chrome.exe command lines on Windows, so the
    # /proc matcher always fails → every portal kills system Chrome mid-apply.
    # PowerShell Win32_Process.CommandLine is the source of truth here.
    profile_win="$(cygpath -w "$profile" 2>/dev/null || echo "$profile")"
    if powershell.exe -NoProfile -Command \
      "\$want = [string]'${profile_win}'; \$hit = Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | Where-Object { \$_.CommandLine -match 'remote-debugging-port=9222' -and (\$_.CommandLine -like ('*' + \$want + '*') -or '${system_profile}' -eq '1') }; if (\$hit) { exit 0 } else { exit 1 }" \
      >/dev/null 2>&1; then
      profile_match=1
    fi
    # System Chrome Default: any :9222 listener is the shared home CDP — reuse it.
    if [[ "$profile_match" -eq 0 && "$system_profile" -eq 1 ]]; then
      if powershell.exe -NoProfile -Command \
        "if (Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | Where-Object { \$_.CommandLine -match 'remote-debugging-port=9222' }) { exit 0 } else { exit 1 }" \
        >/dev/null 2>&1; then
        profile_match=1
        echo "NOTE: Windows system Chrome CDP on :9222 — reusing shared home session (skip kill)."
      fi
    fi
  else
    # Prefer /proc exe+cmdline so we never confuse agent shells with Chrome (Linux/cloud).
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
  fi
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
    if command -v powershell.exe >/dev/null 2>&1; then
      # Git Bash mangles taskkill /F → F:/. A single kill also leaves child
      # chrome.exe that steals the next Start-Process (remote-debugging ignored).
      powershell.exe -NoProfile -Command \
        '1..6 | ForEach-Object { Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue; Start-Sleep -Milliseconds 800 }; if (@(Get-Process chrome -ErrorAction SilentlyContinue).Count -gt 0) { cmd /c "taskkill /F /IM chrome.exe /T" | Out-Null }; Start-Sleep -Seconds 1; $ud = Join-Path $env:LOCALAPPDATA "Google\Chrome\User Data"; @("SingletonLock","SingletonCookie","SingletonSocket") | ForEach-Object { $p = Join-Path $ud $_; if (Test-Path $p) { Remove-Item -Force $p -ErrorAction SilentlyContinue } }' \
        >/dev/null 2>&1 || true
    elif command -v taskkill.exe >/dev/null 2>&1; then
      # Git Bash mangles /F → F:/ — use //F //IM (same as sync-chrome-sessions.sh).
      taskkill.exe //F //IM chrome.exe >/dev/null 2>&1 || true
    else
      bash "$ROOT/scripts/kill-chrome-cdp.sh" all || true
    fi
    # Forced kill looks like a crash → Chrome restores 100+ tabs and Playwright
    # connectOverCDP hangs. Mark a clean exit so the next launch starts blank.
    node - "$profile" <<'NODE' || true
const fs = require("fs");
const path = require("path");
const ud = process.argv[2];
for (const rel of ["Default/Preferences", "Default/Secure Preferences"]) {
  const p = path.join(ud, rel);
  try {
    const j = JSON.parse(fs.readFileSync(p, "utf8"));
    j.profile = j.profile || {};
    j.profile.exit_type = "Normal";
    j.profile.exited_cleanly = true;
    fs.writeFileSync(p, JSON.stringify(j));
    console.error(`NOTE: marked clean Chrome exit in ${rel}`);
  } catch {
    /* missing / locked — ignore */
  }
}
NODE
  elif command -v taskkill.exe >/dev/null 2>&1; then
    # Only kill Chrome instances that expose CDP :9222 (leave normal browsing alone when possible).
    powershell.exe -NoProfile -Command \
      "Get-CimInstance Win32_Process -Filter \"name='chrome.exe'\" | Where-Object { \$_.CommandLine -match 'remote-debugging-port=9222' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }" \
      >/dev/null 2>&1 || true
  else
    bash "$ROOT/scripts/kill-chrome-cdp.sh" cdp || true
  fi
  # Confirm :9222 is actually down before relaunch (stale CDP fools reuse checks).
  for _i in 1 2 3 4 5 6 7 8; do
    if ! curl -fsS "http://127.0.0.1:9222/json/version" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  if curl -fsS "http://127.0.0.1:9222/json/version" >/dev/null 2>&1; then
    echo "WARNING: :9222 still up after kill — Playwright may attach to stale Chrome." >&2
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
  # Careers-only Hitech City: WARP SOCKS breaks Workday/Greenhouse hosts
  # (ERR_SOCKS_CONNECTION_FAILED) and LinkedIn auto-login only burns CAPTCHA time.
  if [[ "$portal" == "hitechcity" && "${HITECHCITY_CAREERS_ONLY:-}" =~ ^(1|true|yes)$ ]]; then
    export LINKEDIN_SKIP_WARP="${LINKEDIN_SKIP_WARP:-1}"
    export LINKEDIN_AUTO_LOGIN="${LINKEDIN_AUTO_LOGIN:-0}"
    export CDP_LIVE_LOGIN_CHECK="${CDP_LIVE_LOGIN_CHECK:-0}"
    echo "NOTE: HITECHCITY_CAREERS_ONLY — skip LinkedIn WARP + auto-login; career ATS uses direct IP."
  fi
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
    # NEVER write the .ps1 under Git Bash /tmp — powershell -File cannot open MSYS paths,
    # so Start-Process never runs and the readiness poll times out (false CDP_DOWN).
    mkdir -p "$ROOT/artifacts"
    ps_file="$ROOT/artifacts/_chrome_cdp_launch_${portal}.ps1"
    ps_file_win="$(cygpath -w "$ps_file" 2>/dev/null || echo "$ps_file")"
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
      # --disable-gpu can crash Chrome mid-CDP on some Windows home GPUs.
      echo "  '--disable-dev-shm-usage',"
      echo "  '--disable-extensions',"
      echo "  '--no-first-run',"
      echo "  '--no-default-browser-check',"
      echo "  '--disable-session-crashed-bubble',"
      echo "  '--hide-crash-restore-bubble',"
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
    echo "NOTE: launching Chrome via PowerShell -File $ps_file_win"
    if ! powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$ps_file_win"; then
      echo "WARNING: PowerShell -File launch failed — retrying inline Start-Process" >&2
      powershell.exe -NoProfile -Command \
        "Start-Process -FilePath '$chrome' -ArgumentList @('--no-sandbox','--disable-dev-shm-usage','--disable-extensions','--no-first-run','--no-default-browser-check','--disable-session-crashed-bubble','--hide-crash-restore-bubble','--remote-debugging-address=127.0.0.1','--remote-debugging-port=9222','--remote-allow-origins=*','--user-data-dir=$profile','--profile-directory=${CHROME_PROFILE_DIRECTORY:-Default}','about:blank')" \
        || true
    fi
  else
    nohup "$chrome" \
      "${headless[@]}" \
      "${proxy_args[@]}" \
      --no-sandbox \
      --disable-gpu \
      --disable-dev-shm-usage \
      --disable-extensions \
      --no-first-run \
      --no-default-browser-check \
      --disable-session-crashed-bubble \
      --hide-crash-restore-bubble \
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
# Windows system Chrome + Default profile can take >20s after taskkill.
for _ in range(90):
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

# Live-verify session for every portal (cookie names can outlive JWT / server invalidation).
# LinkedIn keeps Google SSO / password auto-heal; Hirist uses google_login.js; others fail closed.
live_rc=0
if [[ "${CDP_LIVE_LOGIN_CHECK:-1}" == "1" ]] && command -v node >/dev/null 2>&1; then
  export NODE_PATH="$ROOT/tools/node_modules${NODE_PATH:+:$NODE_PATH}"
  waiter=""
  case "$portal" in
    linkedin|hitechcity) waiter="$ROOT/tools/linkedin/wait_for_cdp_login.js" ;;
    naukri) waiter="$ROOT/tools/naukri/wait_for_cdp_login.js" ;;
    foundit) waiter="$ROOT/tools/foundit/wait_for_cdp_login.js" ;;
    cutshort) waiter="$ROOT/tools/cutshort/wait_for_cdp_login.js" ;;
    instahyre) waiter="$ROOT/tools/instahyre/wait_for_cdp_login.js" ;;
    hirist) waiter="$ROOT/tools/hirist/wait_for_cdp_login.js" ;;
    indeed) waiter="$ROOT/tools/indeed/wait_for_cdp_login.js" ;;
  esac

  if [[ -n "$waiter" && -f "$waiter" ]]; then
    wait_sec=0
    case "$portal" in
      linkedin|hitechcity) wait_sec="${LINKEDIN_LOGIN_WAIT_SEC:-0}" ;;
      naukri) wait_sec="${NAUKRI_LOGIN_WAIT_SEC:-0}" ;;
      foundit) wait_sec="${FOUNDIT_LOGIN_WAIT_SEC:-0}" ;;
      cutshort) wait_sec="${CUTSHORT_LOGIN_WAIT_SEC:-0}" ;;
      instahyre) wait_sec="${INSTAHYRE_LOGIN_WAIT_SEC:-0}" ;;
      hirist) wait_sec="${HIRIST_LOGIN_WAIT_SEC:-0}" ;;
      indeed) wait_sec="${INDEED_LOGIN_WAIT_SEC:-0}" ;;
    esac
    set +e
    if [[ "$wait_sec" -gt 0 ]]; then
      node "$waiter" --open-login --wait "$wait_sec"
      live_rc=$?
    else
      node "$waiter" --open-login
      live_rc=$?
    fi
    set -e

    # --- Auto-heal hooks ---
    if [[ "$live_rc" -ne 0 && ( "$portal" == "linkedin" || "$portal" == "hitechcity" ) ]]; then
      echo "WARNING: LinkedIn CDP not logged in (live check exit $live_rc)." >&2
      if [[ "${LINKEDIN_AUTO_LOGIN:-1}" == "1" && -f "$ROOT/tools/linkedin/auto_login.py" ]]; then
        echo "Attempting unattended LinkedIn auto-login…"
        PY="$(bash "$ROOT/scripts/resolve-python.sh")"
        export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
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
          echo "NOTE: auto-login exit $auto_rc (5=login required, 6=CAPTCHA/checkpoint, 7=temporary restriction)." >&2
          if [[ "$auto_rc" -eq 7 ]]; then
            echo "NOTE: Temporary LinkedIn restriction — runners will skip LI until lift time." >&2
          fi
        fi
      fi
    fi

    if [[ "$live_rc" -ne 0 && "$portal" == "hirist" && "${HIRIST_AUTO_LOGIN:-1}" == "1" ]]; then
      if [[ -f "$ROOT/tools/hirist/google_login.js" ]]; then
        echo "Attempting Hirist Google SSO auto-login…"
        set +e
        node "$ROOT/tools/hirist/google_login.js"
        auto_rc=$?
        set -e
        if [[ "$auto_rc" -eq 0 ]]; then
          node "$ROOT/tools/hirist/wait_for_cdp_login.js"
          live_rc=$?
          if [[ "$live_rc" -eq 0 ]]; then
            bash "$ROOT/scripts/refresh-portal-session-seed.sh" hirist || true
          fi
        fi
      fi
    fi

    if [[ "$live_rc" -eq 0 ]]; then
      seed_portal="$portal"
      [[ "$portal" == "hitechcity" ]] && seed_portal="linkedin"
      refresh_seed="${PORTAL_REFRESH_SEED:-1}"
      if [[ "$seed_portal" == "linkedin" && -n "${LINKEDIN_REFRESH_SEED:-}" ]]; then
        refresh_seed="${LINKEDIN_REFRESH_SEED}"
      fi
      if [[ "$refresh_seed" == "1" ]]; then
        case "$seed_portal" in
          linkedin|naukri|foundit|cutshort|instahyre|indeed|hirist)
            bash "$ROOT/scripts/refresh-portal-session-seed.sh" "$seed_portal" || true
            ;;
        esac
      fi
    else
      echo "WARNING: $portal CDP not logged in (live check exit $live_rc)." >&2
      echo "         Sign in once: bash scripts/home-headed-login.sh ${portal}" >&2
      echo "         Then: bash scripts/refresh-portal-session-seed.sh ${portal} && Save Snapshot" >&2
      # Hard-fail when required (default for apply portals). Hitechcity careers may continue.
      if [[ "${CDP_REQUIRE_LIVE_LOGIN:-1}" == "1" ]]; then
        if [[ "$portal" == "hitechcity" ]]; then
          echo "NOTE: Continuing hitechcity CDP for career-portal applies (LinkedIn blocked)." >&2
          if [[ "${HITECHCITY_CAREERS_NO_WARP:-1}" == "1" && ${#proxy_args[@]} -gt 0 ]]; then
            echo "NOTE: Relaunching Chrome without WARP for career-portal applies." >&2
            bash "$ROOT/scripts/kill-chrome-cdp.sh" cdp || true
            sleep 1
            nohup "$chrome" \
              "${headless[@]}" \
              --no-sandbox \
              --disable-gpu \
              --disable-dev-shm-usage \
              --disable-extensions \
              --remote-debugging-address=127.0.0.1 \
              --remote-debugging-port=9222 \
              --remote-allow-origins='*' \
              --user-data-dir="$profile" \
              "${profile_dir_args[@]}" \
              about:blank >>"$log" 2>&1 &
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
print(f"ERROR: Chrome CDP did not become ready after no-WARP relaunch: {last}", file=sys.stderr)
raise SystemExit(1)
PY
          fi
        else
          echo "ERROR: CDP_REQUIRE_LIVE_LOGIN=1 — refusing to continue without a live $portal session." >&2
          exit "$live_rc"
        fi
      fi
    fi
  fi
fi
