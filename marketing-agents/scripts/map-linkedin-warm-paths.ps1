param(
    [string]$TargetsFile = "marketing-agents/data/public_recompete_targets_burlco.csv",
    [string]$LinkedInConnectionsFile = "marketing-agents/data/linkedin_connections.csv",
    [string]$OutputCsv = "marketing-agents/data/linkedin_warm_paths.csv",
    [string]$OutputBrief = "marketing-agents/briefs/generated/public-capture/linkedin-warm-paths.md"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $TargetsFile)) { throw "Missing file: $TargetsFile" }
if (-not (Test-Path $LinkedInConnectionsFile)) { throw "Missing file: $LinkedInConnectionsFile" }

function Normalize-Text([string]$value) {
    if ([string]::IsNullOrWhiteSpace($value)) { return "" }
    return (($value -replace "[^A-Za-z0-9 ]", " ") -replace "\s+", " ").Trim().ToLowerInvariant()
}

function Get-FirstAvailableValue([object]$row, [string[]]$names) {
    foreach ($n in $names) {
        $prop = $row.PSObject.Properties[$n]
        if ($null -ne $prop -and -not [string]::IsNullOrWhiteSpace([string]$prop.Value)) {
            return [string]$prop.Value
        }
    }
    return ""
}

$targets = @(Import-Csv -Path $TargetsFile) | Where-Object { $_.pursuit_decision -in @("pursue_now", "watchlist_capacity") }
$connectionsRaw = @(Import-Csv -Path $LinkedInConnectionsFile)

if ($connectionsRaw.Count -eq 0) {
    throw "LinkedIn connections file has no rows: $LinkedInConnectionsFile"
}

$connections = foreach ($c in $connectionsRaw) {
    $first = Get-FirstAvailableValue -row $c -names @("First Name", "FirstName", "first_name")
    $last = Get-FirstAvailableValue -row $c -names @("Last Name", "LastName", "last_name")
    $company = Get-FirstAvailableValue -row $c -names @("Company", "Company Name", "company", "company_name")
    $position = Get-FirstAvailableValue -row $c -names @("Position", "Title", "Headline", "position", "headline")
    $email = Get-FirstAvailableValue -row $c -names @("Email Address", "Email", "email")
    $connectedOn = Get-FirstAvailableValue -row $c -names @("Connected On", "connected_on", "Connected")
    $profileUrl = Get-FirstAvailableValue -row $c -names @("Profile URL", "Public Profile URL", "profile_url")

    $fullName = (($first + " " + $last) -replace "\s+", " ").Trim()
    [pscustomobject]@{
        full_name = $fullName
        company = $company
        position = $position
        email = $email
        connected_on = $connectedOn
        profile_url = $profileUrl
        full_name_norm = Normalize-Text $fullName
        company_norm = Normalize-Text $company
        position_norm = Normalize-Text $position
    }
}

$results = @()
foreach ($t in $targets) {
    $entityNorm = Normalize-Text ([string]$t.entity_name)
    $officeNorm = Normalize-Text ([string]$t.office)
    $contactNorm = Normalize-Text ([string]$t.contact_name)

    foreach ($c in $connections) {
        $orgMatch = $false
        $roleMatch = $false
        $nameMatch = $false

        if (-not [string]::IsNullOrWhiteSpace($entityNorm) -and -not [string]::IsNullOrWhiteSpace($c.company_norm)) {
            if ($c.company_norm.Contains($entityNorm) -or $entityNorm.Contains($c.company_norm)) {
                $orgMatch = $true
            }
        }

        if (-not [string]::IsNullOrWhiteSpace($officeNorm) -and -not [string]::IsNullOrWhiteSpace($c.position_norm)) {
            if ($c.position_norm.Contains("purchas") -or $c.position_norm.Contains("clerk") -or $c.position_norm.Contains("administrator") -or $c.position_norm.Contains("procurement") -or $c.position_norm.Contains("business admin")) {
                $roleMatch = $true
            }
        }

        if (-not [string]::IsNullOrWhiteSpace($contactNorm) -and -not [string]::IsNullOrWhiteSpace($c.full_name_norm)) {
            if ($c.full_name_norm -eq $contactNorm) {
                $nameMatch = $true
            }
        }

        if (-not ($orgMatch -or $roleMatch -or $nameMatch)) { continue }

        $score = 0
        if ($nameMatch) { $score += 60 }
        if ($orgMatch) { $score += 30 }
        if ($roleMatch) { $score += 20 }
        if ($score -gt 100) { $score = 100 }

        $pathType = if ($nameMatch) {
            "direct-name-match"
        } elseif ($orgMatch -and $roleMatch) {
            "org-and-role-match"
        } elseif ($orgMatch) {
            "org-match"
        } else {
            "role-match"
        }

        $results += [pscustomobject]@{
            target_id = [string]$t.target_id
            entity_name = [string]$t.entity_name
            office = [string]$t.office
            pursuit_decision = [string]$t.pursuit_decision
            contact_name = [string]$t.contact_name
            linkedin_connection = [string]$c.full_name
            linkedin_company = [string]$c.company
            linkedin_position = [string]$c.position
            connected_on = [string]$c.connected_on
            profile_url = [string]$c.profile_url
            warm_path_type = $pathType
            warm_path_score = "$score"
            intro_request = ("Ask {0} for a warm intro to {1} ({2}) at {3}." -f [string]$c.full_name, [string]$t.contact_name, [string]$t.office, [string]$t.entity_name)
        }
    }
}

$results = @($results | Sort-Object @{Expression = { [int]$_.warm_path_score }; Descending = $true}, entity_name, linkedin_connection)
$results | Export-Csv -Path $OutputCsv -NoTypeInformation

$lines = @()
$lines += "# LinkedIn Warm Path Map"
$lines += ""
$lines += "Targets scanned: $($targets.Count)"
$lines += "Warm-path rows found: $($results.Count)"
$lines += ""

if ($results.Count -eq 0) {
    $lines += "_No warm-path matches found from the current connections export._"
    $lines += ""
    $lines += "Next steps:"
    $lines += "1. Add more local municipal and county contacts on LinkedIn."
    $lines += "2. Re-export LinkedIn connections and rerun this script."
} else {
    $top = $results | Select-Object -First 25
    $lines += "## Top Warm Paths"
    foreach ($r in $top) {
        $lines += ("- {0} | {1} | {2} ({3}) | score {4} | {5}" -f $r.entity_name, $r.office, $r.linkedin_connection, $r.linkedin_company, $r.warm_path_score, $r.warm_path_type)
    }
}

$briefDir = Split-Path -Parent $OutputBrief
if (-not (Test-Path $briefDir)) { New-Item -Path $briefDir -ItemType Directory -Force | Out-Null }
$lines -join [Environment]::NewLine | Set-Content -Path $OutputBrief -Encoding UTF8

Write-Output ("Warm path mapping complete. Rows: {0}" -f $results.Count)
Write-Output ("CSV: {0}" -f $OutputCsv)
Write-Output ("Brief: {0}" -f $OutputBrief)
