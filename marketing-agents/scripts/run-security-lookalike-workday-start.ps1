param(
    [string]$RunDate = "",
    [string]$ScheduledTime = "09:00",
    [int]$MaxLinkedInRows = 20,
    [switch]$SkipRefresh
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
Set-Location $root

$dateValue = if ([string]::IsNullOrWhiteSpace($RunDate)) { (Get-Date).ToString("yyyy-MM-dd") } else { ([datetime]$RunDate).ToString("yyyy-MM-dd") }

if (-not $SkipRefresh) {
    Write-Output "Refreshing security-lookalike cadence..."
    powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-security-lookalike-cadence.ps1 `
        -RunDate $dateValue `
        -ScheduledTime $ScheduledTime `
        -MaxLinkedInRows $MaxLinkedInRows
}

$filesToOpen = @(
    "marketing-agents\data\security_lookalike_email_outbox_queue.csv",
    "marketing-agents\data\security_lookalike_linkedin_outreach_queue.csv",
    ("marketing-agents\briefs\security-lookalike-{0}.md" -f $dateValue)
)

foreach ($f in $filesToOpen) {
    if (Test-Path $f) {
        Start-Process $f | Out-Null
    } else {
        Write-Output ("File not found (skipped): {0}" -f $f)
    }
}

Write-Output "Workday start setup complete."
