param(
  [string]$ManifestPath,
  [string]$ResultsRoot = (Join-Path $PSScriptRoot "..\test-results"),
  [string]$OutputRoot = (Join-Path $PSScriptRoot "..\demo-artifacts"),
  [ValidateSet("auto", "openai", "windows")]
  [string]$Provider = "auto"
)

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "render-demo-narration.ps1") `
  -ManifestPath $ManifestPath `
  -ResultsRoot $ResultsRoot `
  -OutputRoot $OutputRoot `
  -Provider $Provider

if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
