param(
    [string]$Date = "",
    [string]$CallPlanFile = "marketing-agents/data/daily_call_plan.csv",
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$OutputFile = "marketing-agents/briefs/call-runbook.md"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $CallPlanFile)) { throw "Missing file: $CallPlanFile" }
if (-not (Test-Path $PipelineFile)) { throw "Missing file: $PipelineFile" }

$today = if ([string]::IsNullOrWhiteSpace($Date)) { (Get-Date).ToString("yyyy-MM-dd") } else { ([datetime]$Date).ToString("yyyy-MM-dd") }
$calls = @(Import-Csv -Path $CallPlanFile) | Where-Object { $_.call_date -eq $today } | Sort-Object {[int]$_.plan_order}
$pipeline = @(Import-Csv -Path $PipelineFile)

function Get-CleanPhone {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
    $digits = ($Value -replace '[^0-9]', '')
    if ($digits.Length -lt 10) { return "" }
    if ($digits.Length -eq 10) { return "+1$digits" }
    if ($digits.StartsWith("1") -and $digits.Length -eq 11) { return "+$digits" }
    return "+$digits"
}

$lines = @()
$lines += "# Call Runbook - $today"
$lines += ""
$lines += "Use this during call blocks. Keep calls to 3-5 minutes unless invited to go deeper."
$lines += ""

if ($calls.Count -eq 0) {
    $lines += "_No calls scheduled for this date._"
} else {
    foreach ($c in $calls) {
        $p = $pipeline | Where-Object { $_.company_name -eq $c.company_name } | Select-Object -First 1
        $contact = if ([string]::IsNullOrWhiteSpace($c.target_contact)) { "there" } else { $c.target_contact }
        $phone = if ([string]::IsNullOrWhiteSpace($c.contact_phone)) { "" } else { $c.contact_phone }
        $cleanPhone = Get-CleanPhone -Value $phone
        $dial = if ([string]::IsNullOrWhiteSpace($cleanPhone)) { "No valid phone listed" } else { "tel:" + $cleanPhone }
        $hook1 = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.personalization_hook_1)) { "your current operation" } else { $p.personalization_hook_1 }
        $hook2 = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.personalization_hook_2)) { "your contract mix" } else { $p.personalization_hook_2 }
        $bottleneck = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.likely_bottleneck)) { "admin burden between bid and delivery" } else { $p.likely_bottleneck }
        $angle = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.primary_angle)) { "reduce admin drag and protect margin" } else { $p.primary_angle }
        $notes = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.notes)) { "No extra notes" } else { $p.notes }
        $localContext = if ($null -eq $p -or -not $p.PSObject.Properties.Name.Contains("local_ties") -or [string]::IsNullOrWhiteSpace($p.local_ties)) { "South Jersey local business context to verify on call." } else { $p.local_ties }
        $ownerHistory = if ($null -eq $p -or -not $p.PSObject.Properties.Name.Contains("owner_background") -or [string]::IsNullOrWhiteSpace($p.owner_background)) { "Confirm owner history from website/LinkedIn before call." } else { $p.owner_background }
        $trigger = if ($null -eq $p -or -not $p.PSObject.Properties.Name.Contains("recent_trigger") -or [string]::IsNullOrWhiteSpace($p.recent_trigger)) { "No recent trigger captured." } else { $p.recent_trigger }

        $lines += "## $($c.start_time)-$($c.end_time) | $($c.company_name)"
        $lines += "- Contact: $($c.target_contact) ($($c.role))"
        $lines += "- Phone: $phone"
        $lines += "- Click to dial: $dial"
        $lines += "- Context hooks: $hook1 | $hook2"
        $lines += "- Owner/local history: $ownerHistory | $localContext"
        $lines += "- Trigger to reference: $trigger"
        $lines += "- Likely bottleneck: $bottleneck"
        $lines += "- Priority angle: $angle"
        $lines += "- Research notes: $notes"
        $lines += ""
        $lines += "**Open (20-30 sec):**"
        $lines += "Hi $contact, this is Timmy Semenza with Boss Key in South Jersey. I help local cleaning owners reduce the office workload that slows bids and eats margin after award."
        $lines += ""
        $lines += "**Tailored bridge:**"
        $lines += "Based on $hook1 and $hook2, I thought there may be a practical fit."
        $lines += ""
        $lines += "**2 discovery questions:**"
        $lines += "1. Where does your team lose the most time right now between proposals and delivery?"
        $lines += "2. How often do labor assumptions miss after a job starts?"
        $lines += ""
        $lines += "**Close:**"
        $lines += "If helpful, I can run a short diagnostic and show the top 2-3 fixes first. Open to 20 minutes next week?"
        $lines += ""
    }
}

$outDir = Split-Path -Parent $OutputFile
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
$lines -join [Environment]::NewLine | Set-Content -Path $OutputFile -Encoding UTF8

Write-Output "Generated call runbook: $OutputFile"
