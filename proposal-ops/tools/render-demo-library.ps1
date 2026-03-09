param(
  [string]$ResultsRoot = (Join-Path $PSScriptRoot "..\test-results"),
  [string]$OutputRoot = (Join-Path $PSScriptRoot "..\demo-artifacts"),
  [ValidateSet("auto", "openai", "windows")]
  [string]$Provider = "auto"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$resultsRootPath = (Resolve-Path $ResultsRoot).Path
$manifests = Get-ChildItem -Path $resultsRootPath -Recurse -Filter "narration-manifest.json" -File |
  Sort-Object LastWriteTimeUtc -Descending

if (-not $manifests) {
  throw "No narration manifests were found under $resultsRootPath. Run the Playwright Boss Key videos first."
}

$latestByDemo = @{}
foreach ($manifestFile in $manifests) {
  $manifest = Get-Content $manifestFile.FullName -Raw | ConvertFrom-Json
  $demoId = [string]$manifest.demo
  if (-not $latestByDemo.ContainsKey($demoId)) {
    $latestByDemo[$demoId] = $manifestFile.FullName
  }
}

$orderedManifestPaths = $latestByDemo.GetEnumerator() |
  Sort-Object Name |
  ForEach-Object { $_.Value }

foreach ($manifestPath in $orderedManifestPaths) {
  & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "render-demo-narration.ps1") `
    -ManifestPath $manifestPath `
    -OutputRoot $OutputRoot `
    -Provider $Provider

  if ($LASTEXITCODE -ne 0) {
    throw "Narration rendering failed for $manifestPath."
  }
}

Write-Host "Rendered narrated knowledge-base videos to $((Resolve-Path $OutputRoot).Path)"
