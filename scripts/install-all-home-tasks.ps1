# Install Windows Task Scheduler jobs for ALL home-local job automations.
# Replaces cloud Cursor Automations with local Cursor CLI (`agent`) runs.
#
# Run in PowerShell from the MyRepo checkout:
#   powershell -ExecutionPolicy Bypass -File scripts\install-all-home-tasks.ps1
#
# Optional:
#   -BaseTime "17:00"     # first portal start (local clock; default 5 PM)
#   -StaggerMinutes 20    # gap between portals
#   -NotificationTime "19:30"
param(
  [string]$BaseTime = "17:00",
  [int]$StaggerMinutes = 20,
  [string]$NotificationTime = "19:30"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")

function Find-GitBash {
  $candidates = @(
    "$env:LOCALAPPDATA\Programs\Git\bin\bash.exe",
    "C:\Program Files\Git\bin\bash.exe",
    "$env:ProgramFiles\Git\bin\bash.exe",
    "${env:ProgramFiles(x86)}\Git\bin\bash.exe"
  )
  foreach ($c in $candidates) {
    if ($c -and (Test-Path $c)) { return $c }
  }
  $cmd = Get-Command bash.exe -ErrorAction SilentlyContinue
  if ($cmd -and $cmd.Source -notmatch "WindowsApps|system32\\bash") {
    return $cmd.Source
  }
  return $null
}

$Bash = Find-GitBash
if (-not $Bash) {
  throw "Git Bash not found. Install Git for Windows, then re-run this script."
}

$AgentCmd = Join-Path $env:LOCALAPPDATA "cursor-agent\agent.cmd"
if (-not (Test-Path $AgentCmd)) {
  Write-Warning "Cursor agent CLI not found at $AgentCmd"
  Write-Host "Install: irm 'https://cursor.com/install?win32=true' | iex"
  Write-Host "Then run: agent login"
}

function Add-MinutesToTime([string]$Time, [int]$Minutes) {
  $dt = [DateTime]::ParseExact($Time, "HH:mm", $null)
  return $dt.AddMinutes($Minutes).ToString("HH:mm")
}

$Jobs = @(
  @{ Name = "HomeDaily-LinkedIn";   Portal = "linkedin";  Offset = 0 },
  @{ Name = "HomeDaily-Foundit";    Portal = "foundit";   Offset = 1 },
  @{ Name = "HomeDaily-Cutshort";   Portal = "cutshort";  Offset = 2 },
  @{ Name = "HomeDaily-Naukri";     Portal = "naukri";    Offset = 3 },
  @{ Name = "HomeDaily-Instahyre";  Portal = "instahyre"; Offset = 4 },
  @{ Name = "HomeDaily-Indeed";     Portal = "indeed";    Offset = 5 },
  @{ Name = "HomeDaily-HitechCity"; Portal = "hitechcity"; Offset = 6 }
)

$PortalScript = Join-Path $Root "scripts\portal-home-daily.sh"
$NotifScript = Join-Path $Root "scripts\notification-home-daily.sh"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 3)

Write-Host "Repo: $Root"
Write-Host "Bash: $Bash"
Write-Host ""

foreach ($job in $Jobs) {
  $time = Add-MinutesToTime $BaseTime ($job.Offset * $StaggerMinutes)
  $arg = "`"$PortalScript`" $($job.Portal)"
  $Action = New-ScheduledTaskAction -Execute $Bash -Argument $arg -WorkingDirectory "$Root"
  $Trigger = New-ScheduledTaskTrigger -Daily -At $time
  Register-ScheduledTask -TaskName $job.Name -Action $Action -Trigger $Trigger -Settings $Settings -Force | Out-Null
  Write-Host "Installed $($job.Name) daily at $time  (portal=$($job.Portal))"
}

# Also keep legacy IndeedHomeDaily pointing at the same runner (enabled).
$legacyArg = "`"$PortalScript`" indeed"
$legacyTime = Add-MinutesToTime $BaseTime (5 * $StaggerMinutes)
Register-ScheduledTask -TaskName "IndeedHomeDaily" `
  -Action (New-ScheduledTaskAction -Execute $Bash -Argument $legacyArg -WorkingDirectory "$Root") `
  -Trigger (New-ScheduledTaskTrigger -Daily -At $legacyTime) `
  -Settings $Settings -Force | Out-Null
Write-Host "Updated IndeedHomeDaily daily at $legacyTime (enabled)"

# Notification after last portal (hitechcity offset 6)
$notifDefault = Add-MinutesToTime $BaseTime (7 * $StaggerMinutes)
if (-not $PSBoundParameters.ContainsKey('NotificationTime')) {
  $NotificationTime = $notifDefault
}

$notifArg = "`"$NotifScript`""
Register-ScheduledTask -TaskName "HomeDaily-Notification" `
  -Action (New-ScheduledTaskAction -Execute $Bash -Argument $notifArg -WorkingDirectory "$Root") `
  -Trigger (New-ScheduledTaskTrigger -Daily -At $NotificationTime) `
  -Settings $Settings -Force | Out-Null
Write-Host "Installed HomeDaily-Notification daily at $NotificationTime"

Write-Host ""
Write-Host "Prereqs:"
Write-Host "  1) agent login   (or set CURSOR_API_KEY user env var for unattended runs)"
Write-Host "  2) PC awake at schedule times (disable sleep, or use wake timers)"
Write-Host "  3) Logged into LinkedIn/Naukri/Foundit/Cutshort/Instahyre/Indeed in Chrome"
Write-Host "  4) git push access to origin automation-results branch"
Write-Host ""
Write-Host "Test one portal now:"
Write-Host "  & `"$Bash`" `"$PortalScript`" linkedin"
Write-Host ""
Write-Host "Disable all (or -Unregister to remove):"
Write-Host "  powershell -ExecutionPolicy Bypass -File scripts\disable-all-home-tasks.ps1"
Write-Host "Manual remove:"
Write-Host "  Get-ScheduledTask HomeDaily-* | Unregister-ScheduledTask -Confirm:`$false"
Write-Host "  Unregister-ScheduledTask -TaskName IndeedHomeDaily -Confirm:`$false"

Write-Host ""
Write-Host "Cloud automations can stay ON (morning). These home tasks are an evening replica."
Write-Host "Same-day jobs may be skipped if already applied by cloud; that is expected."
