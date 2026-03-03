param(
    [string]$TaskName = "Personal-UserFilesystem-Organizer",
    [string]$Time = "20:00",
    [int]$MinAgeDays = 14,
    [ValidateSet("Copy", "Move")]
    [string]$Mode = "Copy",
    [string]$DestinationRoot = ""
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$scriptPath = Join-Path $root "scripts\organize-user-filesystem.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "Missing script: $scriptPath"
}

if ([string]::IsNullOrWhiteSpace($DestinationRoot)) {
    $DestinationRoot = Join-Path $env:USERPROFILE "Intuitive-Workspace"
}

$arg = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$scriptPath`"",
    "-Apply",
    "-Mode", $Mode,
    "-MinAgeDays", "$MinAgeDays",
    "-DestinationRoot", "`"$DestinationRoot`""
) -join " "

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$userId = if ([string]::IsNullOrWhiteSpace($env:USERDOMAIN)) { $env:USERNAME } else { "$($env:USERDOMAIN)\$($env:USERNAME)" }
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

Write-Output ("Scheduled task '{0}' created for daily run at {1}." -f $TaskName, $Time)
Write-Output ("Mode: {0}" -f $Mode)
Write-Output ("Destination: {0}" -f $DestinationRoot)
Write-Output "Run immediately with:"
Write-Output ("Start-ScheduledTask -TaskName '{0}'" -f $TaskName)
