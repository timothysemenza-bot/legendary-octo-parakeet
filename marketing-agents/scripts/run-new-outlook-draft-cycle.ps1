param(
    [string]$TenantId = "consumers",
    [string]$ClientId = "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
    [string]$FromUserPrincipalName = "",
    [switch]$ApplyReviewDecisions,
    [switch]$IgnoreBusinessHours
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
Set-Location $root

if ($ApplyReviewDecisions) {
    Write-Output "Applying review decisions..."
    powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\apply-email-review-decisions.ps1
}

Write-Output "Authenticating to Microsoft Graph (device code)..."
$token = powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\get-graph-token-devicecode.ps1 -TenantId $TenantId -ClientId $ClientId -EmitOnlyToken
$token = ($token | Select-Object -Last 1).Trim()
if ([string]::IsNullOrWhiteSpace($token)) { throw "No Graph token returned." }

Write-Output "Creating New Outlook drafts from approved queue items..."
$args = @(
    "-ExecutionPolicy","Bypass",
    "-File",".\marketing-agents\scripts\send-outlook-email-batch-graph.ps1",
    "-GraphAccessToken",$token,
    "-WeekdaysOnly","true",
    "-ForceDraft"
)
if (-not [string]::IsNullOrWhiteSpace($FromUserPrincipalName)) {
    $args += @("-FromUserPrincipalName",$FromUserPrincipalName)
}
if ($IgnoreBusinessHours) { $args += "-IgnoreBusinessHours" }

powershell @args
