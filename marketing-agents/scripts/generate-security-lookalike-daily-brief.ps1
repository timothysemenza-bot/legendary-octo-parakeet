param(
    [string]$Date = "",
    [string]$PipelineFile = "marketing-agents/data/security_lookalike_campaign_pipeline.csv",
    [string]$CadenceFile = "marketing-agents/data/security_lookalike_outreach_touch_plan.csv",
    [string]$BlockedCadenceFile = "marketing-agents/data/security_lookalike_outreach_touch_blocked.csv",
    [string]$EmailQueueFile = "marketing-agents/data/security_lookalike_email_outbox_queue.csv",
    [string]$LinkedInQueueFile = "marketing-agents/data/security_lookalike_linkedin_outreach_queue.csv",
    [string]$OutputDir = "marketing-agents/briefs"
)

$ErrorActionPreference = "Stop"

foreach ($f in @($PipelineFile, $CadenceFile, $EmailQueueFile, $LinkedInQueueFile)) {
    if (-not (Test-Path $f)) { throw "Missing required file: $f" }
}
if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null }

$today = if ([string]::IsNullOrWhiteSpace($Date)) { (Get-Date).ToString("yyyy-MM-dd") } else { ([datetime]$Date).ToString("yyyy-MM-dd") }
$todayDt = [datetime]$today

$pipeline = @(Import-Csv -Path $PipelineFile)
$cadence = @(Import-Csv -Path $CadenceFile)
$blocked = if (Test-Path $BlockedCadenceFile) { @(Import-Csv -Path $BlockedCadenceFile) } else { @() }
$emails = @(Import-Csv -Path $EmailQueueFile)
$linkedin = @(Import-Csv -Path $LinkedInQueueFile)

$active = @($pipeline | Where-Object { $_.status -eq "active" }).Count
$p1 = @($pipeline | Where-Object { $_.priority_tier -eq "P1" }).Count
$p2 = @($pipeline | Where-Object { $_.priority_tier -eq "P2" }).Count
$p3 = @($pipeline | Where-Object { $_.priority_tier -eq "P3" }).Count

$touchesToday = @($cadence | Where-Object { $_.touch_date -eq $today -and $_.status -eq "planned" })
$emailTouchesToday = @($touchesToday | Where-Object { $_.channel -match "email" })
$linkedinTouchesToday = @($touchesToday | Where-Object { $_.channel -match "linkedin" })
$blockedCount = @($blocked | Where-Object { $_.status -eq "blocked-missing-contact" }).Count

$queuedEmails = @($emails | Where-Object { $_.status -eq "queued" -and $_.scheduled_date -eq $today }).Count
$queuedLinkedIn = @($linkedin | Where-Object { $_.status -in @("queued","ready-for-review") }).Count

$topAccounts = $pipeline |
    Sort-Object @{Expression = {[int]$_.priority_score}; Descending = $true}, company_name |
    Select-Object -First 10

$emailRows = $emails |
    Where-Object { $_.status -eq "queued" -and $_.scheduled_date -eq $today } |
    Select-Object -First 8

$linkedinRows = $linkedin |
    Where-Object { $_.status -in @("queued","ready-for-review") } |
    Select-Object -First 8

$lines = @()
$lines += "# Security Lookalike Outreach Daily Brief - $today"
$lines += ""
$lines += "## Snapshot"
$lines += "- Active target accounts: $active"
$lines += "- Priority distribution: P1=$p1 | P2=$p2 | P3=$p3"
$lines += "- Planned touches today: $($touchesToday.Count)"
$lines += "- Email touches today: $($emailTouchesToday.Count)"
$lines += "- LinkedIn touches today: $($linkedinTouchesToday.Count)"
$lines += "- Email drafts queued for today: $queuedEmails"
$lines += "- LinkedIn actions queued: $queuedLinkedIn"
$lines += "- Blocked touches (missing contact data): $blockedCount"
$lines += ""
$lines += "## What To Send Today"
$lines += "1. Review and send today's queued email drafts."
$lines += "2. Execute LinkedIn connection notes/DMs for queued accounts."
$lines += "3. Log outcomes and advance next touch dates on responded accounts."
$lines += ""
$lines += "## Top Accounts To Prioritize"
foreach ($a in $topAccounts) {
    $offer = if ([string]::IsNullOrWhiteSpace($a.recommended_offer)) { "N/A" } else { $a.recommended_offer }
    $warm = if ([string]::IsNullOrWhiteSpace($a.linkedin_warm_path)) { "No known warm path" } else { $a.linkedin_warm_path }
    $lines += "- $($a.company_name) | Offer: $offer | Priority $($a.priority_score) | Warm path: $warm"
}
$lines += ""
$lines += "## Email Draft Queue (Today)"
if ($emailRows.Count -eq 0) {
    $lines += "- No email drafts currently scheduled for today."
} else {
    foreach ($e in $emailRows) {
        $to = if ([string]::IsNullOrWhiteSpace($e.to_email)) { "missing-email" } else { $e.to_email }
        $lines += "- $($e.company_name) -> $to | $($e.subject)"
    }
}
$lines += ""
$lines += "## LinkedIn Queue (Next Up)"
if ($linkedinRows.Count -eq 0) {
    $lines += "- No LinkedIn queue rows available."
} else {
    foreach ($li in $linkedinRows) {
        $contact = if ([string]::IsNullOrWhiteSpace($li.target_contact)) { "Target Buyer" } else { $li.target_contact }
        $lines += "- $($li.company_name) | Contact: $contact | Action: review + send connection note"
    }
}
$lines += ""
$lines += "## CFO-Ready Offer Reminder"
$lines += '- Pilot Digest Sprint: `$5,500` one-time'
$lines += '- Managed Digest Retainer: `$6,000/month`'
$lines += '- Embedded Capture Partner: `$9,500/month`'
$lines += ""
$lines += "## End-of-Day Checklist"
$lines += "1. Mark sent/attempted status for email and LinkedIn rows."
$lines += "2. Capture response outcomes in interaction log."
$lines += "3. Move high-intent accounts to discovery scheduling."
$lines += "4. Regenerate tomorrow's brief."

$outFile = Join-Path $OutputDir ("security-lookalike-" + $today + ".md")
$lines -join [Environment]::NewLine | Set-Content -Path $outFile -Encoding UTF8

Write-Output "Generated security lookalike daily brief: $outFile"
