#!/usr/bin/env bash
# Kill Chrome/Chromium processes safely without matching agent bash wrappers.
# pkill -f "chrome" / pkill -f "remote-debugging-port=9222" matches the
# launching shell's command line and aborts portal preflight/CDP launch mid-run.
set -euo pipefail

mode="${1:-cdp}" # cdp | all

is_chrome_exe() {
  local pid="$1"
  local exe
  exe="$(readlink -f "/proc/$pid/exe" 2>/dev/null || true)"
  case "$exe" in
    */chrome|*/chrome-bin|*/google-chrome|*/google-chrome-stable|*/chromium|*/chromium-browser)
      return 0
      ;;
  esac
  # Windows Git Bash / WSL: exe symlink may be unavailable; fall back to comm.
  local comm
  comm="$(ps -p "$pid" -o comm= 2>/dev/null | tr -d ' ' || true)"
  case "$comm" in
    chrome|chrome.exe|google-chrome|google-chrome-stable|chromium|chromium-browser)
      return 0
      ;;
  esac
  return 1
}

cmdline_has() {
  local pid="$1" needle="$2"
  tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null | grep -Fq -- "$needle"
}

killed=0
for pid in /proc/[0-9]*; do
  pid="${pid#/proc/}"
  [[ "$pid" =~ ^[0-9]+$ ]] || continue
  is_chrome_exe "$pid" || continue
  if [[ "$mode" == "cdp" ]]; then
    cmdline_has "$pid" "remote-debugging-port=9222" || continue
  fi
  kill "$pid" 2>/dev/null || true
  killed=$((killed + 1))
done

# Give Chrome a moment to release profile locks.
if [[ "$killed" -gt 0 ]]; then
  sleep 1
fi
exit 0
