param(
    [string]$Title = "Boss Key",
    [string]$Subtitle = "Business Development Acceleration",
    [string]$Accent = "#C5162E",
    [string]$BgStart = "#070B16",
    [string]$BgEnd = "#101A2D",
    [string]$TemplatePath = "marketing-agents/templates/linkedin-banner-template.svg",
    [string]$OutputPath = "boss-key-website/assets/logos/linkedin/boss-key-linkedin-banner-generated.svg",
    [switch]$Open
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $TemplatePath)) {
    throw "Template not found: $TemplatePath"
}

function Escape-XmlText {
    param([string]$Value)
    if ($null -eq $Value) { return "" }
    return [System.Security.SecurityElement]::Escape($Value)
}

$svg = Get-Content -Path $TemplatePath -Raw
$svg = $svg.Replace("__TITLE__", (Escape-XmlText $Title))
$svg = $svg.Replace("__SUBTITLE__", (Escape-XmlText $Subtitle))
$svg = $svg.Replace("__ACCENT__", $Accent)
$svg = $svg.Replace("__BG_START__", $BgStart)
$svg = $svg.Replace("__BG_END__", $BgEnd)

$outDir = Split-Path -Parent $OutputPath
if (-not [string]::IsNullOrWhiteSpace($outDir) -and -not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
}

Set-Content -Path $OutputPath -Value $svg -Encoding UTF8
Write-Output "Generated: $OutputPath"

if ($Open) {
    Start-Process $OutputPath | Out-Null
}
