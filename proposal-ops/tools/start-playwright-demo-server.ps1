Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repoRoot
try {
  $demoArtifactsDir = Join-Path $repoRoot ".artifacts\playwright-demo"
  if (Test-Path $demoArtifactsDir) {
    Remove-Item $demoArtifactsDir -Recurse -Force
  }
  New-Item -ItemType Directory -Path $demoArtifactsDir | Out-Null

  $env:BOSSKEY_ARTIFACTS_DIR = $demoArtifactsDir
  $env:BOSSKEY_DB_PATH = Join-Path $demoArtifactsDir "bosskey_chris_demo.sqlite3"
  $env:BOSSKEY_SECRET_STORE_PATH = Join-Path $demoArtifactsDir "secrets.json"
  $env:BOSSKEY_NOTIFICATION_PROVIDER_MODE = "mock"

  python -m alembic upgrade head
  python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
}
finally {
  Pop-Location
}
