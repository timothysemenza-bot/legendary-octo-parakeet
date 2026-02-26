param(
    [string]$TaskName = "BossKey-SecurityLookalike-WorkdayStart",
    [string]$Time = "08:30",
    [string]$Workdir = "C:\Users\timot\Documents\Proposal-Microsite"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $Workdir "marketing-agents\scripts\run-security-lookalike-workday-start.ps1"
if (-not (Test-Path $scriptPath)) { throw "Missing script: $scriptPath" }

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $Time
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null

Write-Output ("Scheduled task created/updated: {0} at {1}" -f $TaskName, $Time)
