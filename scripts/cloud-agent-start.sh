#!/usr/bin/env bash
# Per-boot start hook for the job-apply automation Cloud Agent environment.
#
# Lifecycle split (see automation-prompts/ENV_READINESS.md):
#   install (scripts/cloud-agent-install.sh) builds the DURABLE baseline once —
#     Python + Playwright + Chromium, resume assets, npm tooling, CDP profile dirs.
#     With environment builds it runs at build time and is NOT re-run per pod.
#   start (this script) runs on EVERY boot to reconcile ephemeral session state:
#     copy the authenticated Desktop Chrome (Default) logins into each portal CDP
#     profile so the daily cron automations do not boot into empty profiles and
#     hit login walls.
#
# Must never block a boot: no `set -e`; the session sync is best-effort and only
# runs when Desktop Chrome has a Default cookie DB to copy from.
set -uo pipefail
cd "$(dirname "$0")/.."

if [[ -f /home/ubuntu/.config/google-chrome/Default/Cookies ]]; then
  bash scripts/sync-chrome-sessions.sh || echo "start: session sync failed (non-fatal); continuing boot."
else
  echo "start: no Desktop Chrome Default cookies yet; skipping session sync."
  echo "start: log into the portals in Desktop Chrome, then Save/Update the environment snapshot."
fi

echo "start: ready."
