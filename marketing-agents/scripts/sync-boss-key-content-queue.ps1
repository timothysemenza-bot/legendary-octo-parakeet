param(
    [string]$SourcesFile = "marketing-agents/data/boss_key_content_sources.csv",
    [string]$QueueFile = "marketing-agents/data/boss_key_content_queue.csv",
    [string]$ArticleDir = "marketing-agents/briefs/generated/boss-key-growth-os/articles",
    [string]$LinkedInDir = "marketing-agents/briefs/generated/boss-key-growth-os/linkedin",
    [switch]$RefreshExisting
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "boss-key-growth-os-helpers.ps1")

$queuePropertyOrder = @(
    "content_id",
    "created_date",
    "cadence_type",
    "source_id",
    "source_type",
    "source_path",
    "source_title",
    "title",
    "slug",
    "summary",
    "article_draft_path",
    "article_output_path",
    "company_linkedin_draft_path",
    "personal_linkedin_draft_path",
    "scheduled_publish_date",
    "owner_decision",
    "review_status",
    "website_status",
    "rss_status",
    "linkedin_company_status",
    "linkedin_personal_status",
    "published_date",
    "notes"
)

function Get-BossKeyArticleDraftText {
    param(
        [string]$Title,
        [string]$Summary,
        [pscustomobject]$Packet
    )

    $linkedInLines = @()
    if ($null -ne $Packet -and -not [string]::IsNullOrWhiteSpace($Packet.'LinkedIn Post')) {
        $linkedInLines = @(
            ($Packet.'LinkedIn Post' -split "`r?`n") |
                Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
                Select-Object -First 6
        )
    }

    $observations = @()
    foreach ($line in $linkedInLines) {
        $trimmed = ([string]$line).Trim()
        if ($trimmed -match '^[0-9]+\)') {
            $observations += $trimmed.Substring(2).Trim()
            continue
        }
        if ($trimmed -match '^Comment "') {
            continue
        }
        if ($trimmed -match 'Owners,') {
            continue
        }
        $observations += $trimmed
    }
    $observations = @($observations | Select-Object -Unique | Select-Object -First 4)

    $operatorNotes = if ($null -eq $Packet) { "" } else { [string]$Packet.'Operator Notes' }
    $outline = if ($null -eq $Packet) { "" } else { [string]$Packet.'Document / Carousel Outline' }

    $lines = @()
    $lines += "# $Title"
    $lines += ""
    $lines += "## Summary"
    $lines += $Summary
    $lines += ""
    $lines += "## Why this matters"
    $lines += $(if ($null -eq $Packet -or [string]::IsNullOrWhiteSpace($Packet.'Source Angle')) {
        "This draft is waiting for owner review before it becomes a published Boss Key insight."
    } else {
        [string]$Packet.'Source Angle'
    })
    $lines += ""
    $lines += "## What I keep seeing"
    if ($observations.Count -eq 0) {
        $lines += "- Tighten the signal before publishing."
        $lines += "- Add one operational observation from live work."
        $lines += "- Keep the CTA practical and review-first."
    } else {
        foreach ($item in $observations) {
            $lines += "- $item"
        }
    }
    $lines += ""
    $lines += "## What to do next"
    $lines += "- Separate owner judgment from day-to-day proposal coordination."
    $lines += "- Put one accountable operator on the handoff between capture, pricing, staffing, and compliance."
    $lines += "- Use a short diagnostic or checklist before the next rebid or proposal cycle."
    $lines += ""
    $lines += "## Draft CTA"
    $lines += "If this is your situation, message me and I will tell you what I would fix first."
    $lines += ""

    if (-not [string]::IsNullOrWhiteSpace($outline)) {
        $lines += "## Supporting outline"
        $lines += $outline.Trim()
        $lines += ""
    }

    if (-not [string]::IsNullOrWhiteSpace($operatorNotes)) {
        $lines += "## Operator notes"
        $lines += $operatorNotes.Trim()
        $lines += ""
    }

    $lines += "## Review status"
    $lines += "Pending owner approval before publish/send."
    return ($lines -join "`n").Trim() + "`n"
}

function Get-BossKeyLinkedInDraftText {
    param(
        [string]$Title,
        [string]$AudienceLabel,
        [pscustomobject]$Packet
    )

    $post = if ($null -eq $Packet) { "" } else { [string]$Packet.'LinkedIn Post' }
    $caption = if ($null -eq $Packet) { "" } else { [string]$Packet.'Short Video Caption' }
    $replies = if ($null -eq $Packet) { "" } else { [string]$Packet.'Comment Reply Options' }
    $dmDrafts = if ($null -eq $Packet) { "" } else { [string]$Packet.'DM Follow-Up Drafts' }

    $lines = @()
    $lines += "# $Title"
    $lines += ""
    $lines += "Audience: $AudienceLabel"
    $lines += "Status: Pending owner approval before publish/send."
    $lines += ""
    $lines += "## Primary draft"
    $lines += $(if ([string]::IsNullOrWhiteSpace($post)) { "Draft pending." } else { $post.Trim() })
    $lines += ""
    $lines += "## Short video caption"
    $lines += $(if ([string]::IsNullOrWhiteSpace($caption)) { "No caption drafted yet." } else { $caption.Trim() })
    $lines += ""
    if (-not [string]::IsNullOrWhiteSpace($replies)) {
        $lines += "## Comment reply options"
        $lines += $replies.Trim()
        $lines += ""
    }
    if (-not [string]::IsNullOrWhiteSpace($dmDrafts)) {
        $lines += "## Follow-up DM drafts"
        $lines += $dmDrafts.Trim()
        $lines += ""
    }
    return ($lines -join "`n").Trim() + "`n"
}

function Convert-BossKeyAsciiText {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return ""
    }

    $clean = [string]$Value
    $clean = $clean.Replace(([string][char]0x2014), " - ")
    $clean = $clean.Replace(([string][char]0x2013), "-")
    $clean = $clean.Replace(([string][char]0x2018), "'")
    $clean = $clean.Replace(([string][char]0x2019), "'")
    $clean = $clean.Replace(([string][char]0x201C), '"')
    $clean = $clean.Replace(([string][char]0x201D), '"')
    $clean = $clean -replace '[^\x00-\x7F]', ''
    return $clean
}

$sources = Import-BossKeyCsv -PathValue $SourcesFile
$queue = New-Object System.Collections.Generic.List[object]
foreach ($row in (Import-BossKeyCsv -PathValue $QueueFile)) {
    $queue.Add($row)
}

$articleDirResolved = Resolve-BossKeyGrowthPath $ArticleDir
$linkedinDirResolved = Resolve-BossKeyGrowthPath $LinkedInDir
Ensure-BossKeyGrowthDirectory -PathValue $articleDirResolved
Ensure-BossKeyGrowthDirectory -PathValue $linkedinDirResolved

$added = 0
$updated = 0

foreach ($source in $sources) {
    $existing = $queue | Where-Object { $_.source_id -eq $source.source_id } | Select-Object -First 1
    if ($null -ne $existing -and -not $RefreshExisting) {
        continue
    }

    $title = if ([string]::IsNullOrWhiteSpace($source.article_title)) { [string]$source.source_title } else { [string]$source.article_title }
    $slug = if ([string]::IsNullOrWhiteSpace($source.slug)) { ConvertTo-BossKeySlug -Value $title } else { [string]$source.slug }
    $contentId = if ($null -ne $existing) { [string]$existing.content_id } else { New-BossKeyId -Prefix "content" -Seed $slug }
    $publishMode = ([string]$source.publish_mode).Trim().ToLowerInvariant()
    $articleOutputPath = if ([string]::IsNullOrWhiteSpace($source.article_output_path)) {
        "boss-key-website/insights/{0}.html" -f $slug
    } else {
        [string]$source.article_output_path
    }

    $packetPath = ""
    if (-not [string]::IsNullOrWhiteSpace($source.operator_packet_path)) {
        $packetPath = [string]$source.operator_packet_path
    } elseif ((([string]$source.source_path).ToLowerInvariant()).EndsWith(".md")) {
        $packetPath = [string]$source.source_path
    }

    $packet = $null
    if (-not [string]::IsNullOrWhiteSpace($packetPath) -and (Test-Path (Resolve-BossKeyGrowthPath $packetPath))) {
        $packet = Parse-BossKeyOperatorPacket -PathValue $packetPath
    }

    $summary = ""
    if ($null -ne $packet -and -not [string]::IsNullOrWhiteSpace($packet.'Source Angle')) {
        $summary = Convert-BossKeyAsciiText -Value (([string]$packet.'Source Angle').Replace("`n", " ").Trim())
    }
    if ([string]::IsNullOrWhiteSpace($summary)) {
        $summary = Convert-BossKeyAsciiText -Value ([string]$source.summary_hint)
    }

    $articleDraftPath = ""
    $companyDraftPath = ""
    $personalDraftPath = ""

    if ($publishMode -ne "existing-output") {
        $articleDraftPath = "marketing-agents/briefs/generated/boss-key-growth-os/articles/{0}.md" -f $contentId
        $companyDraftPath = "marketing-agents/briefs/generated/boss-key-growth-os/linkedin/{0}-company.md" -f $contentId
        $personalDraftPath = "marketing-agents/briefs/generated/boss-key-growth-os/linkedin/{0}-personal.md" -f $contentId

        $articleDraftResolved = Resolve-BossKeyGrowthPath $articleDraftPath
        $companyDraftResolved = Resolve-BossKeyGrowthPath $companyDraftPath
        $personalDraftResolved = Resolve-BossKeyGrowthPath $personalDraftPath

        if ($RefreshExisting -or -not (Test-Path $articleDraftResolved)) {
            (Convert-BossKeyAsciiText -Value (Get-BossKeyArticleDraftText -Title $title -Summary $summary -Packet $packet)) |
                Set-Content -Path $articleDraftResolved -Encoding UTF8
        }

        if ($RefreshExisting -or -not (Test-Path $companyDraftResolved)) {
            (Convert-BossKeyAsciiText -Value (Get-BossKeyLinkedInDraftText -Title $title -AudienceLabel "Boss Key Company Page" -Packet $packet)) |
                Set-Content -Path $companyDraftResolved -Encoding UTF8
        }

        if ($RefreshExisting -or -not (Test-Path $personalDraftResolved)) {
            (Convert-BossKeyAsciiText -Value (Get-BossKeyLinkedInDraftText -Title $title -AudienceLabel "Timmy personal profile" -Packet $packet)) |
                Set-Content -Path $personalDraftResolved -Encoding UTF8
        }
    }

    $rowOut = [ordered]@{
        content_id = $contentId
        created_date = if ([string]::IsNullOrWhiteSpace($source.created_date)) { (Get-Date).ToString("yyyy-MM-dd") } else { [string]$source.created_date }
        cadence_type = [string]$source.cadence_type
        source_id = [string]$source.source_id
        source_type = [string]$source.source_type
        source_path = [string]$source.source_path
        source_title = [string]$source.source_title
        title = $title
        slug = $slug
        summary = $summary
        article_draft_path = $articleDraftPath
        article_output_path = $articleOutputPath
        company_linkedin_draft_path = $companyDraftPath
        personal_linkedin_draft_path = $personalDraftPath
        scheduled_publish_date = [string]$source.scheduled_publish_date
        owner_decision = if ($null -eq $existing) { "review" } else { [string]$existing.owner_decision }
        review_status = if ($publishMode -eq "existing-output") {
            "approved"
        } elseif ($null -eq $existing) {
            "pending-review"
        } else {
            [string]$existing.review_status
        }
        website_status = if ($publishMode -eq "existing-output") {
            "published"
        } elseif ($null -eq $existing) {
            "draft"
        } else {
            [string]$existing.website_status
        }
        rss_status = if ($publishMode -eq "existing-output") {
            "published"
        } elseif ($null -eq $existing) {
            "draft"
        } else {
            [string]$existing.rss_status
        }
        linkedin_company_status = if ($publishMode -eq "existing-output") {
            "rss-auto"
        } elseif ($null -eq $existing) {
            "draft"
        } else {
            [string]$existing.linkedin_company_status
        }
        linkedin_personal_status = if ($null -eq $existing) { "draft" } else { [string]$existing.linkedin_personal_status }
        published_date = if ($publishMode -eq "existing-output") {
            if ([string]::IsNullOrWhiteSpace($source.scheduled_publish_date)) { (Get-Date).ToString("yyyy-MM-dd") } else { [string]$source.scheduled_publish_date }
        } else {
            if ($null -eq $existing) { "" } else { [string]$existing.published_date }
        }
        notes = if ($null -eq $existing) { [string]$source.notes } else { [string]$existing.notes }
    }

    if ($null -ne $existing) {
        $queue.Remove($existing) | Out-Null
        $queue.Add([pscustomobject]$rowOut)
        $updated++
    } else {
        $queue.Add([pscustomobject]$rowOut)
        $added++
    }
}

Export-BossKeyCsv -Rows ($queue.ToArray()) -PathValue $QueueFile -PropertyOrder $queuePropertyOrder
Write-Output ("Boss Key content queue synced. Added: {0}. Updated: {1}. Queue: {2}" -f $added, $updated, $QueueFile)
