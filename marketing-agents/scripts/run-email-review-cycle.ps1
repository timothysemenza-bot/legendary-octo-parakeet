param(
    [string]$ScheduledDate = "",
    [string]$ScheduledTime = "09:30"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$scriptsDir = Join-Path $repoRoot "marketing-agents/scripts"
$dataDir = Join-Path $repoRoot "marketing-agents/data"
$briefDir = Join-Path $repoRoot "marketing-agents/briefs"

Write-Output "Step 1/3: Build new email queue rows (owner approval required)..."
powershell -ExecutionPolicy Bypass -File (Join-Path $scriptsDir "build-email-queue-from-pipeline.ps1") `
    -ScheduledDate $ScheduledDate `
    -ScheduledTime $ScheduledTime `
    -OwnerApproved no `
    -SendMode send

Write-Output "Step 2/3: Build review decisions table..."
powershell -ExecutionPolicy Bypass -File (Join-Path $scriptsDir "build-email-review-decisions.ps1") `
    -OutputFile (Join-Path $dataDir "email_review_decisions.csv")

Write-Output "Step 3/3: Build human-readable review packet..."
powershell -ExecutionPolicy Bypass -File (Join-Path $scriptsDir "generate-email-review-packet.ps1") `
    -OutputFile (Join-Path $briefDir "email-review-packet.md")

Write-Output "Review files:"
Write-Output " - marketing-agents/data/email_review_decisions.csv"
Write-Output " - marketing-agents/briefs/email-review-packet.md"
Write-Output "After edits, apply with:"
Write-Output " powershell -ExecutionPolicy Bypass -File .\\marketing-agents\\scripts\\apply-email-review-decisions.ps1"
Write-Output "Then send approved queue with SMTP/Graph sender."
