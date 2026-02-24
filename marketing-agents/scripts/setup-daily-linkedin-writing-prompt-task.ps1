param(
    [string]$Time = "09:00",
    [string]$TaskName = "BossKey-LinkedIn-WritingPrompt",
    [string]$Workdir = "C:\Users\timot\Documents\Proposal-Microsite"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $Workdir "marketing-agents\scripts\generate-daily-linkedin-writing-prompt.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "Script not found: $scriptPath"
}

$parts = $Time.Split(":")
if ($parts.Count -ne 2) { throw "Time must be HH:mm (24-hour), e.g. 09:00" }
$hour = [int]$parts[0]
$minute = [int]$parts[1]

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$scriptPath`" -OpenInNotepad"

$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At ([datetime]::Today.AddHours($hour).AddMinutes($minute))

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Force | Out-Null

Write-Output "Scheduled task created: $TaskName at $Time (weekdays)."
