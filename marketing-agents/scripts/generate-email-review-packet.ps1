param(
    [string]$QueueFile = "marketing-agents/data/email_outbox_queue.csv",
    [string]$OutputFile = "marketing-agents/briefs/email-review-packet.md",
    [string]$StatusFilter = "queued"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $QueueFile)) { throw "Missing file: $QueueFile" }

$queue = @(Import-Csv -Path $QueueFile)
$rows = $queue | Where-Object { $_.status -eq $StatusFilter }

$lines = @()
$lines += "# Email Review Packet"
$lines += ""
$lines += "Review each draft. To approve or edit, update decisions in:"
$lines += "- marketing-agents/data/email_review_decisions.csv"
$lines += ""
$lines += "Draft count: $($rows.Count)"
$lines += ""

foreach ($r in $rows) {
    $lines += "## $($r.email_id) | $($r.company_name)"
    $lines += "- To: $($r.to_email)"
    $lines += "- Current Approval: $($r.owner_approved)"
    $lines += "- Subject: $($r.subject)"
    $lines += "- Status: $($r.status)"
    $lines += ""
    $lines += "Body (editable):"
    $lines += "-----"
    $lines += $r.body_text
    $lines += "-----"
    $lines += ""
}

if ($rows.Count -eq 0) {
    $lines += "_No queued drafts found._"
}

$dir = Split-Path -Parent $OutputFile
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
$lines -join [Environment]::NewLine | Set-Content -Path $OutputFile -Encoding UTF8

Write-Output "Generated review packet: $OutputFile"
