param(
    [string]$TenantId = "",
    [string]$ClientId = "",
    [string]$FromUserPrincipalName = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($TenantId)) {
    $TenantId = Read-Host "Enter TenantId (Directory ID)"
}
if ([string]::IsNullOrWhiteSpace($ClientId)) {
    $ClientId = Read-Host "Enter ClientId (Application ID)"
}
if ([string]::IsNullOrWhiteSpace($FromUserPrincipalName)) {
    $FromUserPrincipalName = Read-Host "Enter sender email (UPN), e.g. you@yourdomain.com"
}

powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\get-graph-token-devicecode.ps1 `
    -TenantId $TenantId `
    -ClientId $ClientId

powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\run-email-reliable.ps1 `
    -FromUserPrincipalName $FromUserPrincipalName
