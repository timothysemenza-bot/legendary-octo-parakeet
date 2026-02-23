param(
    [ValidateSet("aircall","aircall-workspace","ringcentral","ringcentral-phone")]
    [string]$Provider = "aircall-workspace"
)

$ErrorActionPreference = "Stop"

$packageMap = @{
    "aircall" = "Aircall.Aircall"
    "aircall-workspace" = "Aircall.AircallWorkspace"
    "ringcentral" = "RingCentral.RingCentral"
    "ringcentral-phone" = "RingCentral.RingCentralPhone"
}

$pkg = $packageMap[$Provider]
if ([string]::IsNullOrWhiteSpace($pkg)) { throw "Unsupported provider: $Provider" }

Write-Output ("Installing {0} ({1})..." -f $Provider, $pkg)
winget install --id $pkg --source winget --accept-package-agreements --accept-source-agreements

Write-Output ""
Write-Output "Install attempt complete."
Write-Output "Next steps:"
Write-Output "1) Sign into the dialer app."
Write-Output "2) Set it as default handler for tel: links (Windows Default Apps)."
Write-Output "3) Run run-next-call.ps1 to launch calls in sequence."
