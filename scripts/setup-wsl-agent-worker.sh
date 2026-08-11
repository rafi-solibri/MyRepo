#!/usr/bin/env bash
# One-time + daily helper: install Cursor Agent CLI inside WSL and start a
# My Machines private worker. Use this when native Windows `agent worker start`
# fails with better-sqlite3 NODE_MODULE_VERSION 127 vs 137 (known Cursor bug).
#
# Run INSIDE Ubuntu WSL (not PowerShell, not /mnt/c):
#   bash scripts/setup-wsl-agent-worker.sh
#   bash scripts/setup-wsl-agent-worker.sh --name job-apply-laptop
#   bash scripts/setup-wsl-agent-worker.sh --start-only --name job-apply-laptop
set -euo pipefail

WORKER_NAME="job-apply-laptop"
REPO_URL="${REPO_URL:-https://github.com/rafi-solibri/MyRepo.git}"
REPO_DIR="${REPO_DIR:-$HOME/MyRepo}"
START_ONLY=0
SKIP_CLONE=0

usage() {
  cat <<'EOF'
Usage: bash scripts/setup-wsl-agent-worker.sh [options]

Options:
  --name <worker>     Worker name shown in Cursor My Machines (default: job-apply-laptop)
  --repo-dir <path>   Clone/checkout path on the Linux filesystem (default: ~/MyRepo)
  --repo-url <url>    Git remote (default: https://github.com/rafi-solibri/MyRepo.git)
  --start-only        Skip install/clone; just start the worker from --repo-dir
  --skip-clone        Assume repo already exists at --repo-dir
  -h, --help          Show this help

IMPORTANT:
  - Run this from WSL Ubuntu, not Windows PowerShell ISE.
  - Keep the repo under ~/… (Linux FS). Do NOT use /mnt/c/… for the worker cwd.
  - Native Windows agent install is currently broken for workers; WSL is the workaround.
  - Leave the terminal open while the worker runs.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) WORKER_NAME="${2:?}"; shift 2 ;;
    --repo-dir) REPO_DIR="${2:?}"; shift 2 ;;
    --repo-url) REPO_URL="${2:?}"; shift 2 ;;
    --start-only) START_ONLY=1; shift ;;
    --skip-clone) SKIP_CLONE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if grep -qi microsoft /proc/version 2>/dev/null; then
  echo "OK: running under WSL"
else
  echo "WARNING: /proc/version does not look like WSL. Continue only if this is Linux."
fi

case "$(pwd -P)" in
  /mnt/*)
    echo "WARNING: current directory is under /mnt (Windows drive)."
    echo "Worker cwd will be forced to Linux path: $REPO_DIR"
    ;;
esac

find_agent() {
  if command -v agent >/dev/null 2>&1; then
    command -v agent
    return 0
  fi
  for p in "$HOME/.local/bin/agent" "$HOME/.cursor/bin/agent"; do
    if [[ -x "$p" ]]; then
      echo "$p"
      return 0
    fi
  done
  return 1
}

ensure_path() {
  mkdir -p "$HOME/.local/bin"
  export PATH="$HOME/.local/bin:$HOME/.cursor/bin:$PATH"
  if [[ -f "$HOME/.bashrc" ]] && ! grep -q '.local/bin' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$HOME/.cursor/bin:$PATH"' >>"$HOME/.bashrc"
  fi
}

install_agent() {
  ensure_path
  if find_agent >/dev/null; then
    echo "Cursor Agent already installed: $(find_agent)"
    agent --version || true
    return 0
  fi
  echo "Installing Cursor Agent CLI (Linux)…"
  curl -fsSL https://cursor.com/install | bash
  ensure_path
  hash -r 2>/dev/null || true
  if ! find_agent >/dev/null; then
    echo "ERROR: install finished but 'agent' is not on PATH."
    echo "Open a new WSL shell, or: export PATH=\"\$HOME/.local/bin:\$HOME/.cursor/bin:\$PATH\""
    exit 127
  fi
  agent --version
}

ensure_repo() {
  if [[ -d "$REPO_DIR/.git" ]]; then
    echo "Repo present: $REPO_DIR"
    git -C "$REPO_DIR" fetch origin main
    git -C "$REPO_DIR" checkout main
    git -C "$REPO_DIR" pull --ff-only origin main || true
    return 0
  fi
  if [[ "$SKIP_CLONE" -eq 1 ]]; then
    echo "ERROR: --skip-clone set but $REPO_DIR is not a git repo." >&2
    exit 1
  fi
  echo "Cloning $REPO_URL → $REPO_DIR"
  mkdir -p "$(dirname "$REPO_DIR")"
  git clone "$REPO_URL" "$REPO_DIR"
  git -C "$REPO_DIR" checkout main
}

login_hint() {
  if [[ -n "${CURSOR_API_KEY:-}" ]]; then
    echo "CURSOR_API_KEY is set — unattended auth OK."
    return 0
  fi
  echo "If not logged in yet, run once (interactive browser/device flow):"
  echo "  agent login"
}

start_worker() {
  ensure_path
  local agent_bin
  agent_bin="$(find_agent)" || {
    echo "ERROR: agent CLI missing. Re-run without --start-only." >&2
    exit 127
  }
  if [[ ! -d "$REPO_DIR/.git" ]]; then
    echo "ERROR: repo missing at $REPO_DIR" >&2
    exit 1
  fi
  case "$REPO_DIR" in
    /mnt/*)
      echo "ERROR: repo is on /mnt (Windows FS). Copy/clone to ~/MyRepo and re-run." >&2
      exit 1
      ;;
  esac
  cd "$REPO_DIR"
  login_hint
  echo "Starting worker '$WORKER_NAME' from $REPO_DIR …"
  echo "Leave this terminal open. Tip: add --verbose if it exits immediately."
  exec "$agent_bin" worker start --name "$WORKER_NAME"
}

if [[ "$START_ONLY" -eq 1 ]]; then
  start_worker
fi

install_agent
if [[ "$SKIP_CLONE" -eq 0 ]]; then
  ensure_repo
else
  [[ -d "$REPO_DIR/.git" ]] || { echo "ERROR: missing $REPO_DIR"; exit 1; }
fi
login_hint
echo
echo "Next:"
echo "  1) agent login   # if needed"
echo "  2) bash $REPO_DIR/scripts/setup-wsl-agent-worker.sh --start-only --name $WORKER_NAME"
echo
read -r -p "Start worker '$WORKER_NAME' now? [Y/n] " ans || ans=Y
ans="${ans:-Y}"
if [[ "$ans" =~ ^[Yy]$ ]]; then
  start_worker
fi
