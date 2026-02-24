param(
    [Parameter(Mandatory = $true)][string]$SourcePath,
    [Parameter(Mandatory = $true)][string]$OutputPath,
    [ValidateSet("resize_jpg","headshot_web","headshot_mobile","headshot_enhanced_web","headshot_enhanced_mobile")]
    [string]$JobType = "resize_jpg",
    [int]$MaxLongEdge = 1200,
    [int]$JpgQuality = 10,
    [string]$QueueFile = "marketing-agents/data/photoshop_jobs.csv"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $QueueFile)) { throw "Missing queue file: $QueueFile" }

$resolvedSource = (Resolve-Path $SourcePath).Path
$resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)

if ($JobType -eq "headshot_web") {
    $MaxLongEdge = 1200
    $JpgQuality = 10
}
if ($JobType -eq "headshot_mobile") {
    $MaxLongEdge = 600
    $JpgQuality = 9
}
if ($JobType -eq "headshot_enhanced_web") {
    $MaxLongEdge = 1200
    $JpgQuality = 10
}
if ($JobType -eq "headshot_enhanced_mobile") {
    $MaxLongEdge = 600
    $JpgQuality = 9
}

$jobId = "psjob-" + (Get-Date).ToString("yyyyMMddHHmmss")
$createdAt = (Get-Date).ToString("s")

$rows = @(Import-Csv -Path $QueueFile)
$rows += [pscustomobject]@{
    job_id = $jobId
    created_at = $createdAt
    job_type = $JobType
    source_path = $resolvedSource
    output_path = $resolvedOutput
    max_long_edge = [string]$MaxLongEdge
    jpg_quality = [string]$JpgQuality
    status = "queued"
    last_error = ""
    completed_at = ""
}

$rows | Export-Csv -Path $QueueFile -NoTypeInformation
Write-Output "Queued $jobId ($JobType)"
