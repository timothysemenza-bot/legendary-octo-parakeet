param(
    [string]$PipelineFile = "marketing-agents/data/security_lookalike_campaign_pipeline.csv",
    [string]$OutputFile = "marketing-agents/data/security_lookalike_campaign_pipeline_enriched.csv",
    [int]$TimeoutSec = 12
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $PipelineFile)) { throw "Missing pipeline file: $PipelineFile" }

$rows = @(Import-Csv -Path $PipelineFile)

function Get-DomainFromUrl {
    param([string]$Url)
    if ([string]::IsNullOrWhiteSpace($Url)) { return "" }
    try {
        $u = [uri]$Url
        $hostname = $u.Host.ToLowerInvariant()
        if ($hostname.StartsWith("www.")) { $hostname = $hostname.Substring(4) }
        return $hostname
    } catch {
        return ""
    }
}

function Get-EmailsFromHtml {
    param([string]$Html)
    if ([string]::IsNullOrWhiteSpace($Html)) { return @() }
    $pattern = '(?i)\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b'
    $matches = [regex]::Matches($Html, $pattern)
    $emails = @()
    foreach ($m in $matches) {
        $e = $m.Value.Trim().ToLowerInvariant()
        if ($e -match "example\.com|email\.com|sentry|wixpress|cloudflare|noreply|no-reply") { continue }
        $emails += $e
    }
    return @($emails | Select-Object -Unique)
}

function Score-Email {
    param([string]$Email)
    $e = ($Email | ForEach-Object { $_.ToLowerInvariant() })
    if ($e -match 'proposal|proposals|bd|businessdevelopment|sales|development|capture|rfp|bid') { return 100 }
    if ($e -match 'info|contact|hello|inquiries|enquiries|office') { return 75 }
    return 60
}

function Pick-BestEmail {
    param([string[]]$Emails)
    if ($Emails.Count -eq 0) { return "" }
    $scored = $Emails | ForEach-Object { [pscustomobject]@{ email = $_; score = (Score-Email -Email $_) } }
    return ($scored | Sort-Object -Property @(
        @{ Expression = "score"; Descending = $true },
        @{ Expression = "email"; Descending = $false }
    ) | Select-Object -First 1).email
}

function Try-Fetch {
    param([string]$Url, [int]$TimeoutSec)
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
        return [string]$resp.Content
    } catch {
        return ""
    }
}

$checked = 0
$updated = 0

foreach ($r in $rows) {
    $checked++
    if (-not [string]::IsNullOrWhiteSpace([string]$r.contact_email)) { continue }

    $site = [string]$r.website
    if ([string]::IsNullOrWhiteSpace($site)) { continue }

    $domain = Get-DomainFromUrl -Url $site
    if ([string]::IsNullOrWhiteSpace($domain)) { continue }

    $emails = @()
    $sourcesTried = @()

    $primary = Try-Fetch -Url $site -TimeoutSec $TimeoutSec
    if (-not [string]::IsNullOrWhiteSpace($primary)) {
        $sourcesTried += $site
        $emails += Get-EmailsFromHtml -Html $primary
    }

    foreach ($path in @("/contact", "/contact-us", "/about", "/company/contact")) {
        $url = ("https://" + $domain + $path)
        $html = Try-Fetch -Url $url -TimeoutSec $TimeoutSec
        if (-not [string]::IsNullOrWhiteSpace($html)) {
            $sourcesTried += $url
            $emails += Get-EmailsFromHtml -Html $html
        }
    }

    $emails = @($emails | Select-Object -Unique)
    $best = Pick-BestEmail -Emails $emails

    if ([string]::IsNullOrWhiteSpace($best)) {
        # fallback role-based aliases
        $candidates = @(
            ("sales@" + $domain),
            ("proposals@" + $domain),
            ("bd@" + $domain),
            ("info@" + $domain)
        )
        $best = $candidates[0]
        $r.notes = (([string]$r.notes).Trim() + " | email_enrichment=fallback-guess | email_guess_domain=" + $domain).Trim(" |")
    } else {
        $r.notes = (([string]$r.notes).Trim() + " | email_enrichment=website-found | email_sources=" + (($sourcesTried | Select-Object -First 2) -join ",")).Trim(" |")
    }

    $r.contact_email = $best
    $updated++
}

$rows | Export-Csv -Path $OutputFile -NoTypeInformation
Write-Output ("Enrichment complete. checked={0}, updated={1}, output={2}" -f $checked, $updated, $OutputFile)
