param(
    [string]$TenantId = "consumers",
    [string]$ClientId = "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
    [string]$FromUserPrincipalName = "",
    [switch]$ForceDraft,
    [switch]$IgnoreBusinessHours
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
Set-Location $root

Write-Output "Authenticating to Microsoft Graph (device code)..."
$token = powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\get-graph-token-devicecode.ps1 `
    -TenantId $TenantId `
    -ClientId $ClientId `
    -EmitOnlyToken
$token = ($token | Select-Object -Last 1).Trim()
if ([string]::IsNullOrWhiteSpace($token)) { throw "No Graph token returned." }

$args = @(
    "-ExecutionPolicy", "Bypass",
    "-File", ".\marketing-agents\scripts\send-outlook-email-batch-graph.ps1",
    "-QueueFile", "marketing-agents/data/security_lookalike_email_outbox_queue.csv",
    "-InteractionFile", "marketing-agents/data/security_lookalike_interaction_log.csv",
    "-PipelineFile", "marketing-agents/data/security_lookalike_campaign_pipeline_enriched.csv",
    "-GraphAccessToken", $token
)

if (-not [string]::IsNullOrWhiteSpace($FromUserPrincipalName)) {
    $args += @("-FromUserPrincipalName", $FromUserPrincipalName)
}
if ($ForceDraft) { $args += "-ForceDraft" }
if ($IgnoreBusinessHours) { $args += "-IgnoreBusinessHours" }

powershell @args
