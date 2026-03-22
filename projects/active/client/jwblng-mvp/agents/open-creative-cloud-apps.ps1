param(
    [switch]$OpenPhotoshop,
    [switch]$OpenIllustrator,
    [switch]$OpenAfterEffects,
    [switch]$OpenPremiere,
    [switch]$OpenAll,
    [switch]$OpenFolders
)

$ErrorActionPreference = "SilentlyContinue"

$appCandidates = @{
    Photoshop = @(
        "C:\Program Files\Adobe\Adobe Photoshop 2026\Photoshop.exe",
        "C:\Program Files\Adobe\Adobe Photoshop 2025\Photoshop.exe"
    )
    Illustrator = @(
        "C:\Program Files\Adobe\Adobe Illustrator 2026\Support Files\Contents\Windows\Illustrator.exe",
        "C:\Program Files\Adobe\Adobe Illustrator 2025\Support Files\Contents\Windows\Illustrator.exe"
    )
    AfterEffects = @(
        "C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe",
        "C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\AfterFX.exe"
    )
    Premiere = @(
        "C:\Program Files\Adobe\Adobe Premiere Pro 2026\Adobe Premiere Pro.exe",
        "C:\Program Files\Adobe\Adobe Premiere Pro 2025\Adobe Premiere Pro.exe"
    )
}

function Find-AppPath {
    param([string[]]$Candidates)
    foreach ($path in $Candidates) {
        if (Test-Path $path) { return $path }
    }
    return $null
}

function Start-App {
    param([string]$Name)
    $path = Find-AppPath -Candidates $appCandidates[$Name]
    if ($path) {
        Start-Process -FilePath $path | Out-Null
        Write-Output ("Opened {0}: {1}" -f $Name, $path)
    } else {
        Write-Output ("Could not find {0}. Launch manually from Creative Cloud." -f $Name)
    }
}

if ($OpenAll -or $OpenPhotoshop) { Start-App -Name "Photoshop" }
if ($OpenAll -or $OpenIllustrator) { Start-App -Name "Illustrator" }
if ($OpenAll -or $OpenAfterEffects) { Start-App -Name "AfterEffects" }
if ($OpenAll -or $OpenPremiere) { Start-App -Name "Premiere" }

if ($OpenFolders -or $OpenAll) {
    $root = Split-Path -Parent $PSScriptRoot
    Start-Process "explorer.exe" "$root\assets\stock" | Out-Null
    Start-Process "explorer.exe" "$root\assets\motion" | Out-Null
    Write-Output "Opened asset folders: assets/stock and assets/motion"
}

if (-not ($OpenAll -or $OpenPhotoshop -or $OpenIllustrator -or $OpenAfterEffects -or $OpenPremiere -or $OpenFolders)) {
    Write-Output "Usage examples:"
    Write-Output "  .\agents\open-creative-cloud-apps.ps1 -OpenAll"
    Write-Output "  .\agents\open-creative-cloud-apps.ps1 -OpenIllustrator -OpenAfterEffects -OpenFolders"
}
