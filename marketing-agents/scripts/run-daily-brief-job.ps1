param(
    [string]$CallDate = "",
    [string]$StartTime = "09:15",
    [string]$EndTime = "15:00",
    [int]$CallCount = 12,
    [int]$MinutesPerCall = 20,
    [int]$GapMinutes = 5,
    [string]$BusyIcsUrl = "",
    [string]$BusyIcsFile = "",
    [switch]$OpenBrief
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
Set-Location $root

$icsUrlForSync = $BusyIcsUrl
if ([string]::IsNullOrWhiteSpace($icsUrlForSync) -and -not [string]::IsNullOrWhiteSpace($env:GOOGLE_CALENDAR_ICS_URL)) {
    $icsUrlForSync = $env:GOOGLE_CALENDAR_ICS_URL
}
if (-not [string]::IsNullOrWhiteSpace($icsUrlForSync)) {
    powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\sync-google-calendar-busy-blocks.ps1 -IcsUrl $icsUrlForSync
}

$marketingArgs = @("-ExecutionPolicy", "Bypass", "-File", ".\marketing-agents\scripts\run-daily-marketing.ps1", "-StartTime", $StartTime, "-EndTime", $EndTime, "-CallCount", "$CallCount", "-MinutesPerCall", "$MinutesPerCall")
if (-not [string]::IsNullOrWhiteSpace($CallDate)) {
    $marketingArgs += @("-CallDate", $CallDate)
}
powershell @marketingArgs

$calendarArgs = @("-ExecutionPolicy", "Bypass", "-File", ".\marketing-agents\scripts\build-adaptive-call-calendar.ps1", "-MinutesPerCall", "$MinutesPerCall", "-GapMinutes", "$GapMinutes")
if (-not [string]::IsNullOrWhiteSpace($CallDate)) { $calendarArgs += @("-Date", $CallDate) }
if (-not [string]::IsNullOrWhiteSpace($BusyIcsFile)) { $calendarArgs += @("-BusyIcsFile", $BusyIcsFile) }
$calendarArgs += @("-BusinessStart", $StartTime, "-BusinessEnd", $EndTime)
powershell @calendarArgs

$notifyArgs = @("-ExecutionPolicy", "Bypass", "-File", ".\marketing-agents\scripts\send-daily-brief-notification.ps1")
if (-not [string]::IsNullOrWhiteSpace($CallDate)) {
    $notifyArgs += @("-Date", $CallDate)
}
if ($OpenBrief) { $notifyArgs += "-OpenBrief" }
powershell @notifyArgs

Write-Output "Daily brief job complete."
