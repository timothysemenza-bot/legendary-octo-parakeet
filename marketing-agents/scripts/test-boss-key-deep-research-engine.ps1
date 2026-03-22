Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw "Run this smoke test in PowerShell 7 (pwsh)."
}

. (Join-Path $PSScriptRoot "boss-key-growth-os-helpers.ps1")
. (Join-Path $PSScriptRoot "boss-key-deep-research-helpers.ps1")

function Assert-Condition {
    param(
        [bool]$Condition,
        [string]$Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$generatorScript = Join-Path $PSScriptRoot "run-boss-key-deep-research-article.ps1"
$buildReviewScript = Join-Path $PSScriptRoot "build-boss-key-growth-review.ps1"
$buildSiteScript = Join-Path $PSScriptRoot "build-boss-key-insights-site.ps1"

$fixtureRoot = Join-Path $repoRoot "marketing-agents\test-fixtures\deep-research"
$researchFixture = Join-Path $fixtureRoot "research-pack.json"
$articleFixture = Join-Path $fixtureRoot "article-assembly.json"
$invalidFixture = Join-Path $fixtureRoot "invalid-article-assembly.json"

$markdownSample = @'
# Renderer Test

Paragraph with **bold**, [link](https://example.com), and `code`.

1. One
2. Two

| A | B |
| --- | --- |
| 1 | 2 |

```text
branch -> score -> review
```
'@

$rendered = Convert-BossKeyMarkdownToHtml -Markdown $markdownSample
Assert-Condition ($rendered.Contains("<table>")) "Markdown renderer did not preserve tables."
Assert-Condition ($rendered.Contains("<ol>")) "Markdown renderer did not preserve ordered lists."
Assert-Condition ($rendered.Contains("<strong>bold</strong>")) "Markdown renderer did not preserve bold text."
Assert-Condition ($rendered.Contains('<a href="https://example.com">link</a>')) "Markdown renderer did not preserve links."
Assert-Condition ($rendered.Contains("<pre><code class=`"language-text`">")) "Markdown renderer did not preserve fenced code blocks."

$invalidAssembly = Get-Content -Path $invalidFixture -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 50
$invalidValidation = Test-BossKeyDeepResearchArticleAssembly -Assembly $invalidAssembly -TargetWords 1000 -ArtifactFocus "Intake scoring model"
Assert-Condition (-not $invalidValidation.is_valid) "Invalid article assembly unexpectedly passed validation."
Assert-Condition (($invalidValidation.issues -join " ").Contains("Banned marketing phrase")) "Validator did not catch banned marketing language."
Assert-Condition (($invalidValidation.issues -join " ").Contains("Failure mode count")) "Validator did not catch failure mode count issues."
Assert-Condition (($invalidValidation.issues -join " ").Contains("human control points")) "Validator did not catch missing human control points."

$validAssembly = Get-Content -Path $articleFixture -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 50
$validWordCount = Convert-BossKeyDeepResearchToWordCount -Text (Convert-BossKeyDeepResearchArticleToMarkdown -Assembly $validAssembly)
Assert-Condition ($validWordCount -gt 0) "Valid article assembly fixture did not render into text."

$tmpRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("boss-key-deep-research-smoke-" + [guid]::NewGuid().ToString("N"))
$marketingRoot = Join-Path $tmpRoot "marketing-agents"
$dataDir = Join-Path $marketingRoot "data"
$briefsDir = Join-Path $marketingRoot "briefs"
$articleDir = Join-Path $briefsDir "generated\boss-key-growth-os\articles"
$runRoot = Join-Path $briefsDir "generated\deep-research"
$siteRoot = Join-Path $tmpRoot "boss-key-website"
$insightsDir = Join-Path $siteRoot "insights"
$queueFile = Join-Path $dataDir "boss_key_content_queue.csv"
$reviewPacketFile = Join-Path $briefsDir "boss-key-review-packet-latest.md"
$indexFile = Join-Path $insightsDir "index.html"
$feedFile = Join-Path $insightsDir "feed.xml"

New-Item -ItemType Directory -Force -Path $dataDir, $briefsDir, $articleDir, $runRoot, $insightsDir | Out-Null

& $generatorScript `
    -Topic "Bid/No-Bid Decision Systems in Facilities Services" `
    -Thesis "Reactive qualification moves the real decision behind sunk cost." `
    -TargetAudience "VP Sales, Proposal Director" `
    -IndustryContext "Janitorial / Facilities Management" `
    -ArtifactFocus "Intake scoring model" `
    -Length $validWordCount `
    -RunRoot $runRoot `
    -ArticleDraftDir $articleDir `
    -ArticleOutputBaseDir $insightsDir `
    -ContentQueueFile $queueFile `
    -FixtureResearchPackFile $researchFixture `
    -FixtureArticleAssemblyFile $articleFixture | Out-Null

$queueRows = Import-BossKeyCsvWithSchema -PathValue $queueFile -PropertyOrder (Get-BossKeyContentQueuePropertyOrder)
Assert-Condition (@($queueRows).Count -eq 1) "Expected one queue row after the first fixture run."
Assert-Condition (-not [string]::IsNullOrWhiteSpace([string]$queueRows[0].research_pack_path)) "Research pack path was not written to the queue."
Assert-Condition ([string]::IsNullOrWhiteSpace([string]$queueRows[0].distillation_path)) "Distillation path should be blank when distillation is not requested."
Assert-Condition (Test-Path ([string]$queueRows[0].article_draft_path)) "Article draft file was not created."
Assert-Condition (Test-Path ([string]$queueRows[0].research_pack_path)) "Research pack markdown file was not created."

& $generatorScript `
    -Topic "Proposal readiness gates for regional facilities contractors" `
    -Thesis "Proposal kickoff should start execution, not discovery." `
    -TargetAudience "Proposal Director" `
    -IndustryContext "Facilities Services" `
    -ArtifactFocus "Intake scoring model" `
    -Length $validWordCount `
    -IncludeDistillation `
    -RunRoot $runRoot `
    -ArticleDraftDir $articleDir `
    -ArticleOutputBaseDir $insightsDir `
    -ContentQueueFile $queueFile `
    -FixtureResearchPackFile $researchFixture `
    -FixtureArticleAssemblyFile $articleFixture | Out-Null

$queueRows = Import-BossKeyCsvWithSchema -PathValue $queueFile -PropertyOrder (Get-BossKeyContentQueuePropertyOrder)
Assert-Condition (@($queueRows).Count -eq 2) "Expected two queue rows after the second fixture run."
$distillationRow = @($queueRows | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_.distillation_path) }) | Select-Object -First 1
Assert-Condition ($null -ne $distillationRow) "Expected one queue row with a populated distillation path."
Assert-Condition (Test-Path ([string]$distillationRow.distillation_path)) "Distillation markdown file was not created."

& $buildReviewScript `
    -ContentQueueFile $queueFile `
    -RelationshipQueueFile (Join-Path $dataDir "boss_key_relationship_queue.csv") `
    -ConversationMemoryFile (Join-Path $dataDir "boss_key_conversation_memory.csv") `
    -MeetingQueueFile (Join-Path $dataDir "boss_key_meeting_queue.csv") `
    -PtwQueueFile (Join-Path $dataDir "boss_key_ptw_queue.csv") `
    -ProposalQueueFile (Join-Path $dataDir "boss_key_preconsult_proposals.csv") `
    -KnowledgeBaseFile (Join-Path $dataDir "boss_key_competitive_kb.csv") `
    -OutcomeLogFile (Join-Path $dataDir "boss_key_ptw_outcomes.csv") `
    -PriceBookFile (Join-Path $dataDir "boss_key_private_price_book.csv") `
    -ModifierFile (Join-Path $dataDir "boss_key_price_modifiers.csv") `
    -DecisionFile (Join-Path $dataDir "boss_key_review_decisions.csv") `
    -BusyBlocksFile (Join-Path $dataDir "busy_blocks.csv") `
    -ReviewPacketFile $reviewPacketFile `
    -SkipProposalOpsSync | Out-Null

Assert-Condition (Test-Path $reviewPacketFile) "Review packet was not generated."
$reviewPacketText = Get-Content -Path $reviewPacketFile -Raw -Encoding UTF8
Assert-Condition ($reviewPacketText.Contains("Research pack:")) "Review packet did not include research pack references."
Assert-Condition ($reviewPacketText.Contains("Distillation layer:")) "Review packet did not include distillation references."

$publishedRows = @()
foreach ($row in $queueRows) {
    $published = ConvertTo-BossKeySchemaRow -Row $row -PropertyOrder (Get-BossKeyContentQueuePropertyOrder)
    if ($publishedRows.Count -eq 0) {
        $published.website_status = "approved"
        $published.rss_status = "approved"
        $published.published_date = (Get-Date).ToString("yyyy-MM-dd")
    }
    $publishedRows += $published
}
Export-BossKeyCsv -Rows $publishedRows -PathValue $queueFile -PropertyOrder (Get-BossKeyContentQueuePropertyOrder)

& $buildSiteScript `
    -QueueFile $queueFile `
    -SiteRoot $siteRoot `
    -InsightsIndex $indexFile `
    -FeedFile $feedFile `
    -BaseUrl "https://example.com" | Out-Null

Assert-Condition (Test-Path $indexFile) "Insights index was not built."
Assert-Condition (Test-Path $feedFile) "Insights feed was not built."
$publishedArticlePath = [string]$publishedRows[0].article_output_path
Assert-Condition (Test-Path $publishedArticlePath) "Published article page was not generated."
$publishedArticleHtml = Get-Content -Path $publishedArticlePath -Raw -Encoding UTF8
Assert-Condition ($publishedArticleHtml.Contains("<table>")) "Published article page did not render markdown tables."
Assert-Condition ($publishedArticleHtml.Contains("System Model (Core Contribution)")) "Published article page is missing core section output."

Write-Output ("Deep research smoke test passed. Temp workspace: {0}" -f $tmpRoot)
