param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('home-hero', 'home-cta', 'event-speaker', 'event-book', 'event-halacha')]
  [string]$Slice,

  [ValidateSet('verify', 'apply')]
  [string]$Mode = 'verify'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
Set-Location $repoRoot

[System.Environment]::SetEnvironmentVariable('JWBLNG_SLICE_ID', $Slice, 'Process')

Write-Host "[slice] Repo: $repoRoot"
Write-Host "[slice] Slice: $Slice"
Write-Host "[slice] Mode: $Mode"

if ($Mode -eq 'apply') {
  switch ($Slice) {
    'home-hero' {
      & powershell -ExecutionPolicy Bypass -File jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow homepage -Mode apply -AllowWrites
    }
    'home-cta' {
      & powershell -ExecutionPolicy Bypass -File jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow homepage -Mode apply -AllowWrites
    }
    'event-speaker' {
      & powershell -ExecutionPolicy Bypass -File jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow scopepages -Mode apply -AllowWrites
      & powershell -ExecutionPolicy Bypass -File jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow eventpages -Mode apply -AllowWrites
    }
    'event-book' {
      & powershell -ExecutionPolicy Bypass -File jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow scopepages -Mode apply -AllowWrites
      & powershell -ExecutionPolicy Bypass -File jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow eventpages -Mode apply -AllowWrites
    }
    'event-halacha' {
      & powershell -ExecutionPolicy Bypass -File jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow scopepages -Mode apply -AllowWrites
      & powershell -ExecutionPolicy Bypass -File jwblng-mvp/playwright/scripts/run-flow.ps1 -Flow eventpages -Mode apply -AllowWrites
    }
  }
}

& npm.cmd run pw:jwblng:sliceverify

