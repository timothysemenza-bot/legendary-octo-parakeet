param(
    [string]$QueueFile = "marketing-agents/data/email_outbox_queue.csv",
    [string]$DecisionsFile = "marketing-agents/data/email_review_decisions.csv"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $QueueFile)) { throw "Missing file: $QueueFile" }
if (-not (Test-Path $DecisionsFile)) { throw "Missing file: $DecisionsFile" }

$queue = @(Import-Csv -Path $QueueFile)
$decisions = @(Import-Csv -Path $DecisionsFile)

$approved = 0
$held = 0
$rejected = 0

foreach ($d in $decisions) {
    $row = $queue | Where-Object { $_.email_id -eq $d.email_id } | Select-Object -First 1
    if ($null -eq $row) { continue }

    $decision = $d.decision.ToLowerInvariant().Trim()
    switch ($decision) {
        "approve" {
            if (-not [string]::IsNullOrWhiteSpace($d.revised_subject)) { $row.subject = $d.revised_subject }
            if (-not [string]::IsNullOrWhiteSpace($d.revised_body)) { $row.body_text = $d.revised_body }
            $row.owner_approved = "yes"
            $row.send_mode = if ($d.send_mode) { $d.send_mode } else { "send" }
            $row.status = "queued"
            $row.notes = ("Approved: " + $d.notes)
            $approved++
        }
        "reject" {
            $row.owner_approved = "no"
            $row.status = "rejected"
            $row.notes = ("Rejected: " + $d.notes)
            $rejected++
        }
        default {
            $row.owner_approved = "no"
            $row.status = "queued"
            $row.notes = ("Hold: " + $d.notes)
            $held++
        }
    }
}

$queue | Export-Csv -Path $QueueFile -NoTypeInformation
Write-Output ("Applied decisions -> approved={0}, held={1}, rejected={2}" -f $approved, $held, $rejected)
