param(
    [string]$Date = "",
    [string]$BriefDir = "marketing-agents/briefs",
    [switch]$OpenBrief
)

$ErrorActionPreference = "Stop"

$today = if ([string]::IsNullOrWhiteSpace($Date)) { (Get-Date).ToString("yyyy-MM-dd") } else { ([datetime]$Date).ToString("yyyy-MM-dd") }
$briefPath = Join-Path $BriefDir "$today.md"

if (-not (Test-Path $briefPath)) {
    Write-Output "Brief not found: $briefPath"
    exit 1
}

$content = Get-Content -Path $briefPath
$callsLine = $content | Where-Object { $_ -like "- Calls scheduled today:*" } | Select-Object -First 1
$emailsLine = $content | Where-Object { $_ -like "- Approved emails queued:*" } | Select-Object -First 1

$calls = if ($null -eq $callsLine) { "?" } else { ($callsLine -replace '.*:\s*', '').Trim() }
$emails = if ($null -eq $emailsLine) { "?" } else { ($emailsLine -replace '.*:\s*', '').Trim() }

$title = "Boss Key Daily Brief Ready"
$body = "Calls: $calls | Emails queued: $emails"

$usedToast = $false
try {
    if (Get-Module -ListAvailable -Name BurntToast) {
        Import-Module BurntToast -ErrorAction Stop
        New-BurntToastNotification -Text $title, $body, $briefPath | Out-Null
        $usedToast = $true
    }
} catch {
    $usedToast = $false
}

if (-not $usedToast) {
    try {
        msg.exe $env:USERNAME "$title`n$body`n$briefPath" | Out-Null
    } catch {
        Write-Output "$title - $body"
        Write-Output $briefPath
    }
}

if ($OpenBrief) {
    Start-Process $briefPath | Out-Null
}

Write-Output "Notification sent for $briefPath"
