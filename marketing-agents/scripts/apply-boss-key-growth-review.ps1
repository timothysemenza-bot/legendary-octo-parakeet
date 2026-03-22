param(
    [string]$ContentQueueFile = "marketing-agents/data/boss_key_content_queue.csv",
    [string]$RelationshipQueueFile = "marketing-agents/data/boss_key_relationship_queue.csv",
    [string]$KnowledgeBaseFile = "marketing-agents/data/boss_key_competitive_kb.csv",
    [string]$MeetingQueueFile = "marketing-agents/data/boss_key_meeting_queue.csv",
    [string]$PtwQueueFile = "marketing-agents/data/boss_key_ptw_queue.csv",
    [string]$ProposalQueueFile = "marketing-agents/data/boss_key_preconsult_proposals.csv",
    [string]$DecisionFile = "marketing-agents/data/boss_key_review_decisions.csv",
    [switch]$SkipProposalOpsSync
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "boss-key-growth-os-helpers.ps1")
. (Join-Path $PSScriptRoot "boss-key-ptw-helpers.ps1")

$contentPropertyOrder = Get-BossKeyContentQueuePropertyOrder

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

function Get-BossKeyInvitePacketText {
    param([pscustomobject]$Meeting)

    $slots = @()
    if (-not [string]::IsNullOrWhiteSpace($Meeting.slot_1_start)) { $slots += "- Option A: $($Meeting.slot_1_start) to $($Meeting.slot_1_end)" }
    if (-not [string]::IsNullOrWhiteSpace($Meeting.slot_2_start)) { $slots += "- Option B: $($Meeting.slot_2_start) to $($Meeting.slot_2_end)" }
    if (-not [string]::IsNullOrWhiteSpace($Meeting.slot_3_start)) { $slots += "- Option C: $($Meeting.slot_3_start) to $($Meeting.slot_3_end)" }

    $lines = @()
    $lines += "# $($Meeting.company_name) | Invite packet"
    $lines += ""
    $lines += "Status: Ready to send after owner approval."
    $lines += ""
    $lines += "## Suggested windows"
    $lines += $slots
    $lines += ""
    $lines += "## Suggested calendar description"
    $lines += "Working session to confirm the current bottleneck, define the first Boss Key engagement hypothesis, and align on the fastest useful next step."
    $lines += ""
    return ($lines -join "`n").Trim() + "`n"
}

$contentQueue = New-Object System.Collections.Generic.List[object]
foreach ($row in (Import-BossKeyCsvWithSchema -PathValue $ContentQueueFile -PropertyOrder $contentPropertyOrder)) { $contentQueue.Add($row) }
$relationships = New-Object System.Collections.Generic.List[object]
foreach ($row in (Import-BossKeyCsvWithSchema -PathValue $RelationshipQueueFile -PropertyOrder $relationshipPropertyOrder)) { $relationships.Add($row) }
$meetingQueue = New-Object System.Collections.Generic.List[object]
foreach ($row in (Import-BossKeyCsvWithSchema -PathValue $MeetingQueueFile -PropertyOrder $meetingPropertyOrder)) { $meetingQueue.Add($row) }
$ptwQueue = New-Object System.Collections.Generic.List[object]
foreach ($row in (Import-BossKeyCsvWithSchema -PathValue $PtwQueueFile -PropertyOrder $ptwPropertyOrder)) { $ptwQueue.Add($row) }
$proposalQueue = New-Object System.Collections.Generic.List[object]
foreach ($row in (Import-BossKeyCsvWithSchema -PathValue $ProposalQueueFile -PropertyOrder $proposalPropertyOrder)) { $proposalQueue.Add($row) }
$decisions = Import-BossKeyCsvWithSchema -PathValue $DecisionFile -PropertyOrder @(
    "item_id", "item_type", "title", "current_status", "draft_path",
    "owner_decision", "revision_notes", "send_mode", "scheduled_date", "notes"
)

foreach ($decision in $decisions) {
    $normalized = Normalize-BossKeyDecision -Value $decision.owner_decision
    switch ([string]$decision.item_type) {
        "content" {
            $row = $contentQueue | Where-Object { $_.content_id -eq $decision.item_id } | Select-Object -First 1
            if ($null -eq $row) { continue }

            switch ($normalized) {
                "approve" {
                    $row.owner_decision = "approve"
                    $row.review_status = "approved"
                    $row.website_status = "approved"
                    $row.rss_status = "approved"
                    $row.linkedin_company_status = "rss-auto"
                    $row.linkedin_personal_status = if (
                        -not [string]::IsNullOrWhiteSpace([string]$row.personal_linkedin_draft_path) -or
                        -not [string]::IsNullOrWhiteSpace([string]$row.distillation_path)
                    ) {
                        "ready-to-send"
                    } else {
                        "not-generated"
                    }
                }
                "revise" {
                    $row.owner_decision = "revise"
                    $row.review_status = "needs-revision"
                }
                "reject" {
                    $row.owner_decision = "reject"
                    $row.review_status = "rejected"
                    $row.website_status = "rejected"
                    $row.rss_status = "rejected"
                }
                default {
                    $row.owner_decision = "hold"
                    $row.review_status = "on-hold"
                }
            }
        }
        "linkedin-touch" {
            $row = $relationships | Where-Object { $_.relationship_id -eq $decision.item_id } | Select-Object -First 1
            if ($null -eq $row) { continue }

            switch ($normalized) {
                "approve" {
                    $row.owner_decision = "approve"
                    $row.review_status = "approved"
                    $row.ready_state = "ready-to-send"
                }
                "revise" {
                    $row.owner_decision = "revise"
                    $row.review_status = "needs-edit"
                    $row.ready_state = "needs-edit"
                }
                "reject" {
                    $row.owner_decision = "reject"
                    $row.review_status = "rejected"
                    $row.ready_state = "rejected"
                }
                default {
                    $row.owner_decision = "hold"
                    $row.review_status = "on-hold"
                    $row.ready_state = "on-hold"
                }
            }
        }
        "ptw-analysis" {
            $row = $ptwQueue | Where-Object { $_.ptw_id -eq $decision.item_id } | Select-Object -First 1
            if ($null -eq $row) { continue }
            $relationship = $relationships | Where-Object { $_.relationship_id -eq $row.relationship_id } | Select-Object -First 1

            switch ($normalized) {
                "approve" {
                    $row.owner_decision = "approve"
                    $row.review_status = "approved"
                    $row.status = if ((Get-BossKeyString -Value $row.pursue_recommendation).ToLowerInvariant() -eq "no-bid") { "no-bid" } else { "approved" }
                    if ($null -ne $relationship) {
                        $relationship.ptw_status = $row.status
                        $relationship.ptw_stage = [string]$row.ptw_stage
                        $relationship.ptw_recommendation = [string]$row.pursue_recommendation
                    }
                }
                "revise" {
                    $row.owner_decision = "revise"
                    $row.review_status = "needs-revision"
                    $row.status = "needs-revision"
                    if ($null -ne $relationship) { $relationship.ptw_status = "needs-revision" }
                }
                "reject" {
                    $row.owner_decision = "reject"
                    $row.review_status = "rejected"
                    $row.status = "rejected"
                    if ($null -ne $relationship) { $relationship.ptw_status = "rejected" }
                }
                default {
                    $row.owner_decision = "hold"
                    $row.review_status = "on-hold"
                    $row.status = "on-hold"
                    if ($null -ne $relationship) { $relationship.ptw_status = "on-hold" }
                }
            }
        }
        "meeting" {
            $row = $meetingQueue | Where-Object { $_.meeting_id -eq $decision.item_id } | Select-Object -First 1
            if ($null -eq $row) { continue }
            $relationship = $relationships | Where-Object { $_.relationship_id -eq $row.relationship_id } | Select-Object -First 1

            switch ($normalized) {
                "approve" {
                    $row.owner_decision = "approve"
                    $row.review_status = "approved"
                    $row.status = "pending-ptw-clearance"
                }
                "revise" {
                    $row.owner_decision = "revise"
                    $row.review_status = "needs-edit"
                    $row.status = "needs-edit"
                }
                "reject" {
                    $row.owner_decision = "reject"
                    $row.review_status = "rejected"
                    $row.status = "rejected"
                    if ($null -ne $relationship) { $relationship.meeting_status = "rejected" }
                }
                default {
                    $row.owner_decision = "hold"
                    $row.review_status = "on-hold"
                    $row.status = "on-hold"
                }
            }
        }
        "proposal" {
            $row = $proposalQueue | Where-Object { $_.proposal_id -eq $decision.item_id } | Select-Object -First 1
            if ($null -eq $row) { continue }
            $relationship = $relationships | Where-Object { $_.relationship_id -eq $row.relationship_id } | Select-Object -First 1

            switch ($normalized) {
                "approve" {
                    $row.owner_decision = "approve"
                    $row.review_status = "approved"
                    $row.status = "pending-ptw-clearance"
                }
                "revise" {
                    $row.owner_decision = "revise"
                    $row.review_status = "needs-edit"
                    $row.status = "needs-edit"
                }
                "reject" {
                    $row.owner_decision = "reject"
                    $row.review_status = "rejected"
                    $row.status = "rejected"
                    if ($null -ne $relationship) { $relationship.proposal_status = "rejected" }
                }
                default {
                    $row.owner_decision = "hold"
                    $row.review_status = "on-hold"
                    $row.status = "on-hold"
                }
            }
        }
    }
}

foreach ($ptw in $ptwQueue | Where-Object { (Get-BossKeyString -Value $_.is_active).ToLowerInvariant() -eq "yes" }) {
    $relationship = $relationships | Where-Object { $_.relationship_id -eq $ptw.relationship_id } | Select-Object -First 1
    if ($null -eq $relationship) { continue }
    if ((Get-BossKeyString -Value $ptw.review_status).ToLowerInvariant() -eq "approved" -and (Get-BossKeyString -Value $ptw.pursue_recommendation).ToLowerInvariant() -eq "no-bid") {
        if ((Get-BossKeyString -Value $relationship.meeting_status).ToLowerInvariant() -ne "ready-to-send") { $relationship.meeting_status = "blocked-no-bid" }
        if ((Get-BossKeyString -Value $relationship.proposal_status).ToLowerInvariant() -ne "ready-to-send") { $relationship.proposal_status = "blocked-no-bid" }
    }
}

foreach ($meeting in $meetingQueue.ToArray()) {
    $relationship = $relationships | Where-Object { $_.relationship_id -eq $meeting.relationship_id } | Select-Object -First 1
    $ptw = $ptwQueue | Where-Object { ((Get-BossKeyString -Value $_.is_active).ToLowerInvariant() -eq "yes") -and ($_.relationship_id -eq $meeting.relationship_id) } | Select-Object -First 1
    if ($null -eq $relationship) { continue }
    if ((Get-BossKeyString -Value $meeting.owner_decision).ToLowerInvariant() -ne "approve") { continue }

    $ptwApproved = $null -ne $ptw -and (Get-BossKeyString -Value $ptw.review_status).ToLowerInvariant() -eq "approved"
    if (-not $ptwApproved) {
        $meeting.status = "blocked-on-ptw"
        $relationship.meeting_status = "blocked-on-ptw"
        continue
    }
    if ((Get-BossKeyString -Value $ptw.pursue_recommendation).ToLowerInvariant() -eq "no-bid") {
        $meeting.status = "blocked-no-bid"
        $relationship.meeting_status = "blocked-no-bid"
        continue
    }

    $invitePath = "marketing-agents/briefs/generated/boss-key-growth-os/meetings/{0}-invite-packet.md" -f $meeting.meeting_id
    $inviteResolved = Resolve-BossKeyGrowthPath $invitePath
    Ensure-BossKeyGrowthDirectory -PathValue (Split-Path -Parent $inviteResolved)
    Get-BossKeyInvitePacketText -Meeting $meeting | Set-Content -Path $inviteResolved -Encoding UTF8
    $meeting.status = "ready-to-send"
    $meeting.invite_packet_path = $invitePath
    $relationship.relationship_stage = "meeting-proposed"
    $relationship.meeting_status = "ready-to-send"
}

foreach ($proposal in $proposalQueue.ToArray()) {
    $relationship = $relationships | Where-Object { $_.relationship_id -eq $proposal.relationship_id } | Select-Object -First 1
    $ptw = $ptwQueue | Where-Object { ((Get-BossKeyString -Value $_.is_active).ToLowerInvariant() -eq "yes") -and ($_.relationship_id -eq $proposal.relationship_id) } | Select-Object -First 1
    if ($null -eq $relationship) { continue }
    if ((Get-BossKeyString -Value $proposal.owner_decision).ToLowerInvariant() -ne "approve") { continue }

    $ptwApproved = $null -ne $ptw -and (Get-BossKeyString -Value $ptw.review_status).ToLowerInvariant() -eq "approved"
    if (-not $ptwApproved) {
        $proposal.status = "blocked-on-ptw"
        $proposal.review_status = "blocked-on-ptw"
        $relationship.proposal_status = "blocked-on-ptw"
        continue
    }
    if ((Get-BossKeyString -Value $ptw.pursue_recommendation).ToLowerInvariant() -eq "no-bid") {
        $proposal.status = "blocked-no-bid"
        $proposal.review_status = "blocked-no-bid"
        $relationship.proposal_status = "blocked-no-bid"
        continue
    }
    if ((Get-BossKeyString -Value $proposal.pricing_status).ToLowerInvariant() -in @("needs-ptw-input", "market-assessment-only", "owner-escalation-required") -or
        [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $proposal.recommended_price_usd))) {
        $proposal.status = [string]$proposal.pricing_status
        $proposal.review_status = [string]$proposal.pricing_status
        $relationship.proposal_status = [string]$proposal.pricing_status
        continue
    }

    $proposal.status = "ready-to-send"
    $relationship.relationship_stage = "proposal-approved"
    $relationship.proposal_status = "ready-to-send"
}

Export-BossKeyCsv -Rows ($contentQueue.ToArray()) -PathValue $ContentQueueFile -PropertyOrder $contentPropertyOrder
Export-BossKeyCsv -Rows ($relationships.ToArray()) -PathValue $RelationshipQueueFile -PropertyOrder $relationshipPropertyOrder
Export-BossKeyCsv -Rows ($meetingQueue.ToArray()) -PathValue $MeetingQueueFile -PropertyOrder $meetingPropertyOrder
Export-BossKeyCsv -Rows ($ptwQueue.ToArray()) -PathValue $PtwQueueFile -PropertyOrder $ptwPropertyOrder
Export-BossKeyCsv -Rows ($proposalQueue.ToArray()) -PathValue $ProposalQueueFile -PropertyOrder $proposalPropertyOrder

if (-not $SkipProposalOpsSync) {
    & (Join-Path $PSScriptRoot "sync-boss-key-proposal-ops.ps1") `
        -Mode PersistReviewState `
        -RelationshipQueueFile $RelationshipQueueFile `
        -KnowledgeBaseFile $KnowledgeBaseFile `
        -ProposalQueueFile $ProposalQueueFile | Out-Null
}

& (Join-Path $PSScriptRoot "build-boss-key-insights-site.ps1") -QueueFile $ContentQueueFile | Out-Null

Write-Output "Applied Boss Key review decisions and refreshed the approved Insights site."
