param(
    [int]$Port = 5500
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$cloudflared = "C:\Program Files (x86)\cloudflared\cloudflared.exe"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is not installed or not on PATH."
}

if (-not (Test-Path $cloudflared)) {
    throw "cloudflared was not found at: $cloudflared"
}

Write-Host "Starting local server on http://localhost:$Port ..." -ForegroundColor Cyan
Start-Process -FilePath python -ArgumentList "-m http.server $Port" -WorkingDirectory $root

Start-Sleep -Seconds 2

Write-Host "Starting Cloudflare tunnel..." -ForegroundColor Cyan
Write-Host "Share the https://*.trycloudflare.com URL shown in the new window." -ForegroundColor Yellow
Start-Process -FilePath $cloudflared -ArgumentList "tunnel --url http://localhost:$Port --no-autoupdate" -WorkingDirectory $root

Write-Host ""
Write-Host "Local pages:" -ForegroundColor Green
Write-Host "  http://localhost:$Port/index.html"
Write-Host "  http://localhost:$Port/dashboard.html"
Write-Host "  http://localhost:$Port/proposal.html"
Write-Host ""
Write-Host "Opening proposal page in your default browser..." -ForegroundColor Cyan
Start-Process "http://localhost:$Port/proposal.html"
Write-Host ""
Write-Host "To stop later: close the two spawned windows or end python/cloudflared processes." -ForegroundColor DarkGray
