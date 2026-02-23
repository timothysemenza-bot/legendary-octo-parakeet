param(
    [string]$TaskName = "BossKey-Nightly-Repo-Backup",
    [string]$Time = "21:15",
    [string]$BackupRoot = "",
    [string]$CloudMirrorDir = "",
    [int]$RetentionDays = 30,
    [switch]$EnableGitPush
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$scriptPath = Join-Path $root "marketing-agents\scripts\nightly-repo-backup.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "Missing script: $scriptPath"
}

if ([string]::IsNullOrWhiteSpace($BackupRoot)) {
    $BackupRoot = Join-Path $env:USERPROFILE "Backups\Proposal-Microsite"
}
if ([string]::IsNullOrWhiteSpace($CloudMirrorDir) -and -not [string]::IsNullOrWhiteSpace($env:OneDrive)) {
    $CloudMirrorDir = Join-Path $env:OneDrive "Backups\Proposal-Microsite"
}

$argParts = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$scriptPath`"",
    "-BackupRoot", "`"$BackupRoot`"",
    "-RetentionDays", "$RetentionDays"
)
if (-not [string]::IsNullOrWhiteSpace($CloudMirrorDir)) {
    $argParts += @("-CloudMirrorDir", "`"$CloudMirrorDir`"")
}
if ($EnableGitPush) {
    $argParts += "-EnableGitPush"
}
$arg = $argParts -join " "

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arg -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$userId = if ([string]::IsNullOrWhiteSpace($env:USERDOMAIN)) { $env:USERNAME } else { "$($env:USERDOMAIN)\$($env:USERNAME)" }
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null

Write-Output ("Scheduled task '{0}' created for daily run at {1}." -f $TaskName, $Time)
Write-Output ("Backup root: {0}" -f $BackupRoot)
if (-not [string]::IsNullOrWhiteSpace($CloudMirrorDir)) {
    Write-Output ("Cloud mirror: {0}" -f $CloudMirrorDir)
}
Write-Output "Run now with:"
Write-Output ("Start-ScheduledTask -TaskName '{0}'" -f $TaskName)
