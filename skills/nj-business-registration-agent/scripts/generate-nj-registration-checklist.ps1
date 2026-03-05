param(
    [Parameter(Mandatory=$true)][string]$BusinessName,
    [Parameter(Mandatory=$true)]
    [ValidateSet("llc","corporation","nonprofit","sole-proprietor")]
    [string]$EntityType,
    [switch]$IsForeignEntity,
    [switch]$HasEmployees,
    [switch]$SellsTaxableGoodsOrServices,
    [string]$OutputPath = ".\nj-registration-checklist.md"
)

$ErrorActionPreference = "Stop"

$today = (Get-Date).ToString("yyyy-MM-dd")
$pathType = if ($IsForeignEntity) { "foreign qualification" } elseif ($EntityType -eq "sole-proprietor") { "sole proprietor" } else { "domestic formation" }

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# NJ Business Registration Checklist - $BusinessName")
$lines.Add("")
$lines.Add("Date: $today")
$lines.Add("Entity type: $EntityType")
$lines.Add("Path: $pathType")
$lines.Add("")
$lines.Add("## 1) Intake and Pre-Filing")
$lines.Add("- [ ] Confirm legal business name and one backup name.")
$lines.Add("- [ ] Confirm principal address, mailing address, and registered agent details.")
$lines.Add("- [ ] Confirm owner/manager information and responsible tax contact.")
$lines.Add("- [ ] Confirm NAICS code and planned start date.")

if ($IsForeignEntity) {
    $lines.Add("")
    $lines.Add("## 2) Foreign Qualification")
    $lines.Add("- [ ] Obtain certificate of good standing from home state.")
    $lines.Add("- [ ] Prepare NJ foreign qualification filing.")
    $lines.Add("- [ ] Save filing receipt and NJ business ID.")
} elseif ($EntityType -eq "sole-proprietor") {
    $lines.Add("")
    $lines.Add("## 2) Sole Proprietor Path")
    $lines.Add("- [ ] Confirm whether a trade name (DBA) filing is needed locally.")
    $lines.Add("- [ ] Confirm any local business license requirements.")
} else {
    $lines.Add("")
    $lines.Add("## 2) Formation Filing")
    $lines.Add("- [ ] Confirm NJ name availability.")
    $lines.Add("- [ ] File NJ $EntityType formation with DORES.")
    $lines.Add("- [ ] Save filing receipt and NJ business ID.")
}

$lines.Add("")
$lines.Add("## 3) Tax Registration (NJ-REG)")
$lines.Add("- [ ] Complete NJ-REG for required tax accounts.")

if ($HasEmployees) {
    $lines.Add("- [ ] Register as an NJ employer and set payroll tax process.")
}

if ($SellsTaxableGoodsOrServices) {
    $lines.Add("- [ ] Register for NJ sales tax and prepare collection/remittance process.")
}

$lines.Add("")
$lines.Add("## 4) Federal and Banking")
$lines.Add("- [ ] Obtain EIN if not already assigned.")
$lines.Add("- [ ] Open business bank account after state/EIN documents are ready.")

$lines.Add("")
$lines.Add("## 5) Compliance Setup")
$lines.Add("- [ ] Create annual report reminder (month of formation/qualification anniversary).")
$lines.Add("- [ ] Store copies of formation, NJ-REG, EIN, and agent records.")
$lines.Add("- [ ] Confirm local or industry-specific licensing cadence.")

$lines.Add("")
$lines.Add("## Notes")
$lines.Add("- Verify current filing requirements and fees on official NJ and IRS websites before submission.")
$lines.Add("- This checklist is operational guidance, not legal or tax advice.")

$content = [string]::Join([Environment]::NewLine, $lines)
Set-Content -Path $OutputPath -Value $content -Encoding UTF8

$resolved = (Resolve-Path $OutputPath).Path
Write-Output "Created NJ registration checklist: $resolved"
