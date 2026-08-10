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
  "C:\Program Files\Git\bin\bash.exe",
  "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe",
  "bash"
) | Where-Object { $_ -eq "bash" -or (Test-Path $_) } | Select-Object -First 1

if (-not $Bash) {
  throw "Git Bash not found. Install Git for Windows, or run scripts/indeed-home-daily.sh from WSL."
}

$Action = New-ScheduledTaskAction -Execute $Bash -Argument "`"$Script`"" -WorkingDirectory "$Root"
$Trigger = New-ScheduledTaskTrigger -Daily -At $Time
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Force | Out-Null

Write-Host "Installed scheduled task '$TaskName' daily at $Time"
Write-Host "Prereqs: install Cursor CLI (irm 'https://cursor.com/install?win32=true' | iex), then: agent login"
Write-Host "Test: bash `"$Script`""
Write-Host "Remove: Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"
