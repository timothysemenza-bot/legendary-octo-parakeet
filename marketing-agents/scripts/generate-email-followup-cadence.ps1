param(
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$OutputFile = "marketing-agents/data/outreach_touch_plan.csv",
    [string]$StartDate = "",
    [string]$BlockedOutputFile = "marketing-agents/data/outreach_touch_blocked.csv"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $PipelineFile)) {
    throw "Pipeline file not found: $PipelineFile"
}

$baseDate = if ([string]::IsNullOrWhiteSpace($StartDate)) { (Get-Date).Date } else { ([datetime]$StartDate).Date }
$pipeline = @(Import-Csv -Path $PipelineFile)

function Get-CleanPhone {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
    $digits = ($Value -replace '[^0-9]', '')
    if ($digits.Length -eq 10) { return "+1$digits" }
    if ($digits.Length -eq 11 -and $digits.StartsWith("1")) { return "+$digits" }
    if ($digits.Length -gt 11) { return "+$digits" }
    return ""
}

# Balanced no-response cadence: initial + 4 follow-ups + monthly nurture handoff.
$touchMap = @(
    @{ step = 1; day_offset = 0;  channel = "email"; template_id = "E1"; objective = "Initial introduction and relevance hook" },
    @{ step = 2; day_offset = 3;  channel = "call+voicemail"; template_id = "C1"; objective = "Confirm receipt and qualify operational pain" },
    @{ step = 3; day_offset = 7;  channel = "email"; template_id = "E2"; objective = "Share concise value proof and ask for short call" },
    @{ step = 4; day_offset = 12; channel = "email"; template_id = "E3"; objective = "Low-friction follow-up with direct CTA" },
    @{ step = 5; day_offset = 21; channel = "linkedin+text"; template_id = "L1"; objective = "Light reconnect and relationship touch" },
    @{ step = 6; day_offset = 35; channel = "email"; template_id = "E4"; objective = "Monthly nurture check-in" }
)

$rows = @()
$blocked = @()
foreach ($p in $pipeline) {
    if (($p.status | ForEach-Object { $_.ToLowerInvariant().Trim() }) -ne "active") { continue }
    $hasEmail = -not [string]::IsNullOrWhiteSpace($p.contact_email)
    $hasPhone = -not [string]::IsNullOrWhiteSpace((Get-CleanPhone -Value $p.contact_phone))

    $anchorDate = $baseDate
    if (-not [string]::IsNullOrWhiteSpace($p.next_touch_date)) {
        try { $anchorDate = ([datetime]$p.next_touch_date).Date } catch { $anchorDate = $baseDate }
    }

    foreach ($t in $touchMap) {
        $channel = [string]$t.channel
        $needsEmail = $channel -match "email"
        $needsPhone = $channel -match "call|text"
        if (($needsEmail -and -not $hasEmail) -or ($needsPhone -and -not $hasPhone)) {
            $blocked += [pscustomobject]@{
                company_name = $p.company_name
                contact_name = $p.target_contact
                role = $p.role
                contact_email = $p.contact_email
                contact_phone = $p.contact_phone
                touch_step = $t.step
                touch_date = $anchorDate.AddDays([int]$t.day_offset).ToString("yyyy-MM-dd")
                channel = $channel
                template_id = $t.template_id
                objective = $t.objective
                owner = "Timmy Semenza"
                status = "blocked-missing-contact"
                notes = $(if (-not $hasEmail -and $needsEmail -and -not $hasPhone -and $needsPhone) { "Missing email and phone" } elseif ($needsEmail -and -not $hasEmail) { "Missing email" } else { "Missing phone" })
            }
            continue
        }

        $touchDate = $anchorDate.AddDays([int]$t.day_offset)
        $rows += [pscustomobject]@{
            company_name = $p.company_name
            contact_name = $p.target_contact
            role = $p.role
            contact_email = $p.contact_email
            contact_phone = $p.contact_phone
            touch_step = $t.step
            touch_date = $touchDate.ToString("yyyy-MM-dd")
            channel = $t.channel
            template_id = $t.template_id
            objective = $t.objective
            owner = "Timmy Semenza"
            status = "planned"
            notes = ""
        }
    }
}

$rows | Sort-Object touch_date, company_name, touch_step | Export-Csv -Path $OutputFile -NoTypeInformation
$blocked | Sort-Object touch_date, company_name, touch_step | Export-Csv -Path $BlockedOutputFile -NoTypeInformation
Write-Output ("Generated outreach cadence plan: {0} actionable rows -> {1}" -f $rows.Count, $OutputFile)
Write-Output ("Blocked cadence rows (missing contact info): {0} -> {1}" -f $blocked.Count, $BlockedOutputFile)
