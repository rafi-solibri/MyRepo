#!/usr/bin/env bash
# Per-boot start hook for the job-apply automation Cloud Agent environment.
#
# Lifecycle split (see automation-prompts/ENV_READINESS.md):
#   install (scripts/cloud-agent-install.sh) builds the DURABLE baseline once —
#     Python + Playwright + Chromium, resume assets, npm tooling, CDP profile dirs.
#     With environment builds it runs at build time and is NOT re-run per pod.
#   start (this script) runs on EVERY boot to reconcile ephemeral session state:
#     restore the .portal-sessions seed when Default Chrome lacks auth, then copy
#     Desktop Default logins into each portal CDP profile.
#
# Must never block a boot: no `set -e`; restore/sync are best-effort.
set -uo pipefail
cd "$(dirname "$0")/.."

bash scripts/restore-portal-sessions.sh || echo "start: session restore failed (non-fatal); continuing boot."

if [[ -f /home/ubuntu/.config/google-chrome/Default/Cookies ]]; then
  bash scripts/sync-chrome-sessions.sh || echo "start: session sync failed (non-fatal); continuing boot."
else
  echo "start: no Desktop Chrome Default cookies yet; skipping session sync."
  echo "start: seed .portal-sessions or log into portals in Desktop Chrome, then Save snapshot."
fi

echo "start: ready."
