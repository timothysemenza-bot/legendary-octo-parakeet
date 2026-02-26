param(
    [string]$TargetFile = "marketing-agents/briefs/st-moritz-target-account-list-2026-02-25.csv",
    [string]$CrossRefFile = "",
    [string]$OutputFile = "marketing-agents/data/security_lookalike_campaign_pipeline.csv",
    [string]$RunDate = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $TargetFile)) { throw "Missing target file: $TargetFile" }
$today = if ([string]::IsNullOrWhiteSpace($RunDate)) { (Get-Date).ToString("yyyy-MM-dd") } else { ([datetime]$RunDate).ToString("yyyy-MM-dd") }

$targets = @(Import-Csv -Path $TargetFile)
$xref = @()
if (-not [string]::IsNullOrWhiteSpace($CrossRefFile) -and (Test-Path $CrossRefFile)) {
    $xref = @(Import-Csv -Path $CrossRefFile)
}

function Get-PriorityScore {
    param([string]$Tier)
    switch (($Tier | ForEach-Object { $_.Trim().ToUpperInvariant() })) {
        "P1" { return 95 }
        "P2" { return 85 }
        "P3" { return 75 }
        default { return 70 }
    }
}

function Get-RoleHint {
    param([string]$BuyerTitles)
    if ([string]::IsNullOrWhiteSpace($BuyerTitles)) { return "VP Sales" }
    return (($BuyerTitles -split ";")[0]).Trim()
}

function Get-OfferAngle {
    param([string]$Offer)
    switch (($Offer | ForEach-Object { $_.Trim().ToLowerInvariant() })) {
        "managed retainer" { return "Standardize RFP digest execution with fixed monthly delivery and CFO-visible outputs." }
        "light advisory" { return "Establish repeatable digest process with lighter monthly support and leadership coaching." }
        "pilot sprint" { return "Run a fixed-fee proof sprint to validate cycle-time and risk-visibility improvements." }
        default { return "Improve proposal speed and confidence with structured digest workflows." }
    }
}

$rows = @()
foreach ($t in $targets) {
    $name = [string]$t.account_name
    if ([string]::IsNullOrWhiteSpace($name)) { continue }

    $warmPath = ""
    $warmMatches = ""
    if ($xref.Count -gt 0) {
        $match = $xref | Where-Object { $_.account_name -eq $name } | Select-Object -First 1
        if ($null -ne $match) {
            $warmPath = [string]$match.linkedin_warm_path
            $warmMatches = [string]$match.linkedin_matches
        }
    }

    $offer = [string]$t.recommended_offer
    $annual = [string]$t.annual_value_usd
    $priorityTier = [string]$t.priority_tier
    $score = Get-PriorityScore -Tier $priorityTier
    $roleHint = Get-RoleHint -BuyerTitles ([string]$t.buyer_titles)
    $primaryAngle = Get-OfferAngle -Offer $offer
    $notes = @(
        ("campaign=security-lookalike-outbound"),
        ("priority_tier=" + $priorityTier),
        ("recommended_offer=" + $offer),
        ("annual_value_usd=" + $annual),
        ("segment=" + [string]$t.segment),
        ("warm_path=" + $warmPath),
        ("warm_matches=" + $warmMatches)
    ) -join " | "

    $rows += [pscustomobject]@{
        company_name = $name
        website = [string]$t.website
        location = ""
        target_contact = "Target Buyer"
        role = $roleHint
        contact_email = ""
        contact_phone = ""
        services_or_contract_focus = [string]$t.segment
        personalization_hook_1 = [string]$t.why_fit
        personalization_hook_2 = [string]$t.first_message_angle
        likely_bottleneck = "RFP digest speed, requirement traceability, and stakeholder alignment"
        primary_angle = $primaryAngle
        priority_score = $score
        last_touch_date = ""
        next_touch_date = $today
        stage = "research"
        status = "active"
        notes = $notes
        priority_tier = $priorityTier
        recommended_offer = $offer
        annual_value_usd = $annual
        buyer_titles = [string]$t.buyer_titles
        linkedin_warm_path = $warmPath
        linkedin_matches = $warmMatches
    }
}

$rows | Sort-Object @{Expression = {[int]$_.priority_score}; Descending = $true}, company_name |
    Export-Csv -Path $OutputFile -NoTypeInformation

Write-Output ("Built campaign pipeline: {0} rows -> {1}" -f $rows.Count, $OutputFile)
