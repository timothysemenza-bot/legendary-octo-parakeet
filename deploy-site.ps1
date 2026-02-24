param(
    [string]$ProjectName = "boss-key-website",
    [string]$SourceDir = "boss-key-website",
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "marketing-agents\scripts\deploy-bosskey-pages.ps1"
if (-not (Test-Path $scriptPath)) {
    throw "Deploy script not found: $scriptPath"
}

& $scriptPath -ProjectName $ProjectName -SourceDir $SourceDir -Branch $Branch
