param(
    [string]$SourceFolder = "$env:USERPROFILE\Downloads\jwblng-exports",
    [int]$PollSeconds = 3,
    [switch]$Watch
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$stockDir = Join-Path $root "assets\stock"
$motionDir = Join-Path $root "assets\motion"

New-Item -ItemType Directory -Path $SourceFolder -Force | Out-Null
New-Item -ItemType Directory -Path $stockDir -Force | Out-Null
New-Item -ItemType Directory -Path $motionDir -Force | Out-Null

$map = @{
    "hero-community.jpg"         = Join-Path $stockDir "hero-community.jpg"
    "program-speaker-series.jpg" = Join-Path $stockDir "program-speaker-series.jpg"
    "program-book-club.jpg"      = Join-Path $stockDir "program-book-club.jpg"
    "program-learning-hub.jpg"   = Join-Path $stockDir "program-learning-hub.jpg"
    "member-portrait-1.jpg"      = Join-Path $stockDir "member-portrait-1.jpg"
    "member-portrait-2.jpg"      = Join-Path $stockDir "member-portrait-2.jpg"
    "portal-hero.jpg"            = Join-Path $stockDir "portal-hero.jpg"
    "hero-loop.mp4"              = Join-Path $motionDir "hero-loop.mp4"
    "portal-loop.mp4"            = Join-Path $motionDir "portal-loop.mp4"
    "learning-pulse.json"        = Join-Path $motionDir "learning-pulse.json"
    "network-flow.json"          = Join-Path $motionDir "network-flow.json"
    "portal-engagement.json"     = Join-Path $motionDir "portal-engagement.json"
}

Write-Output "Source folder: $SourceFolder"
Write-Output "Drop exported files with exact names from mapping list."
if ($Watch) {
    Write-Output "Mode: watch (continuous)"
} else {
    Write-Output "Mode: one-shot sync"
}

while ($true) {
    Get-ChildItem -Path $SourceFolder -File | ForEach-Object {
        $name = $_.Name
        if ($map.ContainsKey($name)) {
            Copy-Item -Path $_.FullName -Destination $map[$name] -Force
            Write-Output ("Synced: {0} -> {1}" -f $name, $map[$name])
        }
    }
    if (-not $Watch) { break }
    Start-Sleep -Seconds $PollSeconds
}
