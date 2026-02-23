param(
    [string]$QueueFile = "marketing-agents/data/email_outbox_queue.csv",
    [string]$InteractionFile = "marketing-agents/data/interaction_log.csv",
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [int]$MaxToOpen = 5,
    [int]$PauseSeconds = 2,
    [switch]$IgnoreBusinessHours,
    [string]$BusinessStart = "09:00",
    [string]$BusinessEnd = "17:00",
    [switch]$WeekdaysOnly
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $QueueFile)) { throw "Missing file: $QueueFile" }
if (-not (Test-Path $InteractionFile)) { throw "Missing file: $InteractionFile" }
if (-not (Test-Path $PipelineFile)) { throw "Missing file: $PipelineFile" }

$now = Get-Date
if (-not $IgnoreBusinessHours) {
    if ($WeekdaysOnly -and ($now.DayOfWeek -eq [DayOfWeek]::Saturday -or $now.DayOfWeek -eq [DayOfWeek]::Sunday)) {
        throw "Blocked: weekday-only policy."
    }
    $start = [datetime]::ParseExact(($now.ToString("yyyy-MM-dd") + " " + $BusinessStart), "yyyy-MM-dd HH:mm", $null)
    $end = [datetime]::ParseExact(($now.ToString("yyyy-MM-dd") + " " + $BusinessEnd), "yyyy-MM-dd HH:mm", $null)
    if ($now -lt $start -or $now -gt $end) {
        throw ("Blocked: outside business hours ({0}-{1})." -f $BusinessStart, $BusinessEnd)
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
} | Select-Object -First $MaxToOpen

if ($eligible.Count -eq 0) {
    Write-Output "No approved queue rows to open."
    exit 0
}

function Build-MailToUrl {
    param(
        [string]$To,
        [string]$Cc,
        [string]$Subject,
        [string]$Body
    )
    $params = @()
    if (-not [string]::IsNullOrWhiteSpace($Cc)) { $params += "cc=$([uri]::EscapeDataString($Cc))" }
    if (-not [string]::IsNullOrWhiteSpace($Subject)) { $params += "subject=$([uri]::EscapeDataString($Subject))" }
    if (-not [string]::IsNullOrWhiteSpace($Body)) { $params += "body=$([uri]::EscapeDataString($Body))" }
    $query = if ($params.Count -gt 0) { "?" + ($params -join "&") } else { "" }
    return "mailto:$([uri]::EscapeDataString($To))$query"
}

$opened = 0
foreach ($row in $queue) {
    $match = $eligible | Where-Object { $_.email_id -eq $row.email_id } | Select-Object -First 1
    if ($null -eq $match) { continue }

    if ([string]::IsNullOrWhiteSpace($row.to_email)) {
        $row.status = "blocked-missing-email"
        $row.notes = "Missing to_email"
        continue
    }

    $url = Build-MailToUrl -To $row.to_email -Cc $row.cc_email -Subject $row.subject -Body $row.body_text
    Start-Process $url | Out-Null
    Start-Sleep -Seconds $PauseSeconds

    $row.status = "opened-for-review"
    $row.sent_at = ""
    $row.notes = "Opened in New Outlook compose window for manual review/send."
    $opened++

    $interactions += [pscustomobject]@{
        interaction_id = $row.email_id
        date = (Get-Date).ToString("yyyy-MM-dd")
        company_name = $row.company_name
        contact_name = $row.contact_name
        channel = "email"
        direction = "outbound"
        summary = ("Opened draft for review: {0}" -f $row.subject)
        outcome = "pending-review"
        next_action = "Review and send manually"
        next_touch_date = (Get-Date).AddDays(2).ToString("yyyy-MM-dd")
        owner = "Timmy Semenza"
        created_at = (Get-Date).ToString("s")
    }

    $p = $pipeline | Where-Object { $_.company_name -eq $row.company_name } | Select-Object -First 1
    if ($null -ne $p) {
        $p.last_touch_date = (Get-Date).ToString("yyyy-MM-dd")
        if ([string]::IsNullOrWhiteSpace($p.status)) { $p.status = "active" }
        if ([string]::IsNullOrWhiteSpace($p.stage) -or $p.stage -eq "new" -or $p.stage -eq "research") {
            $p.stage = "outreach-sent"
        }
    }
}

$queue | Export-Csv -Path $QueueFile -NoTypeInformation
$interactions | Export-Csv -Path $InteractionFile -NoTypeInformation
$pipeline | Export-Csv -Path $PipelineFile -NoTypeInformation

Write-Output ("Opened {0} prefilled compose window(s) for review in New Outlook." -f $opened)
