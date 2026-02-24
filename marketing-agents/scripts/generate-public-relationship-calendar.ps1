param(
    [string]$TargetsFile = "marketing-agents/data/public_recompete_targets_burlco.csv",
    [string]$OutputMarkdown = "marketing-agents/briefs/generated/public-capture/public-relationship-calendar-30day.md",
    [string]$OutputIcs = "marketing-agents/briefs/generated/public-capture/public-relationship-calendar-30day.ics",
    [string]$StartDate = "",
    [int]$StartHour = 10
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $TargetsFile)) { throw "Missing file: $TargetsFile" }

function New-IcsDate([datetime]$dt) {
    return $dt.ToString("yyyyMMdd'T'HHmmss")
}

$start = if ([string]::IsNullOrWhiteSpace($StartDate)) { (Get-Date).Date } else { ([datetime]$StartDate).Date }
$targets = @(Import-Csv -Path $TargetsFile | Where-Object { $_.pursuit_decision -eq "pursue_now" })

if ($targets.Count -eq 0) {
    throw "No pursue_now targets found in $TargetsFile"
}

$events = @()
$targetIndex = 0
foreach ($t in $targets) {
    $slotOffsetHours = $targetIndex
    $baseName = [string]$t.entity_name
    $contact = if ([string]::IsNullOrWhiteSpace([string]$t.contact_name)) { [string]$t.office } else { [string]$t.contact_name }
    $phone = [string]$t.contact_phone
    $email = [string]$t.contact_email
    $office = [string]$t.office

    $events += [pscustomobject]@{
        date = $start.AddDays(1)
        start_hour = $StartHour + $slotOffsetHours
        duration = 30
        summary = "Send intro email + meeting request - $baseName"
        description = "Send community-first intro to $contact ($office). Ask for a 20-minute in-person meeting. Email: $email Phone: $phone"
    }
    $events += [pscustomobject]@{
        date = $start.AddDays(3)
        start_hour = $StartHour + $slotOffsetHours
        duration = 20
        summary = "Follow-up call - $baseName"
        description = "Call $contact to confirm receipt and request in-person intro. Phone: $phone"
    }
    $events += [pscustomobject]@{
        date = $start.AddDays(8)
        start_hour = $StartHour + $slotOffsetHours
        duration = 45
        summary = "Attend public meeting / in-person touchpoint - $baseName"
        description = "Show up in person, introduce yourself as local operator, and ask for best process to support pre-RFP planning."
    }
    $events += [pscustomobject]@{
        date = $start.AddDays(11)
        start_hour = $StartHour + $slotOffsetHours
        duration = 40
        summary = "Draft and deliver 1-page local modernization memo - $baseName"
        description = "Deliver tailored one-page memo with bloat hypothesis, proof points, and low-risk pilot recommendation."
    }
    $events += [pscustomobject]@{
        date = $start.AddDays(16)
        start_hour = $StartHour + $slotOffsetHours
        duration = 25
        summary = "Second follow-up call - $baseName"
        description = "Request update on meeting availability and procurement planning timeline."
    }
    $events += [pscustomobject]@{
        date = $start.AddDays(23)
        start_hour = $StartHour + $slotOffsetHours
        duration = 45
        summary = "In-person working session request - $baseName"
        description = "Propose short in-person working session on scope clarity and resident workflow improvements."
    }
    $events += [pscustomobject]@{
        date = $start.AddDays(29)
        start_hour = $StartHour + $slotOffsetHours
        duration = 30
        summary = "30-day account review and go/no-go refresh - $baseName"
        description = "Review relationship progress, update winability evidence, and decide next 30-day plan."
    }
    $targetIndex++
}

$events = @($events | Sort-Object date, start_hour, summary)

$md = @()
$md += "# 30-Day Public Relationship Calendar"
$md += ""
$md += "Start date: $($start.ToString('yyyy-MM-dd'))"
$md += "Targets: $($targets.Count)"
$md += ""
$md += "## Accounts"
foreach ($t in $targets) {
    $md += "- $($t.entity_name) | $($t.office) | $($t.contact_name) | $($t.contact_email) | $($t.contact_phone)"
}
$md += ""
$md += "## Calendar"
foreach ($e in $events) {
    $md += ("- {0} {1}:00 | {2} min | {3}" -f $e.date.ToString("yyyy-MM-dd"), $e.start_hour, $e.duration, $e.summary)
    $md += ("  Action: {0}" -f $e.description)
}

$mdDir = Split-Path -Parent $OutputMarkdown
if (-not (Test-Path $mdDir)) { New-Item -Path $mdDir -ItemType Directory -Force | Out-Null }
$md -join [Environment]::NewLine | Set-Content -Path $OutputMarkdown -Encoding UTF8

$ics = @()
$ics += "BEGIN:VCALENDAR"
$ics += "VERSION:2.0"
$ics += "PRODID:-//Boss Key//Public Relationship Calendar//EN"
$ics += "CALSCALE:GREGORIAN"
$ics += "METHOD:PUBLISH"
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMdd'T'HHmmss'Z'")

$i = 1
foreach ($e in $events) {
    $startDt = [datetime]::new($e.date.Year, $e.date.Month, $e.date.Day, [int]$e.start_hour, 0, 0)
    $endDt = $startDt.AddMinutes([int]$e.duration)
    $uid = ("rel-{0}-{1}@bosskeyops.com" -f $startDt.ToString("yyyyMMdd"), $i)

    $ics += "BEGIN:VEVENT"
    $ics += "UID:$uid"
    $ics += "DTSTAMP:$stamp"
    $ics += "DTSTART:$(New-IcsDate $startDt)"
    $ics += "DTEND:$(New-IcsDate $endDt)"
    $ics += ("SUMMARY:{0}" -f ($e.summary -replace ",", "\,"))
    $ics += ("DESCRIPTION:{0}" -f ($e.description -replace ",", "\,"))
    $ics += "END:VEVENT"
    $i++
}

$ics += "END:VCALENDAR"

$icsDir = Split-Path -Parent $OutputIcs
if (-not (Test-Path $icsDir)) { New-Item -Path $icsDir -ItemType Directory -Force | Out-Null }
$ics -join [Environment]::NewLine | Set-Content -Path $OutputIcs -Encoding UTF8

Write-Output ("Generated 30-day relationship calendar for {0} target(s)." -f $targets.Count)
Write-Output ("Markdown: {0}" -f $OutputMarkdown)
Write-Output ("ICS: {0}" -f $OutputIcs)
