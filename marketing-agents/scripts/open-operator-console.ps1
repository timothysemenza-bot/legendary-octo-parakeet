param(
    [int]$Port = 3201
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$serverScript = Join-Path $root "marketing-agents\\operator-app.js"

function Test-PortListening {
    param([int]$PortNumber)
    try {
        $conn = Get-NetTCPConnection -LocalPort $PortNumber -State Listen -ErrorAction Stop | Select-Object -First 1
        return $null -ne $conn
    } catch {
        return $false
    }
}

if (-not (Test-PortListening -PortNumber $Port)) {
    Start-Process -FilePath "node.exe" -ArgumentList "marketing-agents/operator-app.js" -WorkingDirectory $root -WindowStyle Hidden | Out-Null
    Start-Sleep -Seconds 2
}

Start-Process "http://localhost:$Port" | Out-Null
Write-Output "Operator Console launched: http://localhost:$Port"
