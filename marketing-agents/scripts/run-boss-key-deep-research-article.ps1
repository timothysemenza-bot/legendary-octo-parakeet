param(
    [string]$Topic = "",
    [string]$Thesis = "",
    [string]$TargetAudience = "",
    [string]$IndustryContext = "",
    [string]$ArtifactFocus = "",
    [int]$Length = 3000,
    [string]$Model = "gpt-5",
    [int]$TimeoutSec = 300,
    [string]$ConfigFile = "",
    [string]$ResearchPromptFile = "marketing-agents/prompts/32_boss_key_deep_research_researcher.md",
    [string]$ArticlePromptFile = "marketing-agents/prompts/33_boss_key_deep_research_writer.md",
    [string]$RunRoot = "marketing-agents/briefs/generated/deep-research",
    [string]$ArticleDraftDir = "marketing-agents/briefs/generated/boss-key-growth-os/articles",
    [string]$ArticleOutputBaseDir = "boss-key-website/insights",
    [string]$ContentQueueFile = "marketing-agents/data/boss_key_content_queue.csv",
    [string]$ContentQueueSourceType = "deep-research-generator",
    [string]$FixtureResearchPackFile = "",
    [string]$FixtureArticleAssemblyFile = "",
    [switch]$IncludeDistillation,
    [switch]$PromptOnly,
    [switch]$SkipQueueWrite
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw "Run this script in PowerShell 7 (pwsh)."
}

. (Join-Path $PSScriptRoot "boss-key-growth-os-helpers.ps1")
. (Join-Path $PSScriptRoot "boss-key-deep-research-helpers.ps1")

function Ensure-Dir {
    param([string]$PathValue)

    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return
    }

    if (-not (Test-Path $PathValue)) {
        New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
    }
}

function Load-EnvFile {
    param([string]$FilePath)

    if (-not (Test-Path $FilePath)) {
        return
    }

    foreach ($line in Get-Content -Path $FilePath -Encoding UTF8) {
        $trimmed = ([string]$line).Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed) -or $trimmed.StartsWith("#")) {
            continue
        }

        $splitIndex = $trimmed.IndexOf("=")
        if ($splitIndex -le 0) {
            continue
        }

        $name = $trimmed.Substring(0, $splitIndex).Trim()
        $value = $trimmed.Substring($splitIndex + 1).Trim()
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }

        if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name))) {
            [Environment]::SetEnvironmentVariable($name, $value)
        }
    }
}

function Get-FileText {
    param([string]$PathValue)

    $resolved = Resolve-BossKeyGrowthPath $PathValue
    if (-not (Test-Path $resolved)) {
        return ""
    }

    return Get-Content -Path $resolved -Raw -Encoding UTF8
}

function Get-ConfigValue {
    param(
        [object]$ConfigObject,
        [string]$PropertyName
    )

    if ($null -eq $ConfigObject) {
        return $null
    }

    if ($ConfigObject.PSObject.Properties.Name -contains $PropertyName) {
        return $ConfigObject.$PropertyName
    }

    return $null
}

function Get-BossKeyObjectPropertyValue {
    param(
        [object]$InputObject,
        [string]$PropertyName,
        [object]$DefaultValue = $null
    )

    if ($null -eq $InputObject) {
        return $DefaultValue
    }

    $property = $InputObject.PSObject.Properties[$PropertyName]
    if ($null -eq $property) {
        return $DefaultValue
    }

    return $property.Value
}

function Extract-OutputText {
    param([object]$ResponseObject)

    if ($null -eq $ResponseObject) {
        return ""
    }

    $outputTextProperty = $ResponseObject.PSObject.Properties["output_text"]
    if ($null -ne $outputTextProperty -and -not [string]::IsNullOrWhiteSpace([string]$outputTextProperty.Value)) {
        return [string]$outputTextProperty.Value
    }

    $chunks = New-Object System.Collections.Generic.List[string]
    foreach ($item in @($ResponseObject.output)) {
        $itemContentProperty = $item.PSObject.Properties["content"]
        if ($null -eq $itemContentProperty) {
            continue
        }

        foreach ($content in @($itemContentProperty.Value)) {
            $contentTypeProperty = $content.PSObject.Properties["type"]
            $textProperty = $content.PSObject.Properties["text"]
            $valueProperty = $content.PSObject.Properties["value"]
            $contentType = if ($null -ne $contentTypeProperty) { [string]$contentTypeProperty.Value } else { "" }
            $contentText = ""
            if ($null -ne $textProperty -and -not [string]::IsNullOrWhiteSpace([string]$textProperty.Value)) {
                $contentText = [string]$textProperty.Value
            } elseif ($null -ne $valueProperty -and -not [string]::IsNullOrWhiteSpace([string]$valueProperty.Value)) {
                $contentText = [string]$valueProperty.Value
            }

            if (($contentType -eq "output_text" -or $contentType -eq "text") -and -not [string]::IsNullOrWhiteSpace($contentText)) {
                $chunks.Add($contentText)
            }
        }
    }

    return ($chunks -join "`n`n").Trim()
}

function Invoke-BossKeyResponsesRequest {
    param(
        [string]$ApiKey,
        [string]$ModelName,
        [string]$Instructions,
        [string]$InputText,
        [int]$MaxOutputTokens,
        [string]$ReasoningEffort,
        [hashtable]$TextFormat,
        [object[]]$Tools,
        [string[]]$IncludeItems,
        [int]$RequestTimeoutSec
    )

    $payload = [ordered]@{
        model = $ModelName
        store = $false
        instructions = $Instructions
        input = $InputText
        max_output_tokens = $MaxOutputTokens
        reasoning = @{
            effort = $ReasoningEffort
        }
    }

    if ($null -ne $TextFormat) {
        $payload.text = @{
            format = $TextFormat
        }
    }

    if ($null -ne $Tools -and @($Tools).Count -gt 0) {
        $payload.tools = @($Tools)
    }

    if ($null -ne $IncludeItems -and @($IncludeItems).Count -gt 0) {
        $payload.include = @($IncludeItems)
    }

    $headers = @{
        Authorization = "Bearer $ApiKey"
        "Content-Type" = "application/json"
    }

    $body = $payload | ConvertTo-Json -Depth 30
    $rawResponse = Invoke-WebRequest -Method Post -Uri "https://api.openai.com/v1/responses" -Headers $headers -Body $body -TimeoutSec $RequestTimeoutSec
    $responseText = [string]$rawResponse.Content
    $responseObject = $responseText | ConvertFrom-Json -Depth 50

    return [pscustomobject]@{
        raw_json = $responseText
        response = $responseObject
        output_text = (Extract-OutputText -ResponseObject $responseObject)
    }
}

function New-BossKeyDeepResearchContentId {
    param(
        [string]$Seed,
        [string]$RunStamp
    )

    $token = ConvertTo-BossKeySlug -Value $Seed
    if ($token.Length -gt 24) {
        $token = $token.Substring(0, 24).Trim('-')
    }

    return "content-{0}-{1}" -f $RunStamp, $token
}

function New-BossKeyDeepResearchRunStamp {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmssfff"
    $suffix = [guid]::NewGuid().ToString("N").Substring(0, 8)
    return "{0}-{1}" -f $timestamp, $suffix
}

function ConvertTo-BossKeyStoredPath {
    param([string]$ResolvedPath)

    $fullPath = [System.IO.Path]::GetFullPath($ResolvedPath)
    $repoPath = [System.IO.Path]::GetFullPath($script:RepoRoot)
    if ($fullPath.StartsWith($repoPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $fullPath.Substring($repoPath.Length).TrimStart('\', '/').Replace('\', '/')
    }

    return $fullPath.Replace('\', '/')
}

function Get-BossKeyDeepResearchLocalContext {
    param([string[]]$CandidateFiles)

    $sections = New-Object System.Collections.Generic.List[string]
    $sections.Add("## Boss Key Local Context")
    $sections.Add("")
    $maxCharsPerFile = 3500
    $maxTotalChars = 14000
    $totalChars = 0

    foreach ($relativePath in $CandidateFiles) {
        if ($totalChars -ge $maxTotalChars) {
            break
        }

        $resolved = Resolve-BossKeyGrowthPath $relativePath
        if (-not (Test-Path $resolved)) {
            continue
        }

        $raw = Get-Content -Path $resolved -Raw -Encoding UTF8
        if ([string]::IsNullOrWhiteSpace($raw)) {
            continue
        }

        $trimmed = $raw.Trim()
        $remainingChars = $maxTotalChars - $totalChars
        $allowedChars = [Math]::Min($maxCharsPerFile, $remainingChars)
        if ($allowedChars -le 0) {
            break
        }

        if ($trimmed.Length -gt $allowedChars) {
            $trimmed = $trimmed.Substring(0, $allowedChars).Trim() + "`n`n[Truncated for prompt efficiency.]"
        }

        $sections.Add("### $relativePath")
        $sections.Add($trimmed)
        $sections.Add("")
        $totalChars += $trimmed.Length
    }

    return ($sections -join "`n").Trim()
}

function Get-BossKeyDeepResearchResearchInput {
    param(
        [string]$TopicValue,
        [string]$ThesisValue,
        [string]$AudienceValue,
        [string]$IndustryValue,
        [string]$ArtifactValue,
        [int]$LengthValue,
        [string]$LocalContext
    )

    return @"
Build a research pack for a Boss Key deep-research article.

Requested inputs:
- topic: $TopicValue
- thesis: $(if ([string]::IsNullOrWhiteSpace($ThesisValue)) { "[derive from evidence]" } else { $ThesisValue })
- target_audience: $(if ([string]::IsNullOrWhiteSpace($AudienceValue)) { "[not specified]" } else { $AudienceValue })
- industry_context: $(if ([string]::IsNullOrWhiteSpace($IndustryValue)) { "[not specified]" } else { $IndustryValue })
- artifact_focus: $(if ([string]::IsNullOrWhiteSpace($ArtifactValue)) { "[choose the most useful artifact]" } else { $ArtifactValue })
- target_length_words: $LengthValue

Requirements:
- Prioritize primary or authoritative sources first.
- Use vendor or consultant marketing sources only as supporting context, not as the basis for core claims.
- Identify the operational problem beneath the topic, not just the visible symptom.
- Produce an original, operator-grade synthesis suitable for APMP-aligned proposal and pursuit operations thinking.
- Keep the source list tight and relevant; do not pad it.

$LocalContext
"@
}

function Get-BossKeyDeepResearchArticleInput {
    param(
        [string]$TopicValue,
        [string]$ThesisValue,
        [string]$AudienceValue,
        [string]$IndustryValue,
        [string]$ArtifactValue,
        [int]$LengthValue,
        [bool]$ShouldIncludeDistillation,
        [string]$ResearchPackJson,
        [string]$LocalContext
    )

    return @"
Write a Boss Key deep-research article assembly from the structured research pack below.

Requested inputs:
- topic: $TopicValue
- thesis: $(if ([string]::IsNullOrWhiteSpace($ThesisValue)) { "[derive from research pack]" } else { $ThesisValue })
- target_audience: $(if ([string]::IsNullOrWhiteSpace($AudienceValue)) { "[not specified]" } else { $AudienceValue })
- industry_context: $(if ([string]::IsNullOrWhiteSpace($IndustryValue)) { "[not specified]" } else { $IndustryValue })
- artifact_focus: $(if ([string]::IsNullOrWhiteSpace($ArtifactValue)) { "[choose the most useful artifact]" } else { $ArtifactValue })
- target_length_words: $LengthValue
- distillation_required: $(if ($ShouldIncludeDistillation) { "yes, produce exactly 5 posts" } else { "no, omit distillation_posts" })

Hard requirements:
- This must read like applied research written by an operator.
- No fluff, no motivational framing, no generic AI hype.
- The system model must be the centerpiece.
- The case illustration must be explicitly composite or hypothetical.
- The AI section must clearly separate what should be automated from what should remain human-controlled.
- The artifact layer must be usable as-is in markdown form.

## Research Pack JSON
$ResearchPackJson

$LocalContext
"@
}

function Get-BossKeyDeepResearchRevisionInput {
    param(
        [string]$ArticleInput,
        [string]$PriorAssemblyJson,
        [string[]]$Issues
    )

    $issueLines = @($Issues | ForEach-Object { "- $_" }) -join "`n"
    return @"
$ArticleInput

## Validation Findings To Fix
$issueLines

## Prior Article Assembly JSON
$PriorAssemblyJson

Revise the article assembly so it resolves every validation issue while preserving the best analytical content from the prior draft.
"@
}

function Write-BossKeyDeepResearchPromptPacket {
    param(
        [string]$PathValue,
        [string]$Title,
        [string]$ModelName,
        [string]$Instructions,
        [string]$InputText,
        [hashtable]$FormatSchema,
        [object[]]$Tools,
        [string[]]$IncludeItems
    )

    $schemaJson = if ($null -eq $FormatSchema) { "" } else { $FormatSchema | ConvertTo-Json -Depth 20 }
    $toolsJson = if ($null -eq $Tools -or @($Tools).Count -eq 0) { "[]" } else { @($Tools) | ConvertTo-Json -Depth 10 }
    $includeJson = if ($null -eq $IncludeItems -or @($IncludeItems).Count -eq 0) { "[]" } else { @($IncludeItems) | ConvertTo-Json -Depth 10 }

    $content = @"
# $Title
Model: $ModelName

## Tools
$toolsJson

## Include
$includeJson

## Structured Output Schema
$schemaJson

## System Prompt
$Instructions

## User Input
$InputText
"@

    $content | Set-Content -Path $PathValue -Encoding UTF8
}

function Write-BossKeyDeepResearchMockResponse {
    param(
        [string]$PathValue,
        [string]$FixturePath,
        [string]$Mode
    )

    $mock = [ordered]@{
        fixture_mode = $true
        fixture_path = $FixturePath
        mode = $Mode
        generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    } | ConvertTo-Json -Depth 5

    $mock | Set-Content -Path $PathValue -Encoding UTF8
}

function Upsert-BossKeyDeepResearchQueueRow {
    param(
        [string]$QueueFile,
        [pscustomobject]$Row
    )

    $propertyOrder = Get-BossKeyContentQueuePropertyOrder
    $rows = New-Object System.Collections.Generic.List[object]
    foreach ($existing in (Import-BossKeyCsvWithSchema -PathValue $QueueFile -PropertyOrder $propertyOrder)) {
        if ([string]$existing.content_id -ne [string]$Row.content_id) {
            $rows.Add($existing)
        }
    }

    $rows.Add($Row)
    Export-BossKeyCsv -Rows ($rows.ToArray()) -PathValue $QueueFile -PropertyOrder $propertyOrder
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$script:RepoRoot = $repoRoot
Load-EnvFile (Join-Path $repoRoot ".env")
Load-EnvFile (Join-Path $repoRoot ".env.local")

$configObject = $null
if (-not [string]::IsNullOrWhiteSpace($ConfigFile)) {
    $configResolved = Resolve-BossKeyGrowthPath $ConfigFile
    if (-not (Test-Path $configResolved)) {
        throw "Config file not found: $configResolved"
    }
    $configObject = Get-Content -Path $configResolved -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 20
}

if (-not $PSBoundParameters.ContainsKey("Topic")) {
    $configTopic = Get-ConfigValue -ConfigObject $configObject -PropertyName "topic"
    if (-not [string]::IsNullOrWhiteSpace([string]$configTopic)) { $Topic = [string]$configTopic }
}
if (-not $PSBoundParameters.ContainsKey("Thesis")) {
    $configThesis = Get-ConfigValue -ConfigObject $configObject -PropertyName "thesis"
    if (-not [string]::IsNullOrWhiteSpace([string]$configThesis)) { $Thesis = [string]$configThesis }
}
if (-not $PSBoundParameters.ContainsKey("TargetAudience")) {
    $configAudience = Get-ConfigValue -ConfigObject $configObject -PropertyName "target_audience"
    if (-not [string]::IsNullOrWhiteSpace([string]$configAudience)) { $TargetAudience = [string]$configAudience }
}
if (-not $PSBoundParameters.ContainsKey("IndustryContext")) {
    $configIndustry = Get-ConfigValue -ConfigObject $configObject -PropertyName "industry_context"
    if (-not [string]::IsNullOrWhiteSpace([string]$configIndustry)) { $IndustryContext = [string]$configIndustry }
}
if (-not $PSBoundParameters.ContainsKey("ArtifactFocus")) {
    $configArtifact = Get-ConfigValue -ConfigObject $configObject -PropertyName "artifact_focus"
    if (-not [string]::IsNullOrWhiteSpace([string]$configArtifact)) { $ArtifactFocus = [string]$configArtifact }
}
if (-not $PSBoundParameters.ContainsKey("Length")) {
    $configLength = Get-ConfigValue -ConfigObject $configObject -PropertyName "length"
    if ($null -ne $configLength -and [int]$configLength -gt 0) { $Length = [int]$configLength }
}
if (-not $PSBoundParameters.ContainsKey("Model")) {
    $configModel = Get-ConfigValue -ConfigObject $configObject -PropertyName "model"
    if (-not [string]::IsNullOrWhiteSpace([string]$configModel)) { $Model = [string]$configModel }
}
if (-not $PSBoundParameters.ContainsKey("TimeoutSec")) {
    $configTimeout = Get-ConfigValue -ConfigObject $configObject -PropertyName "timeout_sec"
    if ($null -ne $configTimeout -and [int]$configTimeout -gt 0) { $TimeoutSec = [int]$configTimeout }
}
if (-not $PSBoundParameters.ContainsKey("IncludeDistillation")) {
    $configDistillation = Get-ConfigValue -ConfigObject $configObject -PropertyName "include_distillation"
    if ($null -ne $configDistillation) { $IncludeDistillation = [bool]$configDistillation }
}
if (-not $PSBoundParameters.ContainsKey("PromptOnly")) {
    $configPromptOnly = Get-ConfigValue -ConfigObject $configObject -PropertyName "prompt_only"
    if ($null -ne $configPromptOnly) { $PromptOnly = [bool]$configPromptOnly }
}

if ([string]::IsNullOrWhiteSpace($Topic)) {
    throw "Topic is required. Provide -Topic or set topic in the config file."
}

if ($Length -le 0) {
    $Length = 3000
}

$topicSlug = ConvertTo-BossKeySlug -Value $Topic
$runDate = Get-Date -Format "yyyy-MM-dd"
$runStamp = New-BossKeyDeepResearchRunStamp
$runFolderName = "{0}-{1}" -f $runStamp, $topicSlug
$runRootResolved = Resolve-BossKeyGrowthPath $RunRoot
$runDir = Join-Path (Join-Path $runRootResolved $runDate) $runFolderName
Ensure-Dir $runDir

$researchPromptResolved = Resolve-BossKeyGrowthPath $ResearchPromptFile
$articlePromptResolved = Resolve-BossKeyGrowthPath $ArticlePromptFile
$researchPrompt = Get-FileText $ResearchPromptFile
$articlePrompt = Get-FileText $ArticlePromptFile
if ([string]::IsNullOrWhiteSpace($researchPrompt)) {
    throw "Missing research prompt file: $researchPromptResolved"
}
if ([string]::IsNullOrWhiteSpace($articlePrompt)) {
    throw "Missing article prompt file: $articlePromptResolved"
}

$localContext = Get-BossKeyDeepResearchLocalContext -CandidateFiles @(
    "apmp-foundation-business-blueprint.md",
    "docs/boss-key-early-lifecycle-strategy.md",
    "marketing-agents/PROPOSAL-ENGINE.md",
    "marketing-agents/BOSS-KEY-REVIEW-FIRST-GROWTH-OS.md",
    "proposal-ops/README.md"
)

$researchSchema = Get-BossKeyDeepResearchResearchPackSchema
$articleSchema = Get-BossKeyDeepResearchArticleAssemblySchema
$researchInput = Get-BossKeyDeepResearchResearchInput -TopicValue $Topic -ThesisValue $Thesis -AudienceValue $TargetAudience -IndustryValue $IndustryContext -ArtifactValue $ArtifactFocus -LengthValue $Length -LocalContext $localContext

$researchPacketPath = Join-Path $runDir "research-pass-packet.md"
$articlePacketPath = Join-Path $runDir "article-pass-packet.md"
$promptManifestPath = Join-Path $runDir "prompt-manifest.json"

Write-BossKeyDeepResearchPromptPacket -PathValue $researchPacketPath -Title "Research Pass Packet" -ModelName $Model -Instructions $researchPrompt -InputText $researchInput -FormatSchema $researchSchema -Tools @(@{ type = "web_search" }) -IncludeItems @("web_search_call.action.sources")

$apiKey = [Environment]::GetEnvironmentVariable("OPENAI_API_KEY")
$needsLiveResearch = [string]::IsNullOrWhiteSpace($FixtureResearchPackFile)
$needsLiveArticle = [string]::IsNullOrWhiteSpace($FixtureArticleAssemblyFile)

if ($PromptOnly -or (([string]::IsNullOrWhiteSpace($apiKey)) -and ($needsLiveResearch -or $needsLiveArticle))) {
    $placeholderArticleInput = @"
Run the research pass first, then inject the resulting research-pack.json into the article pass packet below.

Requested inputs:
- topic: $Topic
- thesis: $(if ([string]::IsNullOrWhiteSpace($Thesis)) { "[derive from research pack]" } else { $Thesis })
- target_audience: $(if ([string]::IsNullOrWhiteSpace($TargetAudience)) { "[not specified]" } else { $TargetAudience })
- industry_context: $(if ([string]::IsNullOrWhiteSpace($IndustryContext)) { "[not specified]" } else { $IndustryContext })
- artifact_focus: $(if ([string]::IsNullOrWhiteSpace($ArtifactFocus)) { "[choose the most useful artifact]" } else { $ArtifactFocus })
- target_length_words: $Length
- distillation_required: $(if ($IncludeDistillation) { "yes, produce exactly 5 posts" } else { "no, omit distillation_posts" })

$localContext
"@

    Write-BossKeyDeepResearchPromptPacket -PathValue $articlePacketPath -Title "Article Pass Packet" -ModelName $Model -Instructions $articlePrompt -InputText $placeholderArticleInput -FormatSchema $articleSchema -Tools @() -IncludeItems @()

    $promptManifest = [ordered]@{
        mode = if ($PromptOnly) { "prompt_only" } else { "prompt_only_no_api_key" }
        topic = $Topic
        thesis = $Thesis
        target_audience = $TargetAudience
        industry_context = $IndustryContext
        artifact_focus = $ArtifactFocus
        length = $Length
        include_distillation = [bool]$IncludeDistillation
        model = $Model
        run_dir = $runDir
        research_packet_path = $researchPacketPath
        article_packet_path = $articlePacketPath
    } | ConvertTo-Json -Depth 10

    $promptManifest | Set-Content -Path $promptManifestPath -Encoding UTF8
    Write-Output ("Generated prompt packets: {0}" -f $runDir)
    return
}

$researchPackJsonPath = Join-Path $runDir "research-pack.json"
$researchPackMarkdownPath = Join-Path $runDir "research-pack.md"
$researchRawResponsePath = Join-Path $runDir "research-response.raw.json"

if (-not [string]::IsNullOrWhiteSpace($FixtureResearchPackFile)) {
    $fixtureResearchResolved = Resolve-BossKeyGrowthPath $FixtureResearchPackFile
    if (-not (Test-Path $fixtureResearchResolved)) {
        throw "Research fixture file not found: $fixtureResearchResolved"
    }
    $researchPack = Get-Content -Path $fixtureResearchResolved -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 50
    $researchPackJsonText = Get-Content -Path $fixtureResearchResolved -Raw -Encoding UTF8
    Write-BossKeyDeepResearchMockResponse -PathValue $researchRawResponsePath -FixturePath $fixtureResearchResolved -Mode "research"
} else {
    $researchResponse = Invoke-BossKeyResponsesRequest `
        -ApiKey $apiKey `
        -ModelName $Model `
        -Instructions $researchPrompt `
        -InputText $researchInput `
        -MaxOutputTokens 12000 `
        -ReasoningEffort "medium" `
        -TextFormat $researchSchema `
        -Tools @(@{ type = "web_search" }) `
        -IncludeItems @("web_search_call.action.sources") `
        -RequestTimeoutSec $TimeoutSec
    $researchStatus = [string](Get-BossKeyObjectPropertyValue -InputObject $researchResponse.response -PropertyName "status" -DefaultValue "")
    $researchIncompleteDetails = Get-BossKeyObjectPropertyValue -InputObject $researchResponse.response -PropertyName "incomplete_details"
    $researchIncompleteReason = [string](Get-BossKeyObjectPropertyValue -InputObject $researchIncompleteDetails -PropertyName "reason" -DefaultValue "")
    if ($researchStatus -eq "incomplete" -and $researchIncompleteReason -eq "max_output_tokens") {
        $researchRetryRawResponsePath = Join-Path $runDir "research-response.initial.raw.json"
        $researchResponse.raw_json | Set-Content -Path $researchRetryRawResponsePath -Encoding UTF8
        $researchResponse = Invoke-BossKeyResponsesRequest `
            -ApiKey $apiKey `
            -ModelName $Model `
            -Instructions $researchPrompt `
            -InputText $researchInput `
            -MaxOutputTokens 16000 `
            -ReasoningEffort "medium" `
            -TextFormat $researchSchema `
            -Tools @(@{ type = "web_search" }) `
            -IncludeItems @("web_search_call.action.sources") `
            -RequestTimeoutSec $TimeoutSec
    }
    $researchResponse.raw_json | Set-Content -Path $researchRawResponsePath -Encoding UTF8
    if ([string]::IsNullOrWhiteSpace($researchResponse.output_text)) {
        $finalResearchStatus = [string](Get-BossKeyObjectPropertyValue -InputObject $researchResponse.response -PropertyName "status" -DefaultValue "unknown")
        $finalResearchIncompleteDetails = Get-BossKeyObjectPropertyValue -InputObject $researchResponse.response -PropertyName "incomplete_details"
        $finalResearchReason = [string](Get-BossKeyObjectPropertyValue -InputObject $finalResearchIncompleteDetails -PropertyName "reason" -DefaultValue "")
        throw ("Research pass returned no structured output. Status: {0}. Reason: {1}. Raw response: {2}" -f $finalResearchStatus, $finalResearchReason, $researchRawResponsePath)
    }
    $researchPackJsonText = $researchResponse.output_text
    try {
        $researchPack = $researchPackJsonText | ConvertFrom-Json -Depth 50
    } catch {
        $finalResearchStatus = [string](Get-BossKeyObjectPropertyValue -InputObject $researchResponse.response -PropertyName "status" -DefaultValue "unknown")
        $finalResearchIncompleteDetails = Get-BossKeyObjectPropertyValue -InputObject $researchResponse.response -PropertyName "incomplete_details"
        $finalResearchReason = [string](Get-BossKeyObjectPropertyValue -InputObject $finalResearchIncompleteDetails -PropertyName "reason" -DefaultValue "")
        throw ("Research pass returned invalid JSON. Status: {0}. Reason: {1}. Raw response: {2}. Parser error: {3}" -f $finalResearchStatus, $finalResearchReason, $researchRawResponsePath, $_.Exception.Message)
    }
}

$researchPackJsonText | Set-Content -Path $researchPackJsonPath -Encoding UTF8
(Convert-BossKeyDeepResearchResearchPackToMarkdown -ResearchPack $researchPack) | Set-Content -Path $researchPackMarkdownPath -Encoding UTF8

$articleInput = Get-BossKeyDeepResearchArticleInput `
    -TopicValue $Topic `
    -ThesisValue $Thesis `
    -AudienceValue $TargetAudience `
    -IndustryValue $IndustryContext `
    -ArtifactValue $ArtifactFocus `
    -LengthValue $Length `
    -ShouldIncludeDistillation ([bool]$IncludeDistillation) `
    -ResearchPackJson $researchPackJsonText `
    -LocalContext $localContext

Write-BossKeyDeepResearchPromptPacket -PathValue $articlePacketPath -Title "Article Pass Packet" -ModelName $Model -Instructions $articlePrompt -InputText $articleInput -FormatSchema $articleSchema -Tools @() -IncludeItems @()

$articleAssemblyJsonPath = Join-Path $runDir "article-assembly.json"
$articleRawResponsePath = Join-Path $runDir "article-response.raw.json"
$revisionRawResponsePath = Join-Path $runDir "revision-response.raw.json"

if (-not [string]::IsNullOrWhiteSpace($FixtureArticleAssemblyFile)) {
    $fixtureArticleResolved = Resolve-BossKeyGrowthPath $FixtureArticleAssemblyFile
    if (-not (Test-Path $fixtureArticleResolved)) {
        throw "Article assembly fixture file not found: $fixtureArticleResolved"
    }
    $articleAssembly = Get-Content -Path $fixtureArticleResolved -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 50
    $articleAssemblyJsonText = Get-Content -Path $fixtureArticleResolved -Raw -Encoding UTF8
    Write-BossKeyDeepResearchMockResponse -PathValue $articleRawResponsePath -FixturePath $fixtureArticleResolved -Mode "article"
} else {
    $articleResponse = Invoke-BossKeyResponsesRequest `
        -ApiKey $apiKey `
        -ModelName $Model `
        -Instructions $articlePrompt `
        -InputText $articleInput `
        -MaxOutputTokens 14000 `
        -ReasoningEffort "medium" `
        -TextFormat $articleSchema `
        -Tools @() `
        -IncludeItems @() `
        -RequestTimeoutSec $TimeoutSec
    $articleStatus = [string](Get-BossKeyObjectPropertyValue -InputObject $articleResponse.response -PropertyName "status" -DefaultValue "")
    $articleIncompleteDetails = Get-BossKeyObjectPropertyValue -InputObject $articleResponse.response -PropertyName "incomplete_details"
    $articleIncompleteReason = [string](Get-BossKeyObjectPropertyValue -InputObject $articleIncompleteDetails -PropertyName "reason" -DefaultValue "")
    if ($articleStatus -eq "incomplete" -and $articleIncompleteReason -eq "max_output_tokens") {
        $articleRetryRawResponsePath = Join-Path $runDir "article-response.initial.raw.json"
        $articleResponse.raw_json | Set-Content -Path $articleRetryRawResponsePath -Encoding UTF8
        $articleResponse = Invoke-BossKeyResponsesRequest `
            -ApiKey $apiKey `
            -ModelName $Model `
            -Instructions $articlePrompt `
            -InputText $articleInput `
            -MaxOutputTokens 18000 `
            -ReasoningEffort "medium" `
            -TextFormat $articleSchema `
            -Tools @() `
            -IncludeItems @() `
            -RequestTimeoutSec $TimeoutSec
    }
    $articleResponse.raw_json | Set-Content -Path $articleRawResponsePath -Encoding UTF8
    if ([string]::IsNullOrWhiteSpace($articleResponse.output_text)) {
        $finalArticleStatus = [string](Get-BossKeyObjectPropertyValue -InputObject $articleResponse.response -PropertyName "status" -DefaultValue "unknown")
        $finalArticleIncompleteDetails = Get-BossKeyObjectPropertyValue -InputObject $articleResponse.response -PropertyName "incomplete_details"
        $finalArticleReason = [string](Get-BossKeyObjectPropertyValue -InputObject $finalArticleIncompleteDetails -PropertyName "reason" -DefaultValue "")
        throw ("Article pass returned no structured output. Status: {0}. Reason: {1}. Raw response: {2}" -f $finalArticleStatus, $finalArticleReason, $articleRawResponsePath)
    }
    $articleAssemblyJsonText = $articleResponse.output_text
    try {
        $articleAssembly = $articleAssemblyJsonText | ConvertFrom-Json -Depth 50
    } catch {
        $finalArticleStatus = [string](Get-BossKeyObjectPropertyValue -InputObject $articleResponse.response -PropertyName "status" -DefaultValue "unknown")
        $finalArticleIncompleteDetails = Get-BossKeyObjectPropertyValue -InputObject $articleResponse.response -PropertyName "incomplete_details"
        $finalArticleReason = [string](Get-BossKeyObjectPropertyValue -InputObject $finalArticleIncompleteDetails -PropertyName "reason" -DefaultValue "")
        throw ("Article pass returned invalid JSON. Status: {0}. Reason: {1}. Raw response: {2}. Parser error: {3}" -f $finalArticleStatus, $finalArticleReason, $articleRawResponsePath, $_.Exception.Message)
    }
}

$validation = Test-BossKeyDeepResearchArticleAssembly -Assembly $articleAssembly -TargetWords $Length -ArtifactFocus $ArtifactFocus
if (-not $validation.is_valid) {
    if (-not [string]::IsNullOrWhiteSpace($FixtureArticleAssemblyFile)) {
        throw ("Fixture article assembly failed validation: {0}" -f ($validation.issues -join " | "))
    }

    $revisionInput = Get-BossKeyDeepResearchRevisionInput -ArticleInput $articleInput -PriorAssemblyJson $articleAssemblyJsonText -Issues $validation.issues
    $revisionResponse = Invoke-BossKeyResponsesRequest `
        -ApiKey $apiKey `
        -ModelName $Model `
        -Instructions $articlePrompt `
        -InputText $revisionInput `
        -MaxOutputTokens 14000 `
        -ReasoningEffort "medium" `
        -TextFormat $articleSchema `
        -Tools @() `
        -IncludeItems @() `
        -RequestTimeoutSec $TimeoutSec
    $revisionStatus = [string](Get-BossKeyObjectPropertyValue -InputObject $revisionResponse.response -PropertyName "status" -DefaultValue "")
    $revisionIncompleteDetails = Get-BossKeyObjectPropertyValue -InputObject $revisionResponse.response -PropertyName "incomplete_details"
    $revisionIncompleteReason = [string](Get-BossKeyObjectPropertyValue -InputObject $revisionIncompleteDetails -PropertyName "reason" -DefaultValue "")
    if ($revisionStatus -eq "incomplete" -and $revisionIncompleteReason -eq "max_output_tokens") {
        $revisionRetryRawResponsePath = Join-Path $runDir "revision-response.initial.raw.json"
        $revisionResponse.raw_json | Set-Content -Path $revisionRetryRawResponsePath -Encoding UTF8
        $revisionResponse = Invoke-BossKeyResponsesRequest `
            -ApiKey $apiKey `
            -ModelName $Model `
            -Instructions $articlePrompt `
            -InputText $revisionInput `
            -MaxOutputTokens 18000 `
            -ReasoningEffort "medium" `
            -TextFormat $articleSchema `
            -Tools @() `
            -IncludeItems @() `
            -RequestTimeoutSec $TimeoutSec
    }
    $revisionResponse.raw_json | Set-Content -Path $revisionRawResponsePath -Encoding UTF8
    if ([string]::IsNullOrWhiteSpace($revisionResponse.output_text)) {
        $finalRevisionStatus = [string](Get-BossKeyObjectPropertyValue -InputObject $revisionResponse.response -PropertyName "status" -DefaultValue "unknown")
        $finalRevisionIncompleteDetails = Get-BossKeyObjectPropertyValue -InputObject $revisionResponse.response -PropertyName "incomplete_details"
        $finalRevisionReason = [string](Get-BossKeyObjectPropertyValue -InputObject $finalRevisionIncompleteDetails -PropertyName "reason" -DefaultValue "")
        throw ("Revision pass returned no structured output. Status: {0}. Reason: {1}. Raw response: {2}" -f $finalRevisionStatus, $finalRevisionReason, $revisionRawResponsePath)
    }
    $articleAssemblyJsonText = $revisionResponse.output_text
    try {
        $articleAssembly = $articleAssemblyJsonText | ConvertFrom-Json -Depth 50
    } catch {
        $finalRevisionStatus = [string](Get-BossKeyObjectPropertyValue -InputObject $revisionResponse.response -PropertyName "status" -DefaultValue "unknown")
        $finalRevisionIncompleteDetails = Get-BossKeyObjectPropertyValue -InputObject $revisionResponse.response -PropertyName "incomplete_details"
        $finalRevisionReason = [string](Get-BossKeyObjectPropertyValue -InputObject $finalRevisionIncompleteDetails -PropertyName "reason" -DefaultValue "")
        throw ("Revision pass returned invalid JSON. Status: {0}. Reason: {1}. Raw response: {2}. Parser error: {3}" -f $finalRevisionStatus, $finalRevisionReason, $revisionRawResponsePath, $_.Exception.Message)
    }
    $validation = Test-BossKeyDeepResearchArticleAssembly -Assembly $articleAssembly -TargetWords $Length -ArtifactFocus $ArtifactFocus
    if (-not $validation.is_valid) {
        throw ("Article assembly failed validation after revision: {0}" -f ($validation.issues -join " | "))
    }
}

$articleAssemblyJsonText | Set-Content -Path $articleAssemblyJsonPath -Encoding UTF8

$contentId = New-BossKeyDeepResearchContentId -Seed $articleAssembly.title -RunStamp $runStamp
$articleDraftResolvedDir = Resolve-BossKeyGrowthPath $ArticleDraftDir
Ensure-Dir $articleDraftResolvedDir
$articleDraftPathResolved = Join-Path $articleDraftResolvedDir ("{0}.md" -f $contentId)
$articleDraftStoredPath = ConvertTo-BossKeyStoredPath -ResolvedPath $articleDraftPathResolved

$distillationStoredPath = ""
$distillationPathResolved = ""
if ($IncludeDistillation -and @($articleAssembly.distillation_posts).Count -gt 0) {
    $distillationPathResolved = Join-Path $runDir "distillation-layer.md"
    Ensure-Dir (Split-Path -Parent $distillationPathResolved)
    (Convert-BossKeyDeepResearchDistillationToMarkdown -Posts $articleAssembly.distillation_posts) | Set-Content -Path $distillationPathResolved -Encoding UTF8
    $distillationStoredPath = ConvertTo-BossKeyStoredPath -ResolvedPath $distillationPathResolved
}

$articleMarkdown = [string]$validation.markdown
$articleMarkdown | Set-Content -Path $articleDraftPathResolved -Encoding UTF8

$runSuffix = ($runStamp -split '-')[-1]
$publishedSlug = "{0}-{1}-{2}" -f (ConvertTo-BossKeySlug -Value $articleAssembly.title), $runDate, $runSuffix
$articleOutputResolved = Join-Path (Resolve-BossKeyGrowthPath $ArticleOutputBaseDir) ("{0}.html" -f $publishedSlug)
$articleOutputPath = ConvertTo-BossKeyStoredPath -ResolvedPath $articleOutputResolved
$researchPackStoredPath = ConvertTo-BossKeyStoredPath -ResolvedPath $researchPackMarkdownPath
$researchPackJsonStoredPath = ConvertTo-BossKeyStoredPath -ResolvedPath $researchPackJsonPath
$articleAssemblyStoredPath = ConvertTo-BossKeyStoredPath -ResolvedPath $articleAssemblyJsonPath

$manifestPath = Join-Path $runDir "manifest.json"
$manifestStoredPath = ConvertTo-BossKeyStoredPath -ResolvedPath $manifestPath
$manifest = [ordered]@{
    mode = if (-not [string]::IsNullOrWhiteSpace($FixtureResearchPackFile) -or -not [string]::IsNullOrWhiteSpace($FixtureArticleAssemblyFile)) { "fixture" } else { "live" }
    generated_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    topic = $Topic
    thesis = $Thesis
    target_audience = $TargetAudience
    industry_context = $IndustryContext
    artifact_focus = $ArtifactFocus
    length = $Length
    model = $Model
    include_distillation = [bool]$IncludeDistillation
    content_id = $contentId
    slug = $publishedSlug
    article_title = [string]$articleAssembly.title
    meta_summary = [string]$articleAssembly.meta_summary
    validation = @{
        is_valid = [bool]$validation.is_valid
        word_count = [int]$validation.word_count
        minimum_word_count = [int]$validation.minimum_word_count
        maximum_word_count = [int]$validation.maximum_word_count
        issues = @($validation.issues)
    }
    outputs = @{
        research_pack_json = $researchPackJsonStoredPath
        research_pack_markdown = $researchPackStoredPath
        article_assembly_json = $articleAssemblyStoredPath
        article_draft_markdown = $articleDraftStoredPath
        distillation_markdown = $distillationStoredPath
        article_output_path = $articleOutputPath
    }
} | ConvertTo-Json -Depth 12
$manifest | Set-Content -Path $manifestPath -Encoding UTF8

if (-not $SkipQueueWrite) {
    $queueRow = [pscustomobject]@{
        content_id = $contentId
        created_date = $runDate
        cadence_type = "deep_research"
        source_id = "deep-research-{0}" -f $runStamp
        source_type = $ContentQueueSourceType
        source_path = $manifestStoredPath
        source_title = $Topic
        title = [string]$articleAssembly.title
        slug = $publishedSlug
        summary = [string]$articleAssembly.meta_summary
        article_draft_path = $articleDraftStoredPath
        research_pack_path = $researchPackStoredPath
        distillation_path = $distillationStoredPath
        article_output_path = $articleOutputPath
        company_linkedin_draft_path = ""
        personal_linkedin_draft_path = ""
        scheduled_publish_date = $runDate
        owner_decision = "review"
        review_status = "pending-review"
        website_status = "draft"
        rss_status = "draft"
        linkedin_company_status = "draft"
        linkedin_personal_status = $(if (-not [string]::IsNullOrWhiteSpace($distillationStoredPath)) { "draft" } else { "not-generated" })
        published_date = ""
        notes = "Deep research article generated by the scripted article engine with a supporting research pack."
    }

    Upsert-BossKeyDeepResearchQueueRow -QueueFile $ContentQueueFile -Row $queueRow
}

Write-Output ("Generated deep research article: {0}" -f $articleDraftPathResolved)
Write-Output ("Research pack: {0}" -f $researchPackMarkdownPath)
if (-not [string]::IsNullOrWhiteSpace($distillationStoredPath)) {
    Write-Output ("Distillation layer: {0}" -f $distillationPathResolved)
}
