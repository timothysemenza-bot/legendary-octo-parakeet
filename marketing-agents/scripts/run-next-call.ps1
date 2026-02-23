param(
    [string]$Date = "",
    [string]$CallPlanFile = "marketing-agents/data/daily_call_plan.csv",
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$InteractionFile = "marketing-agents/data/interaction_log.csv",
    [string]$FollowUpFile = "marketing-agents/data/follow_up_events.csv",
    [string]$FollowUpCalendarFile = "marketing-agents/briefs/follow-up-events.ics",
    [string]$StateFile = "marketing-agents/data/call_session_state.json",
    [ValidateSet("tel","googlevoice","none")][string]$DialMode = "tel",
    [switch]$NoPrompt,
    [switch]$DisableAutoFollowUps,
    [switch]$LogOnly,
    [switch]$Reset
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $CallPlanFile)) { throw "Missing file: $CallPlanFile" }
if (-not (Test-Path $PipelineFile)) { throw "Missing file: $PipelineFile" }

function Get-CleanPhone {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
    $digits = ($Value -replace '[^0-9]', '')
    if ($digits.Length -lt 10) { return "" }
    if ($digits.Length -eq 10) { return "+1$digits" }
    if ($digits.Length -eq 11 -and $digits.StartsWith("1")) { return "+$digits" }
    return "+$digits"
}

function Build-GoogleVoiceUrl {
    param([string]$Phone)
    $encoded = [uri]::EscapeDataString($Phone)
    return "https://voice.google.com/u/0/calls?a=nc,$encoded"
}

function Get-DefaultNextTouchDate {
    param(
        [string]$Outcome,
        [datetime]$Today
    )
    switch ($Outcome) {
        "meeting-booked" { return $Today.AddDays(1).ToString("yyyy-MM-dd") }
        "connected" { return $Today.AddDays(2).ToString("yyyy-MM-dd") }
        "voicemail" { return $Today.AddDays(3).ToString("yyyy-MM-dd") }
        "no-answer" { return $Today.AddDays(2).ToString("yyyy-MM-dd") }
        "not-now" { return $Today.AddDays(7).ToString("yyyy-MM-dd") }
        default { return "" }
    }
}

function Ensure-InteractionFile {
    param([string]$Path)
    if (Test-Path $Path) { return }
    $seed = [pscustomobject]@{
        interaction_id = ""
        date = ""
        company_name = ""
        contact_name = ""
        channel = ""
        direction = ""
        summary = ""
        outcome = ""
        next_action = ""
        next_touch_date = ""
        owner = ""
        created_at = ""
    }
    @($seed) | Export-Csv -Path $Path -NoTypeInformation
    $rows = Import-Csv -Path $Path | Where-Object { -not [string]::IsNullOrWhiteSpace($_.interaction_id) }
    $rows | Export-Csv -Path $Path -NoTypeInformation
}

function Ensure-FollowUpFile {
    param([string]$Path)
    if (Test-Path $Path) { return }
    $seed = [pscustomobject]@{
        event_id = ""
        source_interaction_id = ""
        company_name = ""
        contact_name = ""
        outcome = ""
        due_date = ""
        start_time = ""
        end_time = ""
        title = ""
        notes = ""
        status = ""
        created_at = ""
    }
    @($seed) | Export-Csv -Path $Path -NoTypeInformation
    $rows = Import-Csv -Path $Path | Where-Object { -not [string]::IsNullOrWhiteSpace($_.event_id) }
    $rows | Export-Csv -Path $Path -NoTypeInformation
}

function New-CalendarUid {
    param([string]$EventId)
    return ($EventId + "@bosskeyops.com")
}

function Write-FollowUpIcs {
    param(
        [string]$FollowUpPath,
        [string]$CalendarPath
    )

    Ensure-FollowUpFile -Path $FollowUpPath
    $rows = @(Import-Csv -Path $FollowUpPath) | Where-Object { $_.status -ne "cancelled" -and -not [string]::IsNullOrWhiteSpace($_.due_date) }

    $calDir = Split-Path -Parent $CalendarPath
    if (-not (Test-Path $calDir)) { New-Item -ItemType Directory -Force -Path $calDir | Out-Null }

    $ical = @()
    $ical += "BEGIN:VCALENDAR"
    $ical += "VERSION:2.0"
    $ical += "PRODID:-//Boss Key//Follow Ups//EN"
    $ical += "CALSCALE:GREGORIAN"
    $ical += "METHOD:PUBLISH"

    foreach ($r in $rows) {
        $startValue = if ([string]::IsNullOrWhiteSpace($r.start_time)) { "09:00" } else { $r.start_time }
        $endValue = if ([string]::IsNullOrWhiteSpace($r.end_time)) { "09:15" } else { $r.end_time }
        $startDt = [datetime]::ParseExact("$($r.due_date) $startValue", "yyyy-MM-dd HH:mm", $null)
        $endDt = [datetime]::ParseExact("$($r.due_date) $endValue", "yyyy-MM-dd HH:mm", $null)
        $summary = if ([string]::IsNullOrWhiteSpace($r.title)) { "Boss Key Follow-up - $($r.company_name)" } else { $r.title }
        $desc = if ([string]::IsNullOrWhiteSpace($r.notes)) { "Follow up with $($r.company_name)" } else { $r.notes }

        $ical += "BEGIN:VEVENT"
        $ical += "UID:$(New-CalendarUid -EventId $r.event_id)"
        $ical += "DTSTAMP:$((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'))"
        $ical += "DTSTART:$($startDt.ToString('yyyyMMddTHHmmss'))"
        $ical += "DTEND:$($endDt.ToString('yyyyMMddTHHmmss'))"
        $ical += "SUMMARY:$summary"
        $ical += "DESCRIPTION:$desc"
        $ical += "END:VEVENT"
    }

    $ical += "END:VCALENDAR"
    $ical -join [Environment]::NewLine | Set-Content -Path $CalendarPath -Encoding UTF8
}

function Get-FollowUpOffsets {
    param([string]$Outcome)
    switch ($Outcome) {
        "connected" { return @(2, 7) }
        "voicemail" { return @(2, 7) }
        "no-answer" { return @(2, 7) }
        "meeting-booked" { return @(1, 7) }
        "not-now" { return @(7, 14) }
        default { return @() }
    }
}

function Upsert-FollowUpEvents {
    param(
        [string]$FollowUpPath,
        [string]$CalendarPath,
        [object]$PendingCall,
        [string]$Outcome,
        [string]$NextAction,
        [string]$Summary,
        [datetime]$Today
    )
    Ensure-FollowUpFile -Path $FollowUpPath
    $rows = @(Import-Csv -Path $FollowUpPath)
    $offsets = Get-FollowUpOffsets -Outcome $Outcome
    if ($offsets.Count -eq 0) { return }

    foreach ($d in $offsets) {
        $due = $Today.AddDays([int]$d).ToString("yyyy-MM-dd")
        $eventId = "{0}-d{1}" -f $PendingCall.interaction_id, $d
        $title = "Follow-up call - $($PendingCall.company_name)"
        $notes = "Outcome: $Outcome | Next action: $NextAction | Notes: $Summary"

        $existing = $rows | Where-Object { $_.event_id -eq $eventId } | Select-Object -First 1
        if ($null -eq $existing) {
            $rows += [pscustomobject]@{
                event_id = $eventId
                source_interaction_id = $PendingCall.interaction_id
                company_name = $PendingCall.company_name
                contact_name = $PendingCall.contact_name
                outcome = $Outcome
                due_date = $due
                start_time = "09:00"
                end_time = "09:15"
                title = $title
                notes = $notes
                status = "planned"
                created_at = (Get-Date).ToString("s")
            }
        } else {
            $existing.outcome = $Outcome
            $existing.due_date = $due
            $existing.title = $title
            $existing.notes = $notes
            if ([string]::IsNullOrWhiteSpace($existing.status)) { $existing.status = "planned" }
        }
    }

    $rows | Export-Csv -Path $FollowUpPath -NoTypeInformation
    Write-FollowUpIcs -FollowUpPath $FollowUpPath -CalendarPath $CalendarPath
}

function Read-OutcomePrompt {
    Write-Host ""
    Write-Host "Log call outcome:"
    Write-Host "1) connected"
    Write-Host "2) voicemail"
    Write-Host "3) no-answer"
    Write-Host "4) bad-number"
    Write-Host "5) meeting-booked"
    Write-Host "6) not-now"
    Write-Host "7) not-fit"
    Write-Host "8) do-not-contact"

    $map = @{
        "1" = "connected"
        "2" = "voicemail"
        "3" = "no-answer"
        "4" = "bad-number"
        "5" = "meeting-booked"
        "6" = "not-now"
        "7" = "not-fit"
        "8" = "do-not-contact"
    }

    while ($true) {
        $choice = (Read-Host "Choose outcome number (1-8)").Trim()
        if ($map.ContainsKey($choice)) { return $map[$choice] }
        Write-Host "Invalid choice. Enter 1-8."
    }
}

function Get-StageFromOutcome {
    param([string]$Outcome, [string]$CurrentStage)
    switch ($Outcome) {
        "meeting-booked" { return "meeting-scheduled" }
        "connected" { return "connected" }
        "not-fit" { return "closed-lost" }
        "do-not-contact" { return "closed-lost" }
        default {
            if ([string]::IsNullOrWhiteSpace($CurrentStage)) { return "outreach-sent" }
            return $CurrentStage
        }
    }
}

function Get-StatusFromOutcome {
    param([string]$Outcome, [string]$CurrentStatus)
    switch ($Outcome) {
        "not-fit" { return "closed-lost" }
        "do-not-contact" { return "do-not-contact" }
        default {
            if ([string]::IsNullOrWhiteSpace($CurrentStatus)) { return "active" }
            return $CurrentStatus
        }
    }
}

function Save-State {
    param([object]$StateObj, [string]$Path)
    $StateObj.updated_at = (Get-Date).ToString("s")
    $StateObj | ConvertTo-Json -Depth 6 | Set-Content -Path $Path -Encoding UTF8
}

function Log-PendingCallOutcome {
    param(
        [object]$StateObj,
        [string]$InteractionPath,
        [string]$PipelinePath,
        [string]$FollowUpPath,
        [string]$FollowUpCalendarPath,
        [bool]$AutoFollowUps,
        [bool]$PromptEnabled
    )

    if ($null -eq $StateObj.pending_call) { return $false }
    if (-not $StateObj.pending_call.awaiting_log) { return $false }

    $pending = $StateObj.pending_call
    $today = Get-Date

    if (-not $PromptEnabled) {
        Write-Output ("Pending call not logged yet: {0}. Re-run without -NoPrompt to log it." -f $pending.company_name)
        return $false
    }

    Write-Output ""
    Write-Output ("Complete last call: {0} ({1})" -f $pending.company_name, $pending.contact_name)
    $rawOutcome = Read-OutcomePrompt
    if ($rawOutcome -is [array]) {
        $outcome = [string]$rawOutcome[0]
    } else {
        $outcome = [string]$rawOutcome
    }
    $defaultDate = Get-DefaultNextTouchDate -Outcome $outcome -Today $today
    $nextTouchInput = (Read-Host "Next touch date [yyyy-MM-dd] (default: $defaultDate)").Trim()
    $nextTouch = if ([string]::IsNullOrWhiteSpace($nextTouchInput)) { $defaultDate } else { $nextTouchInput }
    $nextAction = (Read-Host "Next action (short)").Trim()
    if ([string]::IsNullOrWhiteSpace($nextAction)) { $nextAction = "Follow-up" }
    $summary = (Read-Host "Call notes summary").Trim()
    if ([string]::IsNullOrWhiteSpace($summary)) {
        $summary = "Outcome logged via queue runner."
    }

    Ensure-InteractionFile -Path $InteractionPath
    $rows = @(Import-Csv -Path $InteractionPath)
    $interactionId = $pending.interaction_id
    $existing = $rows | Where-Object { $_.interaction_id -eq $interactionId } | Select-Object -First 1

    if ($null -eq $existing) {
        $rows += [pscustomobject]@{
            interaction_id = $interactionId
            date = $today.ToString("yyyy-MM-dd")
            company_name = $pending.company_name
            contact_name = $pending.contact_name
            channel = "call"
            direction = "outbound"
            summary = $summary
            outcome = $outcome
            next_action = $nextAction
            next_touch_date = $nextTouch
            owner = "Timmy Semenza"
            created_at = $today.ToString("s")
        }
    } else {
        $existing.date = $today.ToString("yyyy-MM-dd")
        $existing.summary = $summary
        $existing.outcome = $outcome
        $existing.next_action = $nextAction
        $existing.next_touch_date = $nextTouch
        $existing.owner = "Timmy Semenza"
        $existing.created_at = $today.ToString("s")
    }
    $rows | Export-Csv -Path $InteractionPath -NoTypeInformation

    $pipeline = @(Import-Csv -Path $PipelinePath)
    foreach ($p in $pipeline) {
        if ($p.company_name -ne $pending.company_name) { continue }
        $p.last_touch_date = $today.ToString("yyyy-MM-dd")
        if (-not [string]::IsNullOrWhiteSpace($nextTouch)) { $p.next_touch_date = $nextTouch }
        $p.stage = Get-StageFromOutcome -Outcome $outcome -CurrentStage $p.stage
        $p.status = Get-StatusFromOutcome -Outcome $outcome -CurrentStatus $p.status
        if ([string]::IsNullOrWhiteSpace($p.notes)) {
            $p.notes = $summary
        } else {
            $p.notes = ($p.notes + " | " + $today.ToString("yyyy-MM-dd") + ": " + $summary)
        }
    }
    $pipeline | Export-Csv -Path $PipelinePath -NoTypeInformation

    if ($AutoFollowUps) {
        Upsert-FollowUpEvents -FollowUpPath $FollowUpPath -CalendarPath $FollowUpCalendarPath -PendingCall $pending -Outcome $outcome -NextAction $nextAction -Summary $summary -Today $today
    }

    $StateObj.pending_call.awaiting_log = $false
    Save-State -StateObj $StateObj -Path $StateFile

    if ($AutoFollowUps) {
        Write-Output ("Logged outcome for {0}: {1}. Pipeline and follow-ups updated." -f $pending.company_name, $outcome)
    } else {
        Write-Output ("Logged outcome for {0}: {1}. Pipeline updated." -f $pending.company_name, $outcome)
    }
    return $true
}

$todayStr = if ([string]::IsNullOrWhiteSpace($Date)) { (Get-Date).ToString("yyyy-MM-dd") } else { ([datetime]$Date).ToString("yyyy-MM-dd") }
$calls = @(Import-Csv -Path $CallPlanFile) | Where-Object { $_.call_date -eq $todayStr } | Sort-Object { [int]$_.plan_order }
if ($calls.Count -eq 0) {
    Write-Output "No calls scheduled for $todayStr in $CallPlanFile"
    exit 0
}

$pipeline = @(Import-Csv -Path $PipelineFile)
$stateDir = Split-Path -Parent $StateFile
if (-not (Test-Path $stateDir)) { New-Item -ItemType Directory -Force -Path $stateDir | Out-Null }

if ($Reset -or -not (Test-Path $StateFile)) {
    $initial = @{
        call_date = $todayStr
        next_index = 0
        pending_call = $null
        updated_at = (Get-Date).ToString("s")
    }
    Save-State -StateObj $initial -Path $StateFile
}

$state = Get-Content -Raw -Path $StateFile | ConvertFrom-Json
if ($state.call_date -ne $todayStr) {
    $state.call_date = $todayStr
    $state.next_index = 0
    $state.pending_call = $null
    Save-State -StateObj $state -Path $StateFile
}
if (-not ($state.PSObject.Properties.Name -contains "pending_call")) {
    $state | Add-Member -NotePropertyName pending_call -NotePropertyValue $null
}

Log-PendingCallOutcome -StateObj $state -InteractionPath $InteractionFile -PipelinePath $PipelineFile -FollowUpPath $FollowUpFile -FollowUpCalendarPath $FollowUpCalendarFile -AutoFollowUps $(-not $DisableAutoFollowUps.IsPresent) -PromptEnabled $(-not $NoPrompt.IsPresent) | Out-Null

if ($LogOnly) {
    Write-Output "Log-only mode complete."
    exit 0
}

$idx = [int]$state.next_index
if ($idx -ge $calls.Count) {
    Write-Output "Queue complete for today. Use -Reset to run again."
    exit 0
}

$c = $calls[$idx]
$p = $pipeline | Where-Object { $_.company_name -eq $c.company_name } | Select-Object -First 1
$cleanPhone = Get-CleanPhone -Value $c.contact_phone

$hook1 = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.personalization_hook_1)) { "their current operation" } else { $p.personalization_hook_1 }
$hook2 = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.personalization_hook_2)) { "their contract mix" } else { $p.personalization_hook_2 }
$bottleneck = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.likely_bottleneck)) { "admin burden between bid and delivery" } else { $p.likely_bottleneck }
$angle = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.primary_angle)) { "reduce admin load and protect margin" } else { $p.primary_angle }
$notes = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.notes)) { "No notes captured yet." } else { $p.notes }

Write-Output ""
Write-Output ("Next Call [{0}/{1}] | {2}" -f ($idx + 1), $calls.Count, $c.company_name)
Write-Output ("Contact: {0} ({1})" -f $c.target_contact, $c.role)
Write-Output ("Phone: {0}" -f $(if ([string]::IsNullOrWhiteSpace($cleanPhone)) { "Invalid/unavailable" } else { $cleanPhone }))
Write-Output ("Why now: {0}" -f $c.reason)
Write-Output ("Hooks: {0} | {1}" -f $hook1, $hook2)
Write-Output ("Likely bottleneck: {0}" -f $bottleneck)
Write-Output ("Primary angle: {0}" -f $angle)
Write-Output ("Notes: {0}" -f $notes)
Write-Output ""
Write-Output "Talk track:"
Write-Output ("Hi {0}, this is Timmy Semenza with Boss Key in South Jersey. I help local cleaning operators cut office drag so they can move faster and protect margin." -f $(if ([string]::IsNullOrWhiteSpace($c.target_contact)) { "there" } else { $c.target_contact }))
Write-Output ("I noticed {0} and {1}. Are those creating any admin pressure right now?" -f $hook1, $hook2)
Write-Output "If helpful, I can run a short diagnostic and show the top 2-3 process fixes first."
Write-Output ""

if (-not [string]::IsNullOrWhiteSpace($cleanPhone)) {
    try {
        if ($DialMode -eq "tel") {
            Start-Process ("tel:" + $cleanPhone) | Out-Null
            Write-Output ("Dialer launched via tel: {0}" -f $cleanPhone)
        } elseif ($DialMode -eq "googlevoice") {
            $voiceUrl = Build-GoogleVoiceUrl -Phone $cleanPhone
            Start-Process $voiceUrl | Out-Null
            Write-Output ("Opened Google Voice: {0}" -f $voiceUrl)
        } else {
            Write-Output "DialMode=none: no app launched."
        }
    } catch {
        Write-Output ("Dialer launch failed. Call manually: {0}" -f $cleanPhone)
    }
} else {
    Write-Output "No valid phone number to launch."
}

$interactionId = "call-$($todayStr -replace '-','')-$('{0:d3}' -f ([int]$c.plan_order))"
$state.pending_call = @{
    interaction_id = $interactionId
    plan_order = [int]$c.plan_order
    company_name = $c.company_name
    contact_name = $c.target_contact
    role = $c.role
    call_date = $todayStr
    awaiting_log = $true
    created_at = (Get-Date).ToString("s")
}
$state.next_index = $idx + 1
Save-State -StateObj $state -Path $StateFile

$remaining = $calls.Count - [int]$state.next_index
Write-Output ("Queue updated. Remaining calls today: {0}" -f $remaining)
Write-Output "After the call, run this command again to log outcome and move to the next dial."
