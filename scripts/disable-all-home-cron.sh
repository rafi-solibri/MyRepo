#!/usr/bin/env bash
# Disable (remove) home-local job-apply cron entries on macOS / Linux / WSL.
#
# Usage:
#   bash scripts/disable-all-home-cron.sh
#   bash scripts/disable-all-home-cron.sh --what-if
set -euo pipefail

WHAT_IF=0
for arg in "$@"; do
  case "$arg" in
    --what-if|-n) WHAT_IF=1 ;;
    -h|--help)
      echo "Usage: bash scripts/disable-all-home-cron.sh [--what-if]"
      exit 0
      ;;
    *)
      echo "Unknown arg: $arg" >&2
      exit 2
      ;;
  esac
done

# Markers / patterns installed by this repo's home schedules.
PATTERNS=(
  'indeed-home-daily'
  'portal-home-daily'
  'notification-home-daily'
  'HomeDaily-'
  'job-apply-home'
)

existing="$(crontab -l 2>/dev/null || true)"
if [[ -z "${existing//[[:space:]]/}" ]]; then
  echo "No crontab for this user. Nothing to disable."
  exit 0
fi

filtered="$existing"
matched=0
for pat in "${PATTERNS[@]}"; do
  if printf '%s\n' "$filtered" | grep -Fq "$pat"; then
    matched=1
  fi
  filtered="$(printf '%s\n' "$filtered" | grep -vF "$pat" || true)"
done

# Drop PATH= helper lines that only existed for job-apply cron when no other
# jobs remain; otherwise keep them.
other_jobs="$(printf '%s\n' "$filtered" | grep -vE '^(#|$|PATH=)' || true)"
cleaned=""
while IFS= read -r line || [[ -n "$line" ]]; do
  if [[ -z "${other_jobs//[[:space:]]/}" ]] && [[ "$line" =~ ^PATH= ]] && \
     { [[ "$line" == *".cursor/bin"* ]] || [[ "$line" == *"cursor-agent"* ]]; }; then
    continue
  fi
  cleaned+="$line"$'\n'
done <<< "$filtered"
cleaned="$(printf '%s\n' "$cleaned" | awk 'NF{p=1} p' | awk 'BEGIN{n=0} {a[++n]=$0} END{while(n>0 && a[n]=="") n--; for(i=1;i<=n;i++) print a[i]}')"

if [[ "$matched" -eq 0 ]]; then
  echo "No home job-apply cron entries found."
  echo "Nothing to disable."
  exit 0
fi

echo "Home job-apply cron lines currently matching:"
printf '%s\n' "$existing" | grep -E 'indeed-home-daily|portal-home-daily|notification-home-daily|HomeDaily-|job-apply-home' || true
echo

if [[ "$WHAT_IF" -eq 1 ]]; then
  echo "[WhatIf] Would replace crontab with:"
  if [[ -z "${cleaned//[[:space:]]/}" ]]; then
    echo "  (empty crontab)"
  else
    printf '%s\n' "$cleaned"
  fi
  echo "Dry run only. Re-run without --what-if to apply."
  exit 0
fi

if [[ -z "${cleaned//[[:space:]]/}" ]]; then
  crontab -r 2>/dev/null || true
  echo "Removed all crontab entries for this user (only job-apply lines were present)."
else
  printf '%s\n' "$cleaned" | crontab -
  echo "Updated crontab. Remaining entries:"
  crontab -l
fi

echo
echo "Re-install Indeed-only cron later:"
echo "  bash scripts/install-indeed-home-cron.sh 09:00"
echo
echo "Note: Windows Task Scheduler home tasks are separate — on Windows run:"
echo "  powershell -ExecutionPolicy Bypass -File scripts\\disable-all-home-tasks.ps1"
echo
echo "Cursor cloud Automations stay as-is: https://cursor.com/automations"
