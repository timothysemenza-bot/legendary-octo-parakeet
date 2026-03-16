param(
    [string]$ContentSourcesFile = "marketing-agents/data/boss_key_content_sources.csv",
    [string]$ContentQueueFile = "marketing-agents/data/boss_key_content_queue.csv",
    [string]$RelationshipQueueFile = "marketing-agents/data/boss_key_relationship_queue.csv",
    [string]$ConversationMemoryFile = "marketing-agents/data/boss_key_conversation_memory.csv",
    [string]$MeetingQueueFile = "marketing-agents/data/boss_key_meeting_queue.csv",
    [string]$PtwQueueFile = "marketing-agents/data/boss_key_ptw_queue.csv",
    [string]$ProposalQueueFile = "marketing-agents/data/boss_key_preconsult_proposals.csv",
    [string]$KnowledgeBaseFile = "marketing-agents/data/boss_key_competitive_kb.csv",
    [string]$OutcomeLogFile = "marketing-agents/data/boss_key_ptw_outcomes.csv",
    [string]$PriceBookFile = "marketing-agents/data/boss_key_private_price_book.csv",
    [string]$ModifierFile = "marketing-agents/data/boss_key_price_modifiers.csv",
    [string]$DecisionFile = "marketing-agents/data/boss_key_review_decisions.csv",
    [string]$BusyBlocksFile = "marketing-agents/data/busy_blocks.csv",
    [string]$ReviewPacketFile = "marketing-agents/briefs/boss-key-review-packet-latest.md",
    [string]$LinkedInDraftDir = "marketing-agents/briefs/generated/boss-key-growth-os/linkedin",
    [string]$MeetingDraftDir = "marketing-agents/briefs/generated/boss-key-growth-os/meetings",
    [string]$PtwDraftDir = "marketing-agents/briefs/generated/boss-key-growth-os/ptw",
    [string]$ProposalDraftDir = "marketing-agents/briefs/generated/boss-key-growth-os/proposals",
    [switch]$RefreshDrafts,
    [switch]$SkipProposalOpsSync
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "boss-key-growth-os-helpers.ps1")
. (Join-Path $PSScriptRoot "boss-key-ptw-helpers.ps1")

if (-not $SkipProposalOpsSync) {
    & (Join-Path $PSScriptRoot "sync-boss-key-proposal-ops.ps1") `
        -Mode HydrateQueues `
        -RelationshipQueueFile $RelationshipQueueFile `
        -ConversationMemoryFile $ConversationMemoryFile `
        -KnowledgeBaseFile $KnowledgeBaseFile `
        -ProposalQueueFile $ProposalQueueFile | Out-Null
}

$contentPropertyOrder = @(
    "content_id", "created_date", "cadence_type", "source_id", "source_type",
    "source_path", "source_title", "title", "slug", "summary", "article_draft_path",
    "article_output_path", "company_linkedin_draft_path", "personal_linkedin_draft_path",
    "scheduled_publish_date", "owner_decision", "review_status", "website_status",
    "rss_status", "linkedin_company_status", "linkedin_personal_status", "published_date", "notes"
)

$relationshipPropertyOrder = @(
    "relationship_id", "created_date", "company_name", "contact_name", "role",
    "linkedin_profile_url", "linkedin_company_url", "relationship_stage", "warm_signal",
    "fit_confirmed", "pain_point", "desired_outcome", "offer_hypothesis",
    "urgency_level", "scope_breadth", "stakeholder_complexity", "research_load",
    "delivery_intensity", "last_touch_date", "last_interaction_summary",
    "next_best_touch_type", "next_best_touch_path", "meeting_needed", "meeting_status",
    "proposal_status", "ptw_status", "ptw_stage", "ptw_recommendation", "ptw_record_id",
    "owner_decision", "review_status", "ready_state", "notes"
)

$meetingPropertyOrder = @(
    "meeting_id", "relationship_id", "created_date", "company_name", "contact_name",
    "relationship_stage", "meeting_reason", "qualification_summary", "slot_1_start",
    "slot_1_end", "slot_2_start", "slot_2_end", "slot_3_start", "slot_3_end",
    "booking_message_path", "invite_packet_path", "owner_decision", "review_status",
    "status", "notes"
)

$ptwPropertyOrder = @(
    "ptw_id", "relationship_id", "created_date", "refreshed_at", "archived_at",
    "revision_number", "is_active", "company_name", "contact_name", "ptw_stage",
    "target_account_fit", "customer_objective", "customer_need", "customer_value_drivers",
    "buyer_priorities", "evaluation_priorities", "buying_behavior", "delivery_context",
    "timing_context", "budget_signal", "budget_band", "budget_confidence",
    "likely_competitors", "incumbent_status", "substitute_options", "big4_technical",
    "big4_management", "big4_past_performance", "big4_cost_price",
    "differentiation_hypothesis", "recommended_entry_offer", "expansion_offer",
    "price_to_compete_usd", "price_to_win_usd", "minimum_acceptable_price_usd",
    "pursue_recommendation", "data_confidence", "evidence_summary", "assumptions",
    "source_quality_notes", "source_reliability", "source_summary", "ptw_brief_path",
    "owner_decision", "review_status", "status", "notes"
)

$proposalPropertyOrder = @(
    "proposal_id", "relationship_id", "ptw_id", "created_date", "company_name", "contact_name",
    "offer_name", "recommended_entry_offer", "expansion_offer", "ptw_stage",
    "price_to_compete_usd", "recommended_price_usd", "price_to_win_usd",
    "minimum_acceptable_price_usd", "maximum_price_usd", "ptw_confidence",
    "pursue_recommendation", "pricing_basis", "pricing_anchor", "pricing_rationale",
    "ptw_brief_path", "owner_confirmation_required", "discovery_summary", "scope_summary",
    "assumptions", "exclusions", "recommended_agenda", "pricing_status", "proposal_path",
    "owner_decision", "review_status", "status", "notes"
)

$knowledgePropertyOrder = @(
    "knowledge_id", "relationship_id", "company_name", "entity_type", "entity_name",
    "source_type", "source_reference", "source_date", "source_reliability", "confidence",
    "customer_objective", "customer_need", "customer_value_drivers", "buyer_priorities",
    "evaluation_priorities", "buying_behavior", "delivery_context", "timing_context",
    "budget_signal", "budget_band", "competitor_name", "incumbent_status",
    "alternative_option", "big4_technical", "big4_management", "big4_past_performance",
    "big4_cost_price", "differentiation_hypothesis", "evidence_summary", "assumptions",
    "ethical_use_check", "last_validated_date", "notes"
)

$outcomePropertyOrder = @(
    "outcome_id", "relationship_id", "company_name", "closed_date", "actual_quoted_price_usd",
    "actual_award_price_usd", "winning_competitor", "outcome_result", "outcome_driver_summary",
    "price_to_compete_usd", "price_to_win_usd", "calibration_delta_compete_usd",
    "calibration_delta_win_usd", "notes"
)

$decisionPropertyOrder = @(
    "item_id", "item_type", "title", "current_status", "draft_path",
    "owner_decision", "revision_notes", "send_mode", "scheduled_date", "notes"
)

function Get-RelationshipNextTouchType {
    param([pscustomobject]$Relationship)

    if (-not [string]::IsNullOrWhiteSpace($Relationship.next_best_touch_type)) {
        return [string]$Relationship.next_best_touch_type
    }

    switch (([string]$Relationship.relationship_stage).Trim().ToLowerInvariant()) {
        "queued" { return "connection-note" }
        "connection-pending" { return "nurture" }
        "connected" { return "first-dm" }
        "engaged" { return "follow-up" }
        "qualified-pre-consult" { return "meeting-ask" }
        "meeting-proposed" { return "meeting-follow-up" }
        "meeting-booked" { return "prep-note" }
        default { return "follow-up" }
    }
}

function Get-RelationshipMemorySummary {
    param(
        [string]$RelationshipId,
        [object[]]$MemoryRows
    )

    $items = @(
        $MemoryRows |
            Where-Object { $_.relationship_id -eq $RelationshipId } |
            Sort-Object {
                try { [datetime]$_.event_date } catch { Get-Date "1900-01-01" }
            } -Descending
    )

    return @($items | Select-Object -First 3)
}

function Get-RelationshipDraftText {
    param(
        [pscustomobject]$Relationship,
        [string]$TouchType,
        [object[]]$MemoryItems,
        [pscustomobject]$ActivePtw
    )

    $contactName = if ([string]::IsNullOrWhiteSpace($Relationship.contact_name)) { "there" } else { [string]$Relationship.contact_name }
    $painPoint = [string]$Relationship.pain_point
    $desiredOutcome = [string]$Relationship.desired_outcome
    $offer = Get-BossKeyString -Value $(if ($null -eq $ActivePtw) { "" } else { $ActivePtw.recommended_entry_offer }) -Fallback ([string]$Relationship.offer_hypothesis)
    $lastSummary = [string]$Relationship.last_interaction_summary
    $memoryLines = @($MemoryItems | ForEach-Object { "- {0}: {1}" -f $_.event_date, $_.message_summary })
    $ptwRecommendation = Get-BossKeyString -Value $(if ($null -eq $ActivePtw) { "" } else { $ActivePtw.pursue_recommendation })

    $message = switch ($TouchType) {
        "connection-note" {
            "Hi $contactName, Timmy Semenza here. I help facilities-service operators tighten the handoff between opportunity visibility, capture decisions, and proposal execution so owners are not dragged into last-minute chaos. Open to connecting?"
        }
        "first-dm" {
            "Thanks for connecting, $contactName. From what I can see, the fastest useful move may be a focused $offer before anything bigger.`n`nIf helpful, I can send a short outline so you can see how I would tighten the handoff without creating more owner drag."
        }
        "meeting-ask" {
            "Thanks again, $contactName. Based on what you shared, I think the most useful next step is a short working session focused on the first win.`n`nIf you are open to it, I can send 2-3 times and a short pre-read so you can see the logic before we talk."
        }
        default {
            "Quick follow-up, $contactName. The last thing that stood out to me was: $lastSummary`n`nIf helpful, I can send a short note on how Boss Key would approach that through a $offer."
        }
    }

    $lines = @()
    $lines += "# $($Relationship.company_name) | $TouchType"
    $lines += ""
    $lines += "Status: Pending owner approval before send."
    $lines += "Relationship stage: $($Relationship.relationship_stage)"
    if (-not [string]::IsNullOrWhiteSpace($ptwRecommendation)) {
        $lines += "PTW posture: $ptwRecommendation via $offer"
    }
    $lines += ""
    $lines += "## Draft"
    $lines += $message
    $lines += ""
    if ($memoryLines.Count -gt 0) {
        $lines += "## Recent memory"
        $lines += $memoryLines
        $lines += ""
    }
    $lines += "## Discovery anchors"
    $lines += "- Pain point: $painPoint"
    $lines += "- Desired outcome: $desiredOutcome"
    $lines += "- Offer hypothesis: $offer"
    $lines += ""
    return ($lines -join "`n").Trim() + "`n"
}

function Test-BossKeyQualifiedRelationship {
    param([pscustomobject]$Relationship)

    if (([string]$Relationship.fit_confirmed).Trim().ToLowerInvariant() -ne "yes") { return $false }
    if ([string]::IsNullOrWhiteSpace([string]$Relationship.warm_signal)) { return $false }
    foreach ($field in @("pain_point", "desired_outcome", "offer_hypothesis")) {
        if ([string]::IsNullOrWhiteSpace([string]$Relationship.$field)) { return $false }
    }
    return $true
}

function Get-BossKeyModifierPercent {
    param(
        [string]$ModifierName,
        [string]$Level,
        [object[]]$ModifierRows
    )

    $match = $ModifierRows | Where-Object {
        $_.modifier_name -eq $ModifierName -and $_.level -eq $Level
    } | Select-Object -First 1

    if ($null -eq $match) { return 0 }
    try { return [decimal]$match.adjustment_percent } catch { return 0 }
}

function Get-BossKeyMeetingMessageText {
    param(
        [pscustomobject]$Relationship,
        [object[]]$Slots,
        [pscustomobject]$ActivePtw
    )

    $contactName = if ([string]::IsNullOrWhiteSpace($Relationship.contact_name)) { "there" } else { [string]$Relationship.contact_name }
    $offer = Get-BossKeyString -Value $(if ($null -eq $ActivePtw) { "" } else { $ActivePtw.recommended_entry_offer }) -Fallback ([string]$Relationship.offer_hypothesis)
    $slotLines = @()
    foreach ($slot in $Slots) {
        $slotLines += "- {0}" -f (Format-BossKeyDisplayDate -Value $slot.start)
    }

    $lines = @()
    $lines += "# $($Relationship.company_name) | Booking message"
    $lines += ""
    $lines += "Status: Pending owner approval before send."
    $lines += ""
    $lines += "## Draft"
    $lines += "Hi $contactName, based on what you shared about $($Relationship.pain_point), I put together a short pre-consult outline and a few windows if you want to talk it through."
    $lines += ""
    $lines += "The goal would be to test whether $offer is the most winnable first move before anything bigger."
    $lines += ""
    $lines += "I can hold any of these:"
    $lines += $slotLines
    $lines += ""
    $lines += "If one of those works, I will send the formal invite and a short pre-read ahead of the call."
    $lines += ""
    $lines += "## Why I am suggesting a meeting"
    $lines += "- Warm signal captured: $($Relationship.warm_signal)"
    $lines += "- Desired outcome: $($Relationship.desired_outcome)"
    $lines += "- Offer hypothesis: $($Relationship.offer_hypothesis)"
    $lines += ""
    return ($lines -join "`n").Trim() + "`n"
}

function Get-BossKeyProposalText {
    param(
        [pscustomobject]$Relationship,
        [pscustomobject]$ProposalRecord
    )

    $assumptions = @(
        "Access to one discovery conversation before the engagement starts.",
        "Core account context and any prior proposal material can be reviewed before kickoff.",
        "Owner approval remains required before any external deliverable is sent."
    )
    $exclusions = @(
        "No blind proposal submission or auto-sent outreach.",
        "No guaranteed win claims or fabricated supporting evidence.",
        "No expansion beyond the scoped offer without a revised proposal."
    )
    $agenda = @(
        "Confirm the real bottleneck behind $($Relationship.pain_point).",
        "Decide whether the right first move is a $($Relationship.offer_hypothesis) or a narrower starter scope.",
        "Confirm timing, stakeholders, and what a fast first win needs to look like."
    )

    $priceLine = if ((Get-BossKeyDecimal -Value $ProposalRecord.price_to_win_usd) -gt 0) {
        "$" + ([int](Get-BossKeyDecimal -Value $ProposalRecord.price_to_win_usd)).ToString("N0")
    } else {
        "Pending"
    }
    $competeLine = if ((Get-BossKeyDecimal -Value $ProposalRecord.price_to_compete_usd) -gt 0) {
        "$" + ([int](Get-BossKeyDecimal -Value $ProposalRecord.price_to_compete_usd)).ToString("N0")
    } else {
        "Pending"
    }
    $floorLine = if ((Get-BossKeyDecimal -Value $ProposalRecord.minimum_acceptable_price_usd) -gt 0) {
        "$" + ([int](Get-BossKeyDecimal -Value $ProposalRecord.minimum_acceptable_price_usd)).ToString("N0")
    } else {
        "Not configured."
    }

    $lines = @()
    $lines += "# $($Relationship.company_name) | Pre-consult proposal"
    $lines += ""
    $lines += "Status: Pending owner approval before send."
    $lines += ""
    $lines += "## Discovery summary"
    $lines += "- Warm signal: $($Relationship.warm_signal)"
    $lines += "- Pain point: $($Relationship.pain_point)"
    $lines += "- Desired outcome: $($Relationship.desired_outcome)"
    $lines += "- Offer hypothesis: $($Relationship.offer_hypothesis)"
    $lines += "- Latest interaction: $($Relationship.last_interaction_summary)"
    $lines += ""
    $lines += "## Tailored scope"
    $lines += $ProposalRecord.scope_summary
    $lines += ""
    $lines += "## Offer recommendation"
    $lines += "Recommended entry offer: $($ProposalRecord.recommended_entry_offer)"
    $lines += "Expansion offer: $($ProposalRecord.expansion_offer)"
    $lines += "Pursue recommendation: $($ProposalRecord.pursue_recommendation)"
    $lines += ""
    $lines += "## PTW view"
    $lines += "- PTW stage: $($ProposalRecord.ptw_stage)"
    $lines += "- Price to compete: $competeLine"
    $lines += "- Price to win: $priceLine"
    $lines += "- Minimum acceptable price: $floorLine"
    $lines += "- Pricing status: $($ProposalRecord.pricing_status)"
    $lines += "- Pricing rationale: $($ProposalRecord.pricing_rationale)"
    $lines += ""
    $lines += "## Assumptions"
    foreach ($item in $assumptions) { $lines += "- $item" }
    $lines += ""
    $lines += "## Exclusions"
    foreach ($item in $exclusions) { $lines += "- $item" }
    $lines += ""
    $lines += "## Recommended meeting agenda"
    foreach ($item in $agenda) { $lines += "- $item" }
    $lines += ""
    $lines += "## Price recommendation"
    $lines += "- Working recommendation: $priceLine"
    $lines += "- Price to compete: $competeLine"
    $lines += "- Minimum acceptable price: $floorLine"
    $lines += "- Pricing basis: $($ProposalRecord.pricing_basis)"
    $lines += "- Pricing anchor: $($ProposalRecord.pricing_anchor)"
    $lines += "- Owner confirmation required: $($ProposalRecord.owner_confirmation_required)"
    $lines += "- PTW brief: $($ProposalRecord.ptw_brief_path)"
    $lines += "- Pricing status: $($ProposalRecord.pricing_status)"
    $lines += ""
    return ($lines -join "`n").Trim() + "`n"
}

function Sync-BossKeyOutcomeKnowledgeBase {
    param(
        [System.Collections.Generic.List[object]]$KnowledgeQueue,
        [System.Collections.Generic.List[object]]$OutcomeQueue
    )

    foreach ($outcome in $OutcomeQueue.ToArray()) {
        $award = Get-BossKeyDecimal -Value $outcome.actual_award_price_usd
        $quoted = Get-BossKeyDecimal -Value $outcome.actual_quoted_price_usd
        $compete = Get-BossKeyDecimal -Value $outcome.price_to_compete_usd
        $win = Get-BossKeyDecimal -Value $outcome.price_to_win_usd

        if ($award -gt 0 -and $compete -gt 0) { $outcome.calibration_delta_compete_usd = [string][int]($award - $compete) }
        if ($award -gt 0 -and $win -gt 0) { $outcome.calibration_delta_win_usd = [string][int]($award - $win) }

        $knowledgeId = "outcome-" + (Get-BossKeyString -Value $outcome.outcome_id)
        $existing = $KnowledgeQueue | Where-Object { $_.knowledge_id -eq $knowledgeId } | Select-Object -First 1
        if ($null -ne $existing) { $KnowledgeQueue.Remove($existing) | Out-Null }
        $KnowledgeQueue.Add([pscustomobject]@{
            knowledge_id = $knowledgeId; relationship_id = $outcome.relationship_id; company_name = $outcome.company_name; entity_type = "outcome-calibration"; entity_name = (Get-BossKeyString -Value $outcome.winning_competitor -Fallback $outcome.company_name); source_type = "post-award-review"; source_reference = "PTW outcome calibration log"; source_date = $outcome.closed_date; source_reliability = "high"; confidence = "85"; customer_objective = ""; customer_need = ""; customer_value_drivers = ""; buyer_priorities = ""; evaluation_priorities = ""; buying_behavior = ""; delivery_context = ""; timing_context = ""; budget_signal = ""; budget_band = ""; competitor_name = (Get-BossKeyString -Value $outcome.winning_competitor); incumbent_status = ""; alternative_option = ""; big4_technical = ""; big4_management = ""; big4_past_performance = ""; big4_cost_price = ""; differentiation_hypothesis = ""; evidence_summary = ("Quoted: {0} | Award: {1} | Driver: {2}" -f $quoted, $award, (Get-BossKeyString -Value $outcome.outcome_driver_summary)); assumptions = ""; ethical_use_check = "yes"; last_validated_date = (Get-Date).ToString("yyyy-MM-dd"); notes = ("Calibration deltas | compete: {0} | win: {1}" -f $outcome.calibration_delta_compete_usd, $outcome.calibration_delta_win_usd)
        })
    }
}

function Test-BossKeyDecisionQueueCandidate {
    param([string]$ReviewStatus, [string]$Status)

    $review = (Get-BossKeyString -Value $ReviewStatus).ToLowerInvariant()
    $state = (Get-BossKeyString -Value $Status).ToLowerInvariant()
    return ($review -in @("pending-review", "needs-revision", "needs-edit", "blocked-on-ptw")) -or ($state -in @("needs-ptw-input", "market-assessment-only", "owner-escalation-required", "no-bid", "draft"))
}

& (Join-Path $PSScriptRoot "sync-boss-key-content-queue.ps1") `
    -SourcesFile $ContentSourcesFile `
    -QueueFile $ContentQueueFile `
    -RefreshExisting:$RefreshDrafts

Ensure-BossKeyGrowthDirectory -PathValue (Resolve-BossKeyGrowthPath $LinkedInDraftDir)
Ensure-BossKeyGrowthDirectory -PathValue (Resolve-BossKeyGrowthPath $MeetingDraftDir)
Ensure-BossKeyGrowthDirectory -PathValue (Resolve-BossKeyGrowthPath $PtwDraftDir)
Ensure-BossKeyGrowthDirectory -PathValue (Resolve-BossKeyGrowthPath $ProposalDraftDir)

$contentQueue = Import-BossKeyCsvWithSchema -PathValue $ContentQueueFile -PropertyOrder $contentPropertyOrder
$relationships = New-Object System.Collections.Generic.List[object]
foreach ($row in (Import-BossKeyCsvWithSchema -PathValue $RelationshipQueueFile -PropertyOrder $relationshipPropertyOrder)) { $relationships.Add($row) }
$memoryRows = Import-BossKeyCsv -PathValue $ConversationMemoryFile
$meetingQueue = New-Object System.Collections.Generic.List[object]
foreach ($row in (Import-BossKeyCsvWithSchema -PathValue $MeetingQueueFile -PropertyOrder $meetingPropertyOrder)) { $meetingQueue.Add($row) }
$ptwQueue = New-Object System.Collections.Generic.List[object]
foreach ($row in (Import-BossKeyCsvWithSchema -PathValue $PtwQueueFile -PropertyOrder $ptwPropertyOrder)) { $ptwQueue.Add($row) }
$proposalQueue = New-Object System.Collections.Generic.List[object]
foreach ($row in (Import-BossKeyCsvWithSchema -PathValue $ProposalQueueFile -PropertyOrder $proposalPropertyOrder)) { $proposalQueue.Add($row) }
$knowledgeQueue = New-Object System.Collections.Generic.List[object]
foreach ($row in (Import-BossKeyCsvWithSchema -PathValue $KnowledgeBaseFile -PropertyOrder $knowledgePropertyOrder)) { $knowledgeQueue.Add($row) }
$outcomeQueue = New-Object System.Collections.Generic.List[object]
foreach ($row in (Import-BossKeyCsvWithSchema -PathValue $OutcomeLogFile -PropertyOrder $outcomePropertyOrder)) { $outcomeQueue.Add($row) }
$priceBook = Import-BossKeyCsv -PathValue $PriceBookFile
$modifiers = Import-BossKeyCsv -PathValue $ModifierFile
$busyIntervals = Get-BossKeyBusyIntervals -BusyCsvFile $BusyBlocksFile

Sync-BossKeyOutcomeKnowledgeBase -KnowledgeQueue $knowledgeQueue -OutcomeQueue $outcomeQueue

foreach ($relationship in $relationships.ToArray()) {
    $stage = (Get-BossKeyString -Value $relationship.relationship_stage).ToLowerInvariant()
    if ($stage -like "closed*") { continue }

    $activePtw = $null
    if (Test-BossKeyPtwEligibleRelationship -Relationship $relationship) {
        $activePtw = $ptwQueue | Where-Object { $_.relationship_id -eq $relationship.relationship_id -and (Get-BossKeyString -Value $_.is_active).ToLowerInvariant() -eq "yes" } | Select-Object -First 1
        $revision = [int](Get-BossKeyDecimal -Value $(if ($null -eq $activePtw) { "" } else { $activePtw.revision_number })); if ($revision -lt 1) { $revision = 1 }
        if ($RefreshDrafts -and $null -ne $activePtw) {
            $archived = [pscustomobject]@{}
            foreach ($property in $ptwPropertyOrder) {
                Add-Member -InputObject $archived -NotePropertyName $property -NotePropertyValue "" -Force
                if ($activePtw.PSObject.Properties.Name -contains $property) { $archived.$property = [string]$activePtw.$property }
            }
            $archived.is_active = "no"; $archived.archived_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"); $archived.status = "historical"
            $ptwQueue.Remove($activePtw) | Out-Null; $ptwQueue.Add($archived); $activePtw = $null; $revision += 1
        }

        $knowledgeContext = Get-BossKeyKnowledgeContext -Relationship $relationship -KnowledgeRows $knowledgeQueue.ToArray()
        $ptwStage = Get-BossKeyPtwStage -ExistingPtw $activePtw -KnowledgeContext $knowledgeContext
        $confidence = Get-BossKeyPtwConfidence -KnowledgeContext $knowledgeContext -Stage $ptwStage
        $primaryOffer = Get-BossKeyOfferContext -OfferName (Get-BossKeyString -Value $relationship.offer_hypothesis) -PriceBook $priceBook
        $selection = Resolve-BossKeyEntryOffer -PrimaryOffer $primaryOffer -PriceBook $priceBook -KnowledgeContext $knowledgeContext -Confidence $confidence -Stage $ptwStage
        $entryOffer = $selection.entry_offer
        $pricing = Get-BossKeyPtwPricing -Relationship $relationship -OfferContext $entryOffer -KnowledgeContext $knowledgeContext -BudgetContext $selection.budget_context -Confidence $confidence -Stage $ptwStage -ModifierRows $modifiers
        $pursueRecommendation = Get-BossKeyPursueRecommendation -OfferContext $entryOffer -KnowledgeContext $knowledgeContext -PriceToCompete $pricing.price_to_compete -PriceToWin $pricing.price_to_win -Confidence $confidence
        $ptwState = Get-BossKeyPtwStatus -KnowledgeContext $knowledgeContext -OfferContext $entryOffer -PriceToCompete $pricing.price_to_compete -PriceToWin $pricing.price_to_win -Stage $ptwStage -PursueRecommendation $pursueRecommendation
        $ptwId = if ($null -eq $activePtw) { "{0}-r{1}" -f (New-BossKeyId -Prefix "ptw" -Seed $relationship.company_name), $revision } else { [string]$activePtw.ptw_id }
        $ptwPath = "marketing-agents/briefs/generated/boss-key-growth-os/ptw/{0}.md" -f $ptwId

        $activePtw = [pscustomobject]@{
            ptw_id = $ptwId; relationship_id = $relationship.relationship_id; created_date = $(if ($null -eq $activePtw) { (Get-Date).ToString("yyyy-MM-dd") } else { $activePtw.created_date }); refreshed_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"); archived_at = ""; revision_number = [string]$revision; is_active = "yes"; company_name = $relationship.company_name; contact_name = $relationship.contact_name; ptw_stage = $ptwStage; target_account_fit = (Get-BossKeyString -Value $relationship.fit_confirmed -Fallback "yes"); customer_objective = (Get-BossKeyString -Value $knowledgeContext.customer_objective); customer_need = (Get-BossKeyString -Value $knowledgeContext.customer_need); customer_value_drivers = (Get-BossKeyString -Value $knowledgeContext.customer_value_drivers -Fallback (Get-BossKeyString -Value $relationship.desired_outcome)); buyer_priorities = (Get-BossKeyString -Value $knowledgeContext.buyer_priorities); evaluation_priorities = (Get-BossKeyString -Value $knowledgeContext.evaluation_priorities); buying_behavior = (Get-BossKeyString -Value $knowledgeContext.buying_behavior); delivery_context = (Get-BossKeyString -Value $knowledgeContext.delivery_context -Fallback "Initial work likely happens remotely with an operator-facing readout."); timing_context = (Get-BossKeyString -Value $knowledgeContext.timing_context -Fallback ("Urgency level: " + (Get-BossKeyString -Value $relationship.urgency_level -Fallback "medium"))); budget_signal = (Get-BossKeyString -Value $knowledgeContext.budget_signal); budget_band = (Get-BossKeyString -Value $knowledgeContext.budget_band); budget_confidence = [string][int][math]::Round(($confidence * (Get-BossKeyReliabilityScore -Value $knowledgeContext.source_reliability)), 0); likely_competitors = (Get-BossKeyString -Value $knowledgeContext.likely_competitors); incumbent_status = (Get-BossKeyString -Value $knowledgeContext.incumbent_status -Fallback "unknown"); substitute_options = (Get-BossKeyString -Value $knowledgeContext.substitute_options); big4_technical = (Get-BossKeyString -Value $knowledgeContext.big4_technical); big4_management = (Get-BossKeyString -Value $knowledgeContext.big4_management); big4_past_performance = (Get-BossKeyString -Value $knowledgeContext.big4_past_performance); big4_cost_price = (Get-BossKeyString -Value $knowledgeContext.big4_cost_price); differentiation_hypothesis = (Get-BossKeyString -Value $knowledgeContext.differentiation_hypothesis -Fallback "Boss Key can lower owner drag with a narrower first move and clearer handoff."); recommended_entry_offer = $entryOffer.offer_name; expansion_offer = (Get-BossKeyString -Value $selection.expansion_offer); price_to_compete_usd = $(if ($pricing.price_to_compete -gt 0) { [string][int]$pricing.price_to_compete } else { "" }); price_to_win_usd = $(if ($pricing.price_to_win -gt 0) { [string][int]$pricing.price_to_win } else { "" }); minimum_acceptable_price_usd = $(if ($entryOffer.minimum_price -gt 0) { [string][int]$entryOffer.minimum_price } else { "" }); pursue_recommendation = $pursueRecommendation; data_confidence = [string]$confidence; evidence_summary = (Get-BossKeyString -Value $knowledgeContext.evidence_summary -Fallback "Evidence is still being assembled from approved public-source notes and relationship discovery."); assumptions = (Get-BossKeyString -Value $knowledgeContext.assumptions -Fallback "PTW recommendation assumes currently known buyer priorities remain stable through the first consultation."); source_quality_notes = (Get-BossKeyString -Value $knowledgeContext.source_quality_notes -Fallback "Use only approved public-source and direct-discovery evidence."); source_reliability = (Get-BossKeyString -Value $knowledgeContext.source_reliability -Fallback "medium"); source_summary = (Get-BossKeyString -Value $knowledgeContext.source_summary -Fallback "Relationship notes plus reusable competitive knowledge-base entries."); ptw_brief_path = $ptwPath; owner_decision = $(if ($null -eq $activePtw -or $RefreshDrafts) { "review" } else { $activePtw.owner_decision }); review_status = $(if ($null -eq $activePtw -or $RefreshDrafts -or (Get-BossKeyString -Value $activePtw.status).ToLowerInvariant() -ne "approved") { "pending-review" } else { $activePtw.review_status }); status = $ptwState.status; notes = ("Missing fields: " + (Join-BossKeyList -Values $ptwState.missing_fields))
        }
        Get-BossKeyPtwDraftText -Relationship $relationship -PtwRecord $activePtw | Set-Content -Path (Resolve-BossKeyGrowthPath $ptwPath) -Encoding UTF8
        $previousActive = $ptwQueue | Where-Object { $_.relationship_id -eq $relationship.relationship_id -and (Get-BossKeyString -Value $_.is_active).ToLowerInvariant() -eq "yes" } | Select-Object -First 1
        if ($null -ne $previousActive) { $ptwQueue.Remove($previousActive) | Out-Null }
        $ptwQueue.Add($activePtw)
        $existingKnowledge = $knowledgeQueue | Where-Object { $_.knowledge_id -eq ("ptw-model-" + $relationship.relationship_id) } | Select-Object -First 1
        if ($null -ne $existingKnowledge) { $knowledgeQueue.Remove($existingKnowledge) | Out-Null }
        $knowledgeQueue.Add([pscustomobject]@{
            knowledge_id = "ptw-model-$($relationship.relationship_id)"; relationship_id = $relationship.relationship_id; company_name = $relationship.company_name; entity_type = "ptw-model"; entity_name = $activePtw.recommended_entry_offer; source_type = "generated-ptw"; source_reference = $ptwPath; source_date = (Get-Date).ToString("yyyy-MM-dd"); source_reliability = "medium"; confidence = $activePtw.data_confidence; customer_objective = $activePtw.customer_objective; customer_need = $activePtw.customer_need; customer_value_drivers = $activePtw.customer_value_drivers; buyer_priorities = $activePtw.buyer_priorities; evaluation_priorities = $activePtw.evaluation_priorities; buying_behavior = $activePtw.buying_behavior; delivery_context = $activePtw.delivery_context; timing_context = $activePtw.timing_context; budget_signal = $activePtw.budget_signal; budget_band = $activePtw.budget_band; competitor_name = $activePtw.likely_competitors; incumbent_status = $activePtw.incumbent_status; alternative_option = $activePtw.substitute_options; big4_technical = $activePtw.big4_technical; big4_management = $activePtw.big4_management; big4_past_performance = $activePtw.big4_past_performance; big4_cost_price = $activePtw.big4_cost_price; differentiation_hypothesis = $activePtw.differentiation_hypothesis; evidence_summary = $activePtw.evidence_summary; assumptions = $activePtw.assumptions; ethical_use_check = "yes"; last_validated_date = (Get-Date).ToString("yyyy-MM-dd"); notes = ("PTW band | compete: {0} | win: {1} | floor: {2}" -f $activePtw.price_to_compete_usd, $activePtw.price_to_win_usd, $activePtw.minimum_acceptable_price_usd)
        })
        $relationship.ptw_record_id = $ptwId; $relationship.ptw_stage = $ptwStage; $relationship.ptw_recommendation = $pursueRecommendation; $relationship.ptw_status = $ptwState.status

        $meeting = $meetingQueue | Where-Object { $_.relationship_id -eq $relationship.relationship_id } | Select-Object -First 1
        if ((Get-BossKeyString -Value $relationship.meeting_needed).ToLowerInvariant() -eq "yes" -and $pursueRecommendation -in @("pursue", "pursue-cautiously")) {
            $slots = Get-BossKeyOpenSlots -StartDate (Get-Date).AddDays(1) -BusyIntervals $busyIntervals -DaysAhead 10 -SlotMinutes 30 -SlotCount 3
            if ($slots.Count -gt 0) {
                $meetingId = if ($null -eq $meeting) { New-BossKeyId -Prefix "meeting" -Seed $relationship.company_name } else { [string]$meeting.meeting_id }
                $meetingPath = "marketing-agents/briefs/generated/boss-key-growth-os/meetings/{0}-booking.md" -f $meetingId
                if ($RefreshDrafts -or -not (Test-Path (Resolve-BossKeyGrowthPath $meetingPath))) {
                    Get-BossKeyMeetingMessageText -Relationship $relationship -Slots $slots -ActivePtw $activePtw | Set-Content -Path (Resolve-BossKeyGrowthPath $meetingPath) -Encoding UTF8
                }
                if ($null -ne $meeting) { $meetingQueue.Remove($meeting) | Out-Null }
                $meetingQueue.Add([pscustomobject]@{ meeting_id = $meetingId; relationship_id = $relationship.relationship_id; created_date = $(if ($null -eq $meeting) { (Get-Date).ToString("yyyy-MM-dd") } else { $meeting.created_date }); company_name = $relationship.company_name; contact_name = $relationship.contact_name; relationship_stage = $relationship.relationship_stage; meeting_reason = "PTW-qualified consultation for $($entryOffer.offer_name)"; qualification_summary = "$($relationship.warm_signal); PTW $pursueRecommendation; $($relationship.pain_point)"; slot_1_start = $(if ($slots.Count -gt 0) { $slots[0].start.ToString("yyyy-MM-dd HH:mm") } else { "" }); slot_1_end = $(if ($slots.Count -gt 0) { $slots[0].end.ToString("yyyy-MM-dd HH:mm") } else { "" }); slot_2_start = $(if ($slots.Count -gt 1) { $slots[1].start.ToString("yyyy-MM-dd HH:mm") } else { "" }); slot_2_end = $(if ($slots.Count -gt 1) { $slots[1].end.ToString("yyyy-MM-dd HH:mm") } else { "" }); slot_3_start = $(if ($slots.Count -gt 2) { $slots[2].start.ToString("yyyy-MM-dd HH:mm") } else { "" }); slot_3_end = $(if ($slots.Count -gt 2) { $slots[2].end.ToString("yyyy-MM-dd HH:mm") } else { "" }); booking_message_path = $meetingPath; invite_packet_path = $(if ($null -eq $meeting) { "" } else { $meeting.invite_packet_path }); owner_decision = $(if ($null -eq $meeting) { "review" } else { $meeting.owner_decision }); review_status = $(if ($null -eq $meeting -or (Get-BossKeyString -Value $meeting.status).ToLowerInvariant() -ne "ready-to-send") { "pending-review" } else { $meeting.review_status }); status = $(if ($null -eq $meeting) { "draft" } else { $meeting.status }); notes = "Generated from PTW-qualified opportunity." })
                $relationship.meeting_status = "draft-pending-review"
            }
        } elseif ($null -ne $meeting -and (Get-BossKeyString -Value $meeting.status).ToLowerInvariant() -ne "ready-to-send") {
            $meeting.status = "blocked-no-bid"; $meeting.review_status = "blocked-no-bid"; $meeting.notes = "PTW posture does not recommend a consultation yet."; $relationship.meeting_status = "blocked-no-bid"
        }

        $proposal = $proposalQueue | Where-Object { $_.relationship_id -eq $relationship.relationship_id } | Select-Object -First 1
        $proposalId = if ($null -eq $proposal) { New-BossKeyId -Prefix "proposal" -Seed $relationship.company_name } else { [string]$proposal.proposal_id }
        $proposalPath = "marketing-agents/briefs/generated/boss-key-growth-os/proposals/{0}.md" -f $proposalId
        $pricingStatus = switch ($ptwState.status) { "needs-ptw-input" { "needs-ptw-input" } "market-assessment-only" { "market-assessment-only" } "no-bid" { "no-bid" } "owner-escalation-required" { "owner-escalation-required" } default { $entryOffer.pricing_status } }
        if ($null -ne $proposal) { $proposalQueue.Remove($proposal) | Out-Null }
        $proposalRecord = [pscustomobject]@{ proposal_id = $proposalId; relationship_id = $relationship.relationship_id; ptw_id = $ptwId; created_date = $(if ($null -eq $proposal) { (Get-Date).ToString("yyyy-MM-dd") } else { $proposal.created_date }); company_name = $relationship.company_name; contact_name = $relationship.contact_name; offer_name = $relationship.offer_hypothesis; recommended_entry_offer = $entryOffer.offer_name; expansion_offer = (Get-BossKeyString -Value $selection.expansion_offer); ptw_stage = $ptwStage; price_to_compete_usd = $(if ($pricing.price_to_compete -gt 0) { [string][int]$pricing.price_to_compete } else { "" }); recommended_price_usd = $(if ($pricing.price_to_win -gt 0) { [string][int]$pricing.price_to_win } else { "" }); price_to_win_usd = $(if ($pricing.price_to_win -gt 0) { [string][int]$pricing.price_to_win } else { "" }); minimum_acceptable_price_usd = $(if ($entryOffer.minimum_price -gt 0) { [string][int]$entryOffer.minimum_price } else { "" }); maximum_price_usd = $(if ($entryOffer.maximum_price -gt 0) { [string][int]$entryOffer.maximum_price } else { "" }); ptw_confidence = [string]$confidence; pursue_recommendation = $pursueRecommendation; pricing_basis = $pricing.pricing_basis; pricing_anchor = $entryOffer.pricing_anchor; pricing_rationale = $pricing.pricing_rationale; ptw_brief_path = $ptwPath; owner_confirmation_required = $entryOffer.owner_confirmation_required; discovery_summary = "$($relationship.warm_signal); $($relationship.pain_point); $($relationship.desired_outcome)"; scope_summary = "Start with a $($entryOffer.offer_name) aimed at $($relationship.desired_outcome). If it lands, expand into $($selection.expansion_offer)."; assumptions = $activePtw.assumptions; exclusions = "No blind proposal submission; no fabricated competitive claims; no scope expansion without a revised approved packet."; recommended_agenda = "Confirm buyer priorities; validate the first win; test whether the PTW entry offer is the right commercial shape; confirm timing and stakeholders."; pricing_status = $pricingStatus; proposal_path = $proposalPath; owner_decision = $(if ($null -eq $proposal) { "review" } else { $proposal.owner_decision }); review_status = $(if ($null -eq $proposal -or (Get-BossKeyString -Value $proposal.status).ToLowerInvariant() -ne "ready-to-send") { "pending-review" } else { $proposal.review_status }); status = $ptwState.status; notes = "Pre-consult proposal driven by the active Competitive PTW record." }
        Get-BossKeyProposalText -Relationship $relationship -ProposalRecord $proposalRecord | Set-Content -Path (Resolve-BossKeyGrowthPath $proposalPath) -Encoding UTF8
        $proposalQueue.Add($proposalRecord)
        if ((Get-BossKeyString -Value $relationship.proposal_status).ToLowerInvariant() -ne "ready-to-send") { $relationship.proposal_status = $pricingStatus }
    } else {
        $existingActivePtw = $ptwQueue | Where-Object {
            $_.relationship_id -eq $relationship.relationship_id -and
            (Get-BossKeyString -Value $_.is_active).ToLowerInvariant() -eq "yes"
        } | Select-Object -First 1

        if ($null -ne $existingActivePtw) {
            $archivedPtw = ConvertTo-BossKeySchemaRow -Row $existingActivePtw -PropertyOrder $ptwPropertyOrder
            $archivedPtw.is_active = "no"
            $archivedPtw.archived_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            $archivedPtw.status = "historical"
            $ptwQueue.Remove($existingActivePtw) | Out-Null
            $ptwQueue.Add($archivedPtw)
        }

        $relationship.ptw_status = "not-qualified"
        $relationship.ptw_stage = ""
        $relationship.ptw_recommendation = ""
        $relationship.ptw_record_id = ""

        $meeting = $meetingQueue | Where-Object { $_.relationship_id -eq $relationship.relationship_id } | Select-Object -First 1
        if ($null -ne $meeting -and (Get-BossKeyString -Value $meeting.status).ToLowerInvariant() -ne "ready-to-send") {
            $meetingQueue.Remove($meeting) | Out-Null
            $updatedMeeting = ConvertTo-BossKeySchemaRow -Row $meeting -PropertyOrder $meetingPropertyOrder
            $updatedMeeting.owner_decision = "hold"
            $updatedMeeting.review_status = "on-hold"
            $updatedMeeting.status = "awaiting-qualification"
            $updatedMeeting.notes = "Meeting draft paused until the relationship becomes PTW-qualified."
            $meetingQueue.Add($updatedMeeting)
        }
        if ((Get-BossKeyString -Value $relationship.meeting_status).ToLowerInvariant() -ne "ready-to-send") {
            $relationship.meeting_status = $(if ((Get-BossKeyString -Value $relationship.meeting_needed).ToLowerInvariant() -eq "yes") { "awaiting-qualification" } else { "not-needed" })
        }

        $proposal = $proposalQueue | Where-Object { $_.relationship_id -eq $relationship.relationship_id } | Select-Object -First 1
        if ($null -ne $proposal -and (Get-BossKeyString -Value $proposal.status).ToLowerInvariant() -ne "ready-to-send") {
            $proposalQueue.Remove($proposal) | Out-Null
            $updatedProposal = ConvertTo-BossKeySchemaRow -Row $proposal -PropertyOrder $proposalPropertyOrder
            $updatedProposal.owner_decision = "hold"
            $updatedProposal.review_status = "on-hold"
            $updatedProposal.status = "awaiting-ptw-qualification"
            $updatedProposal.pricing_status = "awaiting-ptw-qualification"
            $updatedProposal.notes = "Proposal draft paused until the relationship reaches qualified-pre-consult and an active PTW record exists."
            $proposalQueue.Add($updatedProposal)
        }
        if ((Get-BossKeyString -Value $relationship.proposal_status).ToLowerInvariant() -ne "ready-to-send") {
            $relationship.proposal_status = "awaiting-qualification"
        }
    }

    $touchType = Get-RelationshipNextTouchType -Relationship $relationship
    $touchPath = if ([string]::IsNullOrWhiteSpace($relationship.next_best_touch_path)) { "marketing-agents/briefs/generated/boss-key-growth-os/linkedin/{0}-{1}.md" -f $relationship.relationship_id, $touchType } else { [string]$relationship.next_best_touch_path }
    $touchResolved = Resolve-BossKeyGrowthPath $touchPath
    $memoryItems = Get-RelationshipMemorySummary -RelationshipId $relationship.relationship_id -MemoryRows $memoryRows
    if ($RefreshDrafts -or -not (Test-Path $touchResolved)) { Get-RelationshipDraftText -Relationship $relationship -TouchType $touchType -MemoryItems $memoryItems -ActivePtw $activePtw | Set-Content -Path $touchResolved -Encoding UTF8 }
    $relationship.next_best_touch_type = $touchType; $relationship.next_best_touch_path = $touchPath
    if ((Get-BossKeyString -Value $relationship.ready_state).ToLowerInvariant() -ne "ready-to-send") { $relationship.ready_state = "draft-pending-review" }
    if ((Get-BossKeyString -Value $relationship.review_status).ToLowerInvariant() -ne "approved") { $relationship.review_status = "pending-review" }
}

$decisionRows = New-Object System.Collections.Generic.List[object]

foreach ($content in $contentQueue | Where-Object { $_.review_status -eq "pending-review" -or $_.review_status -eq "needs-revision" }) {
    $decisionRows.Add([pscustomobject]@{
        item_id = [string]$content.content_id
        item_type = "content"
        title = [string]$content.title
        current_status = [string]$content.review_status
        draft_path = [string]$content.article_draft_path
        owner_decision = "hold"
        revision_notes = ""
        send_mode = "publish"
        scheduled_date = [string]$content.scheduled_publish_date
        notes = "Approving publishes the article to the Insights hub, regenerates the RSS feed, and readies the personal LinkedIn draft."
    })
}

foreach ($relationship in $relationships | Where-Object { $_.ready_state -eq "draft-pending-review" }) {
    $decisionRows.Add([pscustomobject]@{
        item_id = [string]$relationship.relationship_id
        item_type = "linkedin-touch"
        title = ("{0} | {1}" -f $relationship.company_name, $relationship.next_best_touch_type)
        current_status = [string]$relationship.relationship_stage
        draft_path = [string]$relationship.next_best_touch_path
        owner_decision = "hold"
        revision_notes = ""
        send_mode = "manual"
        scheduled_date = ""
        notes = "Approving marks the LinkedIn touch ready-to-send only. It does not auto-send."
    })
}

foreach ($ptw in $ptwQueue | Where-Object { (Get-BossKeyString -Value $_.is_active).ToLowerInvariant() -eq "yes" -and (Test-BossKeyDecisionQueueCandidate -ReviewStatus $_.review_status -Status $_.status) }) {
    $decisionRows.Add([pscustomobject]@{
        item_id = [string]$ptw.ptw_id
        item_type = "ptw-analysis"
        title = ("{0} | competitive PTW" -f $ptw.company_name)
        current_status = [string]$ptw.status
        draft_path = [string]$ptw.ptw_brief_path
        owner_decision = "hold"
        revision_notes = ""
        send_mode = "review"
        scheduled_date = ""
        notes = "Approving the PTW analysis unlocks proposal readiness checks but does not send anything."
    })
}

foreach ($meeting in $meetingQueue | Where-Object { Test-BossKeyDecisionQueueCandidate -ReviewStatus $_.review_status -Status $_.status }) {
    $decisionRows.Add([pscustomobject]@{
        item_id = [string]$meeting.meeting_id
        item_type = "meeting"
        title = ("{0} | booking draft" -f $meeting.company_name)
        current_status = [string]$meeting.status
        draft_path = [string]$meeting.booking_message_path
        owner_decision = "hold"
        revision_notes = ""
        send_mode = "manual"
        scheduled_date = [string]$meeting.slot_1_start
        notes = "Approving prepares the invite packet and marks the booking message ready-to-send."
    })
}

foreach ($proposal in $proposalQueue | Where-Object { Test-BossKeyDecisionQueueCandidate -ReviewStatus $_.review_status -Status $_.status }) {
    $decisionRows.Add([pscustomobject]@{
        item_id = [string]$proposal.proposal_id
        item_type = "proposal"
        title = ("{0} | pre-consult proposal" -f $proposal.company_name)
        current_status = [string]$proposal.status
        draft_path = [string]$proposal.proposal_path
        owner_decision = "hold"
        revision_notes = ""
        send_mode = "manual"
        scheduled_date = ""
        notes = "Approving marks the proposal ready-to-send but does not auto-send."
    })
}

Export-BossKeyCsv -Rows ($relationships.ToArray()) -PathValue $RelationshipQueueFile -PropertyOrder $relationshipPropertyOrder
Export-BossKeyCsv -Rows ($meetingQueue.ToArray()) -PathValue $MeetingQueueFile -PropertyOrder $meetingPropertyOrder
Export-BossKeyCsv -Rows ($ptwQueue.ToArray()) -PathValue $PtwQueueFile -PropertyOrder $ptwPropertyOrder
Export-BossKeyCsv -Rows ($proposalQueue.ToArray()) -PathValue $ProposalQueueFile -PropertyOrder $proposalPropertyOrder
Export-BossKeyCsv -Rows ($knowledgeQueue.ToArray()) -PathValue $KnowledgeBaseFile -PropertyOrder $knowledgePropertyOrder
Export-BossKeyCsv -Rows ($outcomeQueue.ToArray()) -PathValue $OutcomeLogFile -PropertyOrder $outcomePropertyOrder
Export-BossKeyCsv -Rows ($decisionRows.ToArray()) -PathValue $DecisionFile -PropertyOrder $decisionPropertyOrder

if (-not $SkipProposalOpsSync) {
    & (Join-Path $PSScriptRoot "sync-boss-key-proposal-ops.ps1") `
        -Mode PersistReviewState `
        -RelationshipQueueFile $RelationshipQueueFile `
        -ConversationMemoryFile $ConversationMemoryFile `
        -KnowledgeBaseFile $KnowledgeBaseFile `
        -ProposalQueueFile $ProposalQueueFile | Out-Null
}

$packetLines = @()
$packetLines += "# Boss Key Review Packet"
$packetLines += ""
$packetLines += "To: timmy@bosskeyops.com"
$packetLines += "Generated: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))"
$packetLines += ""
$packetLines += "Update decisions in:"
$packetLines += "- $DecisionFile"
$packetLines += ""
$packetLines += "Counts:"
$packetLines += "- Content units: $((@($decisionRows | Where-Object { $_.item_type -eq 'content' })).Count)"
$packetLines += "- LinkedIn touches: $((@($decisionRows | Where-Object { $_.item_type -eq 'linkedin-touch' })).Count)"
$packetLines += "- PTW analyses: $((@($decisionRows | Where-Object { $_.item_type -eq 'ptw-analysis' })).Count)"
$packetLines += "- Meeting drafts: $((@($decisionRows | Where-Object { $_.item_type -eq 'meeting' })).Count)"
$packetLines += "- Proposal drafts: $((@($decisionRows | Where-Object { $_.item_type -eq 'proposal' })).Count)"
$packetLines += ""

$contentItems = @($contentQueue | Where-Object { $_.review_status -eq "pending-review" -or $_.review_status -eq "needs-revision" })
if ($contentItems.Count -gt 0) {
    $packetLines += "## Content queue"
    $packetLines += ""
    foreach ($item in $contentItems) {
        $packetLines += "### $($item.content_id) | $($item.title)"
        $packetLines += "- Cadence: $($item.cadence_type)"
        $packetLines += "- Scheduled publish date: $($item.scheduled_publish_date)"
        $packetLines += "- Article draft: $($item.article_draft_path)"
        $packetLines += "- Company LinkedIn draft: $($item.company_linkedin_draft_path)"
        $packetLines += "- Personal LinkedIn draft: $($item.personal_linkedin_draft_path)"
        $packetLines += ""
        if (-not [string]::IsNullOrWhiteSpace($item.article_draft_path) -and (Test-Path (Resolve-BossKeyGrowthPath $item.article_draft_path))) {
            $packetLines += Get-Content -Path (Resolve-BossKeyGrowthPath $item.article_draft_path) -Raw -Encoding UTF8
            $packetLines += ""
        }
    }
}

$relationshipItems = @($relationships | Where-Object { $_.ready_state -eq "draft-pending-review" })
if ($relationshipItems.Count -gt 0) {
    $packetLines += "## LinkedIn relationship queue"
    $packetLines += ""
    foreach ($item in $relationshipItems) {
        $packetLines += "### $($item.relationship_id) | $($item.company_name)"
        $packetLines += "- Stage: $($item.relationship_stage)"
        $packetLines += "- Next touch: $($item.next_best_touch_type)"
        $packetLines += "- Draft: $($item.next_best_touch_path)"
        $packetLines += ""
        if (-not [string]::IsNullOrWhiteSpace($item.next_best_touch_path) -and (Test-Path (Resolve-BossKeyGrowthPath $item.next_best_touch_path))) {
            $packetLines += Get-Content -Path (Resolve-BossKeyGrowthPath $item.next_best_touch_path) -Raw -Encoding UTF8
            $packetLines += ""
        }
    }
}

$ptwItems = @($ptwQueue | Where-Object { (Get-BossKeyString -Value $_.is_active).ToLowerInvariant() -eq "yes" -and (Test-BossKeyDecisionQueueCandidate -ReviewStatus $_.review_status -Status $_.status) })
if ($ptwItems.Count -gt 0) {
    $packetLines += "## Competitive PTW analyses"
    $packetLines += ""
    foreach ($item in $ptwItems) {
        $packetLines += "### $($item.ptw_id) | $($item.company_name)"
        $packetLines += "- PTW stage: $($item.ptw_stage)"
        $packetLines += "- Pursue recommendation: $($item.pursue_recommendation)"
        $packetLines += "- PTW band: compete $($item.price_to_compete_usd) | win $($item.price_to_win_usd) | floor $($item.minimum_acceptable_price_usd)"
        $packetLines += "- Recommended entry offer: $($item.recommended_entry_offer)"
        $packetLines += "- Draft: $($item.ptw_brief_path)"
        $packetLines += ""
        if (-not [string]::IsNullOrWhiteSpace($item.ptw_brief_path) -and (Test-Path (Resolve-BossKeyGrowthPath $item.ptw_brief_path))) {
            $packetLines += Get-Content -Path (Resolve-BossKeyGrowthPath $item.ptw_brief_path) -Raw -Encoding UTF8
            $packetLines += ""
        }
    }
}

$meetingItems = @($meetingQueue | Where-Object { Test-BossKeyDecisionQueueCandidate -ReviewStatus $_.review_status -Status $_.status })
if ($meetingItems.Count -gt 0) {
    $packetLines += "## Meeting recommendations"
    $packetLines += ""
    foreach ($item in $meetingItems) {
        $packetLines += "### $($item.meeting_id) | $($item.company_name)"
        $packetLines += "- Slot 1: $($item.slot_1_start) to $($item.slot_1_end)"
        $packetLines += "- Slot 2: $($item.slot_2_start) to $($item.slot_2_end)"
        $packetLines += "- Slot 3: $($item.slot_3_start) to $($item.slot_3_end)"
        $packetLines += "- Draft: $($item.booking_message_path)"
        $packetLines += ""
        if (-not [string]::IsNullOrWhiteSpace($item.booking_message_path) -and (Test-Path (Resolve-BossKeyGrowthPath $item.booking_message_path))) {
            $packetLines += Get-Content -Path (Resolve-BossKeyGrowthPath $item.booking_message_path) -Raw -Encoding UTF8
            $packetLines += ""
        }
    }
}

$proposalItems = @($proposalQueue | Where-Object { Test-BossKeyDecisionQueueCandidate -ReviewStatus $_.review_status -Status $_.status })
if ($proposalItems.Count -gt 0) {
    $packetLines += "## Pre-consult proposals"
    $packetLines += ""
    foreach ($item in $proposalItems) {
        $packetLines += "### $($item.proposal_id) | $($item.company_name)"
        $packetLines += "- Offer: $($item.recommended_entry_offer)"
        $packetLines += "- PTW stage: $($item.ptw_stage)"
        $packetLines += "- Pursue recommendation: $($item.pursue_recommendation)"
        $packetLines += "- PTW band: compete $($item.price_to_compete_usd) | win $($item.price_to_win_usd) | floor $($item.minimum_acceptable_price_usd)"
        $packetLines += "- Pricing status: $($item.pricing_status)"
        $packetLines += "- Draft: $($item.proposal_path)"
        $packetLines += ""
        if (-not [string]::IsNullOrWhiteSpace($item.proposal_path) -and (Test-Path (Resolve-BossKeyGrowthPath $item.proposal_path))) {
            $packetLines += Get-Content -Path (Resolve-BossKeyGrowthPath $item.proposal_path) -Raw -Encoding UTF8
            $packetLines += ""
        }
    }
}

$reviewPacketResolved = Resolve-BossKeyGrowthPath $ReviewPacketFile
Ensure-BossKeyGrowthDirectory -PathValue (Split-Path -Parent $reviewPacketResolved)
$packetLines -join [Environment]::NewLine | Set-Content -Path $reviewPacketResolved -Encoding UTF8

Write-Output ("Built Boss Key review packet, PTW queue, knowledge base sync, and unified decisions. Packet: {0}. Decisions: {1}" -f $ReviewPacketFile, $DecisionFile)
