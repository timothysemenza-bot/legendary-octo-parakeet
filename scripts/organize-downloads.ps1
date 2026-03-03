param(
    [string]$SourcePath = "",
    [string]$DestinationRoot = "",
    [int]$MinAgeHours = 12,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Ensure-Dir {
    param([string]$PathValue)
    if (-not (Test-Path $PathValue)) {
        New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
    }
}

function Get-Category {
    param([string]$Extension)

    $ext = $Extension.ToLowerInvariant()
    switch ($ext) {
        ".pdf" { return "Documents\PDFs" }
        ".doc" { return "Documents\Word" }
        ".docx" { return "Documents\Word" }
        ".txt" { return "Documents\Text" }
        ".rtf" { return "Documents\Text" }
        ".md" { return "Documents\Text" }
        ".xls" { return "Documents\Spreadsheets" }
        ".xlsx" { return "Documents\Spreadsheets" }
        ".csv" { return "Documents\Spreadsheets" }
        ".ppt" { return "Documents\Presentations" }
        ".pptx" { return "Documents\Presentations" }
        ".jpg" { return "Media\Images" }
        ".jpeg" { return "Media\Images" }
        ".png" { return "Media\Images" }
        ".gif" { return "Media\Images" }
        ".webp" { return "Media\Images" }
        ".svg" { return "Media\Images" }
        ".mp4" { return "Media\Videos" }
        ".mov" { return "Media\Videos" }
        ".mkv" { return "Media\Videos" }
        ".mp3" { return "Media\Audio" }
        ".wav" { return "Media\Audio" }
        ".zip" { return "Archives" }
        ".rar" { return "Archives" }
        ".7z" { return "Archives" }
        ".msi" { return "Installers" }
        ".exe" { return "Installers" }
        ".ps1" { return "Code\PowerShell" }
        ".js" { return "Code\JavaScript" }
        ".ts" { return "Code\TypeScript" }
        ".py" { return "Code\Python" }
        ".json" { return "Code\Data" }
        default { return "Other" }
    }
}

function Resolve-UniquePath {
    param(
        [string]$TargetPath
    )

    if (-not (Test-Path $TargetPath)) {
        return $TargetPath
    }

    $dir = Split-Path -Parent $TargetPath
    $name = [System.IO.Path]::GetFileNameWithoutExtension($TargetPath)
    $ext = [System.IO.Path]::GetExtension($TargetPath)
    $i = 1
    while ($true) {
        $candidate = Join-Path $dir ("{0} ({1}){2}" -f $name, $i, $ext)
        if (-not (Test-Path $candidate)) {
            return $candidate
        }
        $i++
    }
}

if ([string]::IsNullOrWhiteSpace($SourcePath)) {
    $SourcePath = Join-Path $env:USERPROFILE "Downloads"
}
if ([string]::IsNullOrWhiteSpace($DestinationRoot)) {
    $DestinationRoot = Join-Path $env:USERPROFILE "Organized-Files"
}

if (-not (Test-Path $SourcePath)) {
    throw "Source path not found: $SourcePath"
}

Ensure-Dir -PathValue $DestinationRoot

$cutoff = (Get-Date).AddHours(-1 * $MinAgeHours)
$files = Get-ChildItem -Path $SourcePath -File | Where-Object { $_.LastWriteTime -lt $cutoff }

if (-not $files) {
    Write-Output ("No files to organize in '{0}' older than {1} hour(s)." -f $SourcePath, $MinAgeHours)
    exit 0
}

$movedCount = 0
$skipCount = 0

foreach ($file in $files) {
    $category = Get-Category -Extension $file.Extension
    $dateBucket = $file.LastWriteTime.ToString("yyyy-MM")
    $targetDir = Join-Path $DestinationRoot (Join-Path $category $dateBucket)
    $targetPath = Join-Path $targetDir $file.Name
    $targetPath = Resolve-UniquePath -TargetPath $targetPath

    if ($DryRun) {
        Write-Output ("[DRY-RUN] Move '{0}' -> '{1}'" -f $file.FullName, $targetPath)
        $movedCount++
        continue
    }

    Ensure-Dir -PathValue $targetDir
    try {
        Move-Item -Path $file.FullName -Destination $targetPath -Force
        Write-Output ("Moved '{0}' -> '{1}'" -f $file.Name, $targetPath)
        $movedCount++
    }
    catch {
        Write-Output ("Skipped '{0}' ({1})" -f $file.Name, $_.Exception.Message)
        $skipCount++
    }
}

Write-Output ("Done. Moved: {0} | Skipped: {1} | Source: {2} | Destination: {3}" -f $movedCount, $skipCount, $SourcePath, $DestinationRoot)
