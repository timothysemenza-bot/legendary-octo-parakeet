param(
    [string]$QueueFile = "marketing-agents/data/email_outbox_queue.csv",
    [string]$OutputFile = "marketing-agents/data/email_review_decisions.csv",
    [string]$StatusFilter = "queued"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $QueueFile)) { throw "Missing file: $QueueFile" }

$queue = @(Import-Csv -Path $QueueFile)
$rows = $queue | Where-Object { $_.status -eq $StatusFilter } |
    ForEach-Object {
        [pscustomobject]@{
            email_id = $_.email_id
            company_name = $_.company_name
            to_email = $_.to_email
            current_subject = $_.subject
            current_body = $_.body_text
            decision = "hold" # approve | hold | reject
            revised_subject = ""
            revised_body = ""
            send_mode = "send" # send | draft
            notes = ""
        }
    }

$rows | Export-Csv -Path $OutputFile -NoTypeInformation
Write-Output ("Generated review decisions file: {0} ({1} rows)" -f $OutputFile, $rows.Count)
