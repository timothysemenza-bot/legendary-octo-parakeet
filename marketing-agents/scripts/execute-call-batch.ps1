param(
    [Parameter(Mandatory = $true)][string]$BatchId,
    [string]$BatchQueueFile = "marketing-agents/data/call_batch_queue.csv",
    [string]$CallPlanFile = "marketing-agents/data/daily_call_plan.csv",
    [string]$InteractionFile = "marketing-agents/data/interaction_log.csv",
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$BusinessStart = "09:00",
    [string]$BusinessEnd = "17:00",
    [bool]$WeekdaysOnly = $true
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BatchQueueFile)) { throw "Missing file: $BatchQueueFile" }
if (-not (Test-Path $CallPlanFile)) { throw "Missing file: $CallPlanFile" }
if (-not (Test-Path $InteractionFile)) { throw "Missing file: $InteractionFile" }
if (-not (Test-Path $PipelineFile)) { throw "Missing file: $PipelineFile" }

$batches = @(Import-Csv -Path $BatchQueueFile)
$batch = $batches | Where-Object { $_.batch_id -eq $BatchId } | Select-Object -First 1
if ($null -eq $batch) { throw "Batch not found: $BatchId" }

if (($batch.owner_approved | ForEach-Object { $_.ToLowerInvariant().Trim() }) -ne "yes") {
    throw "Batch $BatchId is not owner-approved. Set owner_approved=yes before execution."
}

$plan = @(Import-Csv -Path $CallPlanFile)
if ($plan.Count -eq 0) {
    Write-Output "No calls in daily plan. Nothing to execute."
    exit 0
}

$now = Get-Date
$windowStart = [datetime]::ParseExact(("{0} {1}" -f $batch.call_date, $batch.start_time), "yyyy-MM-dd HH:mm", $null)
$windowEnd = [datetime]::ParseExact(("{0} {1}" -f $batch.call_date, $batch.end_time), "yyyy-MM-dd HH:mm", $null)

# Enforce standard business-hours execution policy.
$businessStartDt = [datetime]::ParseExact(("{0} {1}" -f $batch.call_date, $BusinessStart), "yyyy-MM-dd HH:mm", $null)
$businessEndDt = [datetime]::ParseExact(("{0} {1}" -f $batch.call_date, $BusinessEnd), "yyyy-MM-dd HH:mm", $null)

if ($WeekdaysOnly -and ($windowStart.DayOfWeek -eq [DayOfWeek]::Saturday -or $windowStart.DayOfWeek -eq [DayOfWeek]::Sunday)) {
    throw ("Batch {0} is scheduled on {1}. Weekday-only policy blocks execution." -f $BatchId, $windowStart.DayOfWeek)
}

if ($windowStart -lt $businessStartDt -or $windowEnd -gt $businessEndDt) {
    throw ("Batch {0} window ({1}-{2}) is outside allowed business hours ({3}-{4})." -f $BatchId, $batch.start_time, $batch.end_time, $BusinessStart, $BusinessEnd)
}

if ($now -lt $windowStart -or $now -gt $windowEnd -or $now -lt $businessStartDt -or $now -gt $businessEndDt) {
    Write-Output ("Outside active dialing window/business hours for batch {0}. Preparing calls only." -f $BatchId)
    $mode = "prepare-only"
}
else {
    $mode = "execute-log"
}

$interactions = @(Import-Csv -Path $InteractionFile)
$newRows = @()
$i = 1
foreach ($c in $plan) {
    $interactionId = "{0}-{1:000}" -f $BatchId, $i
    $summary = if ($mode -eq "execute-log") {
        "Call batch executed via {0}; outcome pending manual result entry." -f $batch.dialer_provider
    } else {
        "Call prepared for dialing window; not executed due to time window."
    }

    $newRows += [pscustomobject]@{
        interaction_id = $interactionId
        date = (Get-Date).ToString("yyyy-MM-dd")
        company_name = $c.company_name
        contact_name = $c.target_contact
        channel = "call"
        direction = "outbound"
        summary = $summary
        outcome = "pending"
        next_action = "Update with live call outcome"
        next_touch_date = $c.next_touch_date
        owner = "Tim Semenza"
        created_at = (Get-Date).ToString("s")
    }
    $i++
}

(@($interactions) + @($newRows)) | Export-Csv -Path $InteractionFile -NoTypeInformation

$batch.status = if ($mode -eq "execute-log") { "executed-pending-outcomes" } else { "prepared" }
$batch.record_count = "$($plan.Count)"
$batches | Export-Csv -Path $BatchQueueFile -NoTypeInformation

# Update pipeline stage status to reflect active call sequence
$pipeline = @(Import-Csv -Path $PipelineFile)
foreach ($p in $pipeline) {
    $matched = $plan | Where-Object { $_.company_name -eq $p.company_name } | Select-Object -First 1
    if ($null -eq $matched) { continue }
    if ([string]::IsNullOrWhiteSpace($p.stage) -or $p.stage -eq "new") { $p.stage = "outreach-sent" }
    if ([string]::IsNullOrWhiteSpace($p.status)) { $p.status = "active" }
}
$pipeline | Export-Csv -Path $PipelineFile -NoTypeInformation

Write-Output ("Batch {0}: mode={1}, records={2}. Logged to interaction file." -f $BatchId, $mode, $plan.Count)
