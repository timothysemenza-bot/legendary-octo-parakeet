param(
    [string]$Date = "",
    [string]$CallPlanFile = "marketing-agents/data/daily_call_plan.csv",
    [string]$BusyCsvFile = "marketing-agents/data/busy_blocks.csv",
    [string]$BusyIcsFile = "",
    [string]$BusyIcsUrl = "",
    [string]$OutputPlanFile = "marketing-agents/data/daily_call_plan_adaptive.csv",
    [string]$CalendarFile = "marketing-agents/briefs/daily-call-plan.ics",
    [string]$BusinessStart = "09:15",
    [string]$BusinessEnd = "15:00",
    [int]$MinutesPerCall = 20,
    [int]$GapMinutes = 5,
    [switch]$OpenCalendar
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $CallPlanFile)) { throw "Missing file: $CallPlanFile" }

function Parse-IcsDateTime {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return $null }
    $v = $Value.Trim()

    if ($v -match '^\d{8}$') {
        return [datetime]::ParseExact($v, "yyyyMMdd", $null)
    }
    if ($v -match '^\d{8}T\d{6}Z$') {
        $utc = [datetime]::ParseExact($v, "yyyyMMdd'T'HHmmss'Z'", $null)
        return [datetime]::SpecifyKind($utc, [DateTimeKind]::Utc).ToLocalTime()
    }
    if ($v -match '^\d{8}T\d{4}$') {
        return [datetime]::ParseExact($v, "yyyyMMdd'T'HHmm", $null)
    }
    if ($v -match '^\d{8}T\d{6}$') {
        return [datetime]::ParseExact($v, "yyyyMMdd'T'HHmmss", $null)
    }
    return $null
}

function Add-BusyInterval {
    param(
        [System.Collections.Generic.List[object]]$List,
        [datetime]$Start,
        [datetime]$End,
        [string]$Label
    )
    if ($null -eq $Start -or $null -eq $End) { return }
    if ($End -le $Start) { return }
    $List.Add([pscustomobject]@{
        start = $Start
        end = $End
        label = $Label
    })
}

function Parse-IcsBusy {
    param(
        [string]$IcsText
    )
    $busy = New-Object 'System.Collections.Generic.List[object]'
    if ([string]::IsNullOrWhiteSpace($IcsText)) { return $busy }

    $lines = $IcsText -split "`r?`n"
    $inEvent = $false
    $startRaw = ""
    $endRaw = ""
    $summary = ""
    foreach ($line in $lines) {
        if ($line -eq "BEGIN:VEVENT") {
            $inEvent = $true
            $startRaw = ""
            $endRaw = ""
            $summary = ""
            continue
        }
        if ($line -eq "END:VEVENT") {
            if ($inEvent) {
                $s = Parse-IcsDateTime -Value $startRaw
                $e = Parse-IcsDateTime -Value $endRaw
                Add-BusyInterval -List $busy -Start $s -End $e -Label $(if ([string]::IsNullOrWhiteSpace($summary)) { "calendar event" } else { $summary })
            }
            $inEvent = $false
            continue
        }
        if (-not $inEvent) { continue }

        if ($line -match '^DTSTART(?:;[^:]*)?:(.+)$') { $startRaw = $matches[1].Trim(); continue }
        if ($line -match '^DTEND(?:;[^:]*)?:(.+)$') { $endRaw = $matches[1].Trim(); continue }
        if ($line -match '^SUMMARY:(.+)$') { $summary = $matches[1].Trim(); continue }
    }
    return $busy
}

function New-Uid {
    return ([guid]::NewGuid().ToString() + "@bosskeyops.com")
}

$today = if ([string]::IsNullOrWhiteSpace($Date)) { (Get-Date).ToString("yyyy-MM-dd") } else { ([datetime]$Date).ToString("yyyy-MM-dd") }
$todayDt = [datetime]$today

$allCalls = @(Import-Csv -Path $CallPlanFile)
$calls = $allCalls | Where-Object { $_.call_date -eq $today } | Sort-Object { [int]$_.plan_order }
if ($calls.Count -eq 0) {
    Write-Output "No calls scheduled for $today in $CallPlanFile"
    exit 0
}

$dayStart = [datetime]::ParseExact("$today $BusinessStart", "yyyy-MM-dd HH:mm", $null)
$dayEnd = [datetime]::ParseExact("$today $BusinessEnd", "yyyy-MM-dd HH:mm", $null)

$busy = New-Object 'System.Collections.Generic.List[object]'

if (Test-Path $BusyCsvFile) {
    $busyRows = @(Import-Csv -Path $BusyCsvFile)
    foreach ($b in $busyRows) {
        $s = $null
        $e = $null
        try { $s = [datetime]$b.start } catch { $s = $null }
        try { $e = [datetime]$b.end } catch { $e = $null }
        Add-BusyInterval -List $busy -Start $s -End $e -Label $(if ([string]::IsNullOrWhiteSpace($b.title)) { "busy block" } else { $b.title })
    }
}

if (-not [string]::IsNullOrWhiteSpace($BusyIcsFile) -and (Test-Path $BusyIcsFile)) {
    $icsText = Get-Content -Raw -Path $BusyIcsFile
    $icsBusy = Parse-IcsBusy -IcsText $icsText
    foreach ($item in $icsBusy) { $busy.Add($item) }
}

if (-not [string]::IsNullOrWhiteSpace($BusyIcsUrl)) {
    try {
        $icsTextRemote = (Invoke-WebRequest -Uri $BusyIcsUrl -UseBasicParsing -TimeoutSec 20).Content
        $icsBusyRemote = Parse-IcsBusy -IcsText $icsTextRemote
        foreach ($item in $icsBusyRemote) { $busy.Add($item) }
    } catch {
        Write-Output "Warning: Could not fetch BusyIcsUrl. Continuing with other busy sources."
    }
}

# Limit busy set to target day and business window
$busyToday = @(
    $busy | Where-Object {
        $_.end -gt $dayStart -and $_.start -lt $dayEnd
    } | ForEach-Object {
        [pscustomobject]@{
            start = if ($_.start -lt $dayStart) { $dayStart } else { $_.start }
            end = if ($_.end -gt $dayEnd) { $dayEnd } else { $_.end }
            label = $_.label
        }
    } | Sort-Object start, end
)

$scheduled = @()
$unscheduled = @()
$cursor = $dayStart

foreach ($c in $calls) {
    $duration = [TimeSpan]::FromMinutes($MinutesPerCall)
    $gap = [TimeSpan]::FromMinutes($GapMinutes)
    $slotFound = $false
    $candidateStart = $cursor

    while (-not $slotFound) {
        $candidateEnd = $candidateStart.Add($duration)
        if ($candidateEnd -gt $dayEnd) { break }

        $overlap = $busyToday | Where-Object {
            $_.start -lt $candidateEnd -and $_.end -gt $candidateStart
        } | Sort-Object end | Select-Object -Last 1

        if ($null -eq $overlap) {
            $slotFound = $true
            $scheduled += [pscustomobject]@{
                plan_order = $c.plan_order
                call_date = $today
                start_time = $candidateStart.ToString("HH:mm")
                end_time = $candidateEnd.ToString("HH:mm")
                company_name = $c.company_name
                target_contact = $c.target_contact
                role = $c.role
                contact_phone = $c.contact_phone
                contact_email = $c.contact_email
                reason = $c.reason
                stage = $c.stage
                status = $c.status
                next_touch_date = $c.next_touch_date
                schedule_status = "scheduled"
            }
            $cursor = $candidateEnd.Add($gap)
        } else {
            $candidateStart = $overlap.end.Add($gap)
        }
    }

    if (-not $slotFound) {
        $unscheduled += [pscustomobject]@{
            plan_order = $c.plan_order
            call_date = $today
            start_time = ""
            end_time = ""
            company_name = $c.company_name
            target_contact = $c.target_contact
            role = $c.role
            contact_phone = $c.contact_phone
            contact_email = $c.contact_email
            reason = $c.reason
            stage = $c.stage
            status = $c.status
            next_touch_date = $c.next_touch_date
            schedule_status = "unscheduled-no-slot"
        }
    }
}

$allAdaptive = @($scheduled + $unscheduled) | Sort-Object { [int]$_.plan_order }
$outDir = Split-Path -Parent $OutputPlanFile
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
$allAdaptive | Export-Csv -Path $OutputPlanFile -NoTypeInformation

# Build ICS for scheduled items only
$calDir = Split-Path -Parent $CalendarFile
if (-not (Test-Path $calDir)) { New-Item -ItemType Directory -Force -Path $calDir | Out-Null }

$ical = @()
$ical += "BEGIN:VCALENDAR"
$ical += "VERSION:2.0"
$ical += "PRODID:-//Boss Key//Daily Call Plan//EN"
$ical += "CALSCALE:GREGORIAN"
$ical += "METHOD:PUBLISH"

foreach ($s in $scheduled) {
    $startDt = [datetime]::ParseExact("$($s.call_date) $($s.start_time)", "yyyy-MM-dd HH:mm", $null)
    $endDt = [datetime]::ParseExact("$($s.call_date) $($s.end_time)", "yyyy-MM-dd HH:mm", $null)
    $summary = "Boss Key Call - $($s.company_name)"
    $desc = "Contact: $($s.target_contact) ($($s.role))`nPhone: $($s.contact_phone)`nReason: $($s.reason)"
    $ical += "BEGIN:VEVENT"
    $ical += "UID:$(New-Uid)"
    $ical += "DTSTAMP:$((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'))"
    $ical += "DTSTART:$($startDt.ToString('yyyyMMddTHHmmss'))"
    $ical += "DTEND:$($endDt.ToString('yyyyMMddTHHmmss'))"
    $ical += "SUMMARY:$summary"
    $ical += "DESCRIPTION:$desc"
    $ical += "END:VEVENT"
}

$ical += "END:VCALENDAR"
$ical -join [Environment]::NewLine | Set-Content -Path $CalendarFile -Encoding UTF8

if ($OpenCalendar) {
    Start-Process $CalendarFile | Out-Null
}

Write-Output ("Adaptive plan generated: {0} scheduled, {1} unscheduled." -f $scheduled.Count, $unscheduled.Count)
Write-Output "Plan file: $OutputPlanFile"
Write-Output "Calendar file: $CalendarFile"
