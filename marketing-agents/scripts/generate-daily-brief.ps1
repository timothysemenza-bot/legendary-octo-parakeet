param(
    [string]$Date = "",
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$CallPlanFile = "marketing-agents/data/daily_call_plan.csv",
    [string]$InteractionFile = "marketing-agents/data/interaction_log.csv",
    [string]$EmailQueueFile = "marketing-agents/data/email_outbox_queue.csv",
    [string]$CadenceFile = "marketing-agents/data/outreach_touch_plan.csv",
    [string]$BlockedCadenceFile = "marketing-agents/data/outreach_touch_blocked.csv",
    [string]$LinkedInQueueFile = "marketing-agents/data/linkedin_outreach_queue.csv",
    [string]$ContactEventsFile = "marketing-agents/data/website_contact_events.csv",
    [string]$OutputDir = "marketing-agents/briefs"
)

$ErrorActionPreference = "Stop"

foreach ($f in @($PipelineFile, $CallPlanFile, $InteractionFile, $EmailQueueFile)) {
    if (-not (Test-Path $f)) { throw "Missing required file: $f" }
}
if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null }

$today = if ([string]::IsNullOrWhiteSpace($Date)) { (Get-Date).ToString("yyyy-MM-dd") } else { ([datetime]$Date).ToString("yyyy-MM-dd") }
$todayDt = [datetime]$today

$pipeline = @(Import-Csv -Path $PipelineFile)
$calls = @(Import-Csv -Path $CallPlanFile)
$interactions = @(Import-Csv -Path $InteractionFile)
$emails = @(Import-Csv -Path $EmailQueueFile)
$cadence = if (Test-Path $CadenceFile) { @(Import-Csv -Path $CadenceFile) } else { @() }
$blockedCadence = if (Test-Path $BlockedCadenceFile) { @(Import-Csv -Path $BlockedCadenceFile) } else { @() }
$linkedinQueue = if (Test-Path $LinkedInQueueFile) { @(Import-Csv -Path $LinkedInQueueFile) } else { @() }
$contactEvents = if (Test-Path $ContactEventsFile) { @(Import-Csv -Path $ContactEventsFile) } else { @() }

$activeProspects = @($pipeline | Where-Object { $_.status -eq "active" }).Count
$dueTouches = @($pipeline | Where-Object {
    -not [string]::IsNullOrWhiteSpace($_.next_touch_date) -and ([datetime]$_.next_touch_date).Date -le $todayDt.Date
}).Count

$todaysCalls = @($calls | Where-Object { $_.call_date -eq $today }).Count
$queuedEmails = @($emails | Where-Object { $_.owner_approved -eq "yes" -and $_.status -eq "queued" }).Count
$cadenceToday = @($cadence | Where-Object { $_.touch_date -eq $today -and $_.status -eq "planned" }).Count
$pendingInteractions = @($interactions | Where-Object { $_.outcome -eq "pending" }).Count
$missingEmails = @($pipeline | Where-Object { [string]::IsNullOrWhiteSpace($_.contact_email) }).Count
$missingPhones = @($pipeline | Where-Object { [string]::IsNullOrWhiteSpace($_.contact_phone) }).Count
$blockedCadenceCount = @($blockedCadence | Where-Object { $_.status -eq "blocked-missing-contact" }).Count
$linkedinQueued = @($linkedinQueue | Where-Object { $_.status -eq "queued" -or $_.status -eq "ready-for-review" }).Count
$contactEventsToday = @($contactEvents | Where-Object { $_.event_date -eq $today }).Count
$contactEventsNonSpamToday = @($contactEvents | Where-Object { $_.event_date -eq $today -and $_.spam_flag -ne "yes" }).Count
$contactEventsSpamToday = @($contactEvents | Where-Object { $_.event_date -eq $today -and $_.spam_flag -eq "yes" }).Count

$priorityCalls = $calls | Where-Object { $_.call_date -eq $today } | Sort-Object {[int]$_.plan_order}
$priorityProspects = $pipeline |
    Where-Object { $_.status -eq "active" } |
    Sort-Object {[int]$_.priority_score} -Descending |
    Select-Object -First 5

$emailRows = $emails | Where-Object { $_.owner_approved -eq "yes" -and $_.status -eq "queued" } | Select-Object -First 5
$contactEventsTop = $contactEvents |
    Where-Object { $_.event_date -eq $today -and $_.spam_flag -ne "yes" } |
    Sort-Object event_at -Descending |
    Select-Object -First 6

$actionItems = @()
if ($todaysCalls -gt 0) { $actionItems += "Run today's call block ($todaysCalls calls) and log outcomes immediately." }
if ($queuedEmails -gt 0) { $actionItems += "Send or draft $queuedEmails approved outreach emails from queue." }
if ($cadenceToday -gt 0) { $actionItems += "Execute $cadenceToday cadence touches due today from outreach plan." }
if ($pendingInteractions -gt 0) { $actionItems += "Resolve $pendingInteractions pending interaction outcomes to keep pipeline current." }
if ($missingEmails -gt 0) { $actionItems += "Enrich missing direct emails for $missingEmails prospects (call-first fallback)." }
if ($contactEventsNonSpamToday -gt 0) { $actionItems += "Review $contactEventsNonSpamToday new inbound website contact clicks and prioritize same-day follow-up." }
if ($actionItems.Count -eq 0) { $actionItems += "No urgent blockers detected. Focus on outreach execution and follow-up quality." }

$lines = @()
$lines += "# Daily BD Brief - $today"
$lines += ""
$lines += "## Snapshot"
$lines += "- Active prospects: $activeProspects"
$lines += "- Touches due today or overdue: $dueTouches"
$lines += "- Calls scheduled today: $todaysCalls"
$lines += "- Approved emails queued: $queuedEmails"
$lines += "- Cadence touches due today: $cadenceToday"
$lines += "- Pending interaction logs: $pendingInteractions"
$lines += "- Prospects missing direct email: $missingEmails"
$lines += "- Prospects missing phone: $missingPhones"
$lines += "- Blocked cadence touches (missing contact info): $blockedCadenceCount"
$lines += "- LinkedIn outreach drafts queued for review: $linkedinQueued"
$lines += "- Website contact events today (non-spam/spam/total): $contactEventsNonSpamToday / $contactEventsSpamToday / $contactEventsToday"
$lines += ""
$lines += "## Top Action Items"
$i = 1
foreach ($item in $actionItems) {
    $lines += "$i. $item"
    $i++
}
$lines += ""
$lines += "## Priority Accounts (Top 5)"
foreach ($p in $priorityProspects) {
    $lines += "- $($p.company_name) | Priority $($p.priority_score) | Stage $($p.stage) | Next touch $($p.next_touch_date)"
}
$lines += ""
$lines += "## Today's Call Plan"
if ($priorityCalls.Count -eq 0) {
    $lines += "- No calls scheduled for $today."
} else {
    foreach ($c in $priorityCalls) {
        $contact = if ([string]::IsNullOrWhiteSpace($c.target_contact)) { "TBD" } else { $c.target_contact }
        $phone = if ([string]::IsNullOrWhiteSpace($c.contact_phone)) { "No phone" } else { $c.contact_phone }
        $lines += "- $($c.start_time)-$($c.end_time) | $($c.company_name) | $contact | $phone"
    }
}
$lines += ""
$lines += "## Email Queue (Next Up)"
if ($emailRows.Count -eq 0) {
    $lines += "- No approved queued emails."
} else {
    foreach ($e in $emailRows) {
        $lines += "- $($e.company_name) -> $($e.to_email) | $($e.subject)"
    }
}
$lines += ""
$lines += "## Cadence Touches Due Today"
if ($cadenceToday -eq 0) {
    $lines += "- No planned cadence touches due today."
} else {
    $todayTouches = $cadence | Where-Object { $_.touch_date -eq $today -and $_.status -eq "planned" } | Sort-Object company_name, touch_step
    foreach ($t in $todayTouches) {
        $email = if ([string]::IsNullOrWhiteSpace($t.contact_email)) { "no-email" } else { $t.contact_email }
        $lines += "- $($t.company_name) | Step $($t.touch_step) | $($t.channel) | Template $($t.template_id) | $email"
    }
}
$lines += ""
$lines += "## Inbound Website Contact Signals (Filtered)"
if ($contactEventsTop.Count -eq 0) {
    $lines += "- No non-spam website contact events captured today."
} else {
    foreach ($evt in $contactEventsTop) {
        $ctx = if ([string]::IsNullOrWhiteSpace($evt.context)) { "Website Contact" } else { $evt.context }
        $chan = if ([string]::IsNullOrWhiteSpace($evt.channel)) { "contact" } else { $evt.channel }
        $src = if ([string]::IsNullOrWhiteSpace($evt.source_page)) { "-" } else { $evt.source_page }
        $lines += "- $($evt.event_at) | $chan | $ctx | $src"
    }
}
$lines += ""
$lines += "## End-of-Day Closeout Checklist"
$lines += "1. Update interaction outcomes for all calls made."
$lines += "2. Move pipeline stage/status for any response received."
$lines += "3. Set next_touch_date on every touched account."
$lines += "4. Queue tomorrow's call plan."

$outFile = Join-Path $OutputDir "$today.md"
$lines -join [Environment]::NewLine | Set-Content -Path $outFile -Encoding UTF8

Write-Output "Generated daily brief: $outFile"
