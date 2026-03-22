param(
    [string]$CompareRef = "",
    [switch]$IncludeStatus
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$lines = [System.Collections.Generic.List[string]]::new()

function Add-Line {
    param([string]$Text)
    $lines.Add($Text) | Out-Null
}

Add-Line ('# Change Scope')
Add-Line ('')
Add-Line ('Generated: {0}' -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
Add-Line ('')

if ($CompareRef) {
    Add-Line ('Compare ref: `{0}`' -f $CompareRef)
    Add-Line ('')
    $compareSpec = '{0}...HEAD' -f $CompareRef
    $diffLines = git -C $repoRoot diff --name-status $compareSpec 2>$null
} else {
    Add-Line ('Scope: working tree')
    Add-Line ('')
    $diffLines = git -C $repoRoot status --short 2>$null
}

$normalizedLines = @()
foreach ($line in $diffLines) {
    if (-not [string]::IsNullOrWhiteSpace($line)) {
        $normalizedLines += $line
    }
}

if (-not $normalizedLines) {
    Add-Line ('No changes detected.')
    Write-Output ($lines -join [Environment]::NewLine)
    exit 0
}

Add-Line ('## Raw entries')
Add-Line ('')
foreach ($line in $normalizedLines) {
    Add-Line ('- {0}' -f $line)
}
Add-Line ('')

$groups = @{}
foreach ($line in $normalizedLines) {
    $path = ($line -replace '^[^A-Za-z0-9._\\/-]+', '').Trim()
    if ($path -match ' -> ') {
        $path = ($path -split ' -> ')[-1]
    }
    if (-not $path) {
        continue
    }
    $topLevel = ($path -replace '\\', '/') -split '/' | Select-Object -First 1
    if (-not $groups.ContainsKey($topLevel)) {
        $groups[$topLevel] = [System.Collections.Generic.List[string]]::new()
    }
    $groups[$topLevel].Add($path.Replace('\', '/')) | Out-Null
}

Add-Line ('## Grouped by root')
Add-Line ('')
foreach ($key in ($groups.Keys | Sort-Object)) {
    Add-Line ('- `{0}`: {1} file(s)' -f $key, $groups[$key].Count)
}

if ($IncludeStatus) {
    Add-Line ('')
    Add-Line ('## Branch')
    Add-Line ('')
    $branchStatus = git -C $repoRoot status --short --branch 2>$null
    foreach ($line in $branchStatus) {
        Add-Line ('- {0}' -f $line)
    }
}

Write-Output ($lines -join [Environment]::NewLine)
