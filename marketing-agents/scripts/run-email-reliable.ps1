param(
    [string]$FromUserPrincipalName = "",
    [string]$BusinessStart = "09:00",
    [string]$BusinessEnd = "17:00",
    [bool]$WeekdaysOnly = $true,
    [int]$MaxAttempts = 3,
    [int]$RetryDelaySeconds = 4,
    [switch]$IgnoreBusinessHours
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($env:GRAPH_ACCESS_TOKEN)) {
    throw "GRAPH_ACCESS_TOKEN is not set. Set token in environment before running."
}

$argsList = @(
    "-ExecutionPolicy", "Bypass",
    "-File", ".\marketing-agents\scripts\send-outlook-email-batch-graph.ps1",
    "-GraphAccessToken", $env:GRAPH_ACCESS_TOKEN,
    "-FromUserPrincipalName", $FromUserPrincipalName,
    "-BusinessStart", $BusinessStart,
    "-BusinessEnd", $BusinessEnd,
    "-WeekdaysOnly", ([int]$WeekdaysOnly),
    "-MaxAttempts", $MaxAttempts,
    "-RetryDelaySeconds", $RetryDelaySeconds
)
if ($IgnoreBusinessHours) {
    $argsList += "-IgnoreBusinessHours"
}

& powershell @argsList
