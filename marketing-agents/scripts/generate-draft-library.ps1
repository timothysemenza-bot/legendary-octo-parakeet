param(
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$CandidatesFile = "marketing-agents/data/prospect_candidates.csv",
    [string]$OutputFile = "marketing-agents/data/gmail_draft_library.csv",
    [int]$Count = 10
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $PipelineFile)) { throw "Missing file: $PipelineFile" }
if (-not (Test-Path $CandidatesFile)) { throw "Missing file: $CandidatesFile" }

$pipeline = @(Import-Csv -Path $PipelineFile)
$candidates = @(Import-Csv -Path $CandidatesFile)

function Is-LocalRegion {
    param([string]$Location)
    if ([string]::IsNullOrWhiteSpace($Location)) { return $true }
    $loc = $Location.ToUpperInvariant()
    $localHints = @(
        "CINNAMINSON","BURLINGTON","MOUNT HOLLY","MOORESTOWN","MEDFORD","MARLTON","EVESHAM","MAPLE SHADE","PALMYRA","RIVERTON","RIVERSIDE","DELRAN","WILLINGBORO","PEMBERTON","LUMBERTON",
        "CAMDEN","CHERRY HILL","PENNSAUKEN","COLLINGSWOOD","VOORHEES","BELLMAWR","RUNNEMEDE","HADDONFIELD","HADDON HEIGHTS",
        "DEPTFORD","SEWELL","WOODBURY","MANTUA","GLASSBORO","SWEDESBORO",
        "MOUNT LAUREL","TRENTON","PRINCETON","HAMILTON","LAWRENCEVILLE","EWING",
        "PHILADELPHIA","BENSALEM","BRISTOL","LEVITTOWN","YARDLEY","LANGHORNE","NEWTOWN","DOYLESTOWN","UPPER DARBY","MEDIA","CHESTER",
        "WILMINGTON","NEWARK, DE","NEW CASTLE","DOVER"
    )
    foreach ($h in $localHints) {
        if ($loc.Contains($h)) { return $true }
    }
    return $false
}

$pool = @()

foreach ($p in $pipeline) {
    $priority = 0
    [void][int]::TryParse($p.priority_score, [ref]$priority)
    $pool += [pscustomobject]@{
        company_name = $p.company_name
        to_email = $p.contact_email
        contact_name = $p.target_contact
        location = $p.location
        hook1 = $p.personalization_hook_1
        hook2 = $p.personalization_hook_2
        angle = $p.primary_angle
        priority = $priority
        source = "pipeline"
    }
}

foreach ($c in $candidates) {
    $exists = $pool | Where-Object { $_.company_name -eq $c.company_name } | Select-Object -First 1
    if ($null -ne $exists) { continue }
    $priority = 0
    [void][int]::TryParse($c.priority_score, [ref]$priority)
    $pool += [pscustomobject]@{
        company_name = $c.company_name
        to_email = ""
        contact_name = "Main Office"
        location = $c.location
        hook1 = $c.fit_signals
        hook2 = "local market conditions"
        angle = "reduce administrative workload while protecting service margin"
        priority = $priority
        source = "candidate"
    }
}

$selected = $pool | Sort-Object -Property @{Expression = "priority"; Descending = $true} | Select-Object -First $Count

$rows = @()
foreach ($s in $selected) {
    $contact = if ([string]::IsNullOrWhiteSpace($s.contact_name) -or $s.contact_name -eq "TBD" -or $s.contact_name -eq "Main Office") { "team" } else { $s.contact_name }
    $hook1 = if ([string]::IsNullOrWhiteSpace($s.hook1)) { "your operating setup" } else { $s.hook1.ToLowerInvariant() }
    $hook2 = if ([string]::IsNullOrWhiteSpace($s.hook2)) { "your current contract mix" } else { $s.hook2.ToLowerInvariant() }
    $angle = if ([string]::IsNullOrWhiteSpace($s.angle)) { "reduce admin burden and improve execution consistency" } else { $s.angle }
    $isLocal = Is-LocalRegion -Location ([string]$s.location)
    $introLine = if ($isLocal) {
        "I work with janitorial and facility service operators to reduce the administrative burden between proposals, staffing, scheduling, and reporting so margins hold as work scales."
    } else {
        "I work with janitorial and facility service operators across U.S. markets to reduce the administrative burden between proposals, staffing, scheduling, and reporting so margins hold as work scales."
    }
    $siteVisitLine = if ($isLocal) {
        "If useful, I can meet you at your next site visit and give immediate recommendations tied to what we see in the field."
    } else {
        "If useful, I can review your current workflow and proposal process with you in a short working session and give immediate recommendations."
    }
    $isPublicSector = ($hook1 -match "public|government|municipal|school|federal|state|local") -or ($hook2 -match "public|government|municipal|school|federal|state|local") -or ($angle.ToLowerInvariant() -match "proposal|recompete|compliance|bid")
    $govCredLine = if ($isPublicSector) { "My background includes developing government proposals across federal, state, and local sectors, which helps me keep proposal work compliant and practical." } else { "" }
    $subject = "Idea to reduce admin drag at $($s.company_name)"

    $body = @"
Hi $contact,

$introLine

Given $hook1 and $hook2, there is usually an opportunity to remove manual coordination work and tighten execution handoffs.

My focus is practical: $angle.

$govCredLine

$siteVisitLine

If useful, I can share a short diagnostic framework showing where these workflow leaks typically appear first.

Open to a 20-minute conversation next week?
"@.Trim()

    $rows += [pscustomobject]@{
        draft_id = "dft-" + (Get-Date -Format "yyyyMMddHHmmss") + "-" + ($s.company_name -replace '[^A-Za-z0-9]', '').Substring(0, [Math]::Min(6, ($s.company_name -replace '[^A-Za-z0-9]', '').Length))
        company_name = $s.company_name
        source = $s.source
        to_email = $s.to_email
        email_available = if ([string]::IsNullOrWhiteSpace($s.to_email)) { "no" } else { "yes" }
        subject = $subject
        body_text = $body
    }
}

$rows | Export-Csv -Path $OutputFile -NoTypeInformation
Write-Output ("Generated {0} tailored drafts -> {1}" -f $rows.Count, $OutputFile)
