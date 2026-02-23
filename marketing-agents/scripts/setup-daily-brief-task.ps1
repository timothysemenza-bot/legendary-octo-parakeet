param(
    [string]$TaskName = "BossKey-Daily-Brief",
    [string]$Time = "08:00",
    [string]$BusyIcsUrl = "",
    [string]$BusyIcsFile = "",
    [switch]$OpenBrief,
    [switch]$InstallBurntToast
)

$ErrorActionPreference = "Stop"

if ($InstallBurntToast) {
    try {
        Install-Module BurntToast -Scope CurrentUser -Force -AllowClobber -ErrorAction Stop
        Write-Output "Installed BurntToast module for toast notifications."
    } catch {
        Write-Output "BurntToast install failed. Falling back to msg popups."
    }
}

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$jobScript = Join-Path $root "marketing-agents\\scripts\\run-daily-brief-job.ps1"

if (-not (Test-Path $jobScript)) {
    throw "Missing script: $jobScript"
}

$argParts = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$jobScript`"")
if ($OpenBrief) { $argParts += "-OpenBrief" }
if (-not [string]::IsNullOrWhiteSpace($BusyIcsUrl)) { $argParts += @("-BusyIcsUrl", "`"$BusyIcsUrl`"") }
if (-not [string]::IsNullOrWhiteSpace($BusyIcsFile)) { $argParts += @("-BusyIcsFile", "`"$BusyIcsFile`"") }
$arg = $argParts -join " "

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$userId = if ([string]::IsNullOrWhiteSpace($env:USERDOMAIN)) { $env:USERNAME } else { "$($env:USERDOMAIN)\$($env:USERNAME)" }
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

Write-Output ("Scheduled task '{0}' created for weekdays at {1}." -f $TaskName, $Time)
Write-Output "Test now with:"
Write-Output ("Start-ScheduledTask -TaskName '{0}'" -f $TaskName)
