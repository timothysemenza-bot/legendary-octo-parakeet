param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('join', 'event', 'approve', 'homepage', 'homeverify', 'scopepages', 'eventpages', 'palette', 'audit', 'verify')]
  [string]$Flow,

  [ValidateSet('plan', 'apply')]
  [string]$Mode = 'apply',

  [string]$JoinTitle,
  [string]$JoinPath,

  [string]$EventTitle,
  [string]$EventDate,
  [string]$EventTime,
  [string]$EventTimezone,
  [string]$EventDescription,

  [string]$ContactEmail,
  [string]$ApprovalTag,

  [string]$HomepageName,
  [string]$HomepageHeadline,
  [string]$HomepageSubhead,
  [string]$HomepagePrimaryCtaText,
  [string]$HomepagePrimaryCtaLink,
  [string]$HomepageSecondaryCtaText,
  [string]$HomepageSecondaryCtaLink,
  [string]$HomepageDonationLink,

  [switch]$AllowWrites
)

$ErrorActionPreference = 'Stop'

function Set-EnvIfPresent {
  param(
    [string]$Name,
    [string]$Value
  )
  if ($null -ne $Value -and $Value -ne '') {
    [System.Environment]::SetEnvironmentVariable($Name, $Value, 'Process')
  }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
Set-Location $repoRoot

if ($AllowWrites) {
  if ($Mode -eq 'apply') {
    [System.Environment]::SetEnvironmentVariable('ALLOW_KAJABI_WRITES', '1', 'Process')
  }
}
if ($Mode -eq 'plan' -or -not $AllowWrites) {
  [System.Environment]::SetEnvironmentVariable('ALLOW_KAJABI_WRITES', '0', 'Process')
}
[System.Environment]::SetEnvironmentVariable('JWBLNG_RUN_MODE', $Mode, 'Process')

Set-EnvIfPresent -Name 'JWBLNG_JOIN_PAGE_TITLE' -Value $JoinTitle
Set-EnvIfPresent -Name 'JWBLNG_JOIN_PAGE_PATH' -Value $JoinPath

Set-EnvIfPresent -Name 'JWBLNG_EVENT_TITLE' -Value $EventTitle
Set-EnvIfPresent -Name 'JWBLNG_EVENT_DATE' -Value $EventDate
Set-EnvIfPresent -Name 'JWBLNG_EVENT_TIME' -Value $EventTime
Set-EnvIfPresent -Name 'JWBLNG_EVENT_TIMEZONE' -Value $EventTimezone
Set-EnvIfPresent -Name 'JWBLNG_EVENT_DESCRIPTION' -Value $EventDescription

Set-EnvIfPresent -Name 'JWBLNG_CONTACT_EMAIL_FILTER' -Value $ContactEmail
Set-EnvIfPresent -Name 'JWBLNG_APPROVAL_TAG' -Value $ApprovalTag

Set-EnvIfPresent -Name 'JWBLNG_HOMEPAGE_NAME' -Value $HomepageName
Set-EnvIfPresent -Name 'JWBLNG_HOMEPAGE_HEADLINE' -Value $HomepageHeadline
Set-EnvIfPresent -Name 'JWBLNG_HOMEPAGE_SUBHEAD' -Value $HomepageSubhead
Set-EnvIfPresent -Name 'JWBLNG_HOMEPAGE_PRIMARY_CTA_TEXT' -Value $HomepagePrimaryCtaText
Set-EnvIfPresent -Name 'JWBLNG_HOMEPAGE_PRIMARY_CTA_LINK' -Value $HomepagePrimaryCtaLink
Set-EnvIfPresent -Name 'JWBLNG_HOMEPAGE_SECONDARY_CTA_TEXT' -Value $HomepageSecondaryCtaText
Set-EnvIfPresent -Name 'JWBLNG_HOMEPAGE_SECONDARY_CTA_LINK' -Value $HomepageSecondaryCtaLink
Set-EnvIfPresent -Name 'JWBLNG_HOMEPAGE_DONATION_LINK' -Value $HomepageDonationLink

$scriptMap = @{
  join   = 'pw:jwblng:join'
  event  = 'pw:jwblng:event'
  approve = 'pw:jwblng:approve'
  homepage = 'pw:jwblng:homeapply'
  homeverify = 'pw:jwblng:homebuilderqa'
  scopepages = 'pw:jwblng:scopepages'
  eventpages = 'pw:jwblng:eventpagesapply'
  palette = 'pw:jwblng:palette'
  audit  = 'pw:jwblng:audit'
  verify = 'pw:jwblng:verify'
}

$npmScript = $scriptMap[$Flow]
if (-not $npmScript) {
  throw "Unsupported flow: $Flow"
}

Write-Host "[runner] Repo: $repoRoot"
Write-Host "[runner] Flow: $Flow"
Write-Host "[runner] Mode: $Mode"
Write-Host "[runner] ALLOW_KAJABI_WRITES=$([System.Environment]::GetEnvironmentVariable('ALLOW_KAJABI_WRITES', 'Process'))"
if ($Flow -eq 'approve' -and -not [System.Environment]::GetEnvironmentVariable('JWBLNG_CONTACT_EMAIL_FILTER', 'Process')) {
  throw 'Contact flow requires -ContactEmail (or JWBLNG_CONTACT_EMAIL_FILTER in environment).'
}
if ($Mode -eq 'apply' -and @('join', 'event', 'approve', 'homepage', 'scopepages', 'eventpages', 'palette') -contains $Flow -and [System.Environment]::GetEnvironmentVariable('ALLOW_KAJABI_WRITES', 'Process') -ne '1') {
  throw 'Apply mode for write flow requires -AllowWrites.'
}

& npm.cmd run $npmScript
