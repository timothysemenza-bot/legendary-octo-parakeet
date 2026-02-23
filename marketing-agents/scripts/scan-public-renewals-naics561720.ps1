param(
    [string]$NaicsCode = "561720",
    [string[]]$States = @("NJ", "PA", "DE"),
    [bool]$LocalOnly = $true,
    [string[]]$LocalCityHints = @(
        "CINNAMINSON","BURLINGTON","MOUNT HOLLY","MOORESTOWN","MEDFORD","MARLTON","EVESHAM","MAPLE SHADE","PALMYRA","RIVERTON","RIVERSIDE","DELRAN","WILLINGBORO","PEMBERTON","LUMBERTON","SOUTHAMPTON","SHAMONG","TABERNACLE","FLORENCE","BORDENTOWN","CHESTERFIELD","WESTAMPTON",
        "CAMDEN","CHERRY HILL","PENNSAUKEN","COLLINGSWOOD","GLOUCESTER CITY","HADDONFIELD","HADDON HEIGHTS","AUDUBON","VOORHEES","BELLMAWR","RUNNEMEDE","SOMERDALE","STRATFORD","GIBBSBORO","WINSLOW","BERLIN",
        "DEPTFORD","SEWELL","WASHINGTON TWP","MANTUA","WOODBURY","WESTVILLE","PAULSBORO","GLASSBORO","SWEDESBORO","WOOLWICH",
        "MOUNT LAUREL","MERCERVILLE","TRENTON","PRINCETON","HAMILTON","LAWRENCEVILLE","EWING",
        "PHILADELPHIA","BENSALEM","BRISTOL","LEVITTOWN","YARDLEY","LANGHORNE","NEWTOWN","DOYLESTOWN","UPPER DARBY","MEDIA","CHESTER","SPRINGFIELD","GLENOLDEN",
        "WILMINGTON","NEWARK","NEW CASTLE","DOVER"
    ),
    [int]$DaysAhead = 210,
    [int]$DaysFromNow = 30,
    [int]$LookbackYears = 6,
    [double]$MinEstimatedValue = 50000,
    [int]$MaxPages = 20,
    [int]$PageSize = 100,
    [string]$OpportunityFile = "marketing-agents/data/public_opportunity_log.csv",
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$CandidatesFile = "marketing-agents/data/prospect_candidates.csv",
    [string]$BriefsDir = "marketing-agents/briefs"
)

$ErrorActionPreference = "Stop"

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

function Normalize-Company([string]$name) {
    return ($name -replace "\s+", " ").Trim().ToUpperInvariant()
}

if (-not (Test-Path $OpportunityFile)) { throw "Missing file: $OpportunityFile" }
if (-not (Test-Path $PipelineFile)) { throw "Missing file: $PipelineFile" }
if (-not (Test-Path $CandidatesFile)) { throw "Missing file: $CandidatesFile" }
if (-not (Test-Path $BriefsDir)) { New-Item -ItemType Directory -Path $BriefsDir -Force | Out-Null }

$today = (Get-Date).Date
$windowStart = $today.AddDays($DaysFromNow)
$windowEnd = $today.AddDays($DaysAhead)
$lookbackStart = $today.AddYears(-1 * $LookbackYears)

$locationFilters = @()
foreach ($s in $States) {
    if ([string]::IsNullOrWhiteSpace($s)) { continue }
    $locationFilters += @{
        country = "USA"
        state = $s.ToUpperInvariant()
    }
}

$apiUrl = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
$allResults = @()

for ($page = 1; $page -le $MaxPages; $page++) {
    $body = @{
        filters = @{
            time_period = @(@{
                start_date = $lookbackStart.ToString("yyyy-MM-dd")
                end_date = $today.ToString("yyyy-MM-dd")
                date_type = "action_date"
            })
            naics_codes = @($NaicsCode)
            award_type_codes = @("A", "B", "C", "D")
            place_of_performance_locations = $locationFilters
        }
        fields = @(
            "Award ID",
            "Recipient Name",
            "Award Amount",
            "End Date",
            "Awarding Agency",
            "Awarding Sub Agency",
            "Contract Award Type",
            "Place of Performance State Code",
            "pop_city_name",
            "Description"
        )
        page = $page
        limit = $PageSize
        sort = "End Date"
        order = "desc"
    }

    $json = $body | ConvertTo-Json -Depth 10
    $resp = Invoke-RestMethod -Method Post -Uri $apiUrl -Body $json -ContentType "application/json"
    $pageRows = @($resp.results)
    if ($pageRows.Count -eq 0) { break }
    $allResults += $pageRows
}

if ($allResults.Count -eq 0) {
    Write-Output "No rows returned from USAspending query."
    exit 0
}

$filtered = foreach ($r in $allResults) {
    $company = [string]$r."Recipient Name"
    $awardId = [string]$r."Award ID"
    $endDate = Get-SafeDate ([string]$r."End Date")
    $amount = 0.0
    $rawAmount = ([string]$r."Award Amount").Replace("$", "").Replace(",", "").Trim()
    $parsedAmount = [double]::TryParse($rawAmount, [ref]$amount)
    $state = ([string]$r."Place of Performance State Code").ToUpperInvariant()
    $city = [string]$r."pop_city_name"
    $desc = [string]$r."Description"
    $agency = [string]$r."Awarding Agency"
    $subAgency = [string]$r."Awarding Sub Agency"

    if ([string]::IsNullOrWhiteSpace($company) -or [string]::IsNullOrWhiteSpace($awardId)) { continue }
    if ($null -eq $endDate) { continue }
    if ($endDate -lt $windowStart -or $endDate -gt $windowEnd) { continue }
    if (-not $parsedAmount -or [double]::IsNaN($amount) -or [double]::IsInfinity($amount)) { continue }
    if ($amount -lt $MinEstimatedValue) { continue }
    if ($state -and ($States -notcontains $state)) { continue }
    if ($LocalOnly) {
        if ([string]::IsNullOrWhiteSpace($city)) { continue }
        $cityKey = ($city -replace "\s+", " ").Trim().ToUpperInvariant()
        if ($LocalCityHints -notcontains $cityKey) { continue }
    }

    [pscustomobject]@{
        award_id = $awardId.Trim()
        company = $company.Trim()
        agency = $agency.Trim()
        sub_agency = $subAgency.Trim()
        end_date = $endDate
        amount = $amount
        state = $state
        city = $city.Trim()
        description = ($desc -replace "\s+", " ").Trim()
    }
}

if ($filtered.Count -eq 0) {
    Write-Output ("No NAICS {0} renewal candidates in next {1}-{2} days (states: {3})." -f $NaicsCode, $DaysFromNow, $DaysAhead, ($States -join ","))
    exit 0
}

# De-dup by award id + company.
$dedup = $filtered |
    Group-Object -Property @{ Expression = { "{0}|{1}" -f $_.award_id, (Normalize-Company $_.company) } } |
    ForEach-Object {
        $_.Group | Sort-Object amount -Descending | Select-Object -First 1
    }

$opportunityRows = @(Import-Csv -Path $OpportunityFile)
$pipelineRows = @(Import-Csv -Path $PipelineFile)
$candidateRows = @(Import-Csv -Path $CandidatesFile)

$oppById = @{}
foreach ($o in $opportunityRows) { $oppById[[string]$o.opportunity_id] = $o }

$pipelineByCompany = @{}
foreach ($p in $pipelineRows) {
    $key = Normalize-Company ([string]$p.company_name)
    if (-not [string]::IsNullOrWhiteSpace($key) -and -not $pipelineByCompany.ContainsKey($key)) {
        $pipelineByCompany[$key] = $p
    }
}

$candidateByCompany = @{}
foreach ($c in $candidateRows) {
    $key = Normalize-Company ([string]$c.company_name)
    if (-not [string]::IsNullOrWhiteSpace($key) -and -not $candidateByCompany.ContainsKey($key)) {
        $candidateByCompany[$key] = $c
    }
}

$newOppCount = 0
$updatedOppCount = 0
$newPipelineCount = 0
$newCandidateCount = 0

foreach ($row in $dedup) {
    $daysToEnd = [int]($row.end_date - $today).TotalDays
    if ($daysToEnd -lt 0) { continue }

    $urgencyScore = if ($daysToEnd -le 45) { 25 } elseif ($daysToEnd -le 90) { 20 } elseif ($daysToEnd -le 150) { 12 } else { 8 }
    $valueScore =
        if ($row.amount -ge 1500000) { 30 }
        elseif ($row.amount -ge 500000) { 24 }
        elseif ($row.amount -ge 150000) { 16 }
        elseif ($row.amount -ge 75000) { 10 }
        else { 6 }
    $keywordScore = if ($row.description.ToLowerInvariant() -match "janitor|custodial|clean") { 10 } else { 4 }
    $fitScore = Clamp-Int ($urgencyScore + $valueScore + $keywordScore + 30) 45 98

    $oppId = "USAS-{0}-{1}" -f ($row.award_id -replace "[^A-Za-z0-9]", ""), $row.end_date.ToString("yyyyMMdd")
    $agencyLabel = if ([string]::IsNullOrWhiteSpace($row.sub_agency)) { $row.agency } else { "{0} | {1}" -f $row.agency, $row.sub_agency }
    $location = if ([string]::IsNullOrWhiteSpace($row.city)) { $row.state } else { "{0}, {1}" -f $row.city, $row.state }
    $nextActionDue = $today.AddDays(2)
    $notes = "Incumbent: {0}; Award {1}; Ends {2}; Source: USAspending NAICS {3}" -f $row.company, $row.award_id, (To-DateString $row.end_date), $NaicsCode

    if ($oppById.ContainsKey($oppId)) {
        $existing = $oppById[$oppId]
        $existing.agency = $agencyLabel
        $existing.location = $location
        $existing.due_date = To-DateString $row.end_date
        $existing.estimated_value = ("{0:N2}" -f $row.amount)
        $existing.fit_score = "$fitScore"
        $existing.status = "identified"
        $existing.bid_decision = "target-incumbent-outreach"
        $existing.assigned_owner = "Timmy Semenza"
        $existing.next_action = "Identify owner/GM and send local recompete support outreach."
        $existing.next_action_due = To-DateString $nextActionDue
        $existing.notes = $notes
        $updatedOppCount++
    } else {
        $new = [ordered]@{
            opportunity_id = $oppId
            agency = $agencyLabel
            solicitation_title = ("Incumbent NAICS {0} contract likely to recompete ({1})" -f $NaicsCode, $row.company)
            solicitation_number = $row.award_id
            location = $location
            due_date = To-DateString $row.end_date
            estimated_value = ("{0:N2}" -f $row.amount)
            fit_score = "$fitScore"
            status = "identified"
            bid_decision = "target-incumbent-outreach"
            assigned_owner = "Timmy Semenza"
            next_action = "Identify owner/GM and send local recompete support outreach."
            next_action_due = To-DateString $nextActionDue
            notes = $notes
        }
        $opportunityRows += [pscustomobject]$new
        $oppById[$oppId] = $new
        $newOppCount++
    }

    $companyKey = Normalize-Company $row.company
    if (-not $pipelineByCompany.ContainsKey($companyKey)) {
        $newPipeline = [ordered]@{
            company_name = $row.company
            website = ""
            location = $location
            target_contact = "Owner or GM"
            role = "Owner/GM"
            contact_email = ""
            contact_phone = ""
            services_or_contract_focus = "Public sector janitorial/custodial contracts"
            personalization_hook_1 = ("Current public contract appears to end on {0}" -f (To-DateString $row.end_date))
            personalization_hook_2 = ("Incumbent position on {0}" -f $row.agency)
            likely_bottleneck = "Recompete prep workload and bid deadline compression"
            primary_angle = "Proposal support for recompete readiness, compliance packaging, and bid speed"
            priority_score = "$fitScore"
            last_touch_date = ""
            next_touch_date = To-DateString $today
            stage = "research"
            status = "active"
            notes = ("Renewal radar seed | proposal-support track until contact is enriched | Award {0} | Est value {1:N0}" -f $row.award_id, $row.amount)
        }
        $pipelineRows += [pscustomobject]$newPipeline
        $pipelineByCompany[$companyKey] = $newPipeline
        $newPipelineCount++
    } else {
        $existingPipe = $pipelineByCompany[$companyKey]
        $noEmail = [string]::IsNullOrWhiteSpace([string]$existingPipe.contact_email)
        $noPhone = [string]::IsNullOrWhiteSpace([string]$existingPipe.contact_phone)
        if ($noEmail -and $noPhone) {
            $existingPipe.stage = "research"
            if ([string]::IsNullOrWhiteSpace([string]$existingPipe.primary_angle)) {
                $existingPipe.primary_angle = "Proposal support for recompete readiness, compliance packaging, and bid speed"
            }
            if ([string]::IsNullOrWhiteSpace([string]$existingPipe.notes)) {
                $existingPipe.notes = "proposal-support track until contact is enriched"
            } elseif ($existingPipe.notes -notmatch "proposal-support track") {
                $existingPipe.notes = ($existingPipe.notes + " | proposal-support track until contact is enriched")
            }
        }
    }

    if (-not $candidateByCompany.ContainsKey($companyKey)) {
        $newCandidate = [ordered]@{
            company_name = $row.company
            website = ""
            location = $location
            source = "USASpending renewal radar"
            estimated_size_band = "Unknown"
            estimated_employee_band = "Unknown"
            fit_signals = ("NAICS {0}; incumbent public contract ending {1}" -f $NaicsCode, (To-DateString $row.end_date))
            decision_maker_guess = "Owner or GM"
            priority_score = "$fitScore"
            status = "new"
            notes = ("Agency: {0}; Award: {1}; Est value: {2:N0}" -f $row.agency, $row.award_id, $row.amount)
        }
        $candidateRows += [pscustomobject]$newCandidate
        $candidateByCompany[$companyKey] = $newCandidate
        $newCandidateCount++
    }
}

# Normalize any renewal-seed rows without contact info into research/proposal-support track.
foreach ($p in $pipelineRows) {
    $notesText = [string]$p.notes
    $isRenewalSeed = $notesText -match "Renewal radar seed"
    if (-not $isRenewalSeed) { continue }
    $noEmail = [string]::IsNullOrWhiteSpace([string]$p.contact_email)
    $noPhone = [string]::IsNullOrWhiteSpace([string]$p.contact_phone)
    if ($noEmail -and $noPhone) {
        $p.stage = "research"
        if ([string]::IsNullOrWhiteSpace([string]$p.primary_angle)) {
            $p.primary_angle = "Proposal support for recompete readiness, compliance packaging, and bid speed"
        }
        if ($p.notes -notmatch "proposal-support track") {
            $p.notes = ($notesText + " | proposal-support track until contact is enriched")
        }
    }
}

$opportunityRows | Sort-Object due_date, @{Expression="fit_score";Descending=$true} | Export-Csv -Path $OpportunityFile -NoTypeInformation
$pipelineRows | Sort-Object @{Expression={[int]($_.priority_score)};Descending=$true}, company_name | Export-Csv -Path $PipelineFile -NoTypeInformation
$candidateRows | Sort-Object @{Expression={[int]($_.priority_score)};Descending=$true}, company_name | Export-Csv -Path $CandidatesFile -NoTypeInformation

$top = $dedup |
    Sort-Object @{Expression = { [int]($_.end_date - $today).TotalDays }; Descending = $false }, @{Expression="amount";Descending=$true} |
    Select-Object -First 12

$briefDate = $today.ToString("yyyy-MM-dd")
$briefPath = Join-Path $BriefsDir ("public-renewal-radar-{0}.md" -f $briefDate)
$lines = @()
$lines += "# Public Renewal Radar - $briefDate"
$lines += ""
$lines += "NAICS: $NaicsCode"
$lines += "States: $($States -join ", ")"
$lines += ("Local filter: {0}" -f $(if ($LocalOnly) { "ON (South Jersey + nearby PA/DE)" } else { "OFF (state-wide)" }))
$lines += "Window: $($windowStart.ToString("yyyy-MM-dd")) to $($windowEnd.ToString("yyyy-MM-dd"))"
$lines += ""
$lines += "## Summary"
$lines += "- Opportunities added: $newOppCount"
$lines += "- Opportunities refreshed: $updatedOppCount"
$lines += "- New pipeline accounts: $newPipelineCount"
$lines += "- New prospect candidates: $newCandidateCount"
$lines += ""
$lines += "## Top Renewal Targets"
foreach ($t in $top) {
    $daysOut = [int]($t.end_date - $today).TotalDays
    $lines += ("- {0} | {1} | ends {2} ({3} days) | est `${4:N0} | {5}, {6}" -f $t.company, $t.agency, (To-DateString $t.end_date), $daysOut, $t.amount, $t.city, $t.state)
}
$lines += ""
$lines += "## Recommended Next Action"
$lines += "1. Prioritize outreach to targets ending in <= 90 days."
$lines += "2. Confirm decision-maker and current recompete timeline."
$lines += "3. Offer a 2-week bid readiness sprint focused on admin compression and proposal speed."

$lines -join [Environment]::NewLine | Set-Content -Path $briefPath -Encoding UTF8

Write-Output ("Renewal radar complete. Added {0}, refreshed {1}, pipeline +{2}, candidates +{3}." -f $newOppCount, $updatedOppCount, $newPipelineCount, $newCandidateCount)
Write-Output ("Brief: {0}" -f $briefPath)
