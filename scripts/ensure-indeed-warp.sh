#!/usr/bin/env bash
# Ensure Cloudflare WARP SOCKS proxy is up for Indeed cloud bypass.
#
# Usage:
#   eval "$(bash scripts/ensure-indeed-warp.sh)"
#   # → INDEED_HTTP_PROXY=socks5://127.0.0.1:40000
#
# If INDEED_HTTP_PROXY is already set to a non-local proxy, leaves it alone
# and prints that export.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${WARP_PROXY_PORT:-40000}"
LOCAL="socks5://127.0.0.1:${PORT}"

if [[ -n "${INDEED_HTTP_PROXY:-}" && "${INDEED_HTTP_PROXY}" != *"127.0.0.1:${PORT}"* && "${INDEED_HTTP_PROXY}" != *"localhost:${PORT}"* ]]; then
  printf 'export INDEED_HTTP_PROXY=%q\n' "${INDEED_HTTP_PROXY}"
  exit 0
fi

mkdir -p /tmp/cursor
bash "$ROOT/scripts/start-warp-proxy.sh" start >/tmp/cursor/warp-proxy-start.log 2>&1 || {
  echo "ERROR: WARP SOCKS failed to start; see /tmp/cursor/warp-proxy-start.log" >&2
  exit 1
}

printf 'export INDEED_HTTP_PROXY=%q\n' "$LOCAL"
