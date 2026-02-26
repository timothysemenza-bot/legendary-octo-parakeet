param(
    [string]$ProspectPipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$SecurityPipelineFile = "marketing-agents/data/security_lookalike_campaign_pipeline_enriched.csv",
    [string]$ManualApmpFile = "marketing-agents/data/apmp_member_prospects.csv",
    [string]$OutputCsv = "marketing-agents/data/apmp_linkedin_targets.csv",
    [string]$BriefDir = "marketing-agents/briefs",
    [string]$RunDate = "",
    [int]$MaxRows = 30,
    [int]$MinScore = 70,
    [bool]$IncludeProspectPipeline = $false,
    [bool]$IncludeSecurityPipeline = $false,
    [string]$ExcludeCompanyKeywords = "security;guard;janitorial;cleaning;facility"
)

$ErrorActionPreference = "Stop"

function To-IntOrDefault {
    param(
        [string]$Value,
        [int]$DefaultValue = 70
    )
    $parsed = 0
    if ([int]::TryParse(([string]$Value), [ref]$parsed)) {
        return $parsed
    }
    return $DefaultValue
}

function Build-LinkedInSearchUrl {
    param(
        [string]$Company,
        [string]$Title
    )
    $query = "$Company $Title LinkedIn"
    return "https://www.linkedin.com/search/results/all/?keywords=" + [uri]::EscapeDataString($query)
}

function Has-ProposalSignal {
    param(
        [string]$Title,
        [string]$Angle,
        [string]$Notes,
        [string]$Focus
    )
    $text = (([string]$Title) + " " + ([string]$Angle) + " " + ([string]$Notes) + " " + ([string]$Focus)).ToLowerInvariant()
    return ($text -match "proposal|bid|capture|rfp|tender|pursuit|estimator")
}

function Is-CompanyExcluded {
    param(
        [string]$CompanyName,
        [string]$Keywords
    )
    $name = ([string]$CompanyName).ToLowerInvariant()
    foreach ($k in ($Keywords -split ";" | ForEach-Object { $_.Trim().ToLowerInvariant() } | Where-Object { $_ })) {
        if ($name -match [regex]::Escape($k)) { return $true }
    }
    return $false
}

function Get-Score {
    param(
        [string]$Source,
        [string]$Title,
        [string]$Location,
        [string]$Stage,
        [string]$Status,
        [int]$PriorityScore,
        [string]$PrimaryAngle,
        [string]$Notes,
        [string]$ContactEmail
    )

    # Weighted score: keep spread meaningful so ranking is actionable.
    $score = [math]::Round($PriorityScore * 0.55)
    $titleLower = ([string]$Title).ToLowerInvariant()
    $stageLower = ([string]$Stage).ToLowerInvariant()
    $statusLower = ([string]$Status).ToLowerInvariant()
    $locationLower = ([string]$Location).ToLowerInvariant()
    $angleLower = ([string]$PrimaryAngle).ToLowerInvariant()
    $notesLower = ([string]$Notes).ToLowerInvariant()
    $emailLower = ([string]$ContactEmail).ToLowerInvariant()

    if ($Source -eq "apmp_manual") { $score += 8 }

    if ($titleLower -match "proposal|bid|capture|pursuit|business development|bd") { $score += 8 }
    if ($titleLower -match "director|head|vp|vice president|chief|owner|principal|founder") { $score += 6 }
    elseif ($titleLower -match "manager|lead") { $score += 3 }

    if ($stageLower -in @("research", "engaged", "nurture")) { $score += 3 }
    if ($statusLower -eq "active") { $score += 3 }

    if ($locationLower -match "new jersey|south jersey|philadelphia|pennsylvania|new york|delaware|liberty") { $score += 4 }

    if ($angleLower -match "proposal|rfp|capture|bid|compliance") { $score += 5 }

    if (-not [string]::IsNullOrWhiteSpace($emailLower)) { $score += 2 }

    if ($stageLower -match "disqualified|closed-lost" -or $notesLower -match "no_touch_reject") { $score -= 25 }
    if ($statusLower -in @("inactive", "closed", "blocked")) { $score -= 15 }

    if ($score -lt 0) { $score = 0 }
    if ($score -gt 100) { $score = 100 }
    return $score
}

function Get-Tier {
    param([int]$Score)
    if ($Score -ge 78) { return "P1" }
    if ($Score -ge 70) { return "P2" }
    return "P3"
}

function Ensure-ManualApmpFile {
    param([string]$Path)
    if (Test-Path $Path) { return }

    @() | Select-Object full_name,company_name,title,location,linkedin_url,contact_email,source_notes |
        Export-Csv -Path $Path -NoTypeInformation
}

$today = if ([string]::IsNullOrWhiteSpace($RunDate)) { (Get-Date).ToString("yyyy-MM-dd") } else { ([datetime]$RunDate).ToString("yyyy-MM-dd") }

Ensure-ManualApmpFile -Path $ManualApmpFile

$prospectRows = @()
$securityRows = @()
if ($IncludeProspectPipeline) {
    if (-not (Test-Path $ProspectPipelineFile)) { throw "Missing file: $ProspectPipelineFile" }
    $prospectRows = @(Import-Csv -Path $ProspectPipelineFile)
}
if ($IncludeSecurityPipeline) {
    if (-not (Test-Path $SecurityPipelineFile)) { throw "Missing file: $SecurityPipelineFile" }
    $securityRows = @(Import-Csv -Path $SecurityPipelineFile)
}
$manualRows = @(Import-Csv -Path $ManualApmpFile)

$candidates = @()

foreach ($r in $prospectRows) {
    $company = [string]$r.company_name
    if ([string]::IsNullOrWhiteSpace($company)) { continue }
    if (Is-CompanyExcluded -CompanyName $company -Keywords $ExcludeCompanyKeywords) { continue }

    $title = if ([string]::IsNullOrWhiteSpace([string]$r.role)) { "Proposal Manager" } else { [string]$r.role }
    if (-not (Has-ProposalSignal -Title $title -Angle ([string]$r.primary_angle) -Notes ([string]$r.notes) -Focus ([string]$r.services_or_contract_focus))) { continue }
    $score = Get-Score `
        -Source "prospect_pipeline" `
        -Title $title `
        -Location ([string]$r.location) `
        -Stage ([string]$r.stage) `
        -Status ([string]$r.status) `
        -PriorityScore (To-IntOrDefault -Value ([string]$r.priority_score) -DefaultValue 70) `
        -PrimaryAngle ([string]$r.primary_angle) `
        -Notes ([string]$r.notes) `
        -ContactEmail ([string]$r.contact_email)

    $whyFit = if ([string]::IsNullOrWhiteSpace([string]$r.primary_angle)) {
        "Likely high volume process pressure in proposal and handoff workflow."
    } else {
        [string]$r.primary_angle
    }

    $candidates += [pscustomobject]@{
        run_date = $today
        source = "prospect_pipeline"
        company_name = $company
        person_name = [string]$r.target_contact
        target_title = $title
        location = [string]$r.location
        website = [string]$r.website
        linkedin_url = ""
        linkedin_search_url = Build-LinkedInSearchUrl -Company $company -Title $title
        contact_email = [string]$r.contact_email
        stage = [string]$r.stage
        status = [string]$r.status
        priority_score = To-IntOrDefault -Value ([string]$r.priority_score) -DefaultValue 70
        icp_score = $score
        icp_tier = Get-Tier -Score $score
        why_fit = $whyFit
        next_action = "Connect on LinkedIn and ask for a 20-minute workflow exchange."
        notes = [string]$r.notes
    }
}

foreach ($r in $securityRows) {
    $company = [string]$r.company_name
    if ([string]::IsNullOrWhiteSpace($company)) { continue }
    if (Is-CompanyExcluded -CompanyName $company -Keywords $ExcludeCompanyKeywords) { continue }

    $titleHints = @()
    if (-not [string]::IsNullOrWhiteSpace([string]$r.buyer_titles)) {
        $titleHints = @(([string]$r.buyer_titles -split ";") | ForEach-Object { $_.Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 2)
    }
    if ($titleHints.Count -eq 0) {
        $titleHints = @(
            if ([string]::IsNullOrWhiteSpace([string]$r.role)) { "Proposal Manager" } else { [string]$r.role }
        )
    }

    foreach ($title in $titleHints) {
        if (-not (Has-ProposalSignal -Title $title -Angle ([string]$r.primary_angle) -Notes ([string]$r.notes) -Focus ([string]$r.services_or_contract_focus))) { continue }

        $score = Get-Score `
            -Source "security_pipeline" `
            -Title $title `
            -Location ([string]$r.location) `
            -Stage ([string]$r.stage) `
            -Status ([string]$r.status) `
            -PriorityScore (To-IntOrDefault -Value ([string]$r.priority_score) -DefaultValue 75) `
            -PrimaryAngle ([string]$r.primary_angle) `
            -Notes ([string]$r.notes) `
            -ContactEmail ([string]$r.contact_email)

        $candidates += [pscustomobject]@{
            run_date = $today
            source = "security_pipeline"
            company_name = $company
            person_name = [string]$r.target_contact
            target_title = $title
            location = [string]$r.location
            website = [string]$r.website
            linkedin_url = ""
            linkedin_search_url = Build-LinkedInSearchUrl -Company $company -Title $title
            contact_email = [string]$r.contact_email
            stage = [string]$r.stage
            status = [string]$r.status
            priority_score = To-IntOrDefault -Value ([string]$r.priority_score) -DefaultValue 75
            icp_score = $score
            icp_tier = Get-Tier -Score $score
            why_fit = [string]$r.primary_angle
            next_action = "Send connection request with APMP peer context and ask one workflow pain question."
            notes = [string]$r.notes
        }
    }
}

foreach ($r in $manualRows) {
    $company = [string]$r.company_name
    if ([string]::IsNullOrWhiteSpace($company)) { continue }
    if (Is-CompanyExcluded -CompanyName $company -Keywords $ExcludeCompanyKeywords) { continue }

    $title = if ([string]::IsNullOrWhiteSpace([string]$r.title)) { "Proposal Manager" } else { [string]$r.title }
    $score = Get-Score `
        -Source "apmp_manual" `
        -Title $title `
        -Location ([string]$r.location) `
        -Stage "research" `
        -Status "active" `
        -PriorityScore 80 `
        -PrimaryAngle "APMP practitioner relationship with sponsor-intro potential." `
        -Notes ([string]$r.source_notes) `
        -ContactEmail ([string]$r.contact_email)

    $candidates += [pscustomobject]@{
        run_date = $today
        source = "apmp_manual"
        company_name = $company
        person_name = [string]$r.full_name
        target_title = $title
        location = [string]$r.location
        website = ""
        linkedin_url = [string]$r.linkedin_url
        linkedin_search_url = if ([string]::IsNullOrWhiteSpace([string]$r.linkedin_url)) { Build-LinkedInSearchUrl -Company $company -Title $title } else { [string]$r.linkedin_url }
        contact_email = [string]$r.contact_email
        stage = "research"
        status = "active"
        priority_score = 80
        icp_score = $score
        icp_tier = Get-Tier -Score $score
        why_fit = "APMP relationship with direct context on proposal workflow pain."
        next_action = "Message as APMP peer and request a short workflow exchange."
        notes = [string]$r.source_notes
    }
}

$targetList = $candidates |
    Group-Object company_name,target_title |
    ForEach-Object { $_.Group | Sort-Object @{Expression = {[int]$_.icp_score}; Descending = $true} | Select-Object -First 1 } |
    Where-Object { [int]$_.icp_score -ge $MinScore } |
    Sort-Object @{Expression = {[int]$_.icp_score}; Descending = $true}, company_name, target_title |
    Select-Object -First $MaxRows

$targetList | Export-Csv -Path $OutputCsv -NoTypeInformation

if (-not (Test-Path $BriefDir)) {
    New-Item -ItemType Directory -Path $BriefDir | Out-Null
}

$briefPath = Join-Path $BriefDir ("apmp-linkedin-targets-" + $today + ".md")
$p1Count = @($targetList | Where-Object { $_.icp_tier -eq "P1" }).Count
$p2Count = @($targetList | Where-Object { $_.icp_tier -eq "P2" }).Count
$manualCount = @($targetList | Where-Object { $_.source -eq "apmp_manual" }).Count

$lines = @()
$lines += "# APMP LinkedIn Target List - $today"
$lines += ""
$lines += "Rows selected: $($targetList.Count)"
$lines += "Tier mix: P1=$p1Count | P2=$p2Count"
$lines += "Manual APMP contacts in list: $manualCount"
$lines += "Source switches: IncludeProspectPipeline=$IncludeProspectPipeline | IncludeSecurityPipeline=$IncludeSecurityPipeline"
$lines += ""
$lines += "## Top Targets"

$rank = 1
foreach ($row in $targetList) {
    $displayName = if ([string]::IsNullOrWhiteSpace([string]$row.person_name)) { "Target contact" } else { [string]$row.person_name }
    $lines += ("$rank. {0} | {1} | score {2} ({3}) | source {4}" -f $row.company_name, $row.target_title, $row.icp_score, $row.icp_tier, $row.source)
    $lines += ("   - Contact: {0}" -f $displayName)
    $lines += ("   - Why fit: {0}" -f $row.why_fit)
    $lines += ("   - Next action: {0}" -f $row.next_action)
    $lines += ("   - LinkedIn: {0}" -f $row.linkedin_search_url)
    $rank++
}

$lines += ""
$lines += "## Weekly Rhythm"
$lines += "1. Send 5-8 connection requests from the top of this list."
$lines += "2. Book 3-4 peer workflow exchanges."
$lines += "3. Ask each practitioner for one sponsor intro."
$lines += "4. Move qualified accounts into prospect_pipeline with next-touch dates."

$lines | Set-Content -Path $briefPath -Encoding UTF8

Write-Output ("APMP LinkedIn targets ready: {0} rows -> {1}" -f $targetList.Count, $OutputCsv)
Write-Output ("Brief: {0}" -f $briefPath)
Write-Output ("Tip: add manual APMP contacts in {0} before the next run." -f $ManualApmpFile)
