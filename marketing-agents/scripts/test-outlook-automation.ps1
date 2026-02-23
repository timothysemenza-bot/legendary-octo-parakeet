param()

$ErrorActionPreference = "Continue"

Write-Output "Testing Outlook automation prerequisites..."

try {
    $outlook = New-Object -ComObject Outlook.Application
    Write-Output "COM: OK (Outlook.Application created)"
    try {
        $session = $outlook.Session
        $count = @($session.Accounts).Count
        Write-Output ("Session: OK (accounts detected: {0})" -f $count)
    } catch {
        Write-Output "Session: Unable to read Outlook session/accounts."
    }
} catch {
    Write-Output "COM: FAILED (Outlook COM unavailable)."
    Write-Output "Likely causes:"
    Write-Output "- New Outlook is active (COM automation not supported)."
    Write-Output "- Classic Outlook is not installed or no profile is configured."
    Write-Output "- Outlook is not signed in with a local profile."
    exit 1
}

Write-Output "Result: Outlook automation path is available."
