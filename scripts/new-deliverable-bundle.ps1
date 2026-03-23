param(
    [Parameter(Mandatory = $true)]
    [string]$Slug,

    [string]$Date = "",
    [string]$Title = "",
    [string]$DeliverablesRoot = ""
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$bundleDate = if ($Date) { $Date } else { Get-Date -Format "yyyy-MM-dd" }
$safeSlug = ($Slug.ToLowerInvariant() -replace '[^a-z0-9]+', '-').Trim('-')
$deliverablesPath = if ($DeliverablesRoot) {
    $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($DeliverablesRoot)
} else {
    Join-Path $repoRoot "outputs/deliverables"
}
$bundleRoot = Join-Path $deliverablesPath ("{0}-{1}" -f $safeSlug, $bundleDate)

New-Item -ItemType Directory -Force -Path $bundleRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $bundleRoot "source") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $bundleRoot "export") | Out-Null

$readme = @(
    "# " + ($(if ($Title) { $Title } else { $Slug })),
    "",
    "Date: $bundleDate",
    "",
    "## Contents",
    "",
    "- `source/`: source material or assembly files",
    "- `export/`: final packaged outputs",
    "",
    "## Notes",
    "",
    "Add handoff notes, verification notes, and delivery assumptions here."
) -join [Environment]::NewLine

Set-Content -Path (Join-Path $bundleRoot "README.md") -Value $readme
Write-Output ("Created deliverable bundle at {0}" -f $bundleRoot)
