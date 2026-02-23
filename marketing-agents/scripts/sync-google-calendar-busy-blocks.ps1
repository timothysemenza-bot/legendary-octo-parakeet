param(
    [Parameter(Mandatory = $true)][string]$IcsUrl,
    [string]$OutputFile = "marketing-agents/data/busy_blocks.csv",
    [int]$DaysBack = 1,
    [int]$DaysAhead = 21,
    [switch]$IncludeAllDay
)

$ErrorActionPreference = "Stop"

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
    if ($v -match '^\d{8}T\d{6}$') {
        return [datetime]::ParseExact($v, "yyyyMMdd'T'HHmmss", $null)
    }
    if ($v -match '^\d{8}T\d{4}$') {
        return [datetime]::ParseExact($v, "yyyyMMdd'T'HHmm", $null)
    }
    return $null
}

function Unfold-IcsLines {
    param([string]$IcsText)
    $raw = $IcsText -split "`r?`n"
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($line in $raw) {
        if (($line.StartsWith(" ") -or $line.StartsWith("`t")) -and $out.Count -gt 0) {
            $prev = $out[$out.Count - 1]
            $out[$out.Count - 1] = $prev + $line.TrimStart()
        } else {
            $out.Add($line)
        }
    }
    return $out
}

$windowStart = (Get-Date).Date.AddDays(-1 * [Math]::Abs($DaysBack))
$windowEnd = (Get-Date).Date.AddDays([Math]::Abs($DaysAhead) + 1)

$ics = (Invoke-WebRequest -Uri $IcsUrl -UseBasicParsing -TimeoutSec 25).Content
$lines = Unfold-IcsLines -IcsText $ics

$events = @()
$inEvent = $false
$startRaw = ""
$endRaw = ""
$summary = ""
$allDay = $false

foreach ($line in $lines) {
    if ($line -eq "BEGIN:VEVENT") {
        $inEvent = $true
        $startRaw = ""
        $endRaw = ""
        $summary = ""
        $allDay = $false
        continue
    }
    if ($line -eq "END:VEVENT") {
        if ($inEvent) {
            $s = Parse-IcsDateTime -Value $startRaw
            $e = Parse-IcsDateTime -Value $endRaw
            if ($null -ne $s -and $null -ne $e -and $e -gt $s) {
                if ($allDay -and -not $IncludeAllDay.IsPresent) {
                    # skip all-day by default
                } elseif ($e -gt $windowStart -and $s -lt $windowEnd) {
                    $title = if ([string]::IsNullOrWhiteSpace($summary)) { "Calendar event" } else { $summary }
                    $events += [pscustomobject]@{
                        start = $s.ToString("yyyy-MM-dd HH:mm")
                        end = $e.ToString("yyyy-MM-dd HH:mm")
                        title = $title
                        source = "google-calendar"
                    }
                }
            }
        }
        $inEvent = $false
        continue
    }
    if (-not $inEvent) { continue }

    if ($line -match '^DTSTART(;[^:]*)?:(.+)$') {
        $meta = $matches[1]
        $startRaw = $matches[2].Trim()
        if ($meta -and $meta -match 'VALUE=DATE') { $allDay = $true }
        continue
    }
    if ($line -match '^DTEND(;[^:]*)?:(.+)$') {
        $endRaw = $matches[2].Trim()
        continue
    }
    if ($line -match '^SUMMARY:(.+)$') {
        $summary = $matches[1].Trim()
        continue
    }
}

$rows = @($events | Sort-Object start, end, title)
$outDir = Split-Path -Parent $OutputFile
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
$rows | Export-Csv -Path $OutputFile -NoTypeInformation

Write-Output ("Imported {0} busy blocks from Google Calendar into {1}" -f $rows.Count, $OutputFile)
