param(
    [int]$Depth = 2,
    [string]$OutputPath = ""
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$lines = [System.Collections.Generic.List[string]]::new()

function Add-Line {
    param([string]$Text)
    $lines.Add($Text) | Out-Null
}

Add-Line ('# Repo Audit Snapshot')
Add-Line ('')
Add-Line ('Generated: {0}' -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
Add-Line ('')

Add-Line ('## Top-level directories')
Add-Line ('')
$topLevelDirectories = Get-ChildItem -Path $repoRoot -Directory |
    Sort-Object Name |
    Select-Object -ExpandProperty Name
foreach ($name in $topLevelDirectories) {
    Add-Line ('- `{0}/`' -f $name)
}
Add-Line ('')

Add-Line ('## Shallow folder tree')
Add-Line ('')
$treeEntries = Get-ChildItem -Path $repoRoot -Directory -Recurse -Depth $Depth |
    Where-Object { $_.FullName -notmatch "\\.git($|\\)" } |
    Sort-Object FullName
foreach ($entry in $treeEntries) {
    $relativePath = $entry.FullName.Substring($repoRoot.Length + 1).Replace("\", "/")
    Add-Line ('- `{0}/`' -f $relativePath)
}
Add-Line ('')

Add-Line ('## AGENTS files')
Add-Line ('')
$agentsFiles = Get-ChildItem -Path $repoRoot -Filter AGENTS.md -File -Recurse |
    Sort-Object FullName
if ($agentsFiles) {
    foreach ($file in $agentsFiles) {
        $relativePath = $file.FullName.Substring($repoRoot.Length + 1).Replace("\", "/")
        Add-Line ('- `{0}`' -f $relativePath)
    }
} else {
    Add-Line ('- None found')
}
Add-Line ('')

Add-Line ('## Repo-local skills')
Add-Line ('')
$skillRoot = Join-Path $repoRoot ".agents/skills"
if (Test-Path $skillRoot) {
    $skillNames = Get-ChildItem -Path $skillRoot -Directory |
        Sort-Object Name |
        Select-Object -ExpandProperty Name
    foreach ($skillName in $skillNames) {
        Add-Line ('- `{0}`' -f $skillName)
    }
} else {
    Add-Line ('- `.agents/skills/` is missing')
}
Add-Line ('')

Add-Line ('## Repo-local custom agents')
Add-Line ('')
$customAgentRoot = Join-Path $repoRoot ".codex/agents"
if (Test-Path $customAgentRoot) {
    $customAgents = Get-ChildItem -Path $customAgentRoot -Filter *.toml -File |
        Sort-Object Name |
        Select-Object -ExpandProperty Name
    foreach ($agent in $customAgents) {
        Add-Line ('- `{0}`' -f $agent)
    }
} else {
    Add-Line ('- `.codex/agents/` is missing')
}
Add-Line ('')

Add-Line ('## Git status')
Add-Line ('')
$gitStatus = git -C $repoRoot status --short --branch 2>$null
if ($LASTEXITCODE -eq 0 -and $gitStatus) {
    foreach ($line in $gitStatus) {
        Add-Line ('- {0}' -f $line)
    }
} else {
    Add-Line ('- Git status unavailable')
}

$content = $lines -join [Environment]::NewLine
if ($OutputPath) {
    Set-Content -Path $OutputPath -Value $content
    Write-Output ("Wrote repo audit snapshot to {0}" -f $OutputPath)
} else {
    Write-Output $content
}
