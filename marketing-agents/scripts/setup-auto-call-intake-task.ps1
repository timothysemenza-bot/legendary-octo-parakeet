param(
    [string]$TaskName = "BossKey-Auto-Call-Intake",
    [string]$Time = "08:35",
    [int]$PollSeconds = 20,
    [string]$BusinessStart = "08:30",
    [string]$BusinessEnd = "17:30"
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$jobScript = Join-Path $root "marketing-agents\\scripts\\auto-call-intake-agent.ps1"

if (-not (Test-Path $jobScript)) {
    throw "Missing script: $jobScript"
}

$argParts = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$jobScript`"",
    "-BusinessHoursOnly",
    "-PollSeconds", "$PollSeconds",
    "-BusinessStart", "$BusinessStart",
    "-BusinessEnd", "$BusinessEnd"
)
$arg = $argParts -join " "

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$userId = if ([string]::IsNullOrWhiteSpace($env:USERDOMAIN)) { $env:USERNAME } else { "$($env:USERDOMAIN)\$($env:USERNAME)" }
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

Write-Output ("Scheduled task '{0}' created for weekdays at {1}." -f $TaskName, $Time)
Write-Output "Start now with:"
Write-Output ("Start-ScheduledTask -TaskName '{0}'" -f $TaskName)
