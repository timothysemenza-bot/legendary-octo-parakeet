param(
    [string]$SmtpHost = "smtp-mail.outlook.com",
    [int]$SmtpPort = 587,
    [string]$Username = "",
    [string]$FromAddress = "",
    [switch]$IgnoreBusinessHours
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Username)) {
    $Username = Read-Host "Enter your Microsoft email address (example: you@outlook.com)"
}
if ([string]::IsNullOrWhiteSpace($FromAddress)) {
    $FromAddress = $Username
}

Write-Output "Enter your Microsoft app password when prompted."
$securePwd = Read-Host "App password" -AsSecureString
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePwd)
try {
    $plainPwd = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
}
finally {
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}

$argsList = @(
    "-ExecutionPolicy", "Bypass",
    "-File", ".\marketing-agents\scripts\send-email-batch-smtp.ps1",
    "-SmtpHost", $SmtpHost,
    "-SmtpPort", $SmtpPort,
    "-UseSsl", 1,
    "-SmtpUsername", $Username,
    "-SmtpPassword", $plainPwd,
    "-FromAddress", $FromAddress
)
if ($IgnoreBusinessHours) {
    $argsList += "-IgnoreBusinessHours"
}

& powershell @argsList
