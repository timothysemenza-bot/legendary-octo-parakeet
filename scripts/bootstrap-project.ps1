param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectName,

    [Parameter(Mandatory = $true)]
    [ValidateSet("active", "internal", "pipeline", "completed", "shared")]
    [string]$Lane,

    [string]$Bucket = "general",
    [string]$Slug = "",
    [string]$Description = "",
    [switch]$FlatRoot,
    [switch]$RfpProject
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$safeSlug = if ($Slug) {
    $Slug
} else {
    ($ProjectName.ToLowerInvariant() -replace '[^a-z0-9]+', '-').Trim('-')
}

$projectRoot = if ($FlatRoot) {
    Join-Path $repoRoot ("projects/{0}/{1}" -f $Lane, $safeSlug)
} else {
    Join-Path $repoRoot ("projects/{0}/{1}/{2}" -f $Lane, $Bucket, $safeSlug)
}
$readmeTemplate = Join-Path $repoRoot "templates/project/README.template.md"
$agentsTemplate = Join-Path $repoRoot "templates/project/AGENTS.template.md"
$projectContextTemplate = Join-Path $repoRoot "templates/project/project-context.rfp.template.md"

New-Item -ItemType Directory -Force -Path $projectRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot "docs") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot "inputs") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot "working") | Out-Null
if ($RfpProject) {
    New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot "outputs") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot "outputs/deliverables") | Out-Null
}

if (Test-Path $readmeTemplate) {
    $content = Get-Content -Raw $readmeTemplate
    $content = $content.Replace("__PROJECT_NAME__", $ProjectName)
    $content = $content.Replace("__PROJECT_TYPE__", $Lane)
    if ($Description) {
        $content = $content.Replace("Describe the purpose of this project in one paragraph.", $Description)
    }
    if ($RfpProject) {
        $content = $content.Replace(
            "Generated packages belong in `outputs/`, not inside this project folder.",
            "Generated run bundles belong in `outputs/deliverables/` inside this project."
        )
        $content += @"

## RFP Context

- `project-context.md`: pursuit grounding, timing mode, and known constraints
- `outputs/deliverables/`: dated run bundles for historical replay or live-rfp runs
"@
    }
    Set-Content -Path (Join-Path $projectRoot "README.md") -Value $content
}

if (Test-Path $agentsTemplate) {
    $content = Get-Content -Raw $agentsTemplate
    $content = $content.Replace("__PROJECT_NAME__", $ProjectName)
    if ($RfpProject) {
        $content += @"

## RFP Workflow

- Inspect `project-context.md`, then all files in `inputs/`, before selecting a stage.
- Treat `outputs/deliverables/` as the local run history for continuity between runs.
- On reruns, read the newest local bundle first and carry unresolved actions and assumptions forward.
- Keep source files in `inputs/`; do not scatter clarifications, pricing notes, or addenda outside this project root.
"@
    }
    Set-Content -Path (Join-Path $projectRoot "AGENTS.md") -Value $content
}

if ($RfpProject) {
    $projectContextPath = Join-Path $projectRoot "project-context.md"
    if (-not (Test-Path $projectContextPath)) {
        if (Test-Path $projectContextTemplate) {
            Set-Content -Path $projectContextPath -Value (Get-Content -Raw $projectContextTemplate)
        } else {
            Set-Content -Path $projectContextPath -Value @"
# Project Context

- client name:
- industry:
- due date:
- contract type:
- timing mode:
- known constraints:
"@
        }
    }
}

Write-Output ("Created project scaffold at {0}" -f $projectRoot)
