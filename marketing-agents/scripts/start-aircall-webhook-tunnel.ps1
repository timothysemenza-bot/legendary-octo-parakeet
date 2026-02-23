param(
    [int]$Port = 3201,
    [string]$EnvFile = "marketing-agents/.env.local",
    [string]$DataDir = "marketing-agents/data",
    [switch]$OpenAircallWebhookPage
)

$ErrorActionPreference = "Stop"

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null }
}

function Get-OrCreateWebhookToken {
    param([string]$EnvPath)
    if (-not (Test-Path $EnvPath)) {
        Set-Content -Path $EnvPath -Value "# Local Operator Console settings" -Encoding UTF8
    }
    $lines = Get-Content -Path $EnvPath
    $existing = $lines | Where-Object { $_ -match '^AIRCALL_WEBHOOK_TOKEN=' } | Select-Object -First 1
    if ($existing) {
        return ($existing -replace '^AIRCALL_WEBHOOK_TOKEN=', '').Trim()
    }
    $bytes = New-Object byte[] 24
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $token = [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+','-').Replace('/','_')
    Add-Content -Path $EnvPath -Value ("AIRCALL_WEBHOOK_TOKEN=" + $token)
    return $token
}

function Resolve-CloudflaredPath {
    $cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $candidates = @(
        "C:\Program Files\cloudflared\cloudflared.exe",
        "C:\Program Files (x86)\cloudflared\cloudflared.exe",
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Cloudflare.cloudflared_*"
    )
    foreach ($c in $candidates) {
        if ($c.Contains("*")) {
            $match = Get-ChildItem -Path $c -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($match) {
                $exe = Join-Path $match.FullName "cloudflared.exe"
                if (Test-Path $exe) { return $exe }
            }
        } elseif (Test-Path $c) {
            return $c
        }
    }
    return ""
}

function Ensure-Cloudflared {
    $existing = Resolve-CloudflaredPath
    if (-not [string]::IsNullOrWhiteSpace($existing)) { return $existing }
    Write-Output "Installing cloudflared..."
    winget install --id Cloudflare.cloudflared --source winget --accept-package-agreements --accept-source-agreements | Out-Null
    $resolved = Resolve-CloudflaredPath
    if ([string]::IsNullOrWhiteSpace($resolved)) {
        throw "cloudflared install did not complete successfully."
    }
    return $resolved
}

function Is-PortListening {
    param([int]$PortNumber)
    try {
        $conn = Get-NetTCPConnection -LocalPort $PortNumber -State Listen -ErrorAction Stop | Select-Object -First 1
        return $null -ne $conn
    } catch {
        return $false
    }
}

Ensure-Dir -Path $DataDir
$logPath = Join-Path $DataDir "cloudflared.log"
$pidPath = Join-Path $DataDir "cloudflared.pid"

$token = Get-OrCreateWebhookToken -EnvPath $EnvFile

# Restart Operator Console so it loads updated env token.
$existingOperator = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($existingOperator) {
    try { Stop-Process -Id $existingOperator.OwningProcess -Force } catch {}
}
Start-Process -FilePath "node.exe" -ArgumentList "marketing-agents/operator-app.js" -WorkingDirectory (Resolve-Path ".").Path -WindowStyle Hidden | Out-Null
Start-Sleep -Seconds 2
if (-not (Is-PortListening -PortNumber $Port)) {
    throw "Operator Console did not start on port $Port."
}

$cloudflaredExe = Ensure-Cloudflared

$reuse = $false
if (Test-Path $pidPath) {
    $oldPid = Get-Content -Path $pidPath -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($oldPid -and (Get-Process -Id $oldPid -ErrorAction SilentlyContinue)) { $reuse = $true }
}

if (-not $reuse) {
    if (Test-Path $logPath) { Remove-Item $logPath -Force }
    $proc = Start-Process -FilePath $cloudflaredExe -ArgumentList @("tunnel","--url","http://localhost:$Port","--no-autoupdate","--logfile",$logPath) -PassThru -WindowStyle Hidden
    Set-Content -Path $pidPath -Value $proc.Id -Encoding UTF8
}

$url = ""
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (-not (Test-Path $logPath)) { continue }
    $content = Get-Content -Path $logPath -Raw -ErrorAction SilentlyContinue
    if (-not $content) { continue }
    $m = [regex]::Match($content, 'https://[a-z0-9\-]+\.trycloudflare\.com')
    if ($m.Success) {
        $url = $m.Value
        break
    }
}

if ([string]::IsNullOrWhiteSpace($url)) {
    throw "Tunnel started but URL was not detected. Check log: $logPath"
}

$webhookUrl = "$url/api/aircall-webhook"
Write-Output ""
Write-Output "Tunnel ready."
Write-Output ("Public URL: " + $url)
Write-Output ("Webhook URL: " + $webhookUrl)
Write-Output "Aircall header:"
Write-Output (" - x-webhook-token: " + $token)
Write-Output ""
Write-Output ("Token stored in: " + $EnvFile)
Write-Output ("Tunnel log: " + $logPath)

if ($OpenAircallWebhookPage) {
    Start-Process "https://dashboard.aircall.io/" | Out-Null
}
