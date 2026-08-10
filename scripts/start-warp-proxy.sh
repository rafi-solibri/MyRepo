#!/usr/bin/env bash
# Start Cloudflare WARP in SOCKS5 proxy mode on 127.0.0.1:40000.
#
# IMPORTANT: Never enable full-tunnel WARP (mode warp / warp+doh) on a cloud
# agent — it can blackhole SSH/agent networking. Proxy mode only.
#
# Usage:
#   bash scripts/start-warp-proxy.sh          # start + connect
#   bash scripts/start-warp-proxy.sh status   # print status / port check
#   bash scripts/start-warp-proxy.sh stop     # disconnect (leaves warp-svc up)
set -euo pipefail

PORT="${WARP_PROXY_PORT:-40000}"
SOCKS="socks5h://127.0.0.1:${PORT}"
LOG="${WARP_SVC_LOG:-/tmp/cursor/warp-svc.log}"
mkdir -p /tmp/cursor

cmd="${1:-start}"

have_cli() { command -v warp-cli >/dev/null 2>&1; }
have_svc() { command -v warp-svc >/dev/null 2>&1; }

port_open() {
  python3 - <<PY
import socket
s=socket.socket(); s.settimeout(1.5)
try:
  s.connect(("127.0.0.1", int("${PORT}")))
  print("open")
except Exception:
  print("closed")
finally:
  s.close()
PY
}

ensure_warp_installed() {
  if have_cli && have_svc; then return 0; fi
  echo "Installing cloudflare-warp..."
  curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg \
    | sudo gpg --yes --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
  echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" \
    | sudo tee /etc/apt/sources.list.d/cloudflare-client.list >/dev/null
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y cloudflare-warp
}

ensure_warp_svc() {
  if pgrep -x warp-svc >/dev/null 2>&1; then return 0; fi
  # No systemd in many Cursor cloud pods — run the daemon directly.
  if command -v systemctl >/dev/null 2>&1 && systemctl list-units >/dev/null 2>&1; then
    sudo systemctl enable --now warp-svc 2>/dev/null || true
  fi
  if pgrep -x warp-svc >/dev/null 2>&1; then return 0; fi
  echo "Starting warp-svc (no systemd)..."
  nohup sudo warp-svc >"$LOG" 2>&1 &
  for _ in $(seq 1 40); do
    if warp-cli --accept-tos status >/dev/null 2>&1; then return 0; fi
    sleep 0.25
  done
  echo "ERROR: warp-svc did not become ready; see $LOG" >&2
  return 1
}

configure_and_connect() {
  # Proxy mode MUST be set before connect.
  warp-cli --accept-tos mode proxy
  warp-cli --accept-tos proxy port "$PORT"
  if ! warp-cli --accept-tos registration show >/dev/null 2>&1; then
    warp-cli --accept-tos registration new
  fi
  warp-cli --accept-tos connect
  for _ in $(seq 1 40); do
    if [[ "$(port_open)" == "open" ]]; then
      return 0
    fi
    sleep 0.25
  done
  echo "ERROR: SOCKS port 127.0.0.1:${PORT} not listening" >&2
  warp-cli --accept-tos status || true
  return 1
}

print_status() {
  echo "WARP_PROXY=${SOCKS}"
  if have_cli; then
    warp-cli --accept-tos status || true
  else
    echo "warp-cli: missing"
  fi
  echo "port_${PORT}=$(port_open)"
  if [[ "$(port_open)" == "open" ]]; then
    curl -sS --max-time 20 -x "$SOCKS" https://www.cloudflare.com/cdn-cgi/trace || true
  fi
}

case "$cmd" in
  status)
    print_status
    ;;
  stop)
    have_cli && warp-cli --accept-tos disconnect || true
    print_status
    ;;
  start)
    ensure_warp_installed
    ensure_warp_svc
    configure_and_connect
    print_status
    echo "Ready: export INDEED_HTTP_PROXY=${SOCKS}"
    ;;
  *)
    echo "Usage: $0 [start|status|stop]" >&2
    exit 2
    ;;
esac
