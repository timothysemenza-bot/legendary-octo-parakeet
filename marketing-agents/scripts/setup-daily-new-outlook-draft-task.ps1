param(
    [string]$TaskName = "BossKey-NewOutlook-DraftReview",
    [string]$Time = "08:45",
    [int]$MaxToOpen = 5
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$scriptPath = Join-Path $root "marketing-agents\\scripts\\open-new-outlook-review-drafts.ps1"
if (-not (Test-Path $scriptPath)) { throw "Missing script: $scriptPath" }

$arg = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -WeekdaysOnly -MaxToOpen $MaxToOpen"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$userId = if ([string]::IsNullOrWhiteSpace($env:USERDOMAIN)) { $env:USERNAME } else { "$($env:USERDOMAIN)\$($env:USERNAME)" }
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

Write-Output ("Scheduled task '{0}' created for weekdays at {1}." -f $TaskName, $Time)
Write-Output ("It will open up to {0} prefilled compose windows each day for manual review/send." -f $MaxToOpen)
