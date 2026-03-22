Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$uvicornParents = Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -like '*uvicorn app.main:app*' -and $_.ProcessId -ne $PID
}
foreach ($proc in $uvicornParents) {
  Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
}

$listeners = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
foreach ($listener in $listeners) {
  Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 2

python -m alembic upgrade head

$url = "http://127.0.0.1:8000/proposal-builder"
Start-Job -ScriptBlock {
  param($targetUrl)
  Start-Sleep -Seconds 3
  Start-Process $targetUrl
} -ArgumentList $url | Out-Null
python -m uvicorn app.main:app --reload --reload-dir app --reload-dir migrations
