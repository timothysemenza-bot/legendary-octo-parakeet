param(
    [string]$QueueFile = "marketing-agents/data/email_outbox_queue.csv",
    [string]$OutputFile = "marketing-agents/data/gmail_send_sheet.csv",
    [string]$StatusFilter = "queued"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $QueueFile)) { throw "Missing file: $QueueFile" }

$queue = @(Import-Csv -Path $QueueFile)
$rows = $queue | Where-Object {
    $_.owner_approved.ToLowerInvariant().Trim() -eq "yes" -and
    $_.status -eq $StatusFilter
}

$out = foreach ($r in $rows) {
    [pscustomobject]@{
        email_id = $r.email_id
        company_name = $r.company_name
        contact_name = $r.contact_name
        to_email = $r.to_email
        subject = $r.subject
        body_text = $r.body_text
        notes = $r.notes
    }
}

$out | Export-Csv -Path $OutputFile -NoTypeInformation
Write-Output ("Exported {0} Gmail-ready rows to {1}" -f $out.Count, $OutputFile)
