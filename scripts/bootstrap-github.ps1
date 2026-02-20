param(
    [Parameter(Mandatory = $true)]
    [string]$GitHubOwnerRepo,

    [string]$Branch = 'main',
    [string]$CommitMessage = 'Initial proposal microsite implementation'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-GitExecutable {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        return (Get-Command git).Source
    }

    $candidates = @(
        "$env:ProgramFiles\Git\cmd\git.exe",
        "$env:ProgramFiles\Git\bin\git.exe",
        "${env:ProgramFiles(x86)}\Git\cmd\git.exe",
        "${env:ProgramFiles(x86)}\Git\bin\git.exe",
        "$env:LocalAppData\Programs\Git\cmd\git.exe",
        "$env:LocalAppData\Programs\Git\bin\git.exe"
    ) | Select-Object -Unique

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Ensure-GitPath {
    $git = Get-GitExecutable
    if (-not $git) {
        return $null
    }

    $gitRoot = Split-Path -Path $git -Parent
    if (-not ($env:Path -split ';' | Where-Object { $_ -ieq $gitRoot })) {
        $env:Path = "$gitRoot;$env:Path"
    }

    if (Test-Path $git) {
        return $git
    }

    return $null
}

function TryPersistGitPath {
    $git = Get-GitExecutable
    if (-not $git) {
        return
    }

    $gitRoot = Split-Path -Path $git -Parent
    try {
        $current = [Environment]::GetEnvironmentVariable('Path', 'User')
        if (-not ($current -split ';' | Where-Object { $_ -ieq $gitRoot })) {
            $next = @($gitRoot) + ($current -split ';' | Where-Object { $_ -and $_ -ne $gitRoot })
            [Environment]::SetEnvironmentVariable('Path', ($next -join ';'), 'User')
            Write-Host "Persisted Git path for future shells: $gitRoot"
        }
    } catch {
        Write-Host "Could not persist Path due environment permissions. Current shell was updated for this session."
    }
}

$gitExe = Ensure-GitPath
if (-not $gitExe) {
    Write-Host "Git not found. Install it first, then re-run this script."
    Write-Host 'Example: winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements'
    exit 1
}

Write-Host "Using Git at: $gitExe"
TryPersistGitPath

function Invoke-Git {
    param([string[]]$Arguments)
    & $gitExe @Arguments
}

if (-not (Test-Path '.git')) {
    Write-Host 'Initializing git repository...'
    Invoke-Git @('init') | Out-Null
    Invoke-Git @('branch', '-M', $Branch)
}

Write-Host 'Adding files...'
Invoke-Git @('add', '.') | Out-Null

Write-Host 'Creating initial commit...'
try {
    Invoke-Git @('commit', '-m', $CommitMessage) | Out-Null
} catch {
    Write-Host 'Commit skipped (already committed or no changes). Continuing...'
}

Write-Host 'Configuring GitHub remote...'
$remoteUrl = "https://github.com/$GitHubOwnerRepo.git"
try {
    $remoteNames = Invoke-Git @('remote')
    if ($remoteNames -contains 'origin') {
        Invoke-Git @('remote', 'set-url', 'origin', $remoteUrl)
    } else {
        Invoke-Git @('remote', 'add', 'origin', $remoteUrl)
    }
} catch {
    Write-Host 'Could not configure remote. Check permissions and authentication.'
    throw
}

Write-Host "Pushing to origin/$Branch..."
Invoke-Git @('push', '-u', 'origin', $Branch)

Write-Host 'Done.'
Write-Host 'Next: clone elsewhere and run npm install; copy .env.example to .env, then npm start.'
