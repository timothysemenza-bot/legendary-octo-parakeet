param(
    [string]$RepoRoot = "",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Ensure-Dir {
    param([string]$PathValue)
    if (-not (Test-Path $PathValue)) {
        New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
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

$rules = @(
    @{ Pattern = "_tmp*"; Destination = "workspace\scratch\text" },
    @{ Pattern = "tmp-*"; Destination = "workspace\scratch\text" },
    @{ Pattern = "tmp*.docx"; Destination = "workspace\scratch\docs" },
    @{ Pattern = "probe*.docx"; Destination = "workspace\scratch\docs" },
    @{ Pattern = "proposal-*.docx"; Destination = "workspace\scratch\docs" },
    @{ Pattern = "*-transcript*.json"; Destination = "workspace\records\transcripts" },
    @{ Pattern = "*.srt"; Destination = "workspace\records\transcripts" },
    @{ Pattern = "*Meeting-Prep*.md"; Destination = "workspace\records\notes" },
    @{ Pattern = "meeting-brief-*.md"; Destination = "workspace\records\notes" },
    @{ Pattern = "Ryan-Benton-*.md"; Destination = "workspace\records\notes" },
    @{ Pattern = "rob_profile.txt"; Destination = "workspace\records\notes" },
    @{ Pattern = "*-mvp.html"; Destination = "workspace\prototypes\html" },
    @{ Pattern = "*-article.html"; Destination = "workspace\prototypes\html" },
    @{ Pattern = "cure-psp-legislative-action-plan.html"; Destination = "workspace\prototypes\html" },
    @{ Pattern = "bunny-roguelite.html"; Destination = "workspace\prototypes\html" },
    @{ Pattern = "payload.json"; Destination = "workspace\scratch\data" },
    @{ Pattern = "temp_payload.json"; Destination = "workspace\scratch\data" },
    @{ Pattern = "sample-sharepoint-manifest.json"; Destination = "workspace\scratch\data" }
)

$moved = 0
$seen = @{}

foreach ($rule in $rules) {
    $files = Get-ChildItem -Path $RepoRoot -File -Filter $rule.Pattern -ErrorAction SilentlyContinue
    foreach ($file in $files) {
        if ($seen.ContainsKey($file.FullName)) {
            continue
        }
        $seen[$file.FullName] = $true

        $destDir = Join-Path $RepoRoot $rule.Destination
        $destPath = Resolve-UniquePath -TargetPath (Join-Path $destDir $file.Name)

        if (-not $Apply) {
            Write-Output ("[PREVIEW] MOVE '{0}' -> '{1}'" -f $file.FullName, $destPath)
            $moved++
            continue
        }

        Ensure-Dir -PathValue $destDir
        Move-Item -Path $file.FullName -Destination $destPath -Force
        Write-Output ("Moved '{0}' -> '{1}'" -f $file.Name, $destPath)
        $moved++
    }
}

Write-Output ("Done. Planned/Moved: {0} | Apply: {1}" -f $moved, $Apply.IsPresent)
