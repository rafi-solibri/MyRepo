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
#   LINKEDIN_EMAIL, LINKEDIN_PASSWORD, GOOGLE_EMAIL, GOOGLE_PASSWORD,
#   NAUKRI_WORKDAY_PASSWORD, RESEND_*,
#   CAPSOLVER_API_KEY or TWOCAPTCHA_API_KEY — optional paid solvers.
#   Free path: bash scripts/home-headed-careers-apply.sh (you click hCaptcha).
# GOOGLE_PASSWORD is the Gmail/Google account password used for SSO; when set it
# also fills LINKEDIN_PASSWORD if that key is empty (same account for many owners).
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

# Owner sets one password / email (NAUKRI_WORKDAY_PASSWORD + LINKEDIN_EMAIL).
# Alias so every ATS helper that reads WORKDAY_PASSWORD / APPLY_EMAIL sees them.
if [[ -z "${WORKDAY_PASSWORD:-}" ]]; then
  WORKDAY_PASSWORD="${NAUKRI_WORKDAY_PASSWORD:-${ATS_PASSWORD:-${NAUKRI_ATS_PASSWORD:-${LINKEDIN_PASSWORD:-}}}}"
  export WORKDAY_PASSWORD
fi
if [[ -z "${ATS_PASSWORD:-}" && -n "${WORKDAY_PASSWORD:-}" ]]; then
  ATS_PASSWORD="$WORKDAY_PASSWORD"
  export ATS_PASSWORD
fi
if [[ -z "${APPLY_EMAIL:-}" ]]; then
  APPLY_EMAIL="${NAUKRI_APPLY_EMAIL:-${LINKEDIN_EMAIL:-${GOOGLE_EMAIL:-}}}"
  export APPLY_EMAIL
fi
if [[ -z "${NAUKRI_APPLY_EMAIL:-}" && -n "${APPLY_EMAIL:-}" ]]; then
  NAUKRI_APPLY_EMAIL="$APPLY_EMAIL"
  export NAUKRI_APPLY_EMAIL
fi
# Google account password (Gmail SSO) — alias into LINKEDIN_PASSWORD when unset.
if [[ -z "${LINKEDIN_PASSWORD:-}" && -n "${GOOGLE_PASSWORD:-}" ]]; then
  LINKEDIN_PASSWORD="$GOOGLE_PASSWORD"
  export LINKEDIN_PASSWORD
fi
if [[ -z "${GOOGLE_PASSWORD:-}" && -n "${LINKEDIN_PASSWORD:-}" ]]; then
  GOOGLE_PASSWORD="$LINKEDIN_PASSWORD"
  export GOOGLE_PASSWORD
fi
if [[ -z "${LINKEDIN_EMAIL:-}" && -n "${GOOGLE_EMAIL:-}" ]]; then
  LINKEDIN_EMAIL="$GOOGLE_EMAIL"
  export LINKEDIN_EMAIL
fi
if [[ -z "${GOOGLE_EMAIL:-}" && -n "${LINKEDIN_EMAIL:-}" ]]; then
  GOOGLE_EMAIL="$LINKEDIN_EMAIL"
  export GOOGLE_EMAIL
fi

unset _ROOT _candidates _f _loaded
