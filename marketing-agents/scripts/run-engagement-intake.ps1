param()

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$scriptPath = Join-Path $repoRoot "marketing-agents\scripts\run-engagement-intake.js"

$node = Get-Command node -ErrorAction SilentlyContinue
if ($null -eq $node) {
    throw "Node.js was not found on PATH."
}

& $node.Source $scriptPath
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
