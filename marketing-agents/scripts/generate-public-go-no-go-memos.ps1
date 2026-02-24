param(
    [string]$TargetsFile = "marketing-agents/data/public_recompete_targets_burlco.csv",
    [string]$OutputRoot = "marketing-agents/briefs/generated/go-no-go",
    [string]$Date = "",
    [switch]$IncludeWatchlist
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $TargetsFile)) { throw "Missing file: $TargetsFile" }

function Get-SafeInt([string]$value, [int]$fallback = 0) {
    $n = 0
    if ([int]::TryParse([string]$value, [ref]$n)) { return $n }
    return $fallback
}

function Get-Slug([string]$value) {
    $s = ($value -replace "[^A-Za-z0-9]+", "-").Trim("-").ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($s)) { return "target" }
    return $s
}

$runDate = if ([string]::IsNullOrWhiteSpace($Date)) { (Get-Date).ToString("yyyy-MM-dd") } else { ([datetime]$Date).ToString("yyyy-MM-dd") }
$rows = @(Import-Csv -Path $TargetsFile)

$selected = if ($IncludeWatchlist) {
    $rows | Where-Object { $_.pursuit_decision -in @("pursue_now", "watchlist_capacity") }
} else {
    $rows | Where-Object { $_.pursuit_decision -eq "pursue_now" }
}

$selected = @($selected | Sort-Object @{Expression = { Get-SafeInt $_.qualification_score }; Descending = $true}, @{Expression = { Get-SafeInt $_.winability_score }; Descending = $true})

$outDir = Join-Path $OutputRoot $runDate
if (-not (Test-Path $outDir)) { New-Item -Path $outDir -ItemType Directory -Force | Out-Null }

$indexLines = @()
$indexLines += "# Public Capture GO-NO-GO Memos - $runDate"
$indexLines += ""
$indexLines += "Scope: $(if ($IncludeWatchlist) { "pursue_now + watchlist_capacity" } else { "pursue_now only" })"
$indexLines += ""

if ($selected.Count -eq 0) {
    $indexLines += "_No targets matched the current filter._"
} else {
    $indexLines += "## Targets"
    foreach ($r in $selected) {
        $targetSlug = Get-Slug ([string]$r.target_id)
        $memoFile = "go-no-go-$targetSlug-$runDate.md"
        $memoPath = Join-Path $outDir $memoFile

        $qualification = Get-SafeInt ([string]$r.qualification_score)
        $winability = Get-SafeInt ([string]$r.winability_score)
        $community = Get-SafeInt ([string]$r.community_fit_score)
        $decision = if ([string]$r.pursuit_decision -eq "pursue_now") { "GO" } else { "NO-GO" }
        $confidence = if ($qualification -ge 95) { "High" } elseif ($qualification -ge 80) { "Medium" } else { "Low" }
        $direct = [string]$r.direct_contact_identified
        $noTouch = [string]$r.no_touch_gate

        $lines = @()
        $lines += "# GO-NO-GO Memo - $($r.entity_name)"
        $lines += ""
        $lines += "Date: $runDate"
        $lines += "Target ID: $($r.target_id)"
        $lines += "Decision: **$decision**"
        $lines += "Confidence: **$confidence**"
        $lines += ""
        $lines += "## Score Snapshot"
        $lines += "- Qualification: $qualification"
        $lines += "- Winability: $winability"
        $lines += "- Community Fit: $community"
        $lines += "- No-touch Gate: $noTouch"
        $lines += "- Direct Contact Identified: $direct"
        $lines += ""
        $lines += "## Why This Decision"
        $lines += "- Pursuit status from radar: $($r.pursuit_decision)"
        $lines += "- Primary bloat hypothesis: $($r.bloat_hypothesis)"
        $lines += "- Required proof before commit: $($r.proof_required)"
        $lines += "- Kill criteria: $($r.kill_criteria)"
        $lines += ""
        $lines += "## Relationship Plan"
        $lines += "- Office: $($r.office)"
        $lines += "- Contact: $($r.contact_name) ($($r.contact_role))"
        $lines += "- Email: $($r.contact_email)"
        $lines += "- Phone: $($r.contact_phone)"
        $lines += "- In-person path: $($r.relationship_path)"
        $lines += ""
        $lines += "## Pre-RFP Action Plan (Next 14 Days)"
        $lines += "1. Execute prewire actions: $($r.prewire_actions)"
        $lines += "2. Request in-person intro meeting and confirm procurement calendar."
        $lines += "3. Produce one-page local modernization memo tailored to this entity."
        $lines += ""
        $lines += "## Commercial Shape"
        $lines += "- Offer: $($r.offer_name)"
        $lines += ('- One-time value target: `${0}`' -f [string]$r.est_one_time_value)
        $lines += ('- Monthly retainer target: `${0}`' -f [string]$r.est_monthly_retainer)
        $lines += "- Estimated delivery hours/week: $($r.est_hours_per_week)"
        $lines += ""
        $lines += "## Source"
        $lines += "- $($r.source_url)"
        if (-not [string]::IsNullOrWhiteSpace([string]$r.source_url_2)) {
            $lines += "- $($r.source_url_2)"
        }

        $lines -join [Environment]::NewLine | Set-Content -Path $memoPath -Encoding UTF8

        $indexLines += "- $($r.entity_name) | $decision | qual $qualification | win $winability | community $community | memo: $memoFile"
    }
}

$indexPath = Join-Path $outDir ("go-no-go-index-$runDate.md")
$indexLines -join [Environment]::NewLine | Set-Content -Path $indexPath -Encoding UTF8

Write-Output ("Generated {0} memo(s)." -f $selected.Count)
Write-Output ("Index: {0}" -f $indexPath)
