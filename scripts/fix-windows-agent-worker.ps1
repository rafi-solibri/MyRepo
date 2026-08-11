# Diagnose / unblock Cursor Agent private worker on Windows.
# Native Windows `agent worker start` currently crashes with better-sqlite3
# NODE_MODULE_VERSION 127 vs 137 (Cursor packaging bug — reinstall will NOT fix).
#
# Run in PowerShell (not ISE bash pipe):
#   powershell -ExecutionPolicy Bypass -File scripts\fix-windows-agent-worker.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\fix-windows-agent-worker.ps1 -WorkerName job-apply-laptop
#   powershell -ExecutionPolicy Bypass -File scripts\fix-windows-agent-worker.ps1 -LaunchWsl
param(
  [string]$WorkerName = "job-apply-laptop",
  [switch]$LaunchWsl,
  [switch]$TryNativeReinstall
)

$ErrorActionPreference = "Continue"
$AgentRoot = Join-Path $env:LOCALAPPDATA "cursor-agent"
$BetterSqlite = Join-Path $AgentRoot "node_modules\better-sqlite3\build\Release\better_sqlite3.node"

Write-Host "=== Cursor Agent Windows worker repair ==="
Write-Host "Worker name: $WorkerName"
Write-Host "Agent root:  $AgentRoot"
Write-Host ""

function Test-Wsl {
  try {
    $out = & wsl -l -q 2>$null
    return ($LASTEXITCODE -eq 0 -and $out)
  } catch {
    return $false
  }
}

function Show-KnownBug {
  Write-Host @"
KNOWN BUG (Cursor Windows agent package, Aug 2026):
  better_sqlite3.node compiled for NODE_MODULE_VERSION 127 (Node 22)
  but the bundled runtime expects NODE_MODULE_VERSION 137 (Node 24).

  Cursor staff confirmed: reinstall / cache wipe does NOT fix this.
  Forum: https://forum.cursor.com/t/windows-remote-control-worker-crashes-better-sqlite3-node-module-version-127-vs-137-cursor-3-15-6/167841

OFFICIAL WORKAROUND — run the worker under WSL (Linux build is fine):
  1) wsl --install -d Ubuntu          # once; reboot if prompted
  2) Open Ubuntu (WSL), then:
       curl -fsSL https://cursor.com/install | bash
       agent login
       # clone onto Linux FS — NOT /mnt/c
       git clone https://github.com/rafi-solibri/MyRepo.git ~/MyRepo
       cd ~/MyRepo && git checkout main && git pull
       bash scripts/setup-wsl-agent-worker.sh --name $WorkerName
  3) Leave that WSL terminal open. In https://cursor.com/agents pick machine '$WorkerName'.

WRONG (what broke in PowerShell ISE):
  curl https://cursor.com/install -fsS | bash     # Linux installer in Windows host
RIGHT for native Windows CLI (still broken for workers until Cursor ships a fix):
  irm 'https://cursor.com/install?win32=true' | iex
"@
}

if (-not (Test-Path $AgentRoot)) {
  Write-Host "No $AgentRoot found — Cursor Agent CLI not installed for this user."
  Show-KnownBug
  if ($LaunchWsl) {
    if (Test-Wsl) {
      Write-Host "Launching WSL Ubuntu for setup…"
      wsl -d Ubuntu -- bash -lc "curl -fsSL https://cursor.com/install | bash; echo; echo 'Now: agent login && git clone https://github.com/rafi-solibri/MyRepo.git ~/MyRepo && bash ~/MyRepo/scripts/setup-wsl-agent-worker.sh --name $WorkerName'"
    } else {
      Write-Host "WSL not installed. Run (Admin PowerShell): wsl --install -d Ubuntu"
      exit 1
    }
  }
  exit 1
}

Write-Host "Installed agent tree found."
if (Test-Path $BetterSqlite) {
  Write-Host "Found native module: $BetterSqlite"
} else {
  Write-Host "WARNING: better_sqlite3.node missing (incomplete install)."
}

$agentCmd = Get-Command agent -ErrorAction SilentlyContinue
if ($agentCmd) {
  Write-Host "agent on PATH: $($agentCmd.Source)"
  try { & agent --version } catch { Write-Host "agent --version failed: $_" }
} else {
  $localAgent = Join-Path $AgentRoot "agent.ps1"
  if (Test-Path $localAgent) {
    Write-Host "agent.ps1 present: $localAgent (not necessarily on PATH)"
  } else {
    Write-Host "WARNING: 'agent' not on PATH."
  }
}

Write-Host ""
Show-KnownBug

if ($TryNativeReinstall) {
  Write-Host ""
  Write-Host "Attempting native Windows reinstall (likely will NOT fix ABI mismatch)…"
  try {
    irm 'https://cursor.com/install?win32=true' | iex
  } catch {
    Write-Host "Reinstall failed: $_"
  }
  Write-Host "If worker still fails with NODE_MODULE_VERSION 127/137, use WSL."
}

if ($LaunchWsl) {
  Write-Host ""
  if (-not (Test-Wsl)) {
    Write-Host "WSL missing. Install once (Admin PowerShell), then reboot if asked:"
    Write-Host "  wsl --install -d Ubuntu"
    exit 1
  }
  Write-Host "Opening WSL to run Linux worker setup…"
  $cmd = @"
set -e
export PATH=`$HOME/.local/bin:`$HOME/.cursor/bin:`$PATH
if ! command -v agent >/dev/null 2>&1; then
  curl -fsSL https://cursor.com/install | bash
  export PATH=`$HOME/.local/bin:`$HOME/.cursor/bin:`$PATH
fi
if [[ ! -d `$HOME/MyRepo/.git ]]; then
  git clone https://github.com/rafi-solibri/MyRepo.git `$HOME/MyRepo
fi
cd `$HOME/MyRepo
git fetch origin main && git checkout main && git pull --ff-only origin main || true
bash scripts/setup-wsl-agent-worker.sh --name $WorkerName
"@
  wsl -d Ubuntu -- bash -lc $cmd
  exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Quick unblock from this Windows shell:"
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\fix-windows-agent-worker.ps1 -LaunchWsl"
Write-Host "Or open Ubuntu WSL and run:"
Write-Host "  bash ~/MyRepo/scripts/setup-wsl-agent-worker.sh --name $WorkerName"
