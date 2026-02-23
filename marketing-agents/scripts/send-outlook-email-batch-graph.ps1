param(
    [string]$QueueFile = "marketing-agents/data/email_outbox_queue.csv",
    [string]$InteractionFile = "marketing-agents/data/interaction_log.csv",
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$FromUserPrincipalName = "",
    [string]$GraphAccessToken = "",
    [string]$BusinessStart = "09:00",
    [string]$BusinessEnd = "17:00",
    [string]$WeekdaysOnly = "true",
    [switch]$IgnoreBusinessHours,
    [int]$MaxAttempts = 3,
    [int]$RetryDelaySeconds = 4,
    [switch]$ForceDraft
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $QueueFile)) { throw "Missing file: $QueueFile" }
if (-not (Test-Path $InteractionFile)) { throw "Missing file: $InteractionFile" }
if (-not (Test-Path $PipelineFile)) { throw "Missing file: $PipelineFile" }
if ([string]::IsNullOrWhiteSpace($GraphAccessToken)) { throw "GraphAccessToken is required." }

$weekdaysOnlyEnabled = @("1","true","yes","y") -contains $WeekdaysOnly.ToLowerInvariant().Trim()

$now = Get-Date
if (-not $IgnoreBusinessHours) {
    if ($weekdaysOnlyEnabled -and ($now.DayOfWeek -eq [DayOfWeek]::Saturday -or $now.DayOfWeek -eq [DayOfWeek]::Sunday)) {
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

foreach ($q in $queue) {
    if (-not ($q.PSObject.Properties.Name -contains "attempt_count")) {
        $q | Add-Member -NotePropertyName attempt_count -NotePropertyValue "0"
    }
    if (-not ($q.PSObject.Properties.Name -contains "last_error")) {
        $q | Add-Member -NotePropertyName last_error -NotePropertyValue ""
    }
}

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

$headers = @{
    Authorization = "Bearer $GraphAccessToken"
    "Content-Type" = "application/json"
}

$baseUrl = if ([string]::IsNullOrWhiteSpace($FromUserPrincipalName)) {
    "https://graph.microsoft.com/v1.0/me"
} else {
    "https://graph.microsoft.com/v1.0/users/$FromUserPrincipalName"
}

# Preflight token/account validation before processing queue.
try {
    Invoke-RestMethod -Method Get -Uri "$baseUrl`?\$select=id,displayName,userPrincipalName" -Headers $headers | Out-Null
} catch {
    throw ("Graph preflight failed. Check token validity/scopes/account access. Error: {0}" -f $_.Exception.Message)
}

$sentCount = 0
$draftCount = 0
$blockedCount = 0
$errorCount = 0

function Invoke-WithRetry {
    param(
        [scriptblock]$Action,
        [int]$Attempts,
        [int]$DelaySeconds
    )
    $lastErr = $null
    for ($try = 1; $try -le $Attempts; $try++) {
        try {
            & $Action
            return $true
        } catch {
            $lastErr = $_.Exception.Message
            if ($try -lt $Attempts) {
                Start-Sleep -Seconds $DelaySeconds
            }
        }
    }
    throw $lastErr
}

foreach ($row in $queue) {
    $eligibleRow = $eligible | Where-Object { $_.email_id -eq $row.email_id } | Select-Object -First 1
    if ($null -eq $eligibleRow) { continue }

    if ([string]::IsNullOrWhiteSpace($row.to_email)) {
        $row.status = "blocked-missing-email"
        $row.notes = "Missing to_email"
        $row.last_error = "Missing to_email"
        $blockedCount++
        continue
    }

    $attemptCount = 0
    [void][int]::TryParse($row.attempt_count, [ref]$attemptCount)
    if ($attemptCount -ge $MaxAttempts) {
        $row.status = "failed-max-attempts"
        $row.last_error = "Maximum attempts reached"
        $blockedCount++
        continue
    }

    $message = @{
        subject = $row.subject
        body = @{
            contentType = "Text"
            content = $row.body_text
        }
        toRecipients = @(
            @{
                emailAddress = @{
                    address = $row.to_email
                }
            }
        )
    }

    if (-not [string]::IsNullOrWhiteSpace($row.cc_email)) {
        $message.ccRecipients = @(
            @{
                emailAddress = @{
                    address = $row.cc_email
                }
            }
        )
    }

    $mode = if ($ForceDraft) { "draft" } else { $row.send_mode.ToLowerInvariant().Trim() }
    try {
        if ($mode -eq "send") {
            $payload = @{ message = $message; saveToSentItems = $true } | ConvertTo-Json -Depth 6
            Invoke-WithRetry -Action { Invoke-RestMethod -Method Post -Uri "$baseUrl/sendMail" -Headers $headers -Body $payload | Out-Null } -Attempts $MaxAttempts -DelaySeconds $RetryDelaySeconds | Out-Null
            $row.status = "sent"
            $sentCount++
        } else {
            $draftPayload = $message | ConvertTo-Json -Depth 6
            Invoke-WithRetry -Action { Invoke-RestMethod -Method Post -Uri "$baseUrl/messages" -Headers $headers -Body $draftPayload | Out-Null } -Attempts $MaxAttempts -DelaySeconds $RetryDelaySeconds | Out-Null
            $row.status = "drafted"
            $draftCount++
        }

        $row.sent_at = (Get-Date).ToString("s")
        $row.last_error = ""
    } catch {
        $attemptCount++
        $row.attempt_count = "$attemptCount"
        $row.last_error = $_.Exception.Message
        if ($attemptCount -ge $MaxAttempts) {
            $row.status = "failed-max-attempts"
        } else {
            $row.status = "retry-queued"
        }
        $errorCount++
        continue
    }

    $attemptCount++
    $row.attempt_count = "$attemptCount"

    $interactions += [pscustomobject]@{
        interaction_id = $row.email_id
        date = (Get-Date).ToString("yyyy-MM-dd")
        company_name = $row.company_name
        contact_name = $row.contact_name
        channel = "email"
        direction = "outbound"
        summary = ("Graph Outlook {0}: {1}" -f $row.status, $row.subject)
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

Write-Output ("Processed Graph email batch. sent={0}, drafted={1}, blocked={2}, errors={3}, total_eligible={4}" -f $sentCount, $draftCount, $blockedCount, $errorCount, $eligible.Count)
