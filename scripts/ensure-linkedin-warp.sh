#!/usr/bin/env bash
# Ensure Cloudflare WARP SOCKS proxy is up for LinkedIn cloud CAPTCHA bypass.
#
# Usage:
#   eval "$(bash scripts/ensure-linkedin-warp.sh)"
#   # → LINKEDIN_HTTP_PROXY=socks5://127.0.0.1:40000
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${WARP_PROXY_PORT:-40000}"
LOCAL="socks5://127.0.0.1:${PORT}"

if [[ -n "${LINKEDIN_HTTP_PROXY:-}" && "${LINKEDIN_HTTP_PROXY}" != *"127.0.0.1:${PORT}"* && "${LINKEDIN_HTTP_PROXY}" != *"localhost:${PORT}"* ]]; then
  printf 'export LINKEDIN_HTTP_PROXY=%q\n' "${LINKEDIN_HTTP_PROXY}"
  exit 0
fi

mkdir -p /tmp/cursor
bash "$ROOT/scripts/start-warp-proxy.sh" start >/tmp/cursor/warp-proxy-start.log 2>&1 || {
  echo "ERROR: WARP SOCKS failed to start; see /tmp/cursor/warp-proxy-start.log" >&2
  exit 1
}

printf 'export LINKEDIN_HTTP_PROXY=%q\n' "$LOCAL"
