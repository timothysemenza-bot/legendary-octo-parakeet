param(
    [Parameter(Mandatory=$true)][string]$OrgName,
    [Parameter(Mandatory=$true)][string]$Values,
    [Parameter(Mandatory=$true)][string]$Audience,
    [Parameter(Mandatory=$true)][string]$Goals,
    [string]$OutputPath = ".\creative-brief.md"
)

$ErrorActionPreference = "Stop"

function Pick-Archetypes {
    param([string]$ValueText, [string]$AudienceText)

    $v = $ValueText.ToLowerInvariant()
    $a = $AudienceText.ToLowerInvariant()

    $primary = "Trusted Steward"
    $support = "Strategic Mentor"

    if ($v -match "performance|coaching|leadership|execution") {
        $primary = "Strategic Mentor"
        $support = "Trusted Steward"
    }

    if ($a -match "member|network|community|association") {
        $support = "Community Catalyst"
    }

    if ($a -match "executive|board|donor|investor") {
        $support = "Premium Operator"
    }

    return @{ Primary = $primary; Support = $support }
}

$picked = Pick-Archetypes -ValueText $Values -AudienceText $Audience
$date = (Get-Date).ToString("yyyy-MM-dd")

$template = @'
# Creative Brief: {0}

Date: {1}

## 1) Positioning Core
- Values: {2}
- Audience: {3}
- Primary goals: {4}

## 2) Visual Strategy
- Primary archetype: {5}
- Supporting archetype: {6}
- Recommended tone: warm authority, structured clarity, human professionalism

## 3) Typography and Layout
- Headings: expressive editorial serif
- Body/UI: modern geometric sans
- Layout pattern: high-trust hero + proof + program pathways + clear conversion blocks

## 4) UX Priorities
- One clear primary CTA above the fold
- Fast path to events/programs/membership
- Consistent trust cues: leadership credibility, outcomes, testimonials
- Mobile-first readability and action flow

## 5) Creative Cloud Deliverables
- Photoshop: unified image grade preset + web exports
- Illustrator: icon set + SVG sprite
- After Effects/Premiere: short muted hero loops
- After Effects (Bodymovin): 2-3 lightweight Lottie loops

## 6) Asset List (Production)
- Hero still + hero loop
- Program section images (3)
- Member portraits (2)
- Portal hero still + loop
- Icon sprite (`icons.svg`)
- Lottie files (`learning-pulse.json`, `network-flow.json`, `portal-engagement.json`)

## 7) Review Questions
1. Does the design feel consistent with leadership voice and values?
2. Does a first-time visitor immediately know what to do next?
3. Do visuals feel authentic to the audience rather than generic stock?
'@

$brief = $template -f $OrgName, $date, $Values, $Audience, $Goals, $picked.Primary, $picked.Support

Set-Content -Path $OutputPath -Value $brief -Encoding UTF8
Write-Output ("Created creative brief: {0}" -f (Resolve-Path $OutputPath))
