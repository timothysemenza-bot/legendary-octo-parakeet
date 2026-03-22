param()

$repoRoot = Split-Path -Parent $PSScriptRoot
$customAgentRoot = Join-Path $repoRoot ".codex/agents"
$briefRoot = Join-Path $repoRoot "agents/apmp-foundation"
$docsRoot = Join-Path $repoRoot "docs"
$registryPath = Join-Path $docsRoot "apmp-foundation-agent-map.md"
$briefIndexPath = Join-Path $briefRoot "README.md"

New-Item -ItemType Directory -Force -Path $customAgentRoot | Out-Null
New-Item -ItemType Directory -Force -Path $briefRoot | Out-Null
New-Item -ItemType Directory -Force -Path $docsRoot | Out-Null

$competencies = @(
    [pscustomobject]@{ Id = 1; Unit = "Focus on the Customer"; Title = "Focus on the Customer"; Slug = "focus-on-the-customer"; Use = "customer-first framing, evaluator priorities, and buyer-centered messaging" },
    [pscustomobject]@{ Id = 2; Unit = "Focus on the Customer"; Title = "Identifying Requirements for Compliance and Responsiveness"; Slug = "identifying-requirements-for-compliance-and-responsiveness"; Use = "requirement extraction, compliance mapping, and responsiveness checks" },
    [pscustomobject]@{ Id = 3; Unit = "Focus on the Customer"; Title = "Customer Relationship Management Systems"; Slug = "customer-relationship-management-systems"; Use = "relationship tracking, account memory, and structured customer contact strategy" },
    [pscustomobject]@{ Id = 4; Unit = "Focus on the Customer"; Title = "Developing an Opportunity/Capture Management Strategy"; Slug = "developing-an-opportunity-capture-management-strategy"; Use = "capture planning, positioning, and early win-strategy work" },
    [pscustomobject]@{ Id = 5; Unit = "Focus on the Customer"; Title = "Value Propositions"; Slug = "value-propositions"; Use = "outcome framing, value articulation, and differentiating business benefits" },
    [pscustomobject]@{ Id = 6; Unit = "Focus on the Customer"; Title = "Customer and Competitor Intelligence"; Slug = "customer-and-competitor-intelligence"; Use = "customer research, competitive analysis, and positioning evidence" },
    [pscustomobject]@{ Id = 7; Unit = "Focus on the Customer"; Title = "Executive Summaries"; Slug = "executive-summaries"; Use = "executive summary strategy, structure, and high-level persuasion" },
    [pscustomobject]@{ Id = 8; Unit = "Focus on the Customer"; Title = "Strategy and Win Themes"; Slug = "strategy-and-win-themes"; Use = "win-theme development, message hierarchy, and competitive positioning" },
    [pscustomobject]@{ Id = 9; Unit = "Focus on the Customer"; Title = "Proposal Theme Statements"; Slug = "proposal-theme-statements"; Use = "theme statements, section messaging, and evaluator memory hooks" },
    [pscustomobject]@{ Id = 10; Unit = "Focus on the Customer"; Title = "Features, Benefits, and Discriminators"; Slug = "features-benefits-and-discriminators"; Use = "feature-to-benefit translation and discriminator proofing" },
    [pscustomobject]@{ Id = 11; Unit = "Focus on the Customer"; Title = "Proof Points"; Slug = "proof-points"; Use = "evidence selection, quantified claims, and credibility support" },
    [pscustomobject]@{ Id = 12; Unit = "Focus on the Customer"; Title = "Competitive Price to Win"; Slug = "competitive-price-to-win"; Use = "price-to-win framing, affordability analysis, and value-based pricing logic" },
    [pscustomobject]@{ Id = 13; Unit = "Create Deliverables"; Title = "Create Deliverables"; Slug = "create-deliverables"; Use = "deliverable planning, assembly ownership, and packaging readiness" },
    [pscustomobject]@{ Id = 14; Unit = "Create Deliverables"; Title = "Compliance Matrix"; Slug = "compliance-matrix"; Use = "compliance matrix buildout, maintenance, and gap reviews" },
    [pscustomobject]@{ Id = 15; Unit = "Create Deliverables"; Title = "Cost and Pricing Data"; Slug = "cost-and-pricing-data"; Use = "pricing narratives, cost support material, and pricing consistency checks" },
    [pscustomobject]@{ Id = 16; Unit = "Create Deliverables"; Title = "Developing and Delivering Effective Presentations"; Slug = "developing-and-delivering-effective-presentations"; Use = "oral presentation prep, slide logic, and rehearsal support" },
    [pscustomobject]@{ Id = 17; Unit = "Create Deliverables"; Title = "Proposal Organization"; Slug = "proposal-organization"; Use = "proposal structure, section order, and evaluator-friendly navigation" },
    [pscustomobject]@{ Id = 18; Unit = "Create Deliverables"; Title = "Persuasive Writing"; Slug = "persuasive-writing"; Use = "persuasive proposal drafting and customer-benefit language" },
    [pscustomobject]@{ Id = 19; Unit = "Create Deliverables"; Title = "Writing Clearly"; Slug = "writing-clearly"; Use = "clarity edits, simplification, and readability improvements" },
    [pscustomobject]@{ Id = 20; Unit = "Create Deliverables"; Title = "Headings"; Slug = "headings"; Use = "headline development, section guidance, and message-forward headings" },
    [pscustomobject]@{ Id = 21; Unit = "Create Deliverables"; Title = "Graphics"; Slug = "graphics"; Use = "graphic concepts, captions, and visual proof support" },
    [pscustomobject]@{ Id = 22; Unit = "Create Deliverables"; Title = "Page and Document Design"; Slug = "page-and-document-design"; Use = "document layout, page design, and readability standards" },
    [pscustomobject]@{ Id = 23; Unit = "Manage Processes"; Title = "Managing Internal Risk"; Slug = "managing-internal-risk"; Use = "proposal execution risk logs, mitigations, and escalations" },
    [pscustomobject]@{ Id = 24; Unit = "Manage Processes"; Title = "Lessons Learned Analysis and Management"; Slug = "lessons-learned-analysis-and-management"; Use = "retrospectives, debrief synthesis, and reusable lessons capture" },
    [pscustomobject]@{ Id = 25; Unit = "Use Tools and Systems"; Title = "Use Tools and Systems"; Slug = "use-tools-and-systems"; Use = "tooling choices, collaboration systems, and workflow enablement" },
    [pscustomobject]@{ Id = 26; Unit = "Use Tools and Systems"; Title = "Proposal Management Plans"; Slug = "proposal-management-plans"; Use = "proposal plans, roles, milestones, and management controls" },
    [pscustomobject]@{ Id = 27; Unit = "Use Tools and Systems"; Title = "Content Plans"; Slug = "content-plans"; Use = "content outlines, section ownership, and content development plans" },
    [pscustomobject]@{ Id = 28; Unit = "Use Tools and Systems"; Title = "Knowledge Management"; Slug = "knowledge-management"; Use = "content libraries, reusable assets, and retrieval strategy" },
    [pscustomobject]@{ Id = 29; Unit = "Use Tools and Systems"; Title = "Interviewing Subject Matter Experts"; Slug = "interviewing-subject-matter-experts"; Use = "SME interview prep, extraction prompts, and synthesis" },
    [pscustomobject]@{ Id = 30; Unit = "Use Tools and Systems"; Title = "Maintaining a Library and Writing Standard in Your Organization"; Slug = "maintaining-a-library-and-writing-standard-in-your-organization"; Use = "writing standards, library governance, and reusable content hygiene" },
    [pscustomobject]@{ Id = 31; Unit = "Create Deliverables"; Title = "Relevant Past Performance"; Slug = "relevant-past-performance"; Use = "past performance selection, relevance mapping, and proof formatting" },
    [pscustomobject]@{ Id = 32; Unit = "Create Deliverables"; Title = "Resumes"; Slug = "resumes"; Use = "key-personnel resume tailoring and compliance alignment" },
    [pscustomobject]@{ Id = 33; Unit = "Manage Processes"; Title = "Manage Processes"; Slug = "manage-processes"; Use = "process control, workflow design, and execution discipline" },
    [pscustomobject]@{ Id = 34; Unit = "Manage Processes"; Title = "End-to-End Process"; Slug = "end-to-end-process"; Use = "lifecycle mapping from capture through submission and handoff" },
    [pscustomobject]@{ Id = 35; Unit = "Manage Processes"; Title = "Gate Decisions"; Slug = "gate-decisions"; Use = "go-no-go reviews, pursuit qualification, and decision criteria" },
    [pscustomobject]@{ Id = 36; Unit = "Manage Processes"; Title = "Kickoff Meeting Management"; Slug = "kickoff-meeting-management"; Use = "kickoff agendas, alignment, and launch discipline" },
    [pscustomobject]@{ Id = 37; Unit = "Manage Processes"; Title = "Daily Team Management"; Slug = "daily-team-management"; Use = "day-to-day coordination, task ownership, and issue surfacing" },
    [pscustomobject]@{ Id = 38; Unit = "Manage Processes"; Title = "Review Management"; Slug = "review-management"; Use = "pink, red, gold, and structured review workflows" },
    [pscustomobject]@{ Id = 39; Unit = "Manage Processes"; Title = "Production Management"; Slug = "production-management"; Use = "production control, submission readiness, and final packaging" },
    [pscustomobject]@{ Id = 40; Unit = "Manage Processes"; Title = "Virtual Team Management"; Slug = "virtual-team-management"; Use = "remote-team coordination, collaboration rhythms, and dispersed execution" }
)

function Get-AgentFileName {
    param([pscustomobject]$Competency)
    return ("apmp-{0:D2}-{1}.toml" -f $Competency.Id, $Competency.Slug)
}

function Get-BriefFileName {
    param([pscustomobject]$Competency)
    return ("{0:D2}-{1}.md" -f $Competency.Id, $Competency.Slug)
}

function Get-ShortNickname {
    param([pscustomobject]$Competency)
    $parts = $Competency.Slug -split "-"
    if ($parts.Count -ge 2) {
        return ($parts[0] + " " + $parts[1])
    }
    return $Competency.Slug
}

$registryLines = [System.Collections.Generic.List[string]]::new()
$registryLines.Add('# APMP Foundation Agent Map') | Out-Null
$registryLines.Add('') | Out-Null
$registryLines.Add('This registry maps APMP Foundation Version 4 competency areas to repo-local Codex custom agents and human-readable role briefs.') | Out-Null
$registryLines.Add('') | Out-Null
$registryLines.Add('Source note: the official APMP Helpjuice study guide page is login-gated, so this map is based on publicly accessible secondary summaries of the V4 competency structure.') | Out-Null
$registryLines.Add('') | Out-Null
$registryLines.Add('Public references used for this mapping:') | Out-Null
$registryLines.Add('- [APMP Foundation Study Guide V4 - Key Competency Summaries and Exam Preparation](https://baachuscribble.com/apmp-foundation-study-guide-v4-key-competency-summaries-exam-preparation-3/)') | Out-Null
$registryLines.Add('- [What''s New in the APMP V4 Foundation Certification Exam? A Complete Guide for Students](https://baachuscribble.com/whats-new-in-the-apmp-v4-foundation-certification-exam-a-complete-guide-for-students/)') | Out-Null
$registryLines.Add('') | Out-Null
$registryLines.Add('If you want this aligned one-to-one with the exact member-only Helpjuice chapter wording, regenerate after confirming the official titles.') | Out-Null
$registryLines.Add('') | Out-Null

$briefIndexLines = [System.Collections.Generic.List[string]]::new()
$briefIndexLines.Add('# APMP Foundation Agents') | Out-Null
$briefIndexLines.Add('') | Out-Null
$briefIndexLines.Add('These briefs describe the APMP Foundation V4 competency agents generated for this repository.') | Out-Null
$briefIndexLines.Add('') | Out-Null
$briefIndexLines.Add('Custom agent definitions live in `.codex/agents/`.') | Out-Null
$briefIndexLines.Add('') | Out-Null

$unitOrder = @("Focus on the Customer", "Create Deliverables", "Manage Processes", "Use Tools and Systems")
foreach ($unit in $unitOrder) {
    $registryLines.Add("## $unit") | Out-Null
    $registryLines.Add('') | Out-Null
    $registryLines.Add('| ID | Competency | Custom Agent | Brief | When to use |') | Out-Null
    $registryLines.Add('| --- | --- | --- | --- | --- |') | Out-Null

    $briefIndexLines.Add("## $unit") | Out-Null
    $briefIndexLines.Add('') | Out-Null

    foreach ($competency in ($competencies | Where-Object { $_.Unit -eq $unit } | Sort-Object Id)) {
        $idLabel = '{0:D2}' -f $competency.Id
        $agentFile = Get-AgentFileName -Competency $competency
        $briefFile = Get-BriefFileName -Competency $competency
        $agentPath = Join-Path $customAgentRoot $agentFile
        $briefPath = Join-Path $briefRoot $briefFile

        $previousCompetency = $competencies | Where-Object { $_.Id -eq ($competency.Id - 1) } | Select-Object -First 1
        $nextCompetency = $competencies | Where-Object { $_.Id -eq ($competency.Id + 1) } | Select-Object -First 1

        $adjacentNames = @()
        if ($previousCompetency) {
            $adjacentNames += ("APMP {0:D2} {1}" -f $previousCompetency.Id, $previousCompetency.Title)
        }
        if ($nextCompetency) {
            $adjacentNames += ("APMP {0:D2} {1}" -f $nextCompetency.Id, $nextCompetency.Title)
        }

        $handoffLine = if ($adjacentNames.Count -gt 0) {
            $adjacentNames -join "; "
        } else {
            "implementation-agent; documentation-agent; qa-reviewer"
        }

        $nickname = Get-ShortNickname -Competency $competency
        $agentName = ("apmp_{0:D2}_{1}" -f $competency.Id, ($competency.Slug -replace '-', '_'))
        $agentToml = @"
name = "$agentName"
description = "APMP Foundation competency agent for $($competency.Title). Use for $($competency.Use)."
model = "gpt-5.4-mini"
model_reasoning_effort = "medium"
developer_instructions = """
You are the APMP Foundation competency agent for "$($competency.Title)".

Mission:
- Apply the APMP V4 competency "$($competency.Title)" to the current proposal, capture, bid, or process task.

Scope:
- Focus on $($competency.Use).
- Translate the competency into concrete deliverables, review notes, edits, checklists, or recommendations.
- Keep outputs practical and operator-ready.

Rules:
- Stay anchored to this competency first, then name any adjacent competencies that should continue the work.
- State assumptions, missing inputs, and risks explicitly.
- Prefer customer-ready or operator-ready artifacts over study-note summaries.
- If the task exceeds this competency, recommend the next APMP agent by name.

Output:
- Clear recommendations or edits
- Draft artifacts or checklists where useful
- Handoff notes to the next APMP competency agent when appropriate
"""
nickname_candidates = ["APMP $idLabel", "$nickname", "$($competency.Unit)"]
"@
        Set-Content -Path $agentPath -Value $agentToml

$briefContent = @"
# APMP ${idLabel}: $($competency.Title)

Unit: $($competency.Unit)

Mission: apply the APMP V4 competency "$($competency.Title)" to active bid, proposal, capture, or process work.

Scope:
- focus on $($competency.Use)
- convert the competency into practical outputs, not abstract exam notes
- support draft creation, reviews, planning, and handoffs inside this repo

Constraints:
- stay anchored to this competency unless the task clearly crosses into an adjacent one
- make assumptions explicit
- prefer concise, operator-ready outputs

Inputs:
- current opportunity or project context
- source material, requirements, drafts, or process notes
- deadlines, review checkpoints, and delivery constraints when available

Outputs:
- recommendations, edits, or draft language
- checklists, trackers, or review notes when useful
- a clean handoff suggestion to the next APMP competency agent

Handoff expectations:
- adjacent APMP competencies: $handoffLine
- repo-wide implementation follow-up: implementation-agent, documentation-agent, or qa-reviewer when the work moves from domain guidance to execution
"@
        Set-Content -Path $briefPath -Value $briefContent

        $registryLines.Add(('| {0} | {1} | `.codex/agents/{2}` | `agents/apmp-foundation/{3}` | {4} |' -f $idLabel, $competency.Title, $agentFile, $briefFile, $competency.Use)) | Out-Null
        $briefIndexLines.Add(('- `APMP {0}` {1}' -f $idLabel, $competency.Title)) | Out-Null
    }

    $registryLines.Add('') | Out-Null
    $briefIndexLines.Add('') | Out-Null
}

Set-Content -Path $registryPath -Value ($registryLines -join [Environment]::NewLine)
Set-Content -Path $briefIndexPath -Value ($briefIndexLines -join [Environment]::NewLine)

Write-Output ("Generated {0} APMP Foundation custom agents in {1}" -f $competencies.Count, $customAgentRoot)
Write-Output ("Generated APMP Foundation briefs in {0}" -f $briefRoot)
Write-Output ("Updated registry at {0}" -f $registryPath)
