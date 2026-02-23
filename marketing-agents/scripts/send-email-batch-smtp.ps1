param(
    [string]$QueueFile = "marketing-agents/data/email_outbox_queue.csv",
    [string]$InteractionFile = "marketing-agents/data/interaction_log.csv",
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [Parameter(Mandatory = $true)][string]$SmtpHost,
    [int]$SmtpPort = 587,
    [bool]$UseSsl = $true,
    [Parameter(Mandatory = $true)][string]$SmtpUsername,
    [Parameter(Mandatory = $true)][string]$SmtpPassword,
    [string]$FromAddress = "",
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
    Write-Output "No owner-approved emails eligible for send."
    exit 0
}

$from = if ([string]::IsNullOrWhiteSpace($FromAddress)) { $SmtpUsername } else { $FromAddress }
$secure = ConvertTo-SecureString $SmtpPassword -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential($SmtpUsername, $secure)

$sentCount = 0
$blockedCount = 0

foreach ($row in $queue) {
    $eligibleRow = $eligible | Where-Object { $_.email_id -eq $row.email_id } | Select-Object -First 1
    if ($null -eq $eligibleRow) { continue }

    if ([string]::IsNullOrWhiteSpace($row.to_email)) {
        $row.status = "blocked-missing-email"
        $row.notes = "Missing to_email"
        $blockedCount++
        continue
    }

    try {
        $mailParams = @{
            SmtpServer = $SmtpHost
            Port = $SmtpPort
            UseSsl = $UseSsl
            Credential = $cred
            From = $from
            To = $row.to_email
            Subject = $row.subject
            Body = $row.body_text
            BodyAsHtml = $false
            ErrorAction = "Stop"
        }
        if (-not [string]::IsNullOrWhiteSpace($row.cc_email)) {
            $mailParams["Cc"] = $row.cc_email
        }
        Send-MailMessage @mailParams
        $row.status = "sent"
        $row.sent_at = (Get-Date).ToString("s")
        $sentCount++
    }
    catch {
        $row.status = "error"
        $row.notes = ("SMTP send error: " + $_.Exception.Message)
        continue
    }

    $interactions += [pscustomobject]@{
        interaction_id = $row.email_id
        date = (Get-Date).ToString("yyyy-MM-dd")
        company_name = $row.company_name
        contact_name = $row.contact_name
        channel = "email"
        direction = "outbound"
        summary = ("SMTP sent: {0}" -f $row.subject)
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

Write-Output ("Processed SMTP email batch. sent={0}, blocked={1}, total_eligible={2}" -f $sentCount, $blockedCount, $eligible.Count)
