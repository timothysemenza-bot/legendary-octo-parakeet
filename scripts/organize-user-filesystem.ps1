param(
    [string[]]$SourceRoots = @(),
    [string]$DestinationRoot = "",
    [int]$MinAgeDays = 14,
    [switch]$Apply,
    [ValidateSet("Copy", "Move")]
    [string]$Mode = "Copy",
    [string]$LogPath = "",
    [string[]]$ExcludePathContains = @(
        "\Apple Music\",
        "\iTunes\",
        "\Music\Media\",
        "\Podcasts\"
    )
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
        ".exe" { return "Installers" }
        ".msi" { return "Installers" }
        ".ps1" { return "Code\PowerShell" }
        ".js" { return "Code\JavaScript" }
        ".ts" { return "Code\TypeScript" }
        ".py" { return "Code\Python" }
        ".json" { return "Code\Data" }
        default { return "Other" }
    }
}

function Resolve-UniquePath {
    param([string]$TargetPath)
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

if ([string]::IsNullOrWhiteSpace($DestinationRoot)) {
    $DestinationRoot = Join-Path $env:USERPROFILE "Intuitive-Workspace"
}
Ensure-Dir $DestinationRoot

if (-not $SourceRoots -or $SourceRoots.Count -eq 0) {
    $SourceRoots = @(
        (Join-Path $env:USERPROFILE "Desktop"),
        (Join-Path $env:USERPROFILE "Downloads"),
        (Join-Path $env:USERPROFILE "Documents"),
        (Join-Path $env:USERPROFILE "Pictures"),
        (Join-Path $env:USERPROFILE "Videos"),
        (Join-Path $env:USERPROFILE "Music")
    )
}

$resolvedRoots = @()
foreach ($root in $SourceRoots) {
    if (Test-Path $root) {
        $resolvedRoots += (Resolve-Path $root).Path
    }
}

if (-not $resolvedRoots -or $resolvedRoots.Count -eq 0) {
    throw "No valid source roots were found."
}

$excludePrefixes = @(
    (Join-Path $env:USERPROFILE "AppData"),
    (Join-Path $env:USERPROFILE ".cache"),
    (Join-Path $env:USERPROFILE ".vscode")
) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

$cutoff = (Get-Date).AddDays(-1 * $MinAgeDays)
$ops = New-Object System.Collections.Generic.List[object]
$processed = 0
$skipped = 0

foreach ($root in $resolvedRoots) {
    Write-Output ("Scanning: {0}" -f $root)
    $rootName = Split-Path -Leaf $root
    $files = Get-ChildItem -Path $root -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $cutoff }
    foreach ($file in $files) {
        $isExcluded = $false
        foreach ($prefix in $excludePrefixes) {
            if ($file.FullName.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                $isExcluded = $true
                break
            }
        }
        if (-not $isExcluded -and $ExcludePathContains -and $ExcludePathContains.Count -gt 0) {
            foreach ($needle in $ExcludePathContains) {
                if (-not [string]::IsNullOrWhiteSpace($needle) -and $file.FullName.IndexOf($needle, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
                    $isExcluded = $true
                    break
                }
            }
        }
        if ($isExcluded) {
            $skipped++
            continue
        }
        if ($file.FullName.StartsWith($DestinationRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            $skipped++
            continue
        }

        $category = Get-Category -Extension $file.Extension
        $dateBucket = $file.LastWriteTime.ToString("yyyy-MM")
        $targetDir = Join-Path $DestinationRoot (Join-Path $rootName (Join-Path $category $dateBucket))
        $targetPath = Join-Path $targetDir $file.Name
        $targetPath = Resolve-UniquePath -TargetPath $targetPath

        if (-not $Apply) {
            Write-Output ("[PREVIEW] {0} '{1}' -> '{2}'" -f $Mode.ToUpperInvariant(), $file.FullName, $targetPath)
            $processed++
            continue
        }

        Ensure-Dir $targetDir
        if ($Mode -eq "Move") {
            Move-Item -Path $file.FullName -Destination $targetPath -Force
        } else {
            Copy-Item -Path $file.FullName -Destination $targetPath -Force
        }

        $ops.Add([pscustomobject]@{
            Timestamp = (Get-Date).ToString("s")
            Mode = $Mode
            Source = $file.FullName
            Destination = $targetPath
        }) | Out-Null
        $processed++
    }
}

if ($Apply) {
    if ([string]::IsNullOrWhiteSpace($LogPath)) {
        $LogPath = Join-Path $DestinationRoot ("organizer-log-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".csv")
    }
    $ops | Export-Csv -Path $LogPath -NoTypeInformation -Encoding UTF8
    Write-Output ("Applied mode: {0}. Operation log: {1}" -f $Mode, $LogPath)
}

Write-Output ("Done. Processed: {0} | Skipped: {1} | Apply: {2} | Mode: {3}" -f $processed, $skipped, $Apply.IsPresent, $Mode)
