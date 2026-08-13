#!/usr/bin/env bash
# Source optional job-apply secrets into the current shell (never prints values).
#
# Search order (first existing file wins):
#   1) $JOB_APPLY_SECRETS_FILE
#   2) $ROOT/.cursor/job-apply-secrets.env   (gitignored)
#   3) ~/.cursor/job-apply-secrets.env
#
# Usage (must be sourced, not executed):
#   source scripts/load-job-secrets.sh
#
# Cursor Cloud Automations should ALSO set the same keys as Environment Secrets
# so cron pods get them without relying on a snapshot file:
#   LINKEDIN_EMAIL, LINKEDIN_PASSWORD, NAUKRI_WORKDAY_PASSWORD, RESEND_*, …
set -uo pipefail

_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_candidates=()
[[ -n "${JOB_APPLY_SECRETS_FILE:-}" ]] && _candidates+=("${JOB_APPLY_SECRETS_FILE}")
_candidates+=("$_ROOT/.cursor/job-apply-secrets.env")
_candidates+=("${HOME}/.cursor/job-apply-secrets.env")

_loaded=""
for _f in "${_candidates[@]}"; do
  if [[ -f "$_f" ]]; then
    # shellcheck disable=SC1090
    set -a
    # shellcheck disable=SC1090
    source "$_f"
    set +a
    _loaded="$_f"
    break
  fi
done

if [[ -n "$_loaded" && "${JOB_APPLY_SECRETS_VERBOSE:-0}" == "1" ]]; then
  echo "load-job-secrets: loaded $_loaded" >&2
fi
unset _ROOT _candidates _f _loaded
