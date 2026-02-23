param(
    [string]$TenantId = "consumers",
    [string]$ClientId = "04b07795-8ddb-461a-bbee-02f9e1bf7b46",
    [string]$Scope = "https://graph.microsoft.com/Mail.ReadWrite offline_access",
    [switch]$EmitOnlyToken
)

$ErrorActionPreference = "Stop"

$deviceUrl = "https://login.microsoftonline.com/$TenantId/oauth2/v2.0/devicecode"
$tokenUrl = "https://login.microsoftonline.com/$TenantId/oauth2/v2.0/token"

$deviceResp = Invoke-RestMethod -Method Post -Uri $deviceUrl -ContentType "application/x-www-form-urlencoded" -Body @{
    client_id = $ClientId
    scope = $Scope
}

Write-Output ""
Write-Output "Complete authentication:"
Write-Output $deviceResp.message
Write-Output ""

$interval = [int]$deviceResp.interval
$expiresAt = (Get-Date).AddSeconds([int]$deviceResp.expires_in)

while ((Get-Date) -lt $expiresAt) {
    Start-Sleep -Seconds $interval
    try {
        $tokenResp = Invoke-RestMethod -Method Post -Uri $tokenUrl -ContentType "application/x-www-form-urlencoded" -Body @{
            grant_type = "urn:ietf:params:oauth:grant-type:device_code"
            client_id = $ClientId
            device_code = $deviceResp.device_code
        }

        if ($tokenResp.access_token) {
            if ($EmitOnlyToken) {
                Write-Output $tokenResp.access_token
            } else {
                $env:GRAPH_ACCESS_TOKEN = $tokenResp.access_token
                Write-Output "GRAPH_ACCESS_TOKEN set for current PowerShell session."
                Write-Output ("Token expires in ~{0} seconds." -f $tokenResp.expires_in)
            }
            exit 0
        }
    } catch {
        $errMsg = $_.Exception.Message
        $details = ""
        if ($_.ErrorDetails -and $_.ErrorDetails.Message) {
            $details = $_.ErrorDetails.Message
        }
        $raw = ($errMsg + " " + $details).ToLowerInvariant()
        if ($raw -match "authorization_pending" -or $raw -match "slow_down") {
            continue
        }
        throw $_
    }
}

throw "Timed out waiting for device-code authentication."
