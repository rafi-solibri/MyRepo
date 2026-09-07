# Disable (or remove) ALL home-local job-apply scheduled tasks on this Windows PC.
#
# Run in PowerShell from the MyRepo checkout:
#   powershell -ExecutionPolicy Bypass -File scripts\disable-all-home-tasks.ps1
#
# Options:
#   -Unregister   Remove tasks entirely (default is Disable only — reversible)
#   -WhatIf       Show what would change without changing anything
param(
  [switch]$Unregister,
  [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

$ExactNames = @(
  "HomeDaily-LinkedIn",
  "HomeDaily-Foundit",
  "HomeDaily-Cutshort",
  "HomeDaily-Naukri",
  "HomeDaily-Instahyre",
  "HomeDaily-Indeed",
  "HomeDaily-HitechCity",
  "HomeDaily-Notification",
  "IndeedHomeDaily"
)

function Get-JobApplyHomeTasks {
  $found = @{}
  foreach ($name in $ExactNames) {
    $t = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($t) { $found[$t.TaskName] = $t }
  }
  # Catch any extra HomeDaily-* tasks from older installs.
  Get-ScheduledTask -TaskName "HomeDaily-*" -ErrorAction SilentlyContinue | ForEach-Object {
    $found[$_.TaskName] = $_
  }
  return @($found.Values | Sort-Object TaskName)
}

$tasks = Get-JobApplyHomeTasks
if (-not $tasks -or $tasks.Count -eq 0) {
  Write-Host "No home job-apply scheduled tasks found (HomeDaily-* / IndeedHomeDaily)."
  Write-Host "Nothing to disable."
  exit 0
}

$action = if ($Unregister) { "Unregister" } else { "Disable" }
Write-Host "Found $($tasks.Count) home job-apply task(s). Action: $action"
Write-Host ""

foreach ($t in $tasks) {
  $state = $t.State
  if ($WhatIf) {
    Write-Host "[WhatIf] Would $action $($t.TaskName) (current State=$state)"
    continue
  }
  if ($Unregister) {
    Unregister-ScheduledTask -TaskName $t.TaskName -Confirm:$false
    Write-Host "Removed $($t.TaskName) (was State=$state)"
  } else {
    if ($state -eq "Disabled") {
      Write-Host "Already disabled: $($t.TaskName)"
    } else {
      Disable-ScheduledTask -TaskName $t.TaskName | Out-Null
      Write-Host "Disabled $($t.TaskName) (was State=$state)"
    }
  }
}

Write-Host ""
if ($WhatIf) {
  Write-Host "Dry run only. Re-run without -WhatIf to apply."
} elseif ($Unregister) {
  Write-Host "All home job-apply tasks removed."
  Write-Host "Re-install later: powershell -ExecutionPolicy Bypass -File scripts\install-all-home-tasks.ps1"
} else {
  Write-Host "All home job-apply tasks disabled (schedules kept)."
  Write-Host "Re-enable later:"
  Write-Host "  Get-ScheduledTask HomeDaily-* | Enable-ScheduledTask"
  Write-Host "  Enable-ScheduledTask -TaskName IndeedHomeDaily"
  Write-Host "Or re-install: powershell -ExecutionPolicy Bypass -File scripts\install-all-home-tasks.ps1"
}

Write-Host ""
Write-Host "Also stop any in-flight home run (optional):"
Write-Host "  Get-ScheduledTask HomeDaily-* | Where-Object State -eq Running | Stop-ScheduledTask"
Write-Host "  Stop-ScheduledTask -TaskName IndeedHomeDaily -ErrorAction SilentlyContinue"
Write-Host ""
Write-Host "Note: Cursor cloud Automations (morning 9 AM) are separate and stay as-is."
Write-Host "Toggle them at https://cursor.com/automations if you also want those Off."
