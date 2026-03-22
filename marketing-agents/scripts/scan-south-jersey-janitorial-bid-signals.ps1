param(
    [datetime]$AsOfDate = (Get-Date),
    [string]$OpportunityFile = "marketing-agents/data/public_opportunity_log.csv",
    [string]$CandidatesFile = "marketing-agents/data/prospect_candidates.csv",
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$RelationshipQueueFile = "marketing-agents/data/boss_key_relationship_queue.csv",
    [string]$PtwQueueFile = "marketing-agents/data/boss_key_ptw_queue.csv",
    [string]$ManualSignalsFile = "marketing-agents/data/south_jersey_janitorial_manual_signals.csv",
    [string]$BriefsDir = "marketing-agents/briefs",
    [string]$ResearchPackPath = "marketing-agents/briefs/prospect-research-pack.md",
    [string]$CallRunbookPath = "marketing-agents/briefs/call-runbook.md"
)

$ErrorActionPreference = "Stop"

function Normalize-Company([string]$value) {
    if ([string]::IsNullOrWhiteSpace($value)) { return "" }
    return (($value -replace "\s+", " ").Trim().ToUpperInvariant())
}

function To-DateString([datetime]$value) {
    if ($null -eq $value) { return "" }
    return $value.ToString("yyyy-MM-dd")
}

function To-DateTimeString([datetime]$value) {
    if ($null -eq $value) { return "" }
    return $value.ToString("yyyy-MM-dd HH:mm:ss")
}

function Slugify([string]$value) {
    if ([string]::IsNullOrWhiteSpace($value)) { return "" }
    $slug = $value.ToLowerInvariant() -replace "[^a-z0-9]+", "-"
    return $slug.Trim("-")
}

function Ensure-Path([string]$path) {
    if (-not (Test-Path $path)) {
        throw "Missing required file: $path"
    }
}

function Ensure-Directory([string]$path) {
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
}

function Decode-Html([string]$value) {
    if ($null -eq $value) { return "" }
    return [System.Net.WebUtility]::HtmlDecode(($value -replace "<[^>]+>", " " -replace "\s+", " ").Trim())
}

function Extract-NjStartValue([string]$html, [string]$label) {
    $pattern = "<td class=""t-head-01""[^>]*>\s*$([regex]::Escape($label))\s*</td>\s*<td class=?tableText-01[^>]*>\s*(.*?)\s*</td>"
    $match = [regex]::Match($html, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase -bor [System.Text.RegularExpressions.RegexOptions]::Singleline)
    if (-not $match.Success) { return "" }
    return Decode-Html $match.Groups[1].Value
}

function Get-ExistingProperty([object]$row, [string]$name) {
    if ($row.PSObject.Properties.Name -contains $name) {
        return [string]$row.$name
    }
    return ""
}

function Ensure-OpportunitySchema([object[]]$rows) {
    $normalized = @()
    foreach ($row in $rows) {
        $notes = Get-ExistingProperty $row "notes"
        $vendorName = Get-ExistingProperty $row "vendor_name"
        if ([string]::IsNullOrWhiteSpace($vendorName) -and $notes -match "Incumbent:\s*([^;]+)") {
            $vendorName = $matches[1].Trim()
        }

        $signalType = Get-ExistingProperty $row "signal_type"
        if ([string]::IsNullOrWhiteSpace($signalType) -and $notes -match "Source: USAspending") {
            $signalType = "incumbent_award"
        }

        $sourceUrl = Get-ExistingProperty $row "source_url"
        if ([string]::IsNullOrWhiteSpace($sourceUrl) -and $signalType -eq "incumbent_award") {
            $solicitationNumber = Get-ExistingProperty $row "solicitation_number"
            if (-not [string]::IsNullOrWhiteSpace($solicitationNumber)) {
                $sourceUrl = "https://www.usaspending.gov/search/?keyword=$([uri]::EscapeDataString($solicitationNumber))"
            }
        }

        $normalized += [pscustomobject][ordered]@{
            opportunity_id = Get-ExistingProperty $row "opportunity_id"
            agency = Get-ExistingProperty $row "agency"
            solicitation_title = Get-ExistingProperty $row "solicitation_title"
            solicitation_number = Get-ExistingProperty $row "solicitation_number"
            location = Get-ExistingProperty $row "location"
            due_date = Get-ExistingProperty $row "due_date"
            estimated_value = Get-ExistingProperty $row "estimated_value"
            fit_score = Get-ExistingProperty $row "fit_score"
            status = Get-ExistingProperty $row "status"
            bid_decision = Get-ExistingProperty $row "bid_decision"
            assigned_owner = Get-ExistingProperty $row "assigned_owner"
            next_action = Get-ExistingProperty $row "next_action"
            next_action_due = Get-ExistingProperty $row "next_action_due"
            notes = $notes
            vendor_name = $vendorName
            signal_type = $signalType
            source_url = $sourceUrl
        }
    }
    return $normalized
}

function Upsert-Row([System.Collections.ArrayList]$rows, [hashtable]$index, [string]$key, [hashtable]$orderedRow) {
    if ($index.ContainsKey($key)) {
        $existing = $rows[$index[$key]]
        foreach ($prop in $orderedRow.Keys) {
            $existing.$prop = $orderedRow[$prop]
        }
    } else {
        $rows.Add([pscustomobject]$orderedRow) | Out-Null
        $index[$key] = $rows.Count - 1
    }
}

function Build-Index([object[]]$rows, [string]$propertyName) {
    $index = @{}
    for ($i = 0; $i -lt $rows.Count; $i++) {
        $value = [string]$rows[$i].$propertyName
        if (-not [string]::IsNullOrWhiteSpace($value) -and -not $index.ContainsKey($value)) {
            $index[$value] = $i
        }
    }
    return $index
}

function Find-FirstByCompany([object[]]$rows, [string]$companyName) {
    $normalized = Normalize-Company $companyName
    foreach ($row in $rows) {
        if ((Normalize-Company ([string]$row.company_name)) -eq $normalized) {
            return $row
        }
    }
    return $null
}

function Find-FirstOpportunity([object[]]$rows, [string]$companyName) {
    $normalized = Normalize-Company $companyName
    $matches = @(
        $rows | Where-Object { (Normalize-Company ([string]$_.vendor_name)) -eq $normalized }
    )
    if ($matches.Count -eq 0) { return $null }
    return $matches |
        Sort-Object @{ Expression = { try { [datetime]$_.due_date } catch { Get-Date "2099-12-31" } } }, @{ Expression = { [int]$_.fit_score }; Descending = $true } |
        Select-Object -First 1
}

function Get-NjStartVendorProfile([hashtable]$seed) {
    $orgUrl = "https://www.njstart.gov/bso/external/vendor/vendorProfileOrgInfo.sda?external=true&vendorId=$($seed.vendor_id)"
    $contractsUrl = "https://www.njstart.gov/bso/external/vendor/vendorProfileContractsInfo.sda?external=true&vendorId=$($seed.vendor_id)"

    $orgHtml = (Invoke-WebRequest -Uri $orgUrl -UseBasicParsing).Content
    $contractsHtml = (Invoke-WebRequest -Uri $contractsUrl -UseBasicParsing).Content

    $companyName = Extract-NjStartValue $orgHtml "Company Name:"
    if ([string]::IsNullOrWhiteSpace($companyName)) {
        $companyName = $seed.company_name
    }

    $contactName = Extract-NjStartValue $orgHtml "Emergency Contact Name:"
    $businessDescription = Extract-NjStartValue $orgHtml "Business Description:"
    $vendorEmail = Extract-NjStartValue $orgHtml "Vendor Email:"
    $emergencyEmail = Extract-NjStartValue $orgHtml "Emergency Email:"
    if ([string]::IsNullOrWhiteSpace($vendorEmail)) {
        $vendorEmail = $emergencyEmail
    }
    $phone = Extract-NjStartValue $orgHtml "Emergency Phone:"
    $emergencySupplier = Extract-NjStartValue $orgHtml "Emergency Supplier:"
    $incorporationState = Extract-NjStartValue $orgHtml "Incorporation Details - State:"
    $yearOfIncorporation = Extract-NjStartValue $orgHtml "Year of Incorporation:"
    $hasContracts = ($contractsHtml -notmatch "There are no Contracts found for vendor")

    return [pscustomobject][ordered]@{
        vendor_id = $seed.vendor_id
        county = $seed.county
        batch = $seed.batch
        priority_score = $seed.priority_score
        company_name = $companyName
        contact_name = if ([string]::IsNullOrWhiteSpace($contactName)) { $seed.contact_name } else { $contactName }
        business_description = $businessDescription
        contact_email = $vendorEmail
        contact_phone = $phone
        emergency_supplier = $emergencySupplier
        incorporation_state = $incorporationState
        year_of_incorporation = $yearOfIncorporation
        has_contracts = if ($hasContracts) { "yes" } else { "no" }
        source_url = $orgUrl
        contracts_url = $contractsUrl
        likely_bottleneck = $seed.likely_bottleneck
        primary_angle = $seed.primary_angle
        why_fit = $seed.why_fit
        recommended_first_touch = $seed.recommended_first_touch
        decision_maker_guess = $seed.decision_maker_guess
        offer_angle = $seed.offer_angle
        public_signal_summary = "Active NJSTART vendor profile matched in $($seed.county) County janitorial search."
        evidence_summary = if ($hasContracts) {
            "NJSTART vendor profile and contract tab both visible."
        } else {
            "NJSTART vendor profile is public; contracts tab currently shows no contracts."
        }
    }
}

function Get-SignalLinkLabel([object]$target) {
    switch ([string]$target.signal_type) {
        "incumbent_award" { return "USAspending search" }
        "registered_vendor_supporting" { return "NJSTART profile" }
        "plan_taker" { return "Plan-holder source" }
        "submitted_bidder" { return "Bidder-list source" }
        default { return "Public source" }
    }
}

function Get-TargetSource([object]$target) {
    switch ([string]$target.signal_type) {
        "incumbent_award" { return "USAspending 561720 award radar" }
        "registered_vendor_supporting" { return "NJSTART vendor profile" }
        default {
            if (-not [string]::IsNullOrWhiteSpace([string]$target.source_name)) {
                return [string]$target.source_name
            }
            return "South Jersey public source"
        }
    }
}

function Get-TargetLocation([object]$target) {
    if (-not [string]::IsNullOrWhiteSpace([string]$target.location)) {
        return [string]$target.location
    }
    if (-not [string]::IsNullOrWhiteSpace([string]$target.county)) {
        return "$($target.county) County, NJ"
    }
    return "Unknown"
}

# SEED_DATA_MARKER
$njStartSeeds = @(
    @{ vendor_id = "V00005370"; county = "Burlington"; batch = "primary"; priority_score = 92; company_name = "American Janitorial & Supply"; decision_maker_guess = "Owner"; recommended_first_touch = "phone + email"; likely_bottleneck = "Owner-led public-bid responsiveness and admin load"; primary_angle = "Use the Opportunity Foresight Sprint to tighten proposal/admin flow before the owner gets buried in bid paperwork."; why_fit = "Burlington County janitorial operator with direct owner contact and a public NJSTART vendor profile."; offer_angle = "Opportunity Foresight Sprint" },
    @{ vendor_id = "V00005475"; county = "Burlington"; batch = "primary"; priority_score = 90; company_name = "Daves Cleaning Service Inc"; decision_maker_guess = "Owner or operations lead"; recommended_first_touch = "phone + email"; likely_bottleneck = "Proposal handoff and day-to-day admin drag"; primary_angle = "Position Boss Key as the outside operator who can clean up bid packaging and owner follow-through."; why_fit = "Local janitorial operator with a public vendor profile and direct contact channel."; offer_angle = "Opportunity Foresight Sprint" },
    @{ vendor_id = "V00089025"; county = "Burlington"; batch = "primary"; priority_score = 88; company_name = "HD Housekeeping LLC"; decision_maker_guess = "Owner"; recommended_first_touch = "phone + email"; likely_bottleneck = "Small-team response speed on public-sector opportunities"; primary_angle = "Lead with faster bid readiness and lighter owner admin burden."; why_fit = "South Jersey housekeeping / cleaning profile with a public bid-registration footprint."; offer_angle = "Opportunity Foresight Sprint" },
    @{ vendor_id = "V00057899"; county = "Camden"; batch = "primary"; priority_score = 87; company_name = "BCR Cleaning Service"; decision_maker_guess = "Owner"; recommended_first_touch = "phone + email"; likely_bottleneck = "Owner-managed pursuit discipline and paperwork follow-through"; primary_angle = "Use a South Jersey proposal-support angle tied to public-bid responsiveness."; why_fit = "Camden County cleaning operator with a public NJSTART vendor profile and direct contact path."; offer_angle = "Opportunity Foresight Sprint" },
    @{ vendor_id = "V00092632"; county = "Camden"; batch = "primary"; priority_score = 86; company_name = "J C Williams Cleaning Services LLC."; decision_maker_guess = "Owner"; recommended_first_touch = "phone + email"; likely_bottleneck = "Compliance package assembly and owner-led follow-up"; primary_angle = "Offer a first-win diagnostic focused on bid package speed and cleaner admin execution."; why_fit = "Camden County cleaning-services profile with direct public vendor contact information."; offer_angle = "Opportunity Foresight Sprint" },
    @{ vendor_id = "V00111053"; county = "Burlington"; batch = "watchlist"; priority_score = 78; company_name = "Black Stone Cleaning Company"; decision_maker_guess = "Owner"; recommended_first_touch = "email first"; likely_bottleneck = "Unknown; confirm whether public work is active or only exploratory"; primary_angle = "Keep this as a supporting-signal watchlist account until a second public-bid proof point appears."; why_fit = "Local janitorial vendor registration with direct contact details, but no second bid signal on file yet."; offer_angle = "Opportunity Foresight Sprint" },
    @{ vendor_id = "V00052542"; county = "Burlington"; batch = "watchlist"; priority_score = 76; company_name = "Maldo's Commercial Services L.L.C."; decision_maker_guess = "Owner"; recommended_first_touch = "email first"; likely_bottleneck = "Unknown; validate whether proposal/admin support is the actual pain"; primary_angle = "Watch for a second public-sector signal before pushing hard on outreach."; why_fit = "Burlington County commercial-cleaning registration with a plausible South Jersey footprint."; offer_angle = "Opportunity Foresight Sprint" },
    @{ vendor_id = "V00097338"; county = "Gloucester"; batch = "watchlist"; priority_score = 75; company_name = "BEST Quality Cleaning LLC"; decision_maker_guess = "Owner"; recommended_first_touch = "email first"; likely_bottleneck = "Unknown; registration proves intent but not current public-bid activity"; primary_angle = "Hold until a second proof point lands."; why_fit = "Gloucester County cleaning profile that is worth monitoring but still needs stronger proof."; offer_angle = "Opportunity Foresight Sprint" },
    @{ vendor_id = "V00102040"; county = "Gloucester"; batch = "watchlist"; priority_score = 74; company_name = "CHRISSY'S CLEANING COMPANY, LLC"; decision_maker_guess = "Owner"; recommended_first_touch = "email first"; likely_bottleneck = "Unknown; validate public-sector volume first"; primary_angle = "Treat as a local registration signal and revisit once a second public-bid trace appears."; why_fit = "Gloucester County cleaning-company registration with direct contact information."; offer_angle = "Opportunity Foresight Sprint" },
    @{ vendor_id = "V00055689"; county = "Gloucester"; batch = "watchlist"; priority_score = 73; company_name = "Team Real Clean Services Inc"; decision_maker_guess = "Owner or operations lead"; recommended_first_touch = "email first"; likely_bottleneck = "Unknown; confirm whether they are actively chasing public work"; primary_angle = "Watchlist until a bidder / award / plan-taker trace shows up."; why_fit = "Gloucester County cleaning-services registration with South Jersey relevance."; offer_angle = "Opportunity Foresight Sprint" },
    @{ vendor_id = "V00110797"; county = "Camden"; batch = "watchlist"; priority_score = 72; company_name = "bluejay janitorial facilities maintenance"; decision_maker_guess = "Owner"; recommended_first_touch = "email first"; likely_bottleneck = "Unknown; likely facilities admin and response workload"; primary_angle = "Monitor for a stronger bid signal before prioritizing outreach."; why_fit = "Camden County janitorial / facilities-maintenance registration that is close to your core niche."; offer_angle = "Opportunity Foresight Sprint" },
    @{ vendor_id = "V00033714"; county = "Camden"; batch = "watchlist"; priority_score = 71; company_name = "Elite Commercial Cleaning Services"; decision_maker_guess = "Owner"; recommended_first_touch = "email first"; likely_bottleneck = "Unknown; confirm public-bid motion and admin load"; primary_angle = "Keep warm as a South Jersey cleaning-company registration lead."; why_fit = "Camden County commercial-cleaning profile with direct contact details."; offer_angle = "Opportunity Foresight Sprint" },
    @{ vendor_id = "V00001004"; county = "Camden"; batch = "watchlist"; priority_score = 70; company_name = "Industrial Commercial Cleaning Group Inc."; decision_maker_guess = "Owner or GM"; recommended_first_touch = "email first"; likely_bottleneck = "Unknown; needs second signal before direct pursuit"; primary_angle = "Monitor until bidder or award proof lands."; why_fit = "Camden County industrial/commercial cleaning operator with public vendor registration."; offer_angle = "Opportunity Foresight Sprint" },
    @{ vendor_id = "V00081253"; county = "Gloucester"; batch = "watchlist"; priority_score = 69; company_name = "ProClean USA"; decision_maker_guess = "Owner or GM"; recommended_first_touch = "email first"; likely_bottleneck = "Unknown; verify active public-bid pursuit"; primary_angle = "Hold as a likely local bidder candidate."; why_fit = "Gloucester County cleaning operator with public registration and a clear services name."; offer_angle = "Opportunity Foresight Sprint" },
    @{ vendor_id = "V00060845"; county = "Gloucester"; batch = "watchlist"; priority_score = 68; company_name = "Professional Cleaning Services"; decision_maker_guess = "Owner or ops lead"; recommended_first_touch = "email first"; likely_bottleneck = "Unknown; registration signal only"; primary_angle = "Keep on watchlist until a stronger public-bid trace appears."; why_fit = "Gloucester County cleaning-services registration with direct contact details."; offer_angle = "Opportunity Foresight Sprint" }
)

$awardConfigs = @(
    @{ company_name = "AMERICAN MAINTENANCE & SUPPLIES, INC"; priority_score = 89; why_fit = "Blackwood-area award signal keeps this close to Camden County and inside the South Jersey pursuit lane."; decision_maker_guess = "Owner or GM"; contact_name = "Arturo Garcia III"; contact_email = "agarcia@ammaint.com"; recommended_first_touch = "email first"; likely_bottleneck = "Recompete packaging and compliance handoff"; primary_angle = "Lead with a South Jersey recompete-readiness angle tied to bid discipline and admin compression."; offer_angle = "Opportunity Foresight Sprint" },
    @{ company_name = "OCCUPATIONAL TRAINING CENTER OF BURLINGTON COUNTY"; priority_score = 88; why_fit = "Burlington County organization with repeated custodial award history and direct regional relevance."; decision_maker_guess = "Executive director or contracts lead"; recommended_first_touch = "email first after contact enrichment"; likely_bottleneck = "Multi-award compliance handoff and rebid visibility"; primary_angle = "Position Boss Key as proposal/ops support that protects repeat public-sector work."; offer_angle = "Opportunity Foresight Sprint" },
    @{ company_name = "WORKPRO LLC"; priority_score = 87; why_fit = "Northfield-area janitorial award signal keeps the first batch anchored in the South Jersey corridor."; decision_maker_guess = "Owner or GM"; contact_name = "Azzmeiah R. Vazquez"; recommended_first_touch = "contact lookup -> email"; likely_bottleneck = "Owner-led bid response workload"; primary_angle = "Offer lighter-weight pursuit discipline before the next public cycle compresses."; offer_angle = "Opportunity Foresight Sprint" },
    @{ company_name = "THE FIELDS GROUP, LLC"; priority_score = 86; why_fit = "Atlantic City janitorial award signal keeps this inside the same South Jersey public-work lane."; decision_maker_guess = "Owner or president"; recommended_first_touch = "contact lookup -> email"; likely_bottleneck = "Public-sector response cadence and compliance packaging"; primary_angle = "Lead with proposal support tied to protecting existing public work."; offer_angle = "Opportunity Foresight Sprint" },
    @{ company_name = "N&S PROPERTY SERVICES LLC"; priority_score = 85; why_fit = "Cape May award signal keeps coverage in the southern tip of the state without leaving the janitorial lane."; decision_maker_guess = "Owner or GM"; recommended_first_touch = "contact lookup -> email"; likely_bottleneck = "Public-bid readiness across seasonal / service operations"; primary_angle = "Offer a first-win diagnostic around bid speed and admin control."; offer_angle = "Opportunity Foresight Sprint" },
    @{ company_name = "SILAS FRAZIER REALTY, LLC"; priority_score = 84; why_fit = "Rio Grande custodial award history keeps this squarely in the South Jersey footprint."; decision_maker_guess = "Owner or GM"; recommended_first_touch = "contact lookup -> email"; likely_bottleneck = "Administrative bandwidth around federal service work"; primary_angle = "Lead with public-sector pursuit discipline for a local operator already touching government work."; offer_angle = "Opportunity Foresight Sprint" },
    @{ company_name = "AMD GARCIA, LIMITED LIABILITY COMPANY"; priority_score = 81; why_fit = "Mercer overflow account with live custodial award history and direct New Jersey relevance."; decision_maker_guess = "Owner or GM"; recommended_first_touch = "contact lookup -> email"; likely_bottleneck = "Bid package assembly and labor/admin handoff"; primary_angle = "Offer proposal-support cleanup before the next cycle."; offer_angle = "Opportunity Foresight Sprint" },
    @{ company_name = "Q C CLEANING LLC"; priority_score = 80; why_fit = "Monmouth overflow keeps the batch in New Jersey while still staying inside janitorial public work."; decision_maker_guess = "Owner or GM"; recommended_first_touch = "contact lookup -> email"; likely_bottleneck = "Bid-package follow-through and compliance admin"; primary_angle = "Pitch a practical first-step diagnostic around public-sector response speed."; offer_angle = "Opportunity Foresight Sprint" },
    @{ company_name = "MELGAR FACILITY MAINTENANCE LLC"; priority_score = 79; why_fit = "New Jersey award history makes this a workable overflow target once the strongest South Jersey names are queued."; decision_maker_guess = "Owner or GM"; recommended_first_touch = "contact lookup -> email"; likely_bottleneck = "Public-work reporting and rebid management"; primary_angle = "Position Boss Key as proposal/admin relief that protects recompete readiness."; offer_angle = "Opportunity Foresight Sprint" },
    @{ company_name = "KB FEDERAL MAINTENANCE INC"; priority_score = 78; why_fit = "Another New Jersey janitorial incumbent that helps round out the first federal/public-work tranche."; decision_maker_guess = "Owner or GM"; recommended_first_touch = "contact lookup -> email"; likely_bottleneck = "Compliance packaging and response timing"; primary_angle = "Lead with admin compression and public-bid discipline."; offer_angle = "Opportunity Foresight Sprint" },
    @{ company_name = "DK CLEANING CONTRACTORS LLC"; priority_score = 77; why_fit = "Philadelphia overflow still fits the South Jersey pursuit corridor."; decision_maker_guess = "Owner or GM"; contact_name = "Chidozie Dike"; recommended_first_touch = "contact lookup -> email"; likely_bottleneck = "Recompete prep and deadline compression"; primary_angle = "Pitch nearby proposal support for firms already chasing Army work in the region."; offer_angle = "Opportunity Foresight Sprint" },
    @{ company_name = "INTEGRITY NATIONAL CORPORATION"; priority_score = 76; why_fit = "Philadelphia-based federal janitorial track record makes this a practical nearby overflow target."; decision_maker_guess = "Business-development or contracts lead"; recommended_first_touch = "contact lookup -> email"; likely_bottleneck = "Scaling public-sector admin load across multiple awards"; primary_angle = "Position Boss Key as a fractional proposal / pursuit support layer."; offer_angle = "Procurement Intelligence Retainer" },
    @{ company_name = "UNIVERSAL CLEANING CONCEPTS, LLC"; priority_score = 75; why_fit = "FAA custodial track record in Philadelphia keeps this inside the same corridor."; decision_maker_guess = "Owner or GM"; recommended_first_touch = "contact lookup -> email"; likely_bottleneck = "Compliance packaging and contract follow-through"; primary_angle = "Offer first-step proposal operations support before the next recompete window."; offer_angle = "Opportunity Foresight Sprint" },
    @{ company_name = "CLEANWORK SOLUTIONS LLC"; priority_score = 74; why_fit = "Additional New Jersey custodial incumbent that fills out the verified first-pass batch without leaving the janitorial lane."; decision_maker_guess = "Owner or GM"; recommended_first_touch = "contact lookup -> email"; likely_bottleneck = "Recompete coordination and admin handoff"; primary_angle = "Position Boss Key as the proposal/admin support layer before the next bid cycle tightens."; offer_angle = "Opportunity Foresight Sprint" }
)

# EXECUTION_MARKER
Ensure-Path $OpportunityFile
Ensure-Path $CandidatesFile
Ensure-Path $PipelineFile
Ensure-Path $RelationshipQueueFile
Ensure-Path $PtwQueueFile
Ensure-Path $ManualSignalsFile
Ensure-Directory $BriefsDir

$today = $AsOfDate.Date
$briefDate = To-DateString $today

$opportunityRows = [System.Collections.ArrayList]@(Ensure-OpportunitySchema @(Import-Csv -Path $OpportunityFile))
$candidateRows = [System.Collections.ArrayList]@(Import-Csv -Path $CandidatesFile)
$pipelineRows = [System.Collections.ArrayList]@(Import-Csv -Path $PipelineFile)
$relationshipRows = [System.Collections.ArrayList]@(Import-Csv -Path $RelationshipQueueFile)
$ptwRows = [System.Collections.ArrayList]@(Import-Csv -Path $PtwQueueFile)
$manualSignalRows = @(Import-Csv -Path $ManualSignalsFile)

$opportunityIndex = Build-Index $opportunityRows "opportunity_id"
$candidateIndex = @{}
for ($i = 0; $i -lt $candidateRows.Count; $i++) {
    $key = Normalize-Company ([string]$candidateRows[$i].company_name)
    if (-not [string]::IsNullOrWhiteSpace($key) -and -not $candidateIndex.ContainsKey($key)) {
        $candidateIndex[$key] = $i
    }
}

$pipelineIndex = @{}
for ($i = 0; $i -lt $pipelineRows.Count; $i++) {
    $key = Normalize-Company ([string]$pipelineRows[$i].company_name)
    if (-not [string]::IsNullOrWhiteSpace($key) -and -not $pipelineIndex.ContainsKey($key)) {
        $pipelineIndex[$key] = $i
    }
}

$relationshipIndex = @{}
for ($i = 0; $i -lt $relationshipRows.Count; $i++) {
    $key = Normalize-Company ([string]$relationshipRows[$i].company_name)
    if (-not [string]::IsNullOrWhiteSpace($key) -and -not $relationshipIndex.ContainsKey($key)) {
        $relationshipIndex[$key] = $i
    }
}

$ptwIndex = @{}
for ($i = 0; $i -lt $ptwRows.Count; $i++) {
    $key = Normalize-Company ([string]$ptwRows[$i].company_name)
    if (-not [string]::IsNullOrWhiteSpace($key) -and -not $ptwIndex.ContainsKey($key)) {
        $ptwIndex[$key] = $i
    }
}

$njStartProfiles = foreach ($seed in $njStartSeeds) {
    Get-NjStartVendorProfile $seed
}

$registrationOnlyTargets = @(
    $njStartProfiles |
        Where-Object { $_.has_contracts -ne "yes" } |
        Sort-Object @{ Expression = { [int]$_.priority_score }; Descending = $true }
)

$awardTargets = @()
foreach ($config in $awardConfigs) {
    $opp = Find-FirstOpportunity $opportunityRows $config.company_name
    if ($null -eq $opp) { continue }

    $candidate = Find-FirstByCompany $candidateRows $config.company_name
    $location = [string]$opp.location
    $website = if (-not [string]::IsNullOrWhiteSpace([string]$config.website)) {
        [string]$config.website
    } elseif ($null -ne $candidate) {
        [string]$candidate.website
    } else {
        ""
    }
    $contactName = if (-not [string]::IsNullOrWhiteSpace([string]$config.contact_name)) { [string]$config.contact_name } else { "" }
    $contactEmail = if (-not [string]::IsNullOrWhiteSpace([string]$config.contact_email)) { [string]$config.contact_email } else { "" }
    $contactPhone = if (-not [string]::IsNullOrWhiteSpace([string]$config.contact_phone)) { [string]$config.contact_phone } else { "" }
    $awardId = [string]$opp.solicitation_number
    $dueDate = [string]$opp.due_date
    $sourceUrl = if (-not [string]::IsNullOrWhiteSpace([string]$opp.source_url)) {
        [string]$opp.source_url
    } else {
        "https://www.usaspending.gov/search/?keyword=$([uri]::EscapeDataString($awardId))"
    }

    $awardTargets += [pscustomobject][ordered]@{
        company_name = $config.company_name
        priority_score = $config.priority_score
        location = $location
        website = $website
        contact_name = $contactName
        contact_email = $contactEmail
        contact_phone = $contactPhone
        public_signal_summary = "Federal janitorial incumbent award $awardId ending $dueDate."
        evidence_summary = "USAspending-linked incumbent signal with local or nearby New Jersey / Philly corridor relevance."
        source_url = $sourceUrl
        signal_type = "incumbent_award"
        source_name = "USAspending"
        decision_maker_guess = $config.decision_maker_guess
        recommended_first_touch = $config.recommended_first_touch
        likely_bottleneck = $config.likely_bottleneck
        primary_angle = $config.primary_angle
        why_fit = $config.why_fit
        offer_angle = $config.offer_angle
        agency = [string]$opp.agency
        solicitation_number = $awardId
        due_date = $dueDate
        estimated_value = [string]$opp.estimated_value
    }
}

$manualTargets = @()
foreach ($row in $manualSignalRows) {
    if ([string]::IsNullOrWhiteSpace([string]$row.company_name)) { continue }
    $manualTargets += [pscustomobject][ordered]@{
        company_name = [string]$row.company_name
        priority_score = if ([string]::IsNullOrWhiteSpace([string]$row.priority_score)) { "72" } else { [string]$row.priority_score }
        location = [string]$row.location
        website = [string]$row.website
        contact_name = [string]$row.contact_name
        contact_email = [string]$row.contact_email
        contact_phone = [string]$row.contact_phone
        public_signal_summary = [string]$row.public_signal_summary
        evidence_summary = [string]$row.notes
        source_url = [string]$row.source_url
        signal_type = if ([string]::IsNullOrWhiteSpace([string]$row.signal_type)) { "award_notice" } else { [string]$row.signal_type }
        source_name = [string]$row.source_name
        reference_number = [string]$row.reference_number
        signal_date = [string]$row.signal_date
        decision_maker_guess = [string]$row.decision_maker_guess
        recommended_first_touch = [string]$row.recommended_first_touch
        likely_bottleneck = [string]$row.likely_bottleneck
        primary_angle = [string]$row.primary_angle
        why_fit = [string]$row.why_fit
        offer_angle = [string]$row.offer_angle
        agency = [string]$row.source_name
        solicitation_number = [string]$row.reference_number
        due_date = [string]$row.signal_date
        estimated_value = [string]$row.estimated_value
    }
}

$rankedPrimaryPool = @(
    $manualTargets +
    $awardTargets
) |
    Sort-Object @{ Expression = { [int]$_.priority_score }; Descending = $true }

$seenPrimaryCompanies = @{}
$primaryTargets = @(
    foreach ($target in $rankedPrimaryPool) {
        $companyKey = Normalize-Company $target.company_name
        if (-not $seenPrimaryCompanies.ContainsKey($companyKey)) {
            $seenPrimaryCompanies[$companyKey] = $true
            $target
        }
    }
) | Select-Object -First 15

$primaryCompanyNames = @{}
foreach ($target in $primaryTargets) {
    $primaryCompanyNames[(Normalize-Company $target.company_name)] = $true
}

$watchlistTargets = @(
    $registrationOnlyTargets |
        Where-Object { -not $primaryCompanyNames.ContainsKey((Normalize-Company $_.company_name)) } |
        Select-Object -First 10
)

$topFiveTargets = $primaryTargets | Select-Object -First 5

foreach ($target in $primaryTargets) {
    $companyKey = Normalize-Company $target.company_name
    $targetSource = Get-TargetSource $target
    $candidateNotes = @($target.why_fit, "Signal: $($target.public_signal_summary)", "Evidence: $($target.source_url)") -join " | "

    $candidateRow = [ordered]@{
        company_name = $target.company_name
        website = $target.website
        location = Get-TargetLocation $target
        source = $targetSource
        estimated_size_band = "Unknown"
        estimated_employee_band = "Unknown"
        fit_signals = $target.public_signal_summary
        decision_maker_guess = $target.decision_maker_guess
        priority_score = "$($target.priority_score)"
        status = "new"
        notes = $candidateNotes
    }
    Upsert-Row $candidateRows $candidateIndex $companyKey $candidateRow

    $pipelineNotes = @($target.why_fit, "Evidence: $($target.source_url)") -join " | "
    $pipelineRow = [ordered]@{
        company_name = $target.company_name
        website = $target.website
        location = Get-TargetLocation $target
        target_contact = $target.contact_name
        role = $target.decision_maker_guess
        contact_email = $target.contact_email
        contact_phone = $target.contact_phone
        services_or_contract_focus = switch ([string]$target.signal_type) {
            "incumbent_award" { "Public-sector janitorial / custodial incumbent work" }
            "registered_vendor_supporting" { "NJSTART-registered janitorial services" }
            default { "South Jersey public-sector janitorial bidder / award signal" }
        }
        personalization_hook_1 = $target.public_signal_summary
        personalization_hook_2 = $target.why_fit
        likely_bottleneck = $target.likely_bottleneck
        primary_angle = $target.primary_angle
        priority_score = "$($target.priority_score)"
        last_touch_date = ""
        next_touch_date = $briefDate
        stage = "research"
        status = "active"
        notes = $pipelineNotes
    }
    Upsert-Row $pipelineRows $pipelineIndex $companyKey $pipelineRow

    switch ([string]$target.signal_type) {
        "incumbent_award" {
            $opp = Find-FirstOpportunity $opportunityRows $target.company_name
            if ($null -ne $opp) {
                $oppKey = [string]$opp.opportunity_id
                $oppRow = [ordered]@{
                    opportunity_id = $oppKey
                    agency = [string]$opp.agency
                    solicitation_title = [string]$opp.solicitation_title
                    solicitation_number = [string]$opp.solicitation_number
                    location = [string]$opp.location
                    due_date = [string]$opp.due_date
                    estimated_value = [string]$opp.estimated_value
                    fit_score = "$($target.priority_score)"
                    status = "identified"
                    bid_decision = "target-incumbent-outreach"
                    assigned_owner = "Timmy Semenza"
                    next_action = "Enrich contact data, then send recompete-support outreach."
                    next_action_due = $briefDate
                    notes = @($target.public_signal_summary, $target.why_fit) -join " | "
                    vendor_name = $target.company_name
                    signal_type = "incumbent_award"
                    source_url = $target.source_url
                }
                Upsert-Row $opportunityRows $opportunityIndex $oppKey $oppRow
            }
        }
        "registered_vendor_supporting" {
            $oppKey = "NJSTART-$($target.vendor_id)-$briefDate"
            $oppRow = [ordered]@{
                opportunity_id = $oppKey
                agency = "NJSTART Registered Vendor Search"
                solicitation_title = "NJSTART registered janitorial vendor | $($target.company_name)"
                solicitation_number = [string]$target.vendor_id
                location = "$($target.county) County, NJ"
                due_date = ""
                estimated_value = ""
                fit_score = "$($target.priority_score)"
                status = "identified"
                bid_decision = "target-vendor-outreach"
                assigned_owner = "Timmy Semenza"
                next_action = "Use phone + email outreach around public-bid responsiveness and admin load."
                next_action_due = $briefDate
                notes = @($target.public_signal_summary, "Business description: $($target.business_description)", $target.evidence_summary) -join " | "
                vendor_name = $target.company_name
                signal_type = "registered_vendor_supporting"
                source_url = $target.source_url
            }
            Upsert-Row $opportunityRows $opportunityIndex $oppKey $oppRow
        }
        default {
            $reference = if (-not [string]::IsNullOrWhiteSpace([string]$target.reference_number)) { [string]$target.reference_number } else { Slugify $target.company_name }
            $oppKey = "LOCAL-$reference-$briefDate"
            $oppRow = [ordered]@{
                opportunity_id = $oppKey
                agency = if (-not [string]::IsNullOrWhiteSpace([string]$target.source_name)) { [string]$target.source_name } else { "South Jersey public source" }
                solicitation_title = "South Jersey janitorial public-bid signal | $($target.company_name)"
                solicitation_number = $reference
                location = Get-TargetLocation $target
                due_date = if (-not [string]::IsNullOrWhiteSpace([string]$target.signal_date)) { [string]$target.signal_date } else { "" }
                estimated_value = if (-not [string]::IsNullOrWhiteSpace([string]$target.estimated_value)) { [string]$target.estimated_value } else { "" }
                fit_score = "$($target.priority_score)"
                status = "identified"
                bid_decision = "target-public-bid-outreach"
                assigned_owner = "Timmy Semenza"
                next_action = "Use the public bid signal to drive outreach and contact enrichment."
                next_action_due = $briefDate
                notes = @($target.public_signal_summary, $target.why_fit, $target.evidence_summary) -join " | "
                vendor_name = $target.company_name
                signal_type = [string]$target.signal_type
                source_url = $target.source_url
            }
            Upsert-Row $opportunityRows $opportunityIndex $oppKey $oppRow
        }
    }
}

foreach ($target in $watchlistTargets) {
    $companyKey = Normalize-Company $target.company_name
    $candidateRow = [ordered]@{
        company_name = $target.company_name
        website = ""
        location = "$($target.county) County, NJ"
        source = "NJSTART vendor profile"
        estimated_size_band = "Unknown"
        estimated_employee_band = "Unknown"
        fit_signals = $target.public_signal_summary
        decision_maker_guess = $target.decision_maker_guess
        priority_score = "$($target.priority_score)"
        status = "watchlist"
        notes = @($target.why_fit, "Evidence: $($target.source_url)") -join " | "
    }
    Upsert-Row $candidateRows $candidateIndex $companyKey $candidateRow

    $pipelineRow = [ordered]@{
        company_name = $target.company_name
        website = ""
        location = "$($target.county) County, NJ"
        target_contact = $target.contact_name
        role = $target.decision_maker_guess
        contact_email = $target.contact_email
        contact_phone = $target.contact_phone
        services_or_contract_focus = "NJSTART-registered janitorial services"
        personalization_hook_1 = $target.public_signal_summary
        personalization_hook_2 = "Hold for second public-bid proof before active outbound."
        likely_bottleneck = $target.likely_bottleneck
        primary_angle = $target.primary_angle
        priority_score = "$($target.priority_score)"
        last_touch_date = ""
        next_touch_date = ""
        stage = "research"
        status = "watchlist"
        notes = @($target.why_fit, "Evidence: $($target.source_url)") -join " | "
    }
    Upsert-Row $pipelineRows $pipelineIndex $companyKey $pipelineRow

    $oppKey = "NJSTART-$($target.vendor_id)-$briefDate"
    $oppRow = [ordered]@{
        opportunity_id = $oppKey
        agency = "NJSTART Registered Vendor Search"
        solicitation_title = "NJSTART watchlist janitorial vendor | $($target.company_name)"
        solicitation_number = [string]$target.vendor_id
        location = "$($target.county) County, NJ"
        due_date = ""
        estimated_value = ""
        fit_score = "$($target.priority_score)"
        status = "watchlist"
        bid_decision = "watchlist-supporting-signal"
        assigned_owner = "Timmy Semenza"
        next_action = "Wait for a second public-bid signal before active outreach."
        next_action_due = ""
        notes = @($target.public_signal_summary, $target.evidence_summary) -join " | "
        vendor_name = $target.company_name
        signal_type = "registered_vendor_supporting"
        source_url = $target.source_url
    }
    Upsert-Row $opportunityRows $opportunityIndex $oppKey $oppRow
}

foreach ($target in $topFiveTargets) {
    $companyKey = Normalize-Company $target.company_name
    $slug = Slugify $target.company_name
    $relationshipId = "rel-$(To-DateString $today -replace '-', '')-$slug"
    $ptwId = "ptw-$(To-DateString $today -replace '-', '')-$slug-r1"

    $relationshipRow = [ordered]@{
        relationship_id = $relationshipId
        created_date = $briefDate
        company_name = $target.company_name
        contact_name = $target.contact_name
        role = $target.decision_maker_guess
        linkedin_profile_url = ""
        linkedin_company_url = ""
        relationship_stage = "research"
        warm_signal = "public-bid-signal"
        fit_confirmed = "yes"
        pain_point = $target.likely_bottleneck
        desired_outcome = "Tighten public-bid responsiveness without burying the owner or ops lead in admin work."
        offer_hypothesis = $target.offer_angle
        urgency_level = "medium"
        scope_breadth = "standard"
        stakeholder_complexity = "medium"
        research_load = "low"
        delivery_intensity = "medium"
        last_touch_date = ""
        last_interaction_summary = "No outreach yet. Seeded from live public-bid vendor signal."
        next_best_touch_type = $target.recommended_first_touch
        next_best_touch_path = $CallRunbookPath
        meeting_needed = "yes"
        meeting_status = "not-started"
        proposal_status = "not-started"
        ptw_status = "queued"
        ptw_stage = "market-assessment"
        ptw_recommendation = "pursue"
        ptw_record_id = $ptwId
        owner_decision = "hold"
        review_status = "pending-review"
        ready_state = "queued"
        notes = @($target.public_signal_summary, "Evidence: $($target.source_url)") -join " | "
    }
    Upsert-Row $relationshipRows $relationshipIndex $companyKey $relationshipRow

    $ptwRow = [ordered]@{
        ptw_id = $ptwId
        relationship_id = $relationshipId
        created_date = $briefDate
        refreshed_at = To-DateTimeString $AsOfDate
        archived_at = ""
        revision_number = "1"
        is_active = "yes"
        company_name = $target.company_name
        contact_name = $target.contact_name
        ptw_stage = "market-assessment"
        target_account_fit = "yes"
        customer_objective = "Keep public-bid responsiveness high without pushing more proposal/admin burden onto the owner."
        customer_need = $target.likely_bottleneck
        customer_value_drivers = "Faster public-bid response; cleaner compliance packaging; less owner drag"
        buyer_priorities = "Low-disruption first step; clear value before a longer retainer"
        evaluation_priorities = "Practicality, speed, and whether the first move feels like a real bid/admin fix"
        buying_behavior = "Likely to prefer a defined first diagnostic before a broader engagement"
        delivery_context = "Remote diagnostic plus operator-facing readout"
        timing_context = "Relevant now because the firm is publicly positioned for bid activity"
        budget_signal = "Unknown"
        budget_band = "$4,500-$6,500"
        budget_confidence = "45"
        likely_competitors = "Internal admin patchwork; generic VA support; local ops consultant"
        incumbent_status = "unknown"
        substitute_options = "Handle bids internally until the admin load becomes acute"
        big4_technical = "Competitors can promise admin cleanup without owning the bid-to-delivery handoff"
        big4_management = "Competitors may sell labor hours instead of a clear diagnostic and fix path"
        big4_past_performance = "Local janitorial familiarity may matter more than generic consulting proofs"
        big4_cost_price = "Lower-cost admin help may look attractive if the diagnostic is not tied to public-bid outcomes"
        differentiation_hypothesis = "Boss Key can win by selling a narrow first move tied to public-bid responsiveness and admin relief"
        recommended_entry_offer = "Opportunity Foresight Sprint"
        expansion_offer = "Procurement Intelligence Retainer"
        price_to_compete_usd = "4750"
        price_to_win_usd = ""
        minimum_acceptable_price_usd = "4500"
        pursue_recommendation = "pursue"
        data_confidence = "81"
        evidence_summary = @($target.public_signal_summary, $target.evidence_summary) -join " | "
        assumptions = "Assumes a first paid step will land faster if it is practical, low-disruption, and directly tied to public-bid admin burden."
        source_quality_notes = "Use only approved public-source and direct-discovery evidence."
        source_reliability = "medium"
        source_summary = "Live NJSTART vendor profile and South Jersey janitorial search"
        ptw_brief_path = $ResearchPackPath
        owner_decision = "hold"
        review_status = "pending-review"
        status = "queued"
        notes = "Generated by the South Jersey janitorial bid-signal sweep."
    }
    Upsert-Row $ptwRows $ptwIndex $companyKey $ptwRow
}

$briefPath = Join-Path $BriefsDir "janitorial-public-bid-targets-$briefDate.md"
$briefLines = New-Object System.Collections.Generic.List[string]
$briefLines.Add("# South Jersey Janitorial Public Bid Targets - $briefDate")
$briefLines.Add("")
$briefLines.Add("- Primary targets: $($primaryTargets.Count)")
$briefLines.Add("- Watchlist accounts: $($watchlistTargets.Count)")
$briefLines.Add("- Existing warmed local accounts such as Delta Cleaning Service and Bernadette Janitorial remain in the relationship queue and were not duplicated into this first public-bid sweep.")
$briefLines.Add("")
$briefLines.Add("## Primary Targets")
$briefLines.Add("")
$briefLines.Add("### 1-5 | Call Now | Strongest Verified Public-Sector Signals")
$briefLines.Add("")

$rank = 1
foreach ($target in $topFiveTargets) {
    $linkLabel = Get-SignalLinkLabel $target
    $decisionMaker = if (-not [string]::IsNullOrWhiteSpace([string]$target.contact_name)) {
        "$($target.contact_name) ($($target.decision_maker_guess))"
    } else {
        [string]$target.decision_maker_guess
    }
    $proof = if (-not [string]::IsNullOrWhiteSpace([string]$target.business_description)) {
        "$($target.public_signal_summary) Business description: $($target.business_description)"
    } else {
        $target.public_signal_summary
    }
    $briefLines.Add("#### $rank. $($target.company_name)")
    $briefLines.Add("- Evidence link: [$linkLabel]($($target.source_url))")
    $briefLines.Add("- Public-signal proof: $proof")
    $briefLines.Add("- Why fit: $($target.why_fit)")
    $briefLines.Add("- Likely decision maker: $decisionMaker")
    $briefLines.Add("- Recommended first touch: $($target.recommended_first_touch)")
    $briefLines.Add("- Offer angle: $($target.offer_angle)")
    $briefLines.Add("")
    $rank++
}

$briefLines.Add("### 6-15 | Verified Expansion Targets")
$briefLines.Add("")
foreach ($target in ($primaryTargets | Select-Object -Skip 5)) {
    $linkLabel = Get-SignalLinkLabel $target
    $decisionMaker = if (-not [string]::IsNullOrWhiteSpace([string]$target.contact_name)) {
        "$($target.contact_name) ($($target.decision_maker_guess))"
    } else {
        [string]$target.decision_maker_guess
    }
    $proof = if (-not [string]::IsNullOrWhiteSpace([string]$target.business_description)) {
        "$($target.public_signal_summary) Business description: $($target.business_description)"
    } else {
        $target.public_signal_summary
    }
    $briefLines.Add("#### $rank. $($target.company_name)")
    $briefLines.Add("- Evidence link: [$linkLabel]($($target.source_url))")
    $briefLines.Add("- Public-signal proof: $proof")
    $briefLines.Add("- Why fit: $($target.why_fit)")
    $briefLines.Add("- Likely decision maker: $decisionMaker")
    $briefLines.Add("- Recommended first touch: $($target.recommended_first_touch)")
    $briefLines.Add("- Offer angle: $($target.offer_angle)")
    $briefLines.Add("")
    $rank++
}

$briefLines.Add("## Watchlist (Needs Second Public-Bid Proof)")
$briefLines.Add("")
foreach ($target in $watchlistTargets) {
    $decisionMaker = if (-not [string]::IsNullOrWhiteSpace([string]$target.contact_name)) {
        "$($target.contact_name) ($($target.decision_maker_guess))"
    } else {
        [string]$target.decision_maker_guess
    }
    $briefLines.Add("### $($target.company_name)")
    $briefLines.Add("- Evidence link: [NJSTART profile]($($target.source_url))")
    $briefLines.Add("- Public-signal proof: $($target.public_signal_summary) Business description: $($target.business_description)")
    $briefLines.Add("- Why fit: $($target.why_fit)")
    $briefLines.Add("- Likely decision maker: $decisionMaker")
    $briefLines.Add("- Recommended first touch: $($target.recommended_first_touch)")
    $briefLines.Add("")
}
$briefLines -join [Environment]::NewLine | Set-Content -Path $briefPath -Encoding utf8

$researchLines = New-Object System.Collections.Generic.List[string]
$researchLines.Add("# Prospect Research Pack - $briefDate")
$researchLines.Add("")
$researchLines.Add("Use this as a 2-minute prep sheet before each call.")
$researchLines.Add("")
foreach ($target in $topFiveTargets) {
    $locationLabel = Get-TargetLocation $target
    $websiteLabel = if (-not [string]::IsNullOrWhiteSpace([string]$target.website)) { [string]$target.website } else { "Needs contact enrichment" }
    $callNow = switch ([string]$target.signal_type) {
        "incumbent_award" { "The award/recompete signal is live now, so the pitch can anchor to real public-sector timing." }
        "registered_vendor_supporting" { "The public vendor-registration footprint is live, which makes a public-bid operations conversation timely." }
        default { "A named public-sector bidder or award signal is already public, so the outreach has a concrete proof point." }
    }
    $hooks = @()
    if (-not [string]::IsNullOrWhiteSpace([string]$target.business_description)) { $hooks += [string]$target.business_description }
    $hooks += [string]$target.public_signal_summary
    $hooks += [string]$target.evidence_summary
    $contactNotes = @()
    if (-not [string]::IsNullOrWhiteSpace([string]$target.contact_email)) { $contactNotes += "Contact email $($target.contact_email)" }
    if (-not [string]::IsNullOrWhiteSpace([string]$target.contact_phone)) { $contactNotes += "Contact phone $($target.contact_phone)" }
    if ($contactNotes.Count -eq 0) { $contactNotes += "Direct contact still needs enrichment" }
    $linkLabel = Get-SignalLinkLabel $target

    $researchLines.Add("## $($target.company_name)")
    $researchLines.Add("- Contact: $($target.contact_name)")
    $researchLines.Add("- Location: $locationLabel")
    $researchLines.Add("- Website: $websiteLabel")
    $researchLines.Add("- Why this call now: $callNow")
    $researchLines.Add("- Talking hooks: $($hooks -join ' | ')")
    $researchLines.Add("- Likely issue to confirm: $($target.likely_bottleneck)")
    $researchLines.Add("- Offer angle: $($target.primary_angle)")
    $researchLines.Add("- Notes: $($contactNotes -join ' | ')")
    $researchLines.Add("")
    $researchLines.Add("**Evidence links:**")
    $researchLines.Add("- ${linkLabel}: $($target.source_url)")
    if (-not [string]::IsNullOrWhiteSpace([string]$target.contracts_url)) {
        $researchLines.Add("- Contracts tab: $($target.contracts_url)")
    }
    $researchLines.Add("")
    $researchLines.Add("**20-second opener:**")
    $researchLines.Add("Timmy Semenza here with Boss Key in South Jersey. I work with janitorial operators that already show up in public-sector buying signals and still end up carrying too much of the bid and admin load by hand.")
    $researchLines.Add("")
}
$researchLines -join [Environment]::NewLine | Set-Content -Path $ResearchPackPath -Encoding utf8

$callLines = New-Object System.Collections.Generic.List[string]
$callLines.Add("# Call Runbook - $briefDate")
$callLines.Add("")
$callLines.Add("Use this during call blocks. Keep calls to 3-5 minutes unless invited to go deeper.")
$callLines.Add("")
$slots = @("09:15-09:35", "09:35-09:55", "09:55-10:15", "10:15-10:35", "10:35-10:55")
for ($i = 0; $i -lt $topFiveTargets.Count; $i++) {
    $target = $topFiveTargets[$i]
    $slot = $slots[$i]
    $dial = if ([string]::IsNullOrWhiteSpace($target.contact_phone)) { "" } else { "tel:+1$($target.contact_phone)" }
    $contactDisplay = if (-not [string]::IsNullOrWhiteSpace([string]$target.contact_name)) { [string]$target.contact_name } else { [string]$target.decision_maker_guess }
    $locationLabel = Get-TargetLocation $target
    $contextHook = if (-not [string]::IsNullOrWhiteSpace([string]$target.business_description)) {
        "$($target.business_description) | $($target.public_signal_summary)"
    } else {
        "$($target.public_signal_summary) | $locationLabel"
    }
    $ownerHistory = switch ([string]$target.signal_type) {
        "incumbent_award" { "Public award history is already visible through the incumbent / recompete record." }
        "registered_vendor_supporting" { "NJSTART profile lists direct vendor visibility in the public-buying ecosystem." }
        default { "A named bidder / award trace is visible in a South Jersey public source." }
    }
    $callLines.Add("## $slot | $($target.company_name)")
    $callLines.Add("- Contact: $contactDisplay ($($target.decision_maker_guess))")
    $callLines.Add("- Phone: $($target.contact_phone)")
    $callLines.Add("- Click to dial: $dial")
    $callLines.Add("- Context hooks: $contextHook")
    $callLines.Add("- Owner/local history: $ownerHistory")
    $callLines.Add("- Trigger to reference: $($target.public_signal_summary)")
    $callLines.Add("- Likely bottleneck: $($target.likely_bottleneck)")
    $callLines.Add("- Priority angle: $($target.primary_angle)")
    $callLines.Add("- Research notes: Email $($target.contact_email) | Evidence: $($target.source_url)")
    $callLines.Add("")
    $callLines.Add("**Open (20-30 sec):**")
    $callLines.Add("Hi $contactDisplay, this is Timmy Semenza with Boss Key in South Jersey. I help janitorial operators clean up the proposal and admin work that slows public-sector response and keeps the owner stuck in the weeds.")
    $callLines.Add("")
    $callLines.Add("**Tailored bridge:**")
    $callLines.Add("I saw your public-sector bid signal and figured you may already be visible to buyers, so I wanted to see whether the bid/admin side is as clean as the field side.")
    $callLines.Add("")
    $callLines.Add("**2 discovery questions:**")
    $callLines.Add("1. When a public bid comes in, who owns the response package and follow-up right now?")
    $callLines.Add("2. Where does the admin burden hit hardest - compliance forms, staffing handoff, reporting, or proposal assembly?")
    $callLines.Add("")
    $callLines.Add("**Close:**")
    $callLines.Add("If helpful, I can run a short Opportunity Foresight Sprint and show the first two or three fixes before you commit to anything bigger. Open to 20 minutes next week?")
    $callLines.Add("")
}
$callLines -join [Environment]::NewLine | Set-Content -Path $CallRunbookPath -Encoding utf8

$opportunityRows |
    Sort-Object @{ Expression = { [string]$_.status }; Descending = $false }, @{ Expression = { [int]$_.fit_score }; Descending = $true }, opportunity_id |
    Export-Csv -Path $OpportunityFile -NoTypeInformation

$candidateRows |
    Sort-Object @{ Expression = { [int]$_.priority_score }; Descending = $true }, company_name |
    Export-Csv -Path $CandidatesFile -NoTypeInformation

$pipelineRows |
    Sort-Object @{ Expression = { [int]$_.priority_score }; Descending = $true }, company_name |
    Export-Csv -Path $PipelineFile -NoTypeInformation

$relationshipRows |
    Sort-Object created_date, company_name |
    Export-Csv -Path $RelationshipQueueFile -NoTypeInformation

$ptwRows |
    Sort-Object created_date, company_name |
    Export-Csv -Path $PtwQueueFile -NoTypeInformation

Write-Output "South Jersey janitorial bid-signal sweep complete."
Write-Output "Primary targets: $($primaryTargets.Count)"
Write-Output "Watchlist targets: $($watchlistTargets.Count)"
Write-Output "Brief: $briefPath"
