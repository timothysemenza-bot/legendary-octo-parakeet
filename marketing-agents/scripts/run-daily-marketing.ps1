param(
    [string]$CallDate = "",
    [string]$StartTime = "09:15",
    [string]$EndTime = "15:00",
    [int]$CallCount = 12,
    [int]$MinutesPerCall = 20
)

$ErrorActionPreference = "Stop"

Write-Output "Step 1/7: Scanning NAICS 561720 public renewals..."
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\scan-public-renewals-naics561720.ps1

Write-Output "Step 2/7: Syncing interactions -> pipeline..."
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\sync-interactions-to-pipeline.ps1

Write-Output "Step 3/7: Generating daily call plan..."
$callDateArg = @()
if (-not [string]::IsNullOrWhiteSpace($CallDate)) {
    $callDateArg = @("-CallDate", $CallDate)
}
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-daily-call-plan.ps1 @callDateArg -StartTime $StartTime -EndTime $EndTime -CallCount $CallCount -MinutesPerCall $MinutesPerCall

$briefDate = if ([string]::IsNullOrWhiteSpace($CallDate)) { (Get-Date).ToString("yyyy-MM-dd") } else { $CallDate }

Write-Output "Step 4/7: Generating LinkedIn outreach queue..."
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-linkedin-outreach-queue.ps1 -RunDate $briefDate

Write-Output "Step 5/7: Generating daily BD brief..."
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-daily-brief.ps1 -Date $briefDate

Write-Output "Step 6/7: Generating call runbook..."
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-call-runbook.ps1 -Date $briefDate

Write-Output "Step 7/7: Generating prospect research pack..."
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-prospect-research-pack.ps1 -Date $briefDate

Write-Output "Done. Review:"
Write-Output (" - marketing-agents/briefs/public-renewal-radar-{0}.md" -f $briefDate)
Write-Output " - marketing-agents/data/linkedin_outreach_queue.csv"
Write-Output " - marketing-agents/data/daily_call_plan.csv"
Write-Output " - marketing-agents/data/prospect_pipeline.csv"
Write-Output (" - marketing-agents/briefs/{0}.md" -f $briefDate)
Write-Output " - marketing-agents/briefs/call-runbook.md"
Write-Output " - marketing-agents/briefs/prospect-research-pack.md"
