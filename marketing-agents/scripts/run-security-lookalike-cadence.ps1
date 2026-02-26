param(
    [string]$RunDate = "",
    [string]$ScheduledTime = "09:30",
    [int]$MaxLinkedInRows = 15,
    [string]$TargetFile = "marketing-agents/briefs/st-moritz-target-account-list-2026-02-25.csv",
    [string]$CrossRefFile = "marketing-agents/briefs/st-moritz-target-account-list-crossref-2026-02-25.csv",
    [string]$PipelineFile = "marketing-agents/data/security_lookalike_campaign_pipeline.csv",
    [string]$EnrichedPipelineFile = "marketing-agents/data/security_lookalike_campaign_pipeline_enriched.csv",
    [string]$CadenceFile = "marketing-agents/data/security_lookalike_outreach_touch_plan.csv",
    [string]$BlockedCadenceFile = "marketing-agents/data/security_lookalike_outreach_touch_blocked.csv",
    [string]$EmailQueueFile = "marketing-agents/data/security_lookalike_email_outbox_queue.csv",
    [string]$LinkedInQueueFile = "marketing-agents/data/security_lookalike_linkedin_outreach_queue.csv",
    [string]$BriefDir = "marketing-agents/briefs"
)

$ErrorActionPreference = "Stop"

$dateValue = if ([string]::IsNullOrWhiteSpace($RunDate)) { (Get-Date).ToString("yyyy-MM-dd") } else { ([datetime]$RunDate).ToString("yyyy-MM-dd") }

function Ensure-EmailQueueFile {
    param([string]$Path)
    if (Test-Path $Path) { return }
    $empty = @(
        [pscustomobject]@{
            email_id = ""
            created_date = ""
            company_name = ""
            contact_name = ""
            to_email = ""
            cc_email = ""
            subject = ""
            body_text = ""
            owner_approved = "no"
            send_mode = "draft"
            status = ""
            scheduled_date = ""
            scheduled_time = ""
            sent_at = ""
            attempt_count = "0"
            last_error = ""
            notes = ""
        }
    )
    $empty | Export-Csv -Path $Path -NoTypeInformation
    # Remove placeholder row while keeping header.
    @() | Select-Object email_id,created_date,company_name,contact_name,to_email,cc_email,subject,body_text,owner_approved,send_mode,status,scheduled_date,scheduled_time,sent_at,attempt_count,last_error,notes |
        Export-Csv -Path $Path -NoTypeInformation
}

Write-Output "Step 1/7: Building security lookalike campaign pipeline..."
$buildArgs = @(
    "-ExecutionPolicy", "Bypass",
    "-File", ".\marketing-agents\scripts\build-security-lookalike-campaign-pipeline.ps1",
    "-TargetFile", $TargetFile,
    "-OutputFile", $PipelineFile,
    "-RunDate", $dateValue
)
if (Test-Path $CrossRefFile) {
    $buildArgs += @("-CrossRefFile", $CrossRefFile)
}
powershell @buildArgs

Write-Output "Step 2/7: Enriching contact emails from company websites..."
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\enrich-security-lookalike-contacts.ps1 `
    -PipelineFile $PipelineFile `
    -OutputFile $EnrichedPipelineFile

$activePipelineFile = $EnrichedPipelineFile

Write-Output "Step 3/7: Generating multi-touch cadence plan (email + LinkedIn)..."
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-email-followup-cadence.ps1 `
    -PipelineFile $activePipelineFile `
    -OutputFile $CadenceFile `
    -BlockedOutputFile $BlockedCadenceFile `
    -StartDate $dateValue

Write-Output "Step 4/7: Building email draft queue..."
Ensure-EmailQueueFile -Path $EmailQueueFile
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\build-email-queue-from-pipeline.ps1 `
    -PipelineFile $activePipelineFile `
    -QueueFile $EmailQueueFile `
    -ScheduledDate $dateValue `
    -ScheduledTime $ScheduledTime `
    -OwnerApproved "no" `
    -SendMode "draft"

Write-Output "Step 5/7: Building LinkedIn queue..."
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-linkedin-outreach-queue.ps1 `
    -PipelineFile $activePipelineFile `
    -OutputFile $LinkedInQueueFile `
    -RunDate $dateValue `
    -MaxRows $MaxLinkedInRows

Write-Output "Step 6/7: Generating security lookalike daily execution brief..."
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\generate-security-lookalike-daily-brief.ps1 `
    -Date $dateValue `
    -PipelineFile $activePipelineFile `
    -CadenceFile $CadenceFile `
    -BlockedCadenceFile $BlockedCadenceFile `
    -EmailQueueFile $EmailQueueFile `
    -LinkedInQueueFile $LinkedInQueueFile `
    -OutputDir $BriefDir

$briefPath = Join-Path $BriefDir ("security-lookalike-" + $dateValue + ".md")

Write-Output "Step 7/7: Complete."
Write-Output ("Review files:")
Write-Output (" - " + $PipelineFile)
Write-Output (" - " + $EnrichedPipelineFile)
Write-Output (" - " + $CadenceFile)
Write-Output (" - " + $EmailQueueFile)
Write-Output (" - " + $LinkedInQueueFile)
Write-Output (" - " + $briefPath)
