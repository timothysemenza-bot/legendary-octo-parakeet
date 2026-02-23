param(
    [string]$Date = "",
    [string]$CallPlanFile = "marketing-agents/data/daily_call_plan.csv",
    [string]$PipelineFile = "marketing-agents/data/prospect_pipeline.csv",
    [string]$OutputFile = "marketing-agents/briefs/prospect-research-pack.md"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $CallPlanFile)) { throw "Missing file: $CallPlanFile" }
if (-not (Test-Path $PipelineFile)) { throw "Missing file: $PipelineFile" }

$today = if ([string]::IsNullOrWhiteSpace($Date)) { (Get-Date).ToString("yyyy-MM-dd") } else { ([datetime]$Date).ToString("yyyy-MM-dd") }
$calls = @(Import-Csv -Path $CallPlanFile) | Where-Object { $_.call_date -eq $today } | Sort-Object { [int]$_.plan_order }
$pipeline = @(Import-Csv -Path $PipelineFile)

function New-SearchLink {
    param([string]$Query)
    $q = [uri]::EscapeDataString($Query)
    return "https://www.google.com/search?q=$q"
}

$lines = @()
$lines += "# Prospect Research Pack - $today"
$lines += ""
$lines += "Use this as a 2-minute prep sheet before each call."
$lines += ""

if ($calls.Count -eq 0) {
    $lines += "_No calls scheduled for this date._"
} else {
    foreach ($c in $calls) {
        $p = $pipeline | Where-Object { $_.company_name -eq $c.company_name } | Select-Object -First 1
        $location = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.location)) { "South Jersey" } else { $p.location }
        $website = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.website)) { "" } else { $p.website }
        $contact = if ([string]::IsNullOrWhiteSpace($c.target_contact)) { "Owner/GM" } else { $c.target_contact }
        $hook1 = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.personalization_hook_1)) { "Current operating setup" } else { $p.personalization_hook_1 }
        $hook2 = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.personalization_hook_2)) { "Contract mix and obligations" } else { $p.personalization_hook_2 }
        $bottleneck = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.likely_bottleneck)) { "Admin burden" } else { $p.likely_bottleneck }
        $angle = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.primary_angle)) { "Reduce admin drag and protect margin" } else { $p.primary_angle }
        $notes = if ($null -eq $p -or [string]::IsNullOrWhiteSpace($p.notes)) { "No additional notes captured." } else { $p.notes }

        $lines += "## $($c.company_name)"
        $lines += "- Contact: $contact ($($c.role))"
        $lines += "- Location: $location"
        $lines += "- Website: $website"
        $lines += "- Why this call now: $($c.reason)"
        $lines += "- Talking hooks: $hook1 | $hook2"
        $lines += "- Likely issue to confirm: $bottleneck"
        $lines += "- Offer angle: $angle"
        $lines += "- Notes: $notes"
        $lines += ""
        $lines += "**Owner/local history quick links:**"
        $lines += "- Owner/company history: $(New-SearchLink -Query "$($c.company_name) $location owner history")"
        $lines += "- Local news mentions: $(New-SearchLink -Query "$($c.company_name) $location news")"
        $lines += "- LinkedIn lookup: $(New-SearchLink -Query "$($c.company_name) $contact LinkedIn")"
        $lines += "- BBB/profile lookup: $(New-SearchLink -Query "$($c.company_name) BBB")"
        $lines += ""
        $lines += "**20-second opener:**"
        $lines += "Timmy Semenza here with Boss Key in South Jersey. I help local cleaning owners reduce office work that slows bids and causes margin leakage after award."
        $lines += ""
    }
}

$outDir = Split-Path -Parent $OutputFile
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
$lines -join [Environment]::NewLine | Set-Content -Path $OutputFile -Encoding UTF8

Write-Output "Generated research pack: $OutputFile"
