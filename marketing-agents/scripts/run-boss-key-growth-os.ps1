param(
    [switch]$RefreshDrafts,
    [switch]$ApplyDecisions
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Output "Step 1/2: Build Boss Key review packet and decision file..."
& (Join-Path $scriptRoot "build-boss-key-growth-review.ps1") -RefreshDrafts:$RefreshDrafts

if ($ApplyDecisions) {
    Write-Output "Step 2/2: Apply owner decisions and refresh approved public outputs..."
    & (Join-Path $scriptRoot "apply-boss-key-growth-review.ps1")
} else {
    Write-Output "Step 2/2: Skipped apply step. Review and update marketing-agents/data/boss_key_review_decisions.csv first."
}

Write-Output "Boss Key Growth OS run complete."
