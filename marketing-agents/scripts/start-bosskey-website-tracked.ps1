param(
    [int]$Port = 8088
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$env:PORT = [string]$Port
$env:PUBLIC_DIR = Join-Path $root "boss-key-website"
$env:BRAND_NAME = "Boss Key"
$env:BRAND_TAGLINE = "Website"

Write-Output ("Starting tracked Boss Key website on http://localhost:{0}" -f $Port)
Write-Output ("Public dir: {0}" -f $env:PUBLIC_DIR)
Write-Output "Contact clicks will be logged to marketing-agents/data/website_contact_events.csv"

Push-Location $root
try {
    node .\server.js
}
finally {
    Pop-Location
}
