Set-StrictMode -Version Latest

function Get-BossKeyDeepResearchWordCountBounds {
    param([int]$TargetWords = 3000)

    if ($TargetWords -le 0) {
        $TargetWords = 3000
    }

    if ($TargetWords -ge 2500) {
        $minimum = [math]::Max(2500, [int][math]::Floor($TargetWords * 0.85))
        $maximum = [math]::Min(4000, [int][math]::Ceiling($TargetWords * 1.2))
    } else {
        $minimum = [math]::Max(600, [int][math]::Floor($TargetWords * 0.85))
        $maximum = [math]::Max($minimum, [int][math]::Ceiling($TargetWords * 1.2))
    }
    if ($maximum -lt $minimum) {
        $maximum = $minimum
    }

    return [pscustomobject]@{
        minimum = $minimum
        maximum = $maximum
    }
}

function Get-BossKeyDeepResearchExpectedHeadings {
    return @(
        "Abstract",
        "1. Problem Definition",
        "2. Current State Analysis",
        "3. Failure Modes",
        "4. System Model (Core Contribution)",
        "5. AI Enablement Layer",
        "6. Implementation Path",
        "7. Case Illustration",
        "8. Implications for Leadership",
        "9. Conclusion"
    )
}

function Get-BossKeyDeepResearchBannedPhrases {
    return @(
        "in today's fast-paced world",
        "fast-paced world",
        "game changer",
        "game-changing",
        "cutting-edge",
        "revolutionize",
        "unlock the power",
        "leverage ai",
        "next-level",
        "next level",
        "thought leader",
        "seamless"
    )
}

function Get-BossKeyDeepResearchResearchPackSchema {
    return @{
        type = "json_schema"
        name = "deep_research_pack"
        strict = $true
        schema = @{
            type = "object"
            additionalProperties = $false
            properties = @{
                topic = @{ type = "string"; minLength = 5 }
                thesis_statement = @{ type = "string"; minLength = 40 }
                core_problem_space = @{ type = "string"; minLength = 120 }
                mapped_domains = @{
                    type = "array"
                    minItems = 3
                    items = @{
                        type = "object"
                        additionalProperties = $false
                        properties = @{
                            domain = @{ type = "string"; minLength = 3 }
                            relevance = @{ type = "string"; minLength = 20 }
                        }
                        required = @("domain", "relevance")
                    }
                }
                known_best_practices = @{
                    type = "array"
                    minItems = 4
                    items = @{ type = "string"; minLength = 20 }
                }
                common_failure_modes = @{
                    type = "array"
                    minItems = 3
                    maxItems = 6
                    items = @{
                        type = "object"
                        additionalProperties = $false
                        properties = @{
                            name = @{ type = "string"; minLength = 5 }
                            pattern = @{ type = "string"; minLength = 25 }
                            operational_effect = @{ type = "string"; minLength = 25 }
                        }
                        required = @("name", "pattern", "operational_effect")
                    }
                }
                current_thinking_gaps = @{
                    type = "array"
                    minItems = 3
                    items = @{ type = "string"; minLength = 25 }
                }
                synthesized_perspective = @{ type = "string"; minLength = 120 }
                what_industry_misses = @{ type = "string"; minLength = 120 }
                framework_candidates = @{
                    type = "array"
                    minItems = 2
                    items = @{
                        type = "object"
                        additionalProperties = $false
                        properties = @{
                            name = @{ type = "string"; minLength = 5 }
                            premise = @{ type = "string"; minLength = 30 }
                        }
                        required = @("name", "premise")
                    }
                }
                sources = @{
                    type = "array"
                    minItems = 5
                    items = @{
                        type = "object"
                        additionalProperties = $false
                        properties = @{
                            title = @{ type = "string"; minLength = 5 }
                            url = @{ type = "string"; minLength = 8 }
                            publisher = @{ type = "string"; minLength = 2 }
                            source_class = @{
                                type = "string"
                                enum = @("primary_research", "official_guidance", "industry_analysis", "vendor_marketing", "practitioner_commentary")
                            }
                            authority_level = @{
                                type = "string"
                                enum = @("high", "medium", "supporting")
                            }
                            relevance_note = @{ type = "string"; minLength = 15 }
                            key_fact = @{ type = "string"; minLength = 15 }
                            core_claim_support = @{ type = "boolean" }
                        }
                        required = @("title", "url", "publisher", "source_class", "authority_level", "relevance_note", "key_fact", "core_claim_support")
                    }
                }
            }
            required = @(
                "topic",
                "thesis_statement",
                "core_problem_space",
                "mapped_domains",
                "known_best_practices",
                "common_failure_modes",
                "current_thinking_gaps",
                "synthesized_perspective",
                "what_industry_misses",
                "framework_candidates",
                "sources"
            )
        }
    }
}

function Get-BossKeyDeepResearchArticleAssemblySchema {
    return @{
        type = "json_schema"
        name = "deep_research_article_assembly"
        strict = $true
        schema = @{
            type = "object"
            additionalProperties = $false
            properties = @{
                title = @{ type = "string"; minLength = 12 }
                meta_summary = @{ type = "string"; minLength = 60 }
                abstract = @{ type = "string"; minLength = 150 }
                core_thesis = @{ type = "string"; minLength = 50 }
                system_model_name = @{ type = "string"; minLength = 5 }
                problem_definition = @{ type = "string"; minLength = 180 }
                current_state_analysis = @{ type = "string"; minLength = 220 }
                failure_modes = @{
                    type = "array"
                    minItems = 3
                    maxItems = 6
                    items = @{
                        type = "object"
                        additionalProperties = $false
                        properties = @{
                            name = @{ type = "string"; minLength = 5 }
                            pattern = @{ type = "string"; minLength = 40 }
                            observable_signs = @{ type = "string"; minLength = 30 }
                            operational_effect = @{ type = "string"; minLength = 30 }
                        }
                        required = @("name", "pattern", "observable_signs", "operational_effect")
                    }
                }
                system_model = @{
                    type = "object"
                    additionalProperties = $false
                    properties = @{
                        premise = @{ type = "string"; minLength = 120 }
                        components = @{
                            type = "array"
                            minItems = 3
                            items = @{
                                type = "object"
                                additionalProperties = $false
                                properties = @{
                                    name = @{ type = "string"; minLength = 3 }
                                    purpose = @{ type = "string"; minLength = 20 }
                                    inputs = @{ type = "string"; minLength = 10 }
                                    outputs = @{ type = "string"; minLength = 10 }
                                    owner = @{ type = "string"; minLength = 3 }
                                }
                                required = @("name", "purpose", "inputs", "outputs", "owner")
                            }
                        }
                        decision_logic = @{
                            type = "array"
                            minItems = 3
                            items = @{ type = "string"; minLength = 20 }
                        }
                        operating_rules = @{
                            type = "array"
                            minItems = 3
                            items = @{ type = "string"; minLength = 20 }
                        }
                        artifact_blocks = @{
                            type = "array"
                            minItems = 1
                            items = @{
                                type = "object"
                                additionalProperties = $false
                                properties = @{
                                    artifact_type = @{
                                        type = "string"
                                        enum = @("table", "scoring_model", "decision_tree", "step_sequence", "operating_matrix")
                                    }
                                    title = @{ type = "string"; minLength = 5 }
                                    content_markdown = @{ type = "string"; minLength = 40 }
                                    usage_note = @{ type = "string"; minLength = 20 }
                                }
                                required = @("artifact_type", "title", "content_markdown", "usage_note")
                            }
                        }
                    }
                    required = @("premise", "components", "decision_logic", "operating_rules", "artifact_blocks")
                }
                ai_enablement = @{
                    type = "object"
                    additionalProperties = $false
                    properties = @{
                        role_of_ai = @{ type = "string"; minLength = 60 }
                        automate = @{
                            type = "array"
                            minItems = 3
                            items = @{ type = "string"; minLength = 12 }
                        }
                        human_control_points = @{
                            type = "array"
                            minItems = 3
                            items = @{ type = "string"; minLength = 15 }
                        }
                        execution_notes = @{
                            type = "array"
                            minItems = 3
                            items = @{ type = "string"; minLength = 15 }
                        }
                    }
                    required = @("role_of_ai", "automate", "human_control_points", "execution_notes")
                }
                implementation_path = @{
                    type = "array"
                    minItems = 3
                    items = @{
                        type = "object"
                        additionalProperties = $false
                        properties = @{
                            step_name = @{ type = "string"; minLength = 5 }
                            action = @{ type = "string"; minLength = 25 }
                            output = @{ type = "string"; minLength = 12 }
                            owner = @{ type = "string"; minLength = 3 }
                        }
                        required = @("step_name", "action", "output", "owner")
                    }
                }
                case_illustration = @{
                    type = "object"
                    additionalProperties = $false
                    properties = @{
                        scenario_label = @{ type = "string"; minLength = 5 }
                        context = @{ type = "string"; minLength = 80 }
                        constraints = @{
                            type = "array"
                            minItems = 3
                            items = @{ type = "string"; minLength = 15 }
                        }
                        walk_through = @{
                            type = "array"
                            minItems = 3
                            items = @{ type = "string"; minLength = 25 }
                        }
                        tradeoffs = @{
                            type = "array"
                            minItems = 2
                            items = @{ type = "string"; minLength = 15 }
                        }
                        result = @{ type = "string"; minLength = 60 }
                    }
                    required = @("scenario_label", "context", "constraints", "walk_through", "tradeoffs", "result")
                }
                leadership_implications = @{
                    type = "array"
                    minItems = 3
                    items = @{ type = "string"; minLength = 20 }
                }
                conclusion = @{ type = "string"; minLength = 120 }
                distillation_posts = @{
                    type = "array"
                    items = @{
                        type = "object"
                        additionalProperties = $false
                        properties = @{
                            idea_title = @{ type = "string"; minLength = 5 }
                            post = @{ type = "string"; minLength = 60 }
                        }
                        required = @("idea_title", "post")
                    }
                }
            }
            required = @(
                "title",
                "meta_summary",
                "abstract",
                "core_thesis",
                "system_model_name",
                "problem_definition",
                "current_state_analysis",
                "failure_modes",
                "system_model",
                "ai_enablement",
                "implementation_path",
                "case_illustration",
                "leadership_implications",
                "conclusion"
            )
        }
    }
}

function Convert-BossKeyDeepResearchToWordCount {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return 0
    }

    $matches = [regex]::Matches($Text, '\b[\w''/-]+\b')
    return $matches.Count
}

function Convert-BossKeyDeepResearchTableCell {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return ""
    }

    $clean = ([string]$Value).Trim()
    $clean = $clean -replace '\r?\n+', '<br>'
    $clean = $clean.Replace('|', '\|')
    return $clean
}

function Convert-BossKeyDeepResearchBulletList {
    param([object[]]$Items)

    $lines = New-Object System.Collections.Generic.List[string]
    foreach ($item in @($Items)) {
        if ($null -eq $item) {
            continue
        }
        $text = ([string]$item).Trim()
        if (-not [string]::IsNullOrWhiteSpace($text)) {
            $lines.Add("- $text")
        }
    }
    return ,([string[]]$lines.ToArray())
}

function Convert-BossKeyDeepResearchOrderedList {
    param([object[]]$Items)

    $lines = New-Object System.Collections.Generic.List[string]
    $index = 1
    foreach ($item in @($Items)) {
        if ($null -eq $item) {
            continue
        }
        $text = ([string]$item).Trim()
        if (-not [string]::IsNullOrWhiteSpace($text)) {
            $lines.Add(("{0}. {1}" -f $index, $text))
            $index++
        }
    }
    return ,([string[]]$lines.ToArray())
}

function Add-BossKeyDeepResearchLines {
    param(
        [System.Collections.Generic.List[string]]$Lines,
        [object[]]$Items
    )

    foreach ($item in @($Items)) {
        if ($null -eq $item) {
            continue
        }

        $text = [string]$item
        if (-not [string]::IsNullOrWhiteSpace($text)) {
            $Lines.Add($text)
        }
    }
}

function Convert-BossKeyDeepResearchResearchPackToMarkdown {
    param([pscustomobject]$ResearchPack)

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("# Research Pack")
    $lines.Add("")
    $lines.Add("## Topic")
    $lines.Add([string]$ResearchPack.topic)
    $lines.Add("")
    $lines.Add("## Thesis Statement")
    $lines.Add([string]$ResearchPack.thesis_statement)
    $lines.Add("")
    $lines.Add("## Core Problem Space")
    $lines.Add([string]$ResearchPack.core_problem_space)
    $lines.Add("")
    $lines.Add("## Mapped Domains")
    foreach ($domain in @($ResearchPack.mapped_domains)) {
        $lines.Add("- **$([string]$domain.domain):** $([string]$domain.relevance)")
    }
    $lines.Add("")
    $lines.Add("## Known Best Practices")
    Add-BossKeyDeepResearchLines -Lines $lines -Items (Convert-BossKeyDeepResearchBulletList -Items $ResearchPack.known_best_practices)
    $lines.Add("")
    $lines.Add("## Common Failure Modes")
    foreach ($mode in @($ResearchPack.common_failure_modes)) {
        $lines.Add("### $([string]$mode.name)")
        $lines.Add([string]$mode.pattern)
        $lines.Add("")
        $lines.Add("- Operational effect: $([string]$mode.operational_effect)")
        $lines.Add("")
    }
    $lines.Add("## Gaps in Current Thinking")
    Add-BossKeyDeepResearchLines -Lines $lines -Items (Convert-BossKeyDeepResearchBulletList -Items $ResearchPack.current_thinking_gaps)
    $lines.Add("")
    $lines.Add("## Synthesized Perspective")
    $lines.Add([string]$ResearchPack.synthesized_perspective)
    $lines.Add("")
    $lines.Add("## What the Industry Misses")
    $lines.Add([string]$ResearchPack.what_industry_misses)
    $lines.Add("")
    $lines.Add("## Framework Candidates")
    foreach ($framework in @($ResearchPack.framework_candidates)) {
        $lines.Add("- **$([string]$framework.name):** $([string]$framework.premise)")
    }
    $lines.Add("")
    $lines.Add("## Sources")
    $lines.Add("| Title | Publisher | Class | Authority | Core claim support | Relevance note | URL |")
    $lines.Add("| --- | --- | --- | --- | --- | --- | --- |")
    foreach ($source in @($ResearchPack.sources)) {
        $formattedSourceRow = "| {0} | {1} | {2} | {3} | {4} | {5} | {6} |" -f
            (Convert-BossKeyDeepResearchTableCell -Value $source.title),
            (Convert-BossKeyDeepResearchTableCell -Value $source.publisher),
            (Convert-BossKeyDeepResearchTableCell -Value $source.source_class),
            (Convert-BossKeyDeepResearchTableCell -Value $source.authority_level),
            (Convert-BossKeyDeepResearchTableCell -Value $(if ($source.core_claim_support) { "yes" } else { "no" })),
            (Convert-BossKeyDeepResearchTableCell -Value $source.relevance_note),
            (Convert-BossKeyDeepResearchTableCell -Value $source.url)
        $lines.Add($formattedSourceRow)
    }
    $lines.Add("")
    return ($lines -join "`n").Trim() + "`n"
}

function Convert-BossKeyDeepResearchDistillationToMarkdown {
    param([object[]]$Posts)

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("# Distillation Layer")
    $lines.Add("")
    $index = 1
    foreach ($post in @($Posts)) {
        $lines.Add("## Post ${index}: $([string]$post.idea_title)")
        $lines.Add([string]$post.post)
        $lines.Add("")
        $index++
    }
    return ($lines -join "`n").Trim() + "`n"
}

function Convert-BossKeyDeepResearchArticleToMarkdown {
    param([pscustomobject]$Assembly)

    $caseLabel = ([string]$Assembly.case_illustration.scenario_label).Trim()
    if ([string]::IsNullOrWhiteSpace($caseLabel)) {
        $caseLabel = "Composite operating scenario"
    }

    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("# $([string]$Assembly.title)")
    $lines.Add("")
    $lines.Add("## Abstract")
    $lines.Add([string]$Assembly.abstract)
    $lines.Add("")
    $lines.Add("## 1. Problem Definition")
    $lines.Add([string]$Assembly.problem_definition)
    $lines.Add("")
    $lines.Add("## 2. Current State Analysis")
    $lines.Add([string]$Assembly.current_state_analysis)
    $lines.Add("")
    $lines.Add("## 3. Failure Modes")
    $modeIndex = 1
    foreach ($mode in @($Assembly.failure_modes)) {
        $lines.Add("### Failure Mode ${modeIndex}: $([string]$mode.name)")
        $lines.Add([string]$mode.pattern)
        $lines.Add("")
        $lines.Add("- Observable signs: $([string]$mode.observable_signs)")
        $lines.Add("- Operational effect: $([string]$mode.operational_effect)")
        $lines.Add("")
        $modeIndex++
    }
    $lines.Add("## 4. System Model (Core Contribution)")
    $lines.Add("**$([string]$Assembly.system_model_name)**")
    $lines.Add("")
    $lines.Add([string]$Assembly.system_model.premise)
    $lines.Add("")
    $lines.Add("### Component Map")
    $lines.Add("| Component | Purpose | Inputs | Outputs | Decision Owner |")
    $lines.Add("| --- | --- | --- | --- | --- |")
    foreach ($component in @($Assembly.system_model.components)) {
        $formattedComponentRow = "| {0} | {1} | {2} | {3} | {4} |" -f
            (Convert-BossKeyDeepResearchTableCell -Value $component.name),
            (Convert-BossKeyDeepResearchTableCell -Value $component.purpose),
            (Convert-BossKeyDeepResearchTableCell -Value $component.inputs),
            (Convert-BossKeyDeepResearchTableCell -Value $component.outputs),
            (Convert-BossKeyDeepResearchTableCell -Value $component.owner)
        $lines.Add($formattedComponentRow)
    }
    $lines.Add("")
    $lines.Add("### Decision Logic")
    Add-BossKeyDeepResearchLines -Lines $lines -Items (Convert-BossKeyDeepResearchOrderedList -Items $Assembly.system_model.decision_logic)
    $lines.Add("")
    $lines.Add("### Operating Rules")
    Add-BossKeyDeepResearchLines -Lines $lines -Items (Convert-BossKeyDeepResearchBulletList -Items $Assembly.system_model.operating_rules)
    $lines.Add("")
    foreach ($artifact in @($Assembly.system_model.artifact_blocks)) {
        $lines.Add("### Artifact: $([string]$artifact.title)")
        $lines.Add("- Type: $([string]$artifact.artifact_type)")
        $lines.Add("- Use: $([string]$artifact.usage_note)")
        $lines.Add("")
        $lines.Add([string]$artifact.content_markdown)
        $lines.Add("")
    }
    $lines.Add("## 5. AI Enablement Layer")
    $lines.Add([string]$Assembly.ai_enablement.role_of_ai)
    $lines.Add("")
    $lines.Add("### Automate")
    Add-BossKeyDeepResearchLines -Lines $lines -Items (Convert-BossKeyDeepResearchBulletList -Items $Assembly.ai_enablement.automate)
    $lines.Add("")
    $lines.Add("### Keep Human-Controlled")
    Add-BossKeyDeepResearchLines -Lines $lines -Items (Convert-BossKeyDeepResearchBulletList -Items $Assembly.ai_enablement.human_control_points)
    $lines.Add("")
    $lines.Add("### Execution Notes")
    Add-BossKeyDeepResearchLines -Lines $lines -Items (Convert-BossKeyDeepResearchBulletList -Items $Assembly.ai_enablement.execution_notes)
    $lines.Add("")
    $lines.Add("## 6. Implementation Path")
    $stepIndex = 1
    foreach ($step in @($Assembly.implementation_path)) {
        $lines.Add("### Step ${stepIndex}: $([string]$step.step_name)")
        $lines.Add([string]$step.action)
        $lines.Add("")
        $lines.Add("- Output: $([string]$step.output)")
        $lines.Add("- Owner: $([string]$step.owner)")
        $lines.Add("")
        $stepIndex++
    }
    $lines.Add("## 7. Case Illustration")
    $lines.Add("**$caseLabel**")
    $lines.Add("")
    $lines.Add("_Composite scenario used to show how the system behaves under realistic constraints and tradeoffs._")
    $lines.Add("")
    $lines.Add([string]$Assembly.case_illustration.context)
    $lines.Add("")
    $lines.Add("### Constraints")
    Add-BossKeyDeepResearchLines -Lines $lines -Items (Convert-BossKeyDeepResearchBulletList -Items $Assembly.case_illustration.constraints)
    $lines.Add("")
    $lines.Add("### Walk-through")
    Add-BossKeyDeepResearchLines -Lines $lines -Items (Convert-BossKeyDeepResearchOrderedList -Items $Assembly.case_illustration.walk_through)
    $lines.Add("")
    $lines.Add("### Tradeoffs")
    Add-BossKeyDeepResearchLines -Lines $lines -Items (Convert-BossKeyDeepResearchBulletList -Items $Assembly.case_illustration.tradeoffs)
    $lines.Add("")
    $lines.Add("### Result")
    $lines.Add([string]$Assembly.case_illustration.result)
    $lines.Add("")
    $lines.Add("## 8. Implications for Leadership")
    Add-BossKeyDeepResearchLines -Lines $lines -Items (Convert-BossKeyDeepResearchBulletList -Items $Assembly.leadership_implications)
    $lines.Add("")
    $lines.Add("## 9. Conclusion")
    $lines.Add([string]$Assembly.conclusion)
    $lines.Add("")
    return ($lines -join "`n").Trim() + "`n"
}

function Test-BossKeyDeepResearchArticleAssembly {
    param(
        [pscustomobject]$Assembly,
        [int]$TargetWords = 3000,
        [string]$ArtifactFocus = ""
    )

    $markdown = Convert-BossKeyDeepResearchArticleToMarkdown -Assembly $Assembly
    $headings = @()
    foreach ($line in ($markdown -split "`r?`n")) {
        if ($line -match '^##\s+(.+)$') {
            $headings += $matches[1].Trim()
        }
    }
    $expected = Get-BossKeyDeepResearchExpectedHeadings
    $issues = New-Object System.Collections.Generic.List[string]

    if (($headings -join "||") -ne ($expected -join "||")) {
        $issues.Add("Article headings do not match the required section order.")
    }

    $bounds = Get-BossKeyDeepResearchWordCountBounds -TargetWords $TargetWords
    $wordCount = Convert-BossKeyDeepResearchToWordCount -Text $markdown
    if ($wordCount -lt $bounds.minimum -or $wordCount -gt $bounds.maximum) {
        $issues.Add("Article word count $wordCount is outside the allowed range of $($bounds.minimum)-$($bounds.maximum).")
    }

    $failureModeCount = @($Assembly.failure_modes).Count
    if ($failureModeCount -lt 3 -or $failureModeCount -gt 6) {
        $issues.Add("Failure mode count must be between 3 and 6.")
    }

    $artifactCount = @($Assembly.system_model.artifact_blocks).Count
    if ($artifactCount -lt 1) {
        $issues.Add("At least one usable system artifact is required.")
    }

    if (-not [string]::IsNullOrWhiteSpace($ArtifactFocus)) {
        $focus = $ArtifactFocus.ToLowerInvariant()
        $artifactMatch = $false
        foreach ($artifact in @($Assembly.system_model.artifact_blocks)) {
            $haystack = ("{0} {1} {2}" -f $artifact.artifact_type, $artifact.title, $artifact.content_markdown).ToLowerInvariant()
            if ($haystack.Contains($focus)) {
                $artifactMatch = $true
                break
            }
        }
        if (-not $artifactMatch) {
            $issues.Add("Artifact focus '$ArtifactFocus' was not reflected in the system artifact layer.")
        }
    }

    $humanControlCount = @($Assembly.ai_enablement.human_control_points).Count
    if ($humanControlCount -lt 3) {
        $issues.Add("AI enablement must include explicit human control points.")
    }

    foreach ($phrase in (Get-BossKeyDeepResearchBannedPhrases)) {
        if ($markdown.ToLowerInvariant().Contains($phrase.ToLowerInvariant())) {
            $issues.Add("Banned marketing phrase detected: $phrase")
        }
    }

    $systemName = ([string]$Assembly.system_model_name).Trim()
    if ([string]::IsNullOrWhiteSpace($systemName)) {
        $issues.Add("A named system model is required.")
    }

    return [pscustomobject]@{
        is_valid = ($issues.Count -eq 0)
        word_count = $wordCount
        minimum_word_count = $bounds.minimum
        maximum_word_count = $bounds.maximum
        issues = $issues.ToArray()
        markdown = $markdown
    }
}
