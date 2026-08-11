# Install Windows Task Scheduler job for Indeed home daily.
# Run in PowerShell (as your user) from the MyRepo checkout:
#   powershell -ExecutionPolicy Bypass -File scripts\install-indeed-home-task.ps1
# Optional: -Time "09:00"
param(
  [string]$Time = "09:00",
  [string]$TaskName = "IndeedHomeDaily"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Script = Join-Path $Root "scripts\indeed-home-daily.sh"

# Prefer Git Bash if present
$Bash = @(
  "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe",
  "C:\Program Files\Git\bin\bash.exe",
  "$env:ProgramFiles\Git\bin\bash.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

if (-not $Bash) {
  throw "Git Bash not found. Install Git for Windows. Prefer: powershell -File scripts\install-all-home-tasks.ps1"
}

$Action = New-ScheduledTaskAction -Execute $Bash -Argument "`"$Script`"" -WorkingDirectory "$Root"
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Force | Out-Null

Write-Host "Installed scheduled task '$TaskName' daily at $Time"
Write-Host "Prereqs: prefer WSL Ubuntu for Cursor Agent worker (native Windows worker is broken Aug 2026:"
Write-Host "  better-sqlite3 NODE_MODULE_VERSION 127 vs 137)."
Write-Host "  Fix: powershell -ExecutionPolicy Bypass -File scripts\fix-windows-agent-worker.ps1 -LaunchWsl"
Write-Host "  Or native CLI only: irm 'https://cursor.com/install?win32=true' | iex , then agent login"
Write-Host "Test: bash `"$Script`""
Write-Host "Remove: Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"
