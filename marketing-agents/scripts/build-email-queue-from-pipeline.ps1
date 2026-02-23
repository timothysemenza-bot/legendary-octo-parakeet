param(
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$QueueFile = "marketing-agents/data/email_outbox_queue.csv",
    [string]$ScheduledDate = "",
    [string]$ScheduledTime = "09:30",
    [string]$OwnerApproved = "no",
    [string]$SendMode = "draft"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $PipelineFile)) { throw "Missing file: $PipelineFile" }
if (-not (Test-Path $QueueFile)) { throw "Missing file: $QueueFile" }

$dateValue = if ([string]::IsNullOrWhiteSpace($ScheduledDate)) { (Get-Date).ToString("yyyy-MM-dd") } else { $ScheduledDate }

$pipeline = @(Import-Csv -Path $PipelineFile)
$queue = @(Import-Csv -Path $QueueFile)

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

$newRows = @()
foreach ($p in $pipeline) {
    if ([string]::IsNullOrWhiteSpace($p.contact_email)) { continue }
    $status = ($p.status | ForEach-Object { $_.ToLowerInvariant().Trim() })
    if ($status -eq "do-not-contact" -or $status -eq "closed-lost") { continue }

    $existing = $queue | Where-Object { $_.company_name -eq $p.company_name -and $_.to_email -eq $p.contact_email -and $_.status -in @("queued","drafted","sent") } | Select-Object -First 1
    if ($null -ne $existing) { continue }

    $contact = if ([string]::IsNullOrWhiteSpace($p.target_contact) -or $p.target_contact -eq "Main Office") { "team" } else { $p.target_contact }
    $hook1 = if ([string]::IsNullOrWhiteSpace($p.personalization_hook_1)) { "your operating environment" } else { $p.personalization_hook_1.ToLowerInvariant() }
    $hook2 = if ([string]::IsNullOrWhiteSpace($p.personalization_hook_2)) { "your current service mix" } else { $p.personalization_hook_2.ToLowerInvariant() }
    $angle = if ([string]::IsNullOrWhiteSpace($p.primary_angle)) { "reduce administrative workload and protect margin" } else { $p.primary_angle }
    $isLocal = Is-LocalRegion -Location ([string]$p.location)
    $introLine = if ($isLocal) {
        "I work with janitorial and facility service operators to reduce the administrative burden between proposals, staffing, and reporting so margin does not leak after contract start."
    } else {
        "I work with janitorial and facility service operators across U.S. markets to reduce the administrative burden between proposals, staffing, and reporting so margin does not leak after contract start."
    }
    $siteVisitLine = if ($isLocal) {
        "If it helps, I can meet you on your next site visit, walk the operation with you, and give practical first recommendations on the spot."
    } else {
        "If helpful, I can review your current workflow and proposal process with you in a short working session and provide practical first recommendations."
    }
    $isPublicSector = (([string]$p.services_or_contract_focus).ToLowerInvariant() -match "public|government|municipal|school|federal|state|local") -or (([string]$p.primary_angle).ToLowerInvariant() -match "proposal|recompete|compliance|bid")
    $govCredLine = if ($isPublicSector) { "My background includes developing government proposals across federal, state, and local work, so I can help you tighten both compliance and speed." } else { "" }
    $subject = "Quick idea to reduce admin drag at $($p.company_name)"
    $body = @"
Hi $contact,

$introLine

Given $hook1 and $hook2, a practical next step is a short workflow diagnostic to identify where manual coordination is consuming time and compressing margin.

My focus is straightforward: $angle.

$govCredLine

$siteVisitLine

If useful, I can share the top 2-3 issues we typically find first and what to change quickly in your workflow.

Open to a 20-minute conversation next week?
"@.Trim()

    $emailId = "eml-" + (Get-Date -Format "yyyyMMddHHmmss") + "-" + ($p.company_name -replace '[^A-Za-z0-9]', '').Substring(0, [Math]::Min(6, ($p.company_name -replace '[^A-Za-z0-9]', '').Length))
    $newRows += [pscustomobject]@{
        email_id = $emailId
        created_date = (Get-Date).ToString("yyyy-MM-dd")
        company_name = $p.company_name
        contact_name = $p.target_contact
        to_email = $p.contact_email
        cc_email = ""
        subject = $subject
        body_text = $body
        owner_approved = $OwnerApproved
        send_mode = $SendMode
        status = "queued"
        scheduled_date = $dateValue
        scheduled_time = $ScheduledTime
        sent_at = ""
        attempt_count = "0"
        last_error = ""
        notes = "Generated from prospect_pipeline.csv"
    }
}

if ($newRows.Count -eq 0) {
    Write-Output "No new email rows created."
    exit 0
}

(@($queue) + @($newRows)) | Export-Csv -Path $QueueFile -NoTypeInformation
Write-Output ("Added {0} rows to email queue." -f $newRows.Count)
