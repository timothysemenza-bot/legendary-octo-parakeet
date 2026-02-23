param(
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$OutputFile = "marketing-agents/data/daily_call_plan.csv",
    [string]$CallDate = "",
    [string]$StartTime = "09:15",
    [string]$EndTime = "15:00",
    [int]$CallCount = 12,
    [int]$MinutesPerCall = 20,
    [switch]$AllowMissingPhone
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $PipelineFile)) {
    throw "Pipeline file not found: $PipelineFile"
}

$callDay = if ([string]::IsNullOrWhiteSpace($CallDate)) { (Get-Date).Date } else { [datetime]$CallDate }
$startClock = [datetime]::ParseExact($StartTime, "HH:mm", $null)
$endClock = [datetime]::ParseExact($EndTime, "HH:mm", $null)

$windowStart = [datetime]::new($callDay.Year, $callDay.Month, $callDay.Day, $startClock.Hour, $startClock.Minute, 0)
$windowEnd = [datetime]::new($callDay.Year, $callDay.Month, $callDay.Day, $endClock.Hour, $endClock.Minute, 0)
if ($windowEnd -le $windowStart) {
    throw "EndTime must be later than StartTime. Got StartTime=$StartTime EndTime=$EndTime"
}

$maxSlotsByWindow = [math]::Floor((($windowEnd - $windowStart).TotalMinutes) / [double]$MinutesPerCall)
if ($maxSlotsByWindow -lt 1) {
    throw "No capacity in call window. Increase window or reduce MinutesPerCall."
}

$closedStatuses = @("closed-won", "closed-lost", "do-not-contact")
$today = (Get-Date).Date

$stageWeights = @{
    "new" = 10
    "research" = 20
    "outreach-sent" = 30
    "connected" = 40
    "meeting-requested" = 60
    "meeting-scheduled" = 80
}

$rows = Import-Csv -Path $PipelineFile

function Get-CleanPhone {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
    $digits = ($Value -replace '[^0-9]', '')
    if ($digits.Length -eq 10) { return "+1$digits" }
    if ($digits.Length -eq 11 -and $digits.StartsWith("1")) { return "+$digits" }
    if ($digits.Length -gt 11) { return "+$digits" }
    return ""
}

$scored = foreach ($r in $rows) {
    $status = ($r.status | ForEach-Object { $_.ToLowerInvariant().Trim() })
    if ($closedStatuses -contains $status) { continue }

    if (-not $AllowMissingPhone.IsPresent) {
        $cleanPhone = Get-CleanPhone -Value $r.contact_phone
        if ([string]::IsNullOrWhiteSpace($cleanPhone)) { continue }
    }

    $score = 0
    $basePriority = 0
    [void][int]::TryParse($r.priority_score, [ref]$basePriority)
    $score += $basePriority

    $stage = ($r.stage | ForEach-Object { $_.ToLowerInvariant().Trim() })
    if ($stageWeights.ContainsKey($stage)) {
        $score += $stageWeights[$stage]
    } else {
        $score += 15
    }

    $nextTouch = $null
    if (-not [string]::IsNullOrWhiteSpace($r.next_touch_date)) {
        try { $nextTouch = [datetime]$r.next_touch_date } catch { $nextTouch = $null }
    }

    if ($nextTouch -eq $null) {
        $score += 20
    } elseif ($nextTouch.Date -le $today) {
        $score += 40
    } elseif ($nextTouch.Date -eq $today.AddDays(1)) {
        $score += 10
    }

    $lastTouch = $null
    if (-not [string]::IsNullOrWhiteSpace($r.last_touch_date)) {
        try { $lastTouch = [datetime]$r.last_touch_date } catch { $lastTouch = $null }
    }
    if ($lastTouch -eq $null) {
        $score += 20
    } else {
        $daysSince = [int]($today - $lastTouch.Date).TotalDays
        if ($daysSince -ge 7) { $score += 20 }
        elseif ($daysSince -ge 3) { $score += 10 }
    }

    [pscustomobject]@{
        score = $score
        row = $r
        nextTouch = $nextTouch
    }
}

$selected = $scored |
    Sort-Object -Property @{Expression = "score"; Descending = $true}, @{Expression = { $_.nextTouch }; Descending = $false} |
    Select-Object -First ([math]::Min($CallCount, $maxSlotsByWindow))

$planRows = @()
$cursor = $windowStart
$i = 1

foreach ($item in $selected) {
    $row = $item.row
    $end = $cursor.AddMinutes($MinutesPerCall)

    $reason = if (-not [string]::IsNullOrWhiteSpace($row.next_touch_date)) {
        "Follow-up due"
    } elseif (-not [string]::IsNullOrWhiteSpace($row.last_touch_date)) {
        "Re-engagement"
    } else {
        "New outreach"
    }

    $planRows += [pscustomobject]@{
        plan_order = $i
        call_date = $callDay.ToString("yyyy-MM-dd")
        start_time = $cursor.ToString("HH:mm")
        end_time = $end.ToString("HH:mm")
        company_name = $row.company_name
        target_contact = $row.target_contact
        role = $row.role
        contact_phone = $row.contact_phone
        contact_email = $row.contact_email
        reason = $reason
        stage = $row.stage
        status = $row.status
        next_touch_date = $row.next_touch_date
    }

    $cursor = $end
    $i++
}

$planRows | Export-Csv -Path $OutputFile -NoTypeInformation

Write-Output ("Generated {0} call slots for {1} -> {2}" -f $planRows.Count, $callDay.ToString("yyyy-MM-dd"), $OutputFile)
