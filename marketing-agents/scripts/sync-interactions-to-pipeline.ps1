param(
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$InteractionFile = "marketing-agents/data/interaction_log.csv",
    [int]$DefaultFollowUpDays = 3
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $PipelineFile)) {
    throw "Pipeline file not found: $PipelineFile"
}
if (-not (Test-Path $InteractionFile)) {
    throw "Interaction file not found: $InteractionFile"
}

$pipeline = Import-Csv -Path $PipelineFile
$interactions = Import-Csv -Path $InteractionFile

if ($interactions.Count -eq 0) {
    Write-Output "No interactions to process."
    exit 0
}

$latestByCompany = $interactions |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_.company_name) } |
    Group-Object -Property company_name |
    ForEach-Object {
        $_.Group |
            Sort-Object -Property @{Expression = {
                try { [datetime]$_.date } catch { [datetime]"1900-01-01" }
            }; Descending = $true } |
            Select-Object -First 1
    }

$updated = 0
foreach ($interaction in $latestByCompany) {
    $company = $interaction.company_name
    $row = $pipeline | Where-Object { $_.company_name -eq $company } | Select-Object -First 1
    if ($null -eq $row) { continue }

    $touchDate = $null
    try { $touchDate = [datetime]$interaction.date } catch { $touchDate = Get-Date }

    $nextTouch = $touchDate.AddDays($DefaultFollowUpDays).ToString("yyyy-MM-dd")
    if (-not [string]::IsNullOrWhiteSpace($interaction.next_touch_date)) {
        $nextTouch = $interaction.next_touch_date
    }

    $row.last_touch_date = $touchDate.ToString("yyyy-MM-dd")
    $row.next_touch_date = $nextTouch

    if (-not [string]::IsNullOrWhiteSpace($interaction.outcome)) {
        $o = $interaction.outcome.ToLowerInvariant()
        if ($o -match "meeting scheduled") {
            $row.stage = "meeting-scheduled"
            $row.status = "active"
        } elseif ($o -match "interested|positive|replied") {
            $row.stage = "connected"
            $row.status = "active"
        } elseif ($o -match "no response|voicemail") {
            if ([string]::IsNullOrWhiteSpace($row.stage)) { $row.stage = "outreach-sent" }
            if ([string]::IsNullOrWhiteSpace($row.status)) { $row.status = "active" }
        } elseif ($o -match "not interested|declined") {
            $row.status = "nurture"
        }
    }

    $existingNotes = if ([string]::IsNullOrWhiteSpace($row.notes)) { "" } else { $row.notes + " | " }
    $noteStamp = $touchDate.ToString("yyyy-MM-dd")
    $summary = $interaction.summary
    if ($summary.Length -gt 140) { $summary = $summary.Substring(0, 140) }
    $row.notes = "{0}{1}: {2}" -f $existingNotes, $noteStamp, $summary
    $updated++
}

$pipeline | Export-Csv -Path $PipelineFile -NoTypeInformation
Write-Output ("Updated {0} pipeline rows from interaction log." -f $updated)
