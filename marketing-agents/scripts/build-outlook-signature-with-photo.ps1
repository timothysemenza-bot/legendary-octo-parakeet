param(
    [string]$PhotoPath = "boss-key-website/assets/timothy-semenza-headshot.jpg",
    [string]$OutputHtml = "marketing-agents/templates/email-signature-boss-key.html",
    [string]$Name = "Timmy Semenza",
    [string]$Title = "Founder, Boss Key LLC",
    [string]$PhoneDisplay = "(203) 521-0311",
    [string]$PhoneLink = "+12035210311",
    [string]$Email = "timmy@bosskeyops.com",
    [string]$Website = "https://bosskeyops.com"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $PhotoPath)) { throw "Photo not found: $PhotoPath" }

$bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $PhotoPath))
$b64 = [Convert]::ToBase64String($bytes)
$photoDataUrl = "data:image/jpeg;base64,$b64"

$logoSvg = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100' fill='none'><rect width='100' height='100' rx='16' fill='#F5F7FB'/><path d='M22 12H78L88 22V78L78 88H22L12 78V22L22 12Z' stroke='#0B1020' stroke-width='5.5' stroke-linejoin='miter'/><path d='M50 30L70 50L50 70L30 50L50 30Z' stroke='#0B1020' stroke-width='5.5' stroke-linejoin='miter'/><path d='M50 12V30' stroke='#0B1020' stroke-width='5.5' stroke-linecap='square'/><circle cx='64' cy='50' r='2.8' fill='#C5162E'/></svg>"
$logoDataUrl = "data:image/svg+xml," + [uri]::EscapeDataString($logoSvg)

$html = @"
<table cellpadding="0" cellspacing="0" style="font-family:'Segoe UI',Arial,Helvetica,sans-serif;color:#111111;">
  <tr>
    <td style="padding-right:12px;vertical-align:top;">
      <img src="$photoDataUrl" alt="$Name" width="56" height="56" style="display:block;border-radius:8px;object-fit:cover;">
    </td>
    <td style="padding-right:12px;vertical-align:top;">
      <img src="$logoDataUrl" alt="Boss Key logo" width="28" height="28" style="display:block;">
    </td>
    <td style="vertical-align:top;">
      <div style="font-size:14px;font-weight:700;">$Name</div>
      <div style="font-size:12px;color:#444444;">$Title</div>
      <div style="font-size:12px; margin-top:4px;">
        <a href="tel:$PhoneLink" style="color:#111111;text-decoration:none;">$PhoneDisplay</a> |
        <a href="mailto:$Email" style="color:#111111;text-decoration:none;">$Email</a>
      </div>
      <div style="font-size:12px;">
        <a href="$Website" style="color:#111111;text-decoration:none;">$Website</a>
      </div>
      <div style="font-size:11px;color:#666666;margin-top:6px;">
        Practical proposal and operations support for local janitorial businesses.
      </div>
    </td>
  </tr>
</table>
"@

$outDir = Split-Path -Parent $OutputHtml
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
$html | Set-Content -Path $OutputHtml -Encoding UTF8

Write-Output "Updated signature with embedded photo: $OutputHtml"
