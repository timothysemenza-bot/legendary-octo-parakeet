param(
    [string]$Date = "",
    [string]$CadenceFile = "marketing-agents/data/linkedin_writing_cadence.csv",
    [string]$OutputDir = "marketing-agents/briefs",
    [switch]$OpenInNotepad
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $CadenceFile)) { throw "Missing file: $CadenceFile" }
if (-not (Test-Path $OutputDir)) { New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null }

$runDate = if ([string]::IsNullOrWhiteSpace($Date)) { Get-Date } else { [datetime]$Date }
$dateText = $runDate.ToString("yyyy-MM-dd")
$cadence = @(Import-Csv -Path $CadenceFile)
if ($cadence.Count -eq 0) { throw "Cadence is empty: $CadenceFile" }

# Use weekday rotation Monday=1 ... Saturday=6, Sunday defaults to 1
$dayOfWeek = [int]$runDate.DayOfWeek
$dayIndex = switch ($dayOfWeek) {
    1 { 1 } # Monday
    2 { 2 }
    3 { 3 }
    4 { 4 }
    5 { 5 }
    6 { 6 } # Saturday
    default { 1 } # Sunday
}

$row = $cadence | Where-Object { [int]$_.day_index -eq $dayIndex } | Select-Object -First 1
if ($null -eq $row) {
    $row = $cadence | Select-Object -First 1
}

$outFile = Join-Path $OutputDir ("linkedin-writing-prompt-{0}.md" -f $dateText)

$content = @"
# LinkedIn Writing Prompt - $dateText

Post type: $($row.post_type)
Angle: $($row.angle)
CTA: $($row.cta)

## Prompt
$($row.writing_prompt)

## Your Draft
Write your post below in your own voice:



## Self-check before posting
- Is this written in your words, not generic language?
- Did you include one specific observation from real work?
- Is the CTA clear and singular?
- Is the post 5-10 lines and easy to scan?
"@

$content | Set-Content -Path $outFile -Encoding UTF8
Write-Output ("Generated LinkedIn writing prompt: {0}" -f $outFile)

if ($OpenInNotepad) {
    Start-Process notepad.exe $outFile | Out-Null
}
