param(
    [string]$ProjectName = "boss-key-website",
    [string]$SourceDir = "boss-key-website",
    [string]$Branch = "main",
    [string]$WranglerVersion = "4.69.0"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $SourceDir)) {
    throw "Source directory not found: $SourceDir"
}

Write-Output "Deploying '$SourceDir' to Cloudflare Pages project '$ProjectName'..."
npx.cmd --yes wrangler@$WranglerVersion pages deploy $SourceDir --project-name $ProjectName --branch $Branch
if ($LASTEXITCODE -ne 0) {
    throw "Cloudflare Pages deploy failed (wrangler exit code: $LASTEXITCODE)."
}

Write-Output "Deploy command completed."
