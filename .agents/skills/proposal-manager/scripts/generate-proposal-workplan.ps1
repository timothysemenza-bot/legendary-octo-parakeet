[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OpportunityName,

    [Parameter(Mandatory = $true)]
    [string]$Customer,

    [Parameter(Mandatory = $true)]
    [datetime]$DueDate,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [string]$ResponseType = "RFP",
    [string]$SubmissionMethod = "Portal",
    [string]$ContractType = "",
    [string]$Writers = "",
    [string]$ReviewLead = "",
    [string]$PricingLead = "",
    [string]$ProductionLead = "",
    [string]$TimeZone = "America/New_York",
    [switch]$AllowPastDueDate
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-DisplayValue {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return "TBD"
    }

    return $Value.Trim()
}

function Get-MilestoneOffsets {
    param(
        [datetime]$TargetDate,
        [datetime]$Now
    )

    $daysRemaining = [math]::Floor(($TargetDate - $Now).TotalDays)

    if ($daysRemaining -ge 21) {
        return @{
            Kickoff = 18
            OutlineFreeze = 14
            PinkReview = 10
            RedReview = 5
            GoldReview = 2
            ProductionFreeze = 1
        }
    }

    if ($daysRemaining -ge 14) {
        return @{
            Kickoff = 12
            OutlineFreeze = 9
            PinkReview = 6
            RedReview = 4
            GoldReview = 2
            ProductionFreeze = 1
        }
    }

    if ($daysRemaining -ge 10) {
        return @{
            Kickoff = 8
            OutlineFreeze = 6
            PinkReview = 4
            RedReview = 3
            GoldReview = 2
            ProductionFreeze = 1
        }
    }

    if ($daysRemaining -ge 7) {
        return @{
            Kickoff = 6
            OutlineFreeze = 5
            PinkReview = 4
            RedReview = 3
            GoldReview = 2
            ProductionFreeze = 1
        }
    }

    return @{
        Kickoff = 4
        OutlineFreeze = 3
        PinkReview = 2
        RedReview = 1
        GoldReview = 1
        ProductionFreeze = 0
    }
}

function Get-CheckpointDate {
    param(
        [datetime]$TargetDate,
        [int]$OffsetDays,
        [datetime]$Now,
        [bool]$ClampToNow
    )

    $checkpoint = $TargetDate.AddDays(-1 * $OffsetDays)
    if ($ClampToNow -and $checkpoint -lt $Now) {
        return $Now
    }

    return $checkpoint
}

function Format-DateValue {
    param([datetime]$Value)

    return $Value.ToString("yyyy-MM-dd HH:mm")
}

$now = Get-Date
$isRetrospective = $false

if ($DueDate -le $now -and -not $AllowPastDueDate) {
    throw "DueDate must be in the future."
}

if ($DueDate -le $now) {
    $isRetrospective = $true
}

$offsets = Get-MilestoneOffsets -TargetDate $DueDate -Now $now
$writerItems = @()
if (-not [string]::IsNullOrWhiteSpace($Writers)) {
    $writerItems = $Writers -split "[,;]" | ForEach-Object { $_.Trim() } | Where-Object { $_ }
}

$writerDisplay = if ($writerItems.Count -gt 0) { $writerItems -join ", " } else { "TBD" }
$reviewLeadDisplay = Get-DisplayValue -Value $ReviewLead
$pricingLeadDisplay = Get-DisplayValue -Value $PricingLead
$productionLeadDisplay = Get-DisplayValue -Value $ProductionLead
$contractTypeDisplay = Get-DisplayValue -Value $ContractType

$milestones = @(
    @{
        Milestone = "Kickoff"
        Date = Get-CheckpointDate -TargetDate $DueDate -OffsetDays $offsets.Kickoff -Now $now -ClampToNow (-not $isRetrospective)
        Purpose = "Align scope, owners, dependencies, and rules of engagement."
    },
    @{
        Milestone = "Outline freeze"
        Date = Get-CheckpointDate -TargetDate $DueDate -OffsetDays $offsets.OutlineFreeze -Now $now -ClampToNow (-not $isRetrospective)
        Purpose = "Lock the section structure, page budget, and author assignments."
    },
    @{
        Milestone = "Pink Review"
        Date = Get-CheckpointDate -TargetDate $DueDate -OffsetDays $offsets.PinkReview -Now $now -ClampToNow (-not $isRetrospective)
        Purpose = "Test compliance coverage, structure, and message alignment."
    },
    @{
        Milestone = "Red Review"
        Date = Get-CheckpointDate -TargetDate $DueDate -OffsetDays $offsets.RedReview -Now $now -ClampToNow (-not $isRetrospective)
        Purpose = "Evaluate the draft for buyer readiness and discriminators."
    },
    @{
        Milestone = "Gold Review"
        Date = Get-CheckpointDate -TargetDate $DueDate -OffsetDays $offsets.GoldReview -Now $now -ClampToNow (-not $isRetrospective)
        Purpose = "Confirm production readiness, approvals, and file completeness."
    },
    @{
        Milestone = "Production freeze"
        Date = Get-CheckpointDate -TargetDate $DueDate -OffsetDays $offsets.ProductionFreeze -Now $now -ClampToNow (-not $isRetrospective)
        Purpose = "Lock final files, attachments, and upload sequence."
    }
)

$milestoneRows = ($milestones | ForEach-Object {
    "| {0} | {1} | {2} |" -f $_.Milestone, (Format-DateValue -Value $_.Date), $_.Purpose
}) -join "`r`n"

$deliverableRows = @(
    "| Intake brief | $reviewLeadDisplay | Not started |",
    "| Compliance matrix | $reviewLeadDisplay | Not started |",
    "| Annotated outline | $reviewLeadDisplay | Not started |",
    "| Technical narrative | $writerDisplay | Not started |",
    "| Pricing package | $pricingLeadDisplay | Not started |",
    "| Final production package | $productionLeadDisplay | Not started |"
) -join "`r`n"

$statusSection = if ($isRetrospective) {
@"
## Schedule Status

This workplan is retrospective because the due date has already passed. Use it for testing,
lessons learned, or reconstructing how the pursuit should have been managed.

"@
} else {
    ""
}

$output = @"
# Proposal Workplan - $OpportunityName

## Opportunity Snapshot

| Field | Value |
| --- | --- |
| Opportunity | $OpportunityName |
| Customer | $Customer |
| Response type | $ResponseType |
| Due date | $(Format-DateValue -Value $DueDate) |
| Time zone | $TimeZone |
| Submission method | $SubmissionMethod |
| Contract type | $contractTypeDisplay |
| Writers | $writerDisplay |
| Review lead | $reviewLeadDisplay |
| Pricing lead | $pricingLeadDisplay |
| Production lead | $productionLeadDisplay |

$statusSection
## Backward Schedule

| Milestone | Target date | Purpose |
| --- | --- | --- |
$milestoneRows

## Core Deliverables

| Deliverable | Owner | Status |
| --- | --- | --- |
$deliverableRows

## Data Calls

- Confirm pricing assumptions, rate structure, and approvals.
- Request past performance references, resumes, org chart, and certifications.
- Confirm required forms, signatures, and representations.
- Confirm graphics support, production support, and final upload path.

## Risk Watch List

- Missing source documents, amendments, or addenda
- Misaligned pricing and technical narrative
- Unowned approvals or late executive reviews
- Portal access, file-size limits, or upload timing issues

## Next Actions

1. Confirm the intake facts and open questions.
2. Assign owners for every deliverable and milestone.
3. Launch the first data calls on the same day as kickoff.
4. Freeze the outline before Pink Review.
5. Treat Gold Review as a submission rehearsal, not another draft review.
"@

$parent = Split-Path -Parent $OutputPath
if (-not [string]::IsNullOrWhiteSpace($parent) -and -not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}

Set-Content -LiteralPath $OutputPath -Value $output -Encoding utf8
Write-Host "Created proposal workplan at $OutputPath"
