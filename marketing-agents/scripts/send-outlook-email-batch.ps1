param(
    [string]$QueueFile = "marketing-agents/data/email_outbox_queue.csv",
    [string]$InteractionFile = "marketing-agents/data/interaction_log.csv",
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$FromAccount = "",
    [string]$BusinessStart = "09:00",
    [string]$BusinessEnd = "17:00",
    [bool]$WeekdaysOnly = $true,
    [switch]$IgnoreBusinessHours
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $QueueFile)) { throw "Missing file: $QueueFile" }
if (-not (Test-Path $InteractionFile)) { throw "Missing file: $InteractionFile" }
if (-not (Test-Path $PipelineFile)) { throw "Missing file: $PipelineFile" }

$now = Get-Date
if (-not $IgnoreBusinessHours) {
    if ($WeekdaysOnly -and ($now.DayOfWeek -eq [DayOfWeek]::Saturday -or $now.DayOfWeek -eq [DayOfWeek]::Sunday)) {
        throw "Email send blocked: weekday-only policy."
    }
    $start = [datetime]::ParseExact(($now.ToString("yyyy-MM-dd") + " " + $BusinessStart), "yyyy-MM-dd HH:mm", $null)
    $end = [datetime]::ParseExact(($now.ToString("yyyy-MM-dd") + " " + $BusinessEnd), "yyyy-MM-dd HH:mm", $null)
    if ($now -lt $start -or $now -gt $end) {
        throw ("Email send blocked: outside business hours ({0}-{1})." -f $BusinessStart, $BusinessEnd)
    }
}

$queue = @(Import-Csv -Path $QueueFile)
$interactions = @(Import-Csv -Path $InteractionFile)
$pipeline = @(Import-Csv -Path $PipelineFile)

$today = $now.ToString("yyyy-MM-dd")
$timeNow = $now.ToString("HH:mm")

$eligible = $queue | Where-Object {
    ($_.owner_approved.ToLowerInvariant().Trim() -eq "yes") -and
    ($_.status -eq "queued" -or $_.status -eq "drafted") -and
    ($_.scheduled_date -le $today) -and
    ($_.scheduled_time -le $timeNow)
}

if ($eligible.Count -eq 0) {
    Write-Output "No owner-approved emails eligible for send/draft."
    exit 0
}

try {
    $outlook = New-Object -ComObject Outlook.Application
    $session = $outlook.Session
} catch {
    throw "Unable to access Outlook COM. Ensure Outlook desktop is installed and signed in."
}

$sendAccount = $null
if (-not [string]::IsNullOrWhiteSpace($FromAccount)) {
    foreach ($acc in $session.Accounts) {
        if ($acc.SmtpAddress -and $acc.SmtpAddress.ToLowerInvariant() -eq $FromAccount.ToLowerInvariant()) {
            $sendAccount = $acc
            break
        }
    }
    if ($null -eq $sendAccount) {
        throw "Specified FromAccount not found in Outlook profile: $FromAccount"
    }
}

$sentCount = 0
$draftCount = 0

foreach ($row in $queue) {
    $eligibleRow = $eligible | Where-Object { $_.email_id -eq $row.email_id } | Select-Object -First 1
    if ($null -eq $eligibleRow) { continue }

    if ([string]::IsNullOrWhiteSpace($row.to_email)) {
        $row.status = "blocked-missing-email"
        $row.notes = "Missing to_email"
        continue
    }

    $mail = $outlook.CreateItem(0)
    $mail.To = $row.to_email
    if (-not [string]::IsNullOrWhiteSpace($row.cc_email)) { $mail.CC = $row.cc_email }
    $mail.Subject = $row.subject
    $mail.Body = $row.body_text

    if ($null -ne $sendAccount) {
        $mail.SendUsingAccount = $sendAccount
    }

    $mode = $row.send_mode.ToLowerInvariant().Trim()
    if ($mode -eq "send") {
        $mail.Send()
        $row.status = "sent"
        $sentCount++
    } else {
        $mail.Save()
        $row.status = "drafted"
        $draftCount++
    }

    $row.sent_at = (Get-Date).ToString("s")

    $interactions += [pscustomobject]@{
        interaction_id = $row.email_id
        date = (Get-Date).ToString("yyyy-MM-dd")
        company_name = $row.company_name
        contact_name = $row.contact_name
        channel = "email"
        direction = "outbound"
        summary = ("Outlook {0}: {1}" -f $row.status, $row.subject)
        outcome = "pending"
        next_action = "Monitor for reply and follow up"
        next_touch_date = (Get-Date).AddDays(3).ToString("yyyy-MM-dd")
        owner = "Tim Semenza"
        created_at = (Get-Date).ToString("s")
    }

    $p = $pipeline | Where-Object { $_.company_name -eq $row.company_name } | Select-Object -First 1
    if ($null -ne $p) {
        $p.last_touch_date = (Get-Date).ToString("yyyy-MM-dd")
        $p.next_touch_date = (Get-Date).AddDays(3).ToString("yyyy-MM-dd")
        if ([string]::IsNullOrWhiteSpace($p.stage) -or $p.stage -eq "new" -or $p.stage -eq "research") {
            $p.stage = "outreach-sent"
        }
        if ([string]::IsNullOrWhiteSpace($p.status)) { $p.status = "active" }
    }
}

$queue | Export-Csv -Path $QueueFile -NoTypeInformation
$interactions | Export-Csv -Path $InteractionFile -NoTypeInformation
$pipeline | Export-Csv -Path $PipelineFile -NoTypeInformation

Write-Output ("Processed email batch. sent={0}, drafted={1}, total_eligible={2}" -f $sentCount, $draftCount, $eligible.Count)
