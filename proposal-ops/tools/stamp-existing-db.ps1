Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..")
try {
  python -m alembic stamp head
  Write-Host "Existing DB stamped to head revision."
}
finally {
  Pop-Location
}

