param(
    [int]$DaysLookahead = 365,
    [string]$TargetsFile = "marketing-agents/data/public_recompete_targets_burlco.csv",
    [string]$OpportunityFile = "marketing-agents/data/public_opportunity_log.csv",
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$BriefsDir = "marketing-agents/briefs/generated/public-capture",
    [double]$TargetAnnualRevenue = 350000,
    [double]$PublicRevenueShareCap = 0.40,
    [int]$MaxConcurrentPublicAccounts = 3,
    [double]$SoloDeliveryHoursPerWeek = 30,
    [double]$WeeklyAdminCapHours = 5,
    [double]$DiagnosticFeeTarget = 5500,
    [double]$PublicAdvisoryRetainerTarget = 2500,
    [int]$MinWinabilityScore = 75,
    [int]$MinCommunityFitScore = 80,
    [int]$NoTouchMinWinabilityScore = 80
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls11 -bor [Net.SecurityProtocolType]::Tls

function Get-SafeDate([string]$value) {
    if ([string]::IsNullOrWhiteSpace($value)) { return $null }
    try { return ([datetime]$value).Date } catch { return $null }
}

function To-DateString([datetime]$value) {
    if ($null -eq $value) { return "" }
    return $value.ToString("yyyy-MM-dd")
}

function Clamp-Int([double]$value, [int]$min, [int]$max) {
    $i = [int][math]::Round($value)
    if ($i -lt $min) { return $min }
    if ($i -gt $max) { return $max }
    return $i
}

function Normalize-Name([string]$value) {
    if ([string]::IsNullOrWhiteSpace($value)) { return "" }
    return (($value -replace "\s+", " ").Trim()).ToUpperInvariant()
}

function Get-OfferProfile([string]$entityName, [string]$office) {
    $entity = [string]$entityName
    $officeText = [string]$office
    if ($entity -like "*County*" -or $entity -like "*College*") {
        return [ordered]@{
            offer_name = "Discovery + Procurement Readiness Sprint"
            one_time_value = 7500
            monthly_retainer = 2500
            est_hours_per_week = 10
            duration_weeks = 3
        }
    }

    if ($officeText -like "*IT*" -or $officeText -like "*Purchasing*") {
        return [ordered]@{
            offer_name = "Civic Digital Discovery Sprint"
            one_time_value = 5500
            monthly_retainer = 2500
            est_hours_per_week = 8
            duration_weeks = 2
        }
    }

    return [ordered]@{
        offer_name = "Resident Workflow Diagnostic"
        one_time_value = 5500
        monthly_retainer = 2500
        est_hours_per_week = 8
        duration_weeks = 2
    }
}

function Get-RemoteText([string]$Url) {
    try {
        $resp = Invoke-WebRequest -Uri $Url -TimeoutSec 35 -ErrorAction Stop
        $content = [string]$resp.Content
        if (-not [string]::IsNullOrWhiteSpace($content)) {
            return [pscustomobject]@{ ok = $true; text = $content; source = "invoke-webrequest" }
        }
    } catch {
    }

    try {
        $curlPath = (Get-Command curl.exe -ErrorAction Stop).Source
        $content = & $curlPath -L --max-time 35 -s $Url
        $text = [string]$content
        if (-not [string]::IsNullOrWhiteSpace($text)) {
            return [pscustomobject]@{ ok = $true; text = $text; source = "curl" }
        }
    } catch {
    }

    return [pscustomobject]@{ ok = $false; text = ""; source = "none" }
}

function Extract-DateCandidates([string]$text) {
    $dates = New-Object System.Collections.Generic.List[datetime]
    if ([string]::IsNullOrWhiteSpace($text)) { return $dates }

    $monthPattern = "(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}"
    $isoPattern = "\b(20\d{2})-(0[1-9]|1[0-2])-([0-2]\d|3[01])\b"

    foreach ($m in [regex]::Matches($text, $monthPattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
        $d = Get-SafeDate $m.Value
        if ($null -ne $d) { $dates.Add($d) }
    }
    foreach ($m in [regex]::Matches($text, $isoPattern)) {
        $d = Get-SafeDate $m.Value
        if ($null -ne $d) { $dates.Add($d) }
    }

    return $dates
}

function Upsert-Opportunity(
    [object[]]$OpportunityRows,
    [hashtable]$OppById,
    [string]$OpportunityId,
    [string]$Agency,
    [string]$Title,
    [string]$SolicitationNumber,
    [string]$Location,
    [datetime]$DueDate,
    [string]$EstimatedValue,
    [int]$FitScore,
    [string]$NextAction,
    [datetime]$NextActionDue,
    [string]$Notes
) {
    $dueDateText = To-DateString $DueDate
    $nextActionDueText = To-DateString $NextActionDue
    if ($OppById.ContainsKey($OpportunityId)) {
        $row = $OppById[$OpportunityId]
        $row.agency = $Agency
        $row.solicitation_title = $Title
        $row.solicitation_number = $SolicitationNumber
        $row.location = $Location
        $row.due_date = $dueDateText
        $row.estimated_value = $EstimatedValue
        $row.fit_score = "$FitScore"
        $row.status = "identified"
        $row.bid_decision = "target-pre-rfp-capture"
        $row.assigned_owner = "Timmy Semenza"
        $row.next_action = $NextAction
        $row.next_action_due = $nextActionDueText
        $row.notes = $Notes
        return @{ rows = $OpportunityRows; created = $false }
    }

    $newRow = [pscustomobject][ordered]@{
        opportunity_id = $OpportunityId
        agency = $Agency
        solicitation_title = $Title
        solicitation_number = $SolicitationNumber
        location = $Location
        due_date = $dueDateText
        estimated_value = $EstimatedValue
        fit_score = "$FitScore"
        status = "identified"
        bid_decision = "target-pre-rfp-capture"
        assigned_owner = "Timmy Semenza"
        next_action = $NextAction
        next_action_due = $nextActionDueText
        notes = $Notes
    }

    $OpportunityRows += $newRow
    $OppById[$OpportunityId] = $newRow
    return @{ rows = $OpportunityRows; created = $true }
}

if (-not (Test-Path $OpportunityFile)) { throw "Missing file: $OpportunityFile" }
if (-not (Test-Path $PipelineFile)) { throw "Missing file: $PipelineFile" }
if (-not (Test-Path $BriefsDir)) { New-Item -ItemType Directory -Path $BriefsDir -Force | Out-Null }

$today = (Get-Date).Date
$windowEnd = $today.AddDays($DaysLookahead)
$nextActionDue = $today.AddDays(1)

$targets = @(
    [ordered]@{
        id = "BURLCO-COUNTY"
        entity_name = "Burlington County"
        office = "Purchasing"
        location = "Burlington County, NJ"
        contract_focus = "County website modernization and digital service workflows"
        source_url = "https://www.co.burlington.nj.us/490/Bid-Solicitations"
        source_url_2 = "https://burlcobids.ionwave.net/SourcingEvents.aspx?SourceType=1"
        contact_name = "Purchasing Agent"
        contact_role = "County Purchasing"
        contact_email = ""
        contact_phone = "609-265-5012"
        cadence_hint = "rolling"
        last_signal = "2026-02-20"
        baseline_priority = 82
        incumbent_lock_risk = 6
        buying_access_score = 8
        scope_match_score = 9
        local_proximity_score = 9
        community_anchor_score = 10
        in_person_access_score = 9
    },
    [ordered]@{
        id = "BURLINGTON-TWP"
        entity_name = "Burlington Township"
        office = "Clerk/Purchasing"
        location = "Burlington Township, NJ"
        contract_focus = "IT support and municipal web platform refresh"
        source_url = "https://twp.burlington.nj.us/news-events/?FeedID=1547"
        source_url_2 = "https://twp.burlington.nj.us/news-events/?FeedID=1551"
        contact_name = "Municipal Clerk"
        contact_role = "Clerk/Purchasing"
        contact_email = ""
        contact_phone = "609-386-4444"
        cadence_hint = "annual-q4"
        last_signal = "2025-12-18"
        baseline_priority = 93
        incumbent_lock_risk = 5
        buying_access_score = 8
        scope_match_score = 9
        local_proximity_score = 10
        community_anchor_score = 10
        in_person_access_score = 10
    },
    [ordered]@{
        id = "MEDFORD-TWP"
        entity_name = "Medford Township"
        office = "Administration / IT"
        location = "Medford Township, NJ"
        contract_focus = "IT services (administration + police) and civic software support"
        source_url = "https://medfordtownship.com/bids/"
        source_url_2 = ""
        contact_name = "Municipal Administration"
        contact_role = "Administration / Purchasing"
        contact_email = ""
        contact_phone = "609-654-2608"
        cadence_hint = "annual-q4"
        last_signal = "2025-12-20"
        baseline_priority = 95
        incumbent_lock_risk = 5
        buying_access_score = 8
        scope_match_score = 9
        local_proximity_score = 10
        community_anchor_score = 10
        in_person_access_score = 10
    },
    [ordered]@{
        id = "RCBC"
        entity_name = "Rowan College at Burlington County"
        office = "Purchasing"
        location = "Mount Laurel, NJ"
        contract_focus = "College digital experience, web, and managed IT services"
        source_url = "https://rcbc.edu/vendor-opportunities"
        source_url_2 = "https://rcbc.edu/current-legal-notices"
        contact_name = "Purchasing"
        contact_role = "Procurement"
        contact_email = "purchasing@rcbc.edu"
        contact_phone = "856-291-4221"
        cadence_hint = "rolling"
        last_signal = "2026-01-15"
        baseline_priority = 88
        incumbent_lock_risk = 7
        buying_access_score = 7
        scope_match_score = 8
        local_proximity_score = 8
        community_anchor_score = 9
        in_person_access_score = 8
    },
    [ordered]@{
        id = "WILLINGBORO-TWP"
        entity_name = "Willingboro Township"
        office = "Township Clerk"
        location = "Willingboro, NJ"
        contract_focus = "Municipal website refresh and resident communications systems"
        source_url = "https://www.willingboronj.gov/departments/township-clerk/rfp-rfq-bids"
        source_url_2 = ""
        contact_name = "Township Clerk"
        contact_role = "Clerk/Purchasing"
        contact_email = ""
        contact_phone = ""
        cadence_hint = "annual-q4"
        last_signal = "2026-01-10"
        baseline_priority = 78
        incumbent_lock_risk = 6
        buying_access_score = 6
        scope_match_score = 8
        local_proximity_score = 9
        community_anchor_score = 9
        in_person_access_score = 8
    },
    [ordered]@{
        id = "MOUNT-HOLLY"
        entity_name = "Mount Holly Township"
        office = "Township Clerk"
        location = "Mount Holly, NJ"
        contract_focus = "Website and public communications modernization"
        source_url = "https://twp.mountholly.nj.us/bid-advertisements/"
        source_url_2 = "https://cdn.townweb.com/twp.mountholly.nj.us/wp-content/uploads/2025/11/2026_RFP_Package-All_Professionals.pdf"
        contact_name = "Stephanie Marnell"
        contact_role = "Township Clerk"
        contact_email = "smarnell@twp.mountholly.nj.us"
        contact_phone = "609-845-1101"
        cadence_hint = "annual-q4"
        last_signal = "2025-11-15"
        baseline_priority = 80
        incumbent_lock_risk = 7
        buying_access_score = 7
        scope_match_score = 8
        local_proximity_score = 10
        community_anchor_score = 10
        in_person_access_score = 10
    },
    [ordered]@{
        id = "CITY-OF-BURLINGTON"
        entity_name = "City of Burlington"
        office = "Business Administration / Purchasing"
        location = "Burlington, NJ"
        contract_focus = "City website and resident service workflow modernization"
        source_url = "https://www.burlingtonnj.us/purchasing/"
        source_url_2 = ""
        contact_name = "James Conyer"
        contact_role = "Business Administrator"
        contact_email = "JConyer@burlingtonnj.us"
        contact_phone = "609-386-0200 x133"
        cadence_hint = "rolling"
        last_signal = "2026-01-25"
        baseline_priority = 83
        incumbent_lock_risk = 7
        buying_access_score = 8
        scope_match_score = 9
        local_proximity_score = 10
        community_anchor_score = 10
        in_person_access_score = 10
    }
)

$targetRows = @()

foreach ($target in $targets) {
    $sourceText = ""
    $fetchStatus = "ok"
    $fetchMethods = New-Object System.Collections.Generic.List[string]
    $keywordHits = New-Object System.Collections.Generic.List[string]
    $latestDate = Get-SafeDate $target.last_signal

    $urls = @($target.source_url, $target.source_url_2) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    foreach ($url in $urls) {
        $page = Get-RemoteText -Url $url
        if ($page.ok) {
            $sourceText += "`n" + $page.text
            $fetchMethods.Add($page.source)
        } else {
            $fetchStatus = "partial"
        }
    }

    if ([string]::IsNullOrWhiteSpace($sourceText)) {
        $sourceText = ""
        $fetchStatus = "fallback"
    }

    $lower = $sourceText.ToLowerInvariant()
    foreach ($k in @("it support", "information technology", "website", "web design", "digital", "software", "vendor opportunities", "rfp", "rfq", "legal notice")) {
        if ($lower -like ("*" + $k + "*")) { $keywordHits.Add($k) }
    }

    $dateCandidates = Extract-DateCandidates $sourceText
    if ($dateCandidates.Count -gt 0) {
        $candidateLatest = $dateCandidates | Sort-Object -Descending | Select-Object -First 1
        if ($null -ne $candidateLatest -and $candidateLatest -gt $latestDate) {
            $latestDate = $candidateLatest
        }
    }

    $expectedDate = $null
    switch ($target.cadence_hint) {
        "annual-q4" {
            if ($null -eq $latestDate) {
                $expectedDate = [datetime]::new($today.Year, 11, 15)
            } else {
                $expectedDate = $latestDate.AddYears(1)
            }
        }
        default {
            if ($null -eq $latestDate) {
                $expectedDate = $today.AddDays(60)
            } else {
                $expectedDate = $latestDate.AddMonths(9)
            }
        }
    }

    $daysToExpected = [int]($expectedDate - $today).TotalDays
    $inWindow = $expectedDate -le $windowEnd
    $keywordScore = if ($keywordHits.Count -ge 4) { 10 } elseif ($keywordHits.Count -ge 2) { 6 } else { 2 }
    $recencyScore = if ($null -ne $latestDate) {
        $daysFromSignal = [int]($today - $latestDate).TotalDays
        if ($daysFromSignal -le 45) { 12 } elseif ($daysFromSignal -le 120) { 8 } else { 4 }
    } else { 0 }
    $windowScore = if ($daysToExpected -le 60) { 16 } elseif ($daysToExpected -le 120) { 12 } elseif ($inWindow) { 8 } else { 3 }
    $contactScore = if (-not [string]::IsNullOrWhiteSpace($target.contact_email) -or -not [string]::IsNullOrWhiteSpace($target.contact_phone)) { 5 } else { 1 }
    $fetchScore = if ($fetchStatus -eq "ok") { 5 } elseif ($fetchStatus -eq "partial") { 3 } else { 1 }
    $priority = Clamp-Int ($target.baseline_priority + $keywordScore + $recencyScore + $windowScore + $contactScore + $fetchScore - 20) 55 99

    $notes = @()
    $notes += ("Fetch status: {0}" -f $fetchStatus)
    if ($fetchMethods.Count -gt 0) { $notes += ("Fetch method: {0}" -f (($fetchMethods | Select-Object -Unique) -join ", ")) }
    $notes += ("Cadence hint: {0}" -f $target.cadence_hint)
    if ($keywordHits.Count -gt 0) { $notes += ("Keyword hits: {0}" -f (($keywordHits | Select-Object -Unique) -join ", ")) }

    $targetRows += [pscustomobject][ordered]@{
        target_id = [string]$target.id
        entity_name = [string]$target.entity_name
        office = [string]$target.office
        contract_focus = [string]$target.contract_focus
        source_url = [string]$target.source_url
        source_url_2 = [string]$target.source_url_2
        last_signal_date = To-DateString $latestDate
        expected_recompete_date = To-DateString $expectedDate
        days_to_expected = "$daysToExpected"
        in_lookahead_window = if ($inWindow) { "yes" } else { "no" }
        priority_score = "$priority"
        contact_name = [string]$target.contact_name
        contact_role = [string]$target.contact_role
        contact_email = [string]$target.contact_email
        contact_phone = [string]$target.contact_phone
        next_action = "Request pre-RFP discovery call and ask for web/digital renewal timing."
        next_action_due = To-DateString $nextActionDue
        offer_name = ""
        est_one_time_value = ""
        est_monthly_retainer = ""
        est_hours_per_week = ""
        financial_fit_score = ""
        solo_fit_score = ""
        winability_score = ""
        winability_gate = ""
        direct_contact_identified = ""
        no_touch_gate = ""
        qualification_score = ""
        qualification_gate = ""
        community_fit_score = ""
        community_gate = ""
        displacement_score = ""
        bloat_hypothesis = ""
        proof_required = ""
        kill_criteria = ""
        relationship_path = ""
        prewire_actions = ""
        capacity_gate = ""
        pursuit_decision = ""
        notes = ($notes -join " | ")
    }
}

$targetRows = $targetRows | Sort-Object @{ Expression = { [int]$_.priority_score }; Descending = $true }, @{ Expression = { [int]$_.days_to_expected }; Descending = $false }

$opportunityRows = @(Import-Csv -Path $OpportunityFile)
$pipelineRows = @(Import-Csv -Path $PipelineFile)

# Remove legacy rows created with date-suffixed IDs so reruns remain idempotent.
$opportunityRows = @(
    $opportunityRows | Where-Object {
        $id = [string]$_.opportunity_id
        $isLegacy = $id -match "^BURLCO-DIG-[A-Z0-9]+-\d{8}$"
        -not $isLegacy
    }
)

$oppById = @{}
foreach ($o in $opportunityRows) { $oppById[[string]$o.opportunity_id] = $o }

$pipelineByName = @{}
foreach ($p in $pipelineRows) {
    $key = Normalize-Name ([string]$p.company_name)
    if (-not [string]::IsNullOrWhiteSpace($key) -and -not $pipelineByName.ContainsKey($key)) {
        $pipelineByName[$key] = $p
    }
}

$activePublicRows = @(
    $pipelineRows | Where-Object {
        $notes = [string]$_.notes
        $status = ([string]$_.status).ToLowerInvariant()
        $stage = ([string]$_.stage).ToLowerInvariant()
        $isCapacityConsumingStage = $stage -in @("outreach-sent", "connected", "proposal", "active-pursuit")
        ($notes -match "digital_recompete_target_id=") -and ($status -eq "active") -and $isCapacityConsumingStage
    }
)

$monthlyRevenueTarget = [double]($TargetAnnualRevenue / 12.0)
$publicMonthlyRevenueCap = [double]($monthlyRevenueTarget * $PublicRevenueShareCap)
$activePublicCount = $activePublicRows.Count
$currentPublicMonthlyCommit = [double]($activePublicCount * $PublicAdvisoryRetainerTarget)
$availableDeliveryHours = [double]($SoloDeliveryHoursPerWeek - $WeeklyAdminCapHours)
$openSlots = [math]::Max(0, ($MaxConcurrentPublicAccounts - $activePublicCount))
$publicRevenueHeadroom = [math]::Max(0, ($publicMonthlyRevenueCap - $currentPublicMonthlyCommit))

$targetRowsScoped = @()
$slotUse = 0
foreach ($r in $targetRows) {
    $targetMeta = $targets | Where-Object { $_.id -eq [string]$r.target_id } | Select-Object -First 1
    $offer = Get-OfferProfile -entityName ([string]$r.entity_name) -office ([string]$r.office)
    $hours = [double]$offer.est_hours_per_week
    $oneTime = [double]$offer.one_time_value
    $monthlyRetainer = [double]$offer.monthly_retainer

    $financialFit = Clamp-Int (([int]$r.priority_score) + ($(if ($oneTime -ge $DiagnosticFeeTarget) { 8 } else { 3 })) + ($(if ($monthlyRetainer -le $publicRevenueHeadroom) { 8 } else { 2 }))) 55 99
    $soloFit = Clamp-Int (([int]$r.priority_score) + ($(if ($hours -le $availableDeliveryHours) { 10 } else { -8 })) + ($(if (([int]$r.days_to_expected) -le 365) { 6 } else { 2 }))) 50 99

    $capacityGate = if ($hours -le $availableDeliveryHours) { "pass" } else { "fail-hours" }

    $contactability = if (-not [string]::IsNullOrWhiteSpace([string]$r.contact_email)) { 10 } elseif (-not [string]::IsNullOrWhiteSpace([string]$r.contact_phone)) { 8 } else { 4 }
    $runwayScore = if (([int]$r.days_to_expected) -ge 180 -and ([int]$r.days_to_expected) -le 420) { 10 } elseif (([int]$r.days_to_expected) -ge 120) { 8 } else { 5 }
    $signalStrength = if ([string]$r.notes -match "Keyword hits:") { 9 } else { 5 }
    $buyingAccess = if ($null -ne $targetMeta) { [int]$targetMeta.buying_access_score } else { 6 }
    $scopeMatch = if ($null -ne $targetMeta) { [int]$targetMeta.scope_match_score } else { 7 }
    $localProximity = if ($null -ne $targetMeta) { [int]$targetMeta.local_proximity_score } else { 8 }
    $incumbentRisk = if ($null -ne $targetMeta) { [int]$targetMeta.incumbent_lock_risk } else { 7 }
    $incumbentAdvantage = 11 - $incumbentRisk

    $winabilityRaw = (($contactability * 0.18) + ($runwayScore * 0.18) + ($signalStrength * 0.14) + ($buyingAccess * 0.16) + ($scopeMatch * 0.14) + ($localProximity * 0.10) + ($incumbentAdvantage * 0.10)) * 10
    $winabilityScore = Clamp-Int $winabilityRaw 45 99
    $winabilityGate = if ($winabilityScore -ge $MinWinabilityScore) { "pass" } else { "fail-winability" }
    $hasNamedContact = (-not [string]::IsNullOrWhiteSpace([string]$r.contact_name)) -and (([string]$r.contact_name).ToLowerInvariant() -notin @("purchasing","municipal administration","township clerk","purchasing agent"))
    $hasDirectChannel = (-not [string]::IsNullOrWhiteSpace([string]$r.contact_email)) -or (-not [string]::IsNullOrWhiteSpace([string]$r.contact_phone))
    $directContactIdentified = if ($hasDirectChannel -and (($hasNamedContact) -or (-not [string]::IsNullOrWhiteSpace([string]$r.contact_email)))) { "yes" } else { "no" }
    $noTouchGate = if ($winabilityScore -ge $NoTouchMinWinabilityScore -and $directContactIdentified -eq "yes") { "pass" } else { "fail-no-touch" }

    $communityAnchor = if ($null -ne $targetMeta) { [int]$targetMeta.community_anchor_score } else { 7 }
    $inPersonAccess = if ($null -ne $targetMeta) { [int]$targetMeta.in_person_access_score } else { 7 }
    $localRootedness = $localProximity
    $communityFitRaw = (($communityAnchor * 0.45) + ($inPersonAccess * 0.30) + ($localRootedness * 0.25)) * 10
    $communityFitScore = Clamp-Int $communityFitRaw 50 99
    $communityGate = if ($communityFitScore -ge $MinCommunityFitScore) { "pass" } else { "fail-community" }

    $complexitySignal = if (([string]$r.entity_name -match "County|College") -or ([string]$r.office -match "IT|Purchasing")) { 9 } else { 7 }
    $workflowSignal = if (([string]$r.notes -match "software|information technology|digital|website")) { 9 } else { 6 }
    $timingSignal = if (([int]$r.days_to_expected) -ge 180 -and ([int]$r.days_to_expected) -le 420) { 9 } elseif (([int]$r.days_to_expected) -ge 120) { 7 } else { 5 }
    $displacementRaw = (($complexitySignal * 0.45) + ($workflowSignal * 0.35) + ($timingSignal * 0.20)) * 10
    $displacementScore = Clamp-Int $displacementRaw 40 99

    $bloatHypothesis = "Manual content/update cycles and vendor handoff overhead are slowing resident-facing changes."
    if (([string]$r.entity_name -match "County|College")) {
        $bloatHypothesis = "Multi-department approvals and managed-service layering are likely increasing cycle time and cost."
    } elseif (([string]$r.office -match "IT")) {
        $bloatHypothesis = "IT support + civic web scope may be bundled too broadly, inflating change-request overhead."
    }
    $proofRequired = "Confirm current platform/vendor, average change turnaround time, and who owns content approval."
    $killCriteria = "No near-term renewal, no access to buyer/stakeholder, or no operational pain acknowledged."

    $prewire = @(
        "Confirm contracting officer or buyer of record and add to direct contact map."
        "Request a non-sales capability briefing focused on scope clarity and procurement readiness."
        "Deliver a one-page risk-and-scope memo tailored to this entity."
        "Ask for expected renewal/advertisement month and board approval path."
    ) -join " "

    $relationshipPath = "Attend one public meeting, request an in-person intro with the contracting office, and follow with a one-page local modernization memo."
    $qCapacity = if ($capacityGate -eq "pass") { 20 } else { 0 }
    $qWinability = if ($winabilityGate -eq "pass") { 20 } else { 0 }
    $qCommunity = if ($communityGate -eq "pass") { 20 } else { 0 }
    $qNoTouch = if ($noTouchGate -eq "pass") { 25 } else { 0 }
    $qTiming = if (([int]$r.days_to_expected) -ge 150 -and ([int]$r.days_to_expected) -le 450) { 15 } else { 5 }
    $qualificationRaw = $qCapacity + $qWinability + $qCommunity + $qNoTouch + $qTiming
    $qualificationScore = Clamp-Int $qualificationRaw 0 100
    $qualificationGate = if ($qualificationScore -ge 80) { "pass" } else { "fail-qualification" }

    $decision = "watchlist_capacity"
    if ($noTouchGate -ne "pass" -or $qualificationGate -ne "pass") {
        $decision = "no_touch_reject"
    } elseif ($capacityGate -eq "pass" -and $winabilityGate -eq "pass" -and $communityGate -eq "pass" -and $slotUse -lt $openSlots -and $monthlyRetainer -le $publicRevenueHeadroom) {
        $decision = "pursue_now"
        $slotUse++
        $publicRevenueHeadroom -= $monthlyRetainer
    } else {
        $decision = "watchlist_capacity"
    }

    $targetRowsScoped += [pscustomobject][ordered]@{
        target_id = [string]$r.target_id
        entity_name = [string]$r.entity_name
        office = [string]$r.office
        contract_focus = [string]$r.contract_focus
        source_url = [string]$r.source_url
        source_url_2 = [string]$r.source_url_2
        last_signal_date = [string]$r.last_signal_date
        expected_recompete_date = [string]$r.expected_recompete_date
        days_to_expected = [string]$r.days_to_expected
        in_lookahead_window = [string]$r.in_lookahead_window
        priority_score = [string]$r.priority_score
        contact_name = [string]$r.contact_name
        contact_role = [string]$r.contact_role
        contact_email = [string]$r.contact_email
        contact_phone = [string]$r.contact_phone
        next_action = [string]$r.next_action
        next_action_due = [string]$r.next_action_due
        offer_name = [string]$offer.offer_name
        est_one_time_value = ("{0:N0}" -f $oneTime)
        est_monthly_retainer = ("{0:N0}" -f $monthlyRetainer)
        est_hours_per_week = ("{0:N1}" -f $hours)
        financial_fit_score = "$financialFit"
        solo_fit_score = "$soloFit"
        winability_score = "$winabilityScore"
        winability_gate = $winabilityGate
        direct_contact_identified = $directContactIdentified
        no_touch_gate = $noTouchGate
        qualification_score = "$qualificationScore"
        qualification_gate = $qualificationGate
        community_fit_score = "$communityFitScore"
        community_gate = $communityGate
        displacement_score = "$displacementScore"
        bloat_hypothesis = $bloatHypothesis
        proof_required = $proofRequired
        kill_criteria = $killCriteria
        relationship_path = $relationshipPath
        prewire_actions = $prewire
        capacity_gate = $capacityGate
        pursuit_decision = $decision
        notes = [string]$r.notes
    }
}

$targetRows = $targetRowsScoped | Sort-Object @{ Expression = { if ([string]$_.pursuit_decision -eq "pursue_now") { 1 } else { 0 } }; Descending = $true }, @{ Expression = { [int]$_.priority_score }; Descending = $true }, @{ Expression = { [int]$_.days_to_expected }; Descending = $false }
$targetRows | Export-Csv -Path $TargetsFile -NoTypeInformation

$newOpp = 0
$newPipeline = 0

foreach ($r in $targetRows) {
    $dueDate = Get-SafeDate ([string]$r.expected_recompete_date)
    if ($null -eq $dueDate) { $dueDate = $today.AddDays(90) }

    $oppId = "BURLCO-DIG-{0}" -f ($r.target_id -replace "[^A-Za-z0-9]", "")
    $opp = Upsert-Opportunity `
        -OpportunityRows $opportunityRows `
        -OppById $oppById `
        -OpportunityId $oppId `
        -Agency ([string]$r.entity_name) `
        -Title ("Likely recompete: {0}" -f [string]$r.contract_focus) `
        -SolicitationNumber ([string]$r.target_id) `
        -Location ([string]$r.office + " | " + [string]$r.entity_name) `
        -DueDate $dueDate `
        -EstimatedValue "Unknown" `
        -FitScore ([int]$r.priority_score) `
        -NextAction $(if ([string]$r.pursuit_decision -eq "pursue_now") { [string]$r.next_action } elseif ([string]$r.pursuit_decision -eq "no_touch_reject") { "Do not outreach. Improve contact intelligence and winability before re-evaluating." } else { "Hold for capacity/winability/community fit; review in next weekly planning cycle." }) `
        -NextActionDue (Get-SafeDate ([string]$r.next_action_due)) `
        -Notes ('Source: {0}; last signal {1}; expected recompete {2}; pursuit={3}; qualification={4}; no_touch={5}; direct_contact={6}; winability={7}; community_fit={8}; displacement={9}; offer={10}; one-time=${11}; monthly=${12}; hours/wk={13}; bloat_hypothesis={14}; proof_required={15}; kill_criteria={16}; relationship_path={17}; prewire={18}; {19}' -f [string]$r.source_url, [string]$r.last_signal_date, [string]$r.expected_recompete_date, [string]$r.pursuit_decision, [string]$r.qualification_score, [string]$r.no_touch_gate, [string]$r.direct_contact_identified, [string]$r.winability_score, [string]$r.community_fit_score, [string]$r.displacement_score, [string]$r.offer_name, [string]$r.est_one_time_value, [string]$r.est_monthly_retainer, [string]$r.est_hours_per_week, [string]$r.bloat_hypothesis, [string]$r.proof_required, [string]$r.kill_criteria, [string]$r.relationship_path, [string]$r.prewire_actions, [string]$r.notes)

    $opportunityRows = $opp.rows
    if ($opp.created) { $newOpp++ }

    $pipelineCompanyName = ([string]$r.entity_name + " - " + [string]$r.office)
    $pipelineKey = Normalize-Name $pipelineCompanyName
    if (-not $pipelineByName.ContainsKey($pipelineKey)) {
        $newPipe = [pscustomobject][ordered]@{
            company_name = $pipelineCompanyName
            website = [string]$r.source_url
            location = [string]$r.office + ", Burlington County area"
            target_contact = [string]$r.contact_name
            role = [string]$r.contact_role
            contact_email = [string]$r.contact_email
            contact_phone = [string]$r.contact_phone
            services_or_contract_focus = [string]$r.contract_focus
            personalization_hook_1 = ("Public procurement signal dated {0}" -f [string]$r.last_signal_date)
            personalization_hook_2 = ("Likely recompete around {0}" -f [string]$r.expected_recompete_date)
            likely_bottleneck = "Staff capacity for digital modernization and procurement lead time"
            primary_angle = ("{0} to define practical modernization scope before bid release" -f [string]$r.offer_name)
            priority_score = [string]$r.priority_score
            last_touch_date = ""
            next_touch_date = To-DateString $today
            stage = $(if ([string]$r.pursuit_decision -eq "pursue_now") { "research" } elseif ([string]$r.pursuit_decision -eq "no_touch_reject") { "disqualified" } else { "watchlist" })
            status = "active"
            notes = ('Auto-seeded from Burlington County digital recompete radar ({0}) | digital_recompete_target_id={1} | pursuit={2} | qualification={3} | no_touch={4} | direct_contact={5} | winability={6} | community_fit={7} | displacement={8} | offer={9} | est_one_time=${10} | est_monthly=${11} | est_hours_per_week={12}' -f (To-DateString $today), [string]$r.target_id, [string]$r.pursuit_decision, [string]$r.qualification_score, [string]$r.no_touch_gate, [string]$r.direct_contact_identified, [string]$r.winability_score, [string]$r.community_fit_score, [string]$r.displacement_score, [string]$r.offer_name, [string]$r.est_one_time_value, [string]$r.est_monthly_retainer, [string]$r.est_hours_per_week)
        }
        $pipelineRows += $newPipe
        $pipelineByName[$pipelineKey] = $newPipe
        $newPipeline++
    } else {
        $existingPipe = $pipelineByName[$pipelineKey]
        $existingPipe.priority_score = [string]$r.priority_score
        $existingPipe.stage = $(if ([string]$r.pursuit_decision -eq "pursue_now") { "research" } elseif ([string]$r.pursuit_decision -eq "no_touch_reject") { "disqualified" } else { "watchlist" })
        $existingPipe.primary_angle = ("{0} to define practical modernization scope before bid release" -f [string]$r.offer_name)
        if ([string]::IsNullOrWhiteSpace([string]$existingPipe.notes)) {
            $existingPipe.notes = ("digital_recompete_target_id={0}" -f [string]$r.target_id)
        }
        if (($existingPipe.notes -notmatch "digital_recompete_target_id=")) {
            $existingPipe.notes = ($existingPipe.notes + (" | digital_recompete_target_id={0}" -f [string]$r.target_id))
        }
    }
}

$opportunityRows | Sort-Object due_date, @{Expression="fit_score";Descending=$true} | Export-Csv -Path $OpportunityFile -NoTypeInformation
$pipelineRows | Sort-Object @{Expression={[int]($_.priority_score)};Descending=$true}, company_name | Export-Csv -Path $PipelineFile -NoTypeInformation

$briefDate = $today.ToString("yyyy-MM-dd")
$briefPath = Join-Path $BriefsDir ("public-digital-recompete-radar-{0}.md" -f $briefDate)
$top = $targetRows | Select-Object -First 10

$lines = @()
$lines += "# Burlington Public Digital Recompete Radar - $briefDate"
$lines += ""
$lines += "Lookahead window: next $DaysLookahead days"
$lines += "Rows generated: $($targetRows.Count)"
$lines += "New opportunities seeded: $newOpp"
$lines += "New pipeline rows seeded: $newPipeline"
$lines += ('Financial architecture: annual target ${0:N0}; public cap {1:P0} (${2:N0}/mo); current public commit ${3:N0}/mo; open public slots {4}' -f $TargetAnnualRevenue, $PublicRevenueShareCap, $publicMonthlyRevenueCap, $currentPublicMonthlyCommit, $openSlots)
$lines += ("Solo capacity: delivery {0:N1} hrs/week after admin cap ({1:N1}h total, {2:N1}h admin cap)" -f $availableDeliveryHours, $SoloDeliveryHoursPerWeek, $WeeklyAdminCapHours)
$lines += ("Winability gate: minimum score {0}" -f $MinWinabilityScore)
$lines += ("Community gate: minimum score {0}" -f $MinCommunityFitScore)
$lines += ("No-touch rule: require winability >= {0} and direct contact identified" -f $NoTouchMinWinabilityScore)
$lines += ""
$lines += "## Priority Targets"
foreach ($t in $top) {
    $lines += ('- {0} | {1} | expected {2} ({3} days) | score {4} | winability {5} | community {6} | qualification {7} | no_touch {8} | direct_contact {9} | pursuit {10} | offer {11} (${12} + ${13}/mo) | contact: {14} ({15}) {16}' -f `
        $t.entity_name, $t.office, $t.expected_recompete_date, $t.days_to_expected, $t.priority_score, $t.winability_score, $t.community_fit_score, $t.qualification_score, $t.no_touch_gate, $t.direct_contact_identified, $t.pursuit_decision, $t.offer_name, $t.est_one_time_value, $t.est_monthly_retainer, `
        $t.contact_name, $t.contact_role, $t.contact_phone)
}
$lines += ""
$lines += "## Next Actions"
$lines += "1. Send a pre-RFP outreach email only to rows marked pursue_now."
$lines += "2. Ask for contract renewal timing and whether a market-sounding call is possible."
$lines += "3. Lead with a scoped discovery sprint that fits solo delivery and your target margin."
$lines += "4. Keep no_touch_reject targets out of outreach until direct contact and winability criteria are met."
$lines += ""
$lines += "## Intelligence Discipline"
$lines += "1. Only pursue accounts where the bloat hypothesis can be validated with direct evidence."
$lines += "2. Use kill criteria to disqualify quickly and avoid low-yield follow-up."
$lines += "3. Capture every call outcome as procurement intelligence for the next cycle."
$lines += ""
$lines += "## Community Discipline"
$lines += "1. Prioritize targets where you can show up in person and build repeated local trust."
$lines += "2. Request community-facing meetings before discussing services in detail."
$lines += "3. Reinforce that work stays accountable to local outcomes and resident experience."

$lines -join [Environment]::NewLine | Set-Content -Path $briefPath -Encoding UTF8

Write-Output ("Burlington digital recompete radar complete. Targets: {0}; new opps: {1}; new pipeline: {2}" -f $targetRows.Count, $newOpp, $newPipeline)
Write-Output ("Targets CSV: {0}" -f $TargetsFile)
Write-Output ("Brief: {0}" -f $briefPath)
