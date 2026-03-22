param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectName,

    [Parameter(Mandatory = $true)]
    [ValidateSet("active", "internal", "pipeline", "completed", "shared")]
    [string]$Lane,

    [string]$Bucket = "general",
    [string]$Slug = "",
    [string]$Description = ""
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$safeSlug = if ($Slug) {
    $Slug
} else {
    ($ProjectName.ToLowerInvariant() -replace '[^a-z0-9]+', '-').Trim('-')
}

$projectRoot = Join-Path $repoRoot ("projects/{0}/{1}/{2}" -f $Lane, $Bucket, $safeSlug)
$readmeTemplate = Join-Path $repoRoot "templates/project/README.template.md"
$agentsTemplate = Join-Path $repoRoot "templates/project/AGENTS.template.md"

New-Item -ItemType Directory -Force -Path $projectRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot "docs") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot "inputs") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot "working") | Out-Null

if (Test-Path $readmeTemplate) {
    $content = Get-Content -Raw $readmeTemplate
    $content = $content.Replace("__PROJECT_NAME__", $ProjectName)
    $content = $content.Replace("__PROJECT_TYPE__", $Lane)
    if ($Description) {
        $content = $content.Replace("Describe the purpose of this project in one paragraph.", $Description)
    }
    Set-Content -Path (Join-Path $projectRoot "README.md") -Value $content
}

if (Test-Path $agentsTemplate) {
    $content = Get-Content -Raw $agentsTemplate
    $content = $content.Replace("__PROJECT_NAME__", $ProjectName)
    Set-Content -Path (Join-Path $projectRoot "AGENTS.md") -Value $content
}

Write-Output ("Created project scaffold at {0}" -f $projectRoot)
