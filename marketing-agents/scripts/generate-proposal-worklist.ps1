param(
    [string]$JobsFile = "marketing-agents/data/proposal_jobs.csv",
    [string]$OutputFile = "marketing-agents/data/proposal_worklist.csv",
    [int]$LookaheadDays = 14
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $JobsFile)) {
    throw "Jobs file not found: $JobsFile"
}

$today = (Get-Date).Date
$cutoff = $today.AddDays($LookaheadDays)

$rows = Import-Csv -Path $JobsFile

$openStages = @("intake", "drafting", "qa", "owner-review", "submission-ready")

$work = foreach ($r in $rows) {
    $stage = ($r.proposal_stage | ForEach-Object { $_.ToLowerInvariant().Trim() })
    if (-not ($openStages -contains $stage)) { continue }

    $deadline = $null
    if (-not [string]::IsNullOrWhiteSpace($r.submission_deadline)) {
        try { $deadline = [datetime]$r.submission_deadline } catch { $deadline = $null }
    }
    if (($deadline -ne $null) -and ($deadline.Date -gt $cutoff)) { continue }

    $daysToDeadline = if ($deadline -eq $null) { 999 } else { [int]($deadline.Date - $today).TotalDays }
    $priority = if ($daysToDeadline -le 2) { "critical" }
        elseif ($daysToDeadline -le 5) { "high" }
        elseif ($daysToDeadline -le 10) { "medium" }
        else { "normal" }

    [pscustomobject]@{
        job_id = $r.job_id
        client_name = $r.client_name
        opportunity_id = $r.opportunity_id
        proposal_stage = $r.proposal_stage
        submission_deadline = $r.submission_deadline
        days_to_deadline = $daysToDeadline
        priority = $priority
        owner_approval_status = $r.owner_approval_status
        compliance_status = $r.compliance_status
        next_internal_review = $r.next_internal_review
        primary_risk = $r.primary_risk
        notes = $r.notes
    }
}

$work | Sort-Object -Property @{Expression = "days_to_deadline"; Descending = $false} |
    Export-Csv -Path $OutputFile -NoTypeInformation

Write-Output ("Generated proposal worklist: {0} items -> {1}" -f $work.Count, $OutputFile)
