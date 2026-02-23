param(
    [string]$SourcePath = "",
    [string]$BackupRoot = "",
    [string]$CloudMirrorDir = "",
    [int]$RetentionDays = 30,
    [switch]$EnableGitPush
)

$ErrorActionPreference = "Stop"

function Resolve-DefaultSourcePath {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Ensure-Dir {
    param([string]$PathValue)
    if (-not (Test-Path $PathValue)) {
        New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
    }
}

function Is-GitRepo {
    param([string]$PathValue)
    return (Test-Path (Join-Path $PathValue ".git"))
}

if ([string]::IsNullOrWhiteSpace($SourcePath)) {
    $SourcePath = Resolve-DefaultSourcePath
}
$SourcePath = (Resolve-Path $SourcePath).Path

if ([string]::IsNullOrWhiteSpace($BackupRoot)) {
    $BackupRoot = Join-Path $env:USERPROFILE "Backups\Proposal-Microsite"
}
Ensure-Dir $BackupRoot

$repoName = Split-Path -Leaf $SourcePath
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$zipName = "{0}-{1}.zip" -f $repoName, $stamp
$zipPath = Join-Path $BackupRoot $zipName

Write-Output ("Source: {0}" -f $SourcePath)
Write-Output ("Backup zip: {0}" -f $zipPath)

$tempMeta = Join-Path $env:TEMP ("backup-meta-" + [guid]::NewGuid().ToString("N") + ".txt")
$stageDir = Join-Path $env:TEMP ("backup-stage-" + [guid]::NewGuid().ToString("N"))
try {
    $meta = @()
    $meta += ("Backup Time: " + (Get-Date).ToString("s"))
    $meta += ("Source Path: " + $SourcePath)
    if (Is-GitRepo $SourcePath) {
        $meta += ("Git Branch: " + ((git -C $SourcePath rev-parse --abbrev-ref HEAD) 2>$null))
        $meta += ("Git Commit: " + ((git -C $SourcePath rev-parse HEAD) 2>$null))
        $meta += ("Git Status: " + ((git -C $SourcePath status --short) 2>$null | Out-String).Trim())
    }
    $meta -join [Environment]::NewLine | Set-Content -Path $tempMeta -Encoding UTF8

    Ensure-Dir $stageDir
    $roboArgs = @(
        "`"$SourcePath`"",
        "`"$stageDir`"",
        "/E",
        "/R:1",
        "/W:1",
        "/NFL",
        "/NDL",
        "/NJH",
        "/NJS",
        "/NP"
    )
    $null = & robocopy @roboArgs
    $roboCode = $LASTEXITCODE
    if ($roboCode -gt 7) {
        throw ("Robocopy staging failed with exit code {0}" -f $roboCode)
    }

    Compress-Archive -Path (Join-Path $stageDir "*") -DestinationPath $zipPath -CompressionLevel Optimal -Force

    $metaCopy = [System.IO.Path]::ChangeExtension($zipPath, ".meta.txt")
    Copy-Item -Path $tempMeta -Destination $metaCopy -Force

    if ($EnableGitPush -and (Is-GitRepo $SourcePath)) {
        Write-Output "Git push enabled: attempting add/commit/push."
        git -C $SourcePath add -A
        $hasChanges = git -C $SourcePath diff --cached --name-only
        if (-not [string]::IsNullOrWhiteSpace(($hasChanges | Out-String).Trim())) {
            $msg = "automated backup checkpoint " + (Get-Date -Format "yyyy-MM-dd HH:mm")
            git -C $SourcePath commit -m $msg | Out-Null
            git -C $SourcePath push | Out-Null
            Write-Output "Git commit/push complete."
        } else {
            Write-Output "No staged changes. Skipping commit/push."
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($CloudMirrorDir)) {
        Ensure-Dir $CloudMirrorDir
        $mirrorZip = Join-Path $CloudMirrorDir $zipName
        $mirrorMeta = [System.IO.Path]::ChangeExtension($mirrorZip, ".meta.txt")
        Copy-Item -Path $zipPath -Destination $mirrorZip -Force
        Copy-Item -Path ([System.IO.Path]::ChangeExtension($zipPath, ".meta.txt")) -Destination $mirrorMeta -Force
        Write-Output ("Cloud mirror copy complete: {0}" -f $CloudMirrorDir)
    }

    if ($RetentionDays -gt 0) {
        $cutoff = (Get-Date).AddDays(-1 * $RetentionDays)
        Get-ChildItem -Path $BackupRoot -File | Where-Object { $_.LastWriteTime -lt $cutoff } | Remove-Item -Force -ErrorAction SilentlyContinue
        if (-not [string]::IsNullOrWhiteSpace($CloudMirrorDir) -and (Test-Path $CloudMirrorDir)) {
            Get-ChildItem -Path $CloudMirrorDir -File | Where-Object { $_.LastWriteTime -lt $cutoff } | Remove-Item -Force -ErrorAction SilentlyContinue
        }
    }

    $zipInfo = Get-Item $zipPath
    Write-Output ("Backup complete: {0} ({1:N0} bytes)" -f $zipInfo.FullName, $zipInfo.Length)
}
finally {
    Remove-Item -Path $tempMeta -Force -ErrorAction SilentlyContinue
    Remove-Item -Path $stageDir -Recurse -Force -ErrorAction SilentlyContinue
}
