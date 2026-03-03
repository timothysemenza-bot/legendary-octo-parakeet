param(
    [string]$TaskName = "Personal-Downloads-Organizer",
    [string]$Time = "18:30",
    [string]$SourcePath = "",
    [string]$DestinationRoot = "",
    [int]$MinAgeHours = 12
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$scriptPath = Join-Path $root "scripts\organize-downloads.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "Missing script: $scriptPath"
}

if ([string]::IsNullOrWhiteSpace($SourcePath)) {
    $SourcePath = Join-Path $env:USERPROFILE "Downloads"
}
if ([string]::IsNullOrWhiteSpace($DestinationRoot)) {
    $DestinationRoot = Join-Path $env:USERPROFILE "Organized-Files"
}

$arg = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$scriptPath`"",
    "-SourcePath", "`"$SourcePath`"",
    "-DestinationRoot", "`"$DestinationRoot`"",
    "-MinAgeHours", "$MinAgeHours"
) -join " "

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$userId = if ([string]::IsNullOrWhiteSpace($env:USERDOMAIN)) { $env:USERNAME } else { "$($env:USERDOMAIN)\$($env:USERNAME)" }
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

Write-Output ("Scheduled task '{0}' created for daily run at {1}." -f $TaskName, $Time)
Write-Output ("Source: {0}" -f $SourcePath)
Write-Output ("Destination: {0}" -f $DestinationRoot)
Write-Output "Run immediately with:"
Write-Output ("Start-ScheduledTask -TaskName '{0}'" -f $TaskName)
