param(
    [string]$DataDir = "marketing-agents/data"
)

$ErrorActionPreference = "Stop"

$pidPath = Join-Path $DataDir "cloudflared.pid"
if (-not (Test-Path $pidPath)) {
    Write-Output "No tunnel PID file found."
    exit 0
}

$cloudflaredPid = Get-Content -Path $pidPath -ErrorAction SilentlyContinue | Select-Object -First 1
if ($cloudflaredPid) {
    try {
        Stop-Process -Id $cloudflaredPid -Force
        Write-Output "Stopped cloudflared process $cloudflaredPid."
    } catch {
        Write-Output "cloudflared process not running."
    }
}

Remove-Item $pidPath -Force -ErrorAction SilentlyContinue
