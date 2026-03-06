Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Push-Location (Join-Path $PSScriptRoot "..")
try {
  $dbPath = ".\.artifacts\bosskey_pursuit_os.sqlite3"
  if (Test-Path $dbPath) {
    Remove-Item $dbPath -Force
    Write-Host "Removed $dbPath"
  } else {
    Write-Host "No existing DB at $dbPath"
  }

  python -m alembic upgrade head
  Write-Host "Database reset and migrated."
}
finally {
  Pop-Location
}

