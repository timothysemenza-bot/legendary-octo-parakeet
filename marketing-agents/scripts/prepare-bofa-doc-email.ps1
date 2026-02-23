param(
  [string]$ConfirmationNumber = "158275973"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$workspace = Split-Path -Parent $root
$submissionDir = Join-Path $workspace "boss-key-llc-admin\bank-of-america-submission"
$emailDraft = Join-Path $submissionDir "email-to-bofa.txt"

if (-not (Test-Path $submissionDir)) {
  throw "Submission folder not found: $submissionDir"
}

$required = @(
  "BOSS_KEY_LLC_NJ_Organizing_Document.pdf",
  "BOSS_KEY_LLC_IRS_EIN_CP575.pdf"
)

$missing = @()
foreach ($name in $required) {
  if (-not (Test-Path (Join-Path $submissionDir $name))) {
    $missing += $name
  }
}

if ($missing.Count -gt 0) {
  throw ("Missing required file(s): " + ($missing -join ", "))
}

if (Test-Path $emailDraft) {
  $body = Get-Content $emailDraft -Raw
} else {
  $body = @"
To: SmallBus.Documents@bankofamerica.com
Subject: Confirmation #$ConfirmationNumber - BOSS KEY LLC - Required Documents

Hello Bank of America Small Business Documents Team,

Please find attached the requested documentation to complete my business checking application.

Business legal name: BOSS KEY LLC
Confirmation number: $ConfirmationNumber
Owner/authorized signer: Timothy Charles Semenza
Phone: (203) 521-0311

Attached documents:
1) BOSS_KEY_LLC_NJ_Organizing_Document.pdf
2) BOSS_KEY_LLC_IRS_EIN_CP575.pdf

Please confirm receipt and advise if any additional documents are needed.

Thank you,
Timmy Semenza
BOSS KEY LLC
"@
}

Set-Clipboard -Value $body
Start-Process explorer.exe $submissionDir

Write-Host "Ready: email text copied to clipboard."
Write-Host "Folder opened: $submissionDir"
Write-Host "To: SmallBus.Documents@bankofamerica.com"
Write-Host "Subject: Confirmation #$ConfirmationNumber - BOSS KEY LLC - Required Documents"
