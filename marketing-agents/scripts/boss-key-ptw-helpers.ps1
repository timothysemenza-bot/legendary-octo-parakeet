Set-StrictMode -Version Latest

function Get-BossKeyString {
    param(
        [object]$Value,
        [string]$Fallback = ""
    )

    if ($null -eq $Value) { return $Fallback }
    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) { return $Fallback }
    return $text.Trim()
}

function Get-BossKeyDecimal {
    param([object]$Value)

    if ($null -eq $Value) { return 0 }
    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) { return 0 }
    try { return [decimal]($text -replace '[^\d\.\-]', '') } catch { return 0 }
}

function Get-BossKeyObjectValue {
    param(
        [object]$Object,
        [string]$PropertyName
    )

    if ($null -eq $Object) { return $null }
    if ($Object.PSObject.Properties.Name -notcontains $PropertyName) { return $null }
    return $Object.$PropertyName
}

function Split-BossKeyList {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) { return ,@() }
    return ,@(
        $Value -split '(?:\r?\n|;|\|)' |
            ForEach-Object { $_.Trim() } |
            Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
            Select-Object -Unique
    )
}

function Join-BossKeyList {
    param([object[]]$Values)

    return (
        @($Values |
            Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } |
            ForEach-Object { [string]$_ } |
            Select-Object -Unique) -join "; "
    )
}

function Get-BossKeyReliabilityScore {
    param([string]$Value)

    switch ((Get-BossKeyString -Value $Value).ToLowerInvariant()) {
        "verified" { return 1.0 }
        "high" { return 0.85 }
        "medium" { return 0.65 }
        "low" { return 0.45 }
        default { return 0.55 }
    }
}

function Get-BossKeyBudgetContext {
    param(
        [string]$BudgetBand,
        [string]$BudgetSignal
    )

    $sourceText = Get-BossKeyString -Value $BudgetBand -Fallback $BudgetSignal
    if ([string]::IsNullOrWhiteSpace($sourceText)) {
        return [pscustomobject]@{ label = ""; minimum = 0; maximum = 0; midpoint = 0 }
    }

    $numbers = [regex]::Matches($sourceText, '\d[\d,]*') |
        ForEach-Object { [int](($_.Value) -replace ',', '') }

    $minimum = 0
    $maximum = 0
    if ($numbers.Count -ge 2) {
        $minimum = [int]$numbers[0]
        $maximum = [int]$numbers[1]
    } elseif ($numbers.Count -eq 1) {
        $only = [int]$numbers[0]
        if ($sourceText -match '(?i)under|below|less than') {
            $maximum = $only
        } elseif ($sourceText -match '(?i)over|above|more than|starting at') {
            $minimum = $only
        } else {
            $minimum = $only
            $maximum = $only
        }
    }

    $midpoint = 0
    if ($minimum -gt 0 -and $maximum -gt 0) {
        $midpoint = [math]::Round(($minimum + $maximum) / 2, 0)
    } elseif ($maximum -gt 0) {
        $midpoint = [math]::Round($maximum * 0.85, 0)
    } elseif ($minimum -gt 0) {
        $midpoint = [math]::Round($minimum * 1.1, 0)
    }

    return [pscustomobject]@{
        label = $sourceText
        minimum = $minimum
        maximum = $maximum
        midpoint = $midpoint
    }
}

function Test-BossKeyPtwEligibleRelationship {
    param([pscustomobject]$Relationship)

    if ((Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $Relationship -PropertyName "fit_confirmed")).ToLowerInvariant() -ne "yes") { return $false }
    if ([string]::IsNullOrWhiteSpace((Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $Relationship -PropertyName "warm_signal")))) { return $false }
    foreach ($field in @("pain_point", "desired_outcome", "offer_hypothesis")) {
        if ([string]::IsNullOrWhiteSpace((Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $Relationship -PropertyName $field)))) { return $false }
    }

    $stage = (Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $Relationship -PropertyName "relationship_stage")).ToLowerInvariant()
    if ($stage -in @("qualified-pre-consult", "meeting-proposed", "meeting-booked", "proposal-drafted", "proposal-approved")) {
        return $true
    }

    return ((Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $Relationship -PropertyName "meeting_needed")).ToLowerInvariant() -eq "yes")
}

function Get-BossKeyOfferContext {
    param(
        [string]$OfferName,
        [object[]]$PriceBook
    )

    $row = $PriceBook | Where-Object { (Get-BossKeyObjectValue -Object $_ -PropertyName "offer_name") -eq $OfferName } | Select-Object -First 1
    if ($null -eq $row) {
        return [pscustomobject]@{
            offer_name = $OfferName
            base_price = 0
            minimum_price = 0
            maximum_price = 0
            pricing_status = "owner-price-book-needed"
            owner_confirmation_required = "yes"
            pricing_anchor = "No internal pricing anchor found yet."
            starter_strategy_allowed = "no"
            starter_offer_name = ""
            expansion_offer_name = ""
            notes = "Price-book row missing."
        }
    }

    return [pscustomobject]@{
        offer_name = [string](Get-BossKeyObjectValue -Object $row -PropertyName "offer_name")
        base_price = Get-BossKeyDecimal -Value (Get-BossKeyObjectValue -Object $row -PropertyName "base_price_usd")
        minimum_price = Get-BossKeyDecimal -Value (Get-BossKeyObjectValue -Object $row -PropertyName "minimum_price_usd")
        maximum_price = Get-BossKeyDecimal -Value (Get-BossKeyObjectValue -Object $row -PropertyName "maximum_price_usd")
        pricing_status = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "pricing_status") -Fallback "owner-confirmation-required"
        owner_confirmation_required = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "owner_confirmation_required") -Fallback "yes"
        pricing_anchor = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "pricing_anchor") -Fallback "No internal pricing anchor found yet."
        starter_strategy_allowed = (Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "starter_strategy_allowed") -Fallback "no").ToLowerInvariant()
        starter_offer_name = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "starter_offer_name")
        expansion_offer_name = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "expansion_offer_name")
        notes = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "notes")
    }
}

function Get-BossKeyKnowledgeContext {
    param(
        [pscustomobject]$Relationship,
        [object[]]$KnowledgeRows
    )

    $rows = @(
        $KnowledgeRows |
            Where-Object {
                (Get-BossKeyObjectValue -Object $_ -PropertyName "relationship_id") -eq (Get-BossKeyObjectValue -Object $Relationship -PropertyName "relationship_id") -or
                ((Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $_ -PropertyName "company_name")).ToLowerInvariant() -eq ((Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $Relationship -PropertyName "company_name")).ToLowerInvariant()))
            }
    )
    $primaryRows = @(
        $rows |
            Where-Object {
                (Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $_ -PropertyName "source_type")).ToLowerInvariant() -ne "generated-ptw"
            }
    )
    if ($primaryRows.Count -eq 0) { $primaryRows = $rows }
    $generatedRows = @(
        $rows |
            Where-Object {
                (Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $_ -PropertyName "source_type")).ToLowerInvariant() -eq "generated-ptw"
            }
    )

    $context = [ordered]@{
        customer_objective = ""
        customer_need = ""
        customer_value_drivers = ""
        buyer_priorities = ""
        evaluation_priorities = ""
        buying_behavior = ""
        delivery_context = ""
        timing_context = ""
        budget_signal = ""
        budget_band = ""
        likely_competitors = ""
        incumbent_status = ""
        substitute_options = ""
        big4_technical = ""
        big4_management = ""
        big4_past_performance = ""
        big4_cost_price = ""
        differentiation_hypothesis = ""
        evidence_summary = ""
        assumptions = ""
        source_quality_notes = ""
        source_reliability = ""
        confidence = 0
        source_summary = ""
    }

    $budgetSignals = New-Object System.Collections.Generic.List[string]
    $budgetBands = New-Object System.Collections.Generic.List[string]
    $competitors = New-Object System.Collections.Generic.List[string]
    $alternatives = New-Object System.Collections.Generic.List[string]
    $evidence = New-Object System.Collections.Generic.List[string]
    $assumptions = New-Object System.Collections.Generic.List[string]
    $sourceRefs = New-Object System.Collections.Generic.List[string]
    $reliabilityValues = New-Object System.Collections.Generic.List[decimal]
    $confidenceValues = New-Object System.Collections.Generic.List[decimal]

    foreach ($row in $primaryRows) {
        foreach ($field in @(
            "customer_objective", "customer_need", "customer_value_drivers", "buyer_priorities",
            "evaluation_priorities", "buying_behavior", "delivery_context", "timing_context",
            "incumbent_status", "big4_technical", "big4_management", "big4_past_performance",
            "big4_cost_price", "differentiation_hypothesis", "source_quality_notes"
        )) {
            if ([string]::IsNullOrWhiteSpace($context[$field])) {
                $context[$field] = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName $field)
            }
        }

        foreach ($item in (Split-BossKeyList -Value (Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "budget_signal")))) { $budgetSignals.Add($item) }
        foreach ($item in (Split-BossKeyList -Value (Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "budget_band")))) { $budgetBands.Add($item) }
        foreach ($item in (Split-BossKeyList -Value (Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "competitor_name")))) { $competitors.Add($item) }
        foreach ($item in (Split-BossKeyList -Value (Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "alternative_option")))) { $alternatives.Add($item) }
        foreach ($item in (Split-BossKeyList -Value (Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "evidence_summary")))) { $evidence.Add($item) }
        foreach ($item in (Split-BossKeyList -Value (Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "assumptions")))) { $assumptions.Add($item) }

        $sourceRef = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "source_reference")
        if (-not [string]::IsNullOrWhiteSpace($sourceRef)) {
            $sourceRefs.Add(($sourceRef + " [" + (Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "source_type") -Fallback "source") + "]").Trim())
        }

        $reliabilityValues.Add([decimal](Get-BossKeyReliabilityScore -Value (Get-BossKeyObjectValue -Object $row -PropertyName "source_reliability")))
        $confidenceValues.Add((Get-BossKeyDecimal -Value (Get-BossKeyObjectValue -Object $row -PropertyName "confidence")))
    }

    foreach ($row in $generatedRows) {
        foreach ($field in @(
            "customer_objective", "customer_need", "customer_value_drivers", "buyer_priorities",
            "evaluation_priorities", "buying_behavior", "delivery_context", "timing_context",
            "incumbent_status", "big4_technical", "big4_management", "big4_past_performance",
            "big4_cost_price", "differentiation_hypothesis"
        )) {
            if ([string]::IsNullOrWhiteSpace($context[$field])) {
                $context[$field] = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName $field)
            }
        }

        if ([string]::IsNullOrWhiteSpace($context["budget_signal"])) {
            $context["budget_signal"] = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "budget_signal")
        }
        if ([string]::IsNullOrWhiteSpace($context["budget_band"])) {
            $context["budget_band"] = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "budget_band")
        }
        if ([string]::IsNullOrWhiteSpace($context["likely_competitors"])) {
            $context["likely_competitors"] = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "competitor_name")
        }
        if ([string]::IsNullOrWhiteSpace($context["substitute_options"])) {
            $context["substitute_options"] = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "alternative_option")
        }
        if ([string]::IsNullOrWhiteSpace($context["evidence_summary"])) {
            $context["evidence_summary"] = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "evidence_summary")
        }
        if ([string]::IsNullOrWhiteSpace($context["assumptions"])) {
            $context["assumptions"] = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $row -PropertyName "assumptions")
        }
    }

    if ($budgetSignals.Count -gt 0) { $context["budget_signal"] = Join-BossKeyList -Values $budgetSignals.ToArray() }
    if ($budgetBands.Count -gt 0) { $context["budget_band"] = Join-BossKeyList -Values $budgetBands.ToArray() }
    if ($competitors.Count -gt 0) { $context["likely_competitors"] = Join-BossKeyList -Values $competitors.ToArray() }
    if ($alternatives.Count -gt 0) { $context["substitute_options"] = Join-BossKeyList -Values $alternatives.ToArray() }
    if ($evidence.Count -gt 0) { $context["evidence_summary"] = Join-BossKeyList -Values $evidence.ToArray() }
    if ($assumptions.Count -gt 0) { $context["assumptions"] = Join-BossKeyList -Values $assumptions.ToArray() }
    if ($sourceRefs.Count -gt 0) { $context["source_summary"] = Join-BossKeyList -Values $sourceRefs.ToArray() }

    if ($confidenceValues.Count -gt 0) {
        $context["confidence"] = [math]::Round((($confidenceValues | Measure-Object -Average).Average), 0)
    }

    if ($reliabilityValues.Count -gt 0) {
        $avg = ($reliabilityValues | Measure-Object -Average).Average
        if ($avg -ge 0.9) { $context["source_reliability"] = "verified" }
        elseif ($avg -ge 0.8) { $context["source_reliability"] = "high" }
        elseif ($avg -ge 0.6) { $context["source_reliability"] = "medium" }
        else { $context["source_reliability"] = "low" }
    }

    if ([string]::IsNullOrWhiteSpace($context["customer_need"])) {
        $context["customer_need"] = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $Relationship -PropertyName "pain_point")
    }
    if ([string]::IsNullOrWhiteSpace($context["customer_objective"])) {
        $context["customer_objective"] = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $Relationship -PropertyName "desired_outcome")
    }

    return [pscustomobject]$context
}

function Get-BossKeyPtwStage {
    param(
        [pscustomobject]$ExistingPtw,
        [pscustomobject]$KnowledgeContext
    )

    $existing = Get-BossKeyString -Value (Get-BossKeyObjectValue -Object $ExistingPtw -PropertyName "ptw_stage")
    if (-not [string]::IsNullOrWhiteSpace($existing)) { return $existing }

    $hasOpportunitySignals =
        (-not [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.buyer_priorities))) -and
        (-not [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.evaluation_priorities))) -and
        (-not [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.buying_behavior))) -and
        (-not [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.likely_competitors)))

    if ($hasOpportunitySignals) { return "opportunity-analysis" }
    return "market-assessment"
}

function Get-BossKeyPtwConfidence {
    param(
        [pscustomobject]$KnowledgeContext,
        [string]$Stage
    )

    $score = 35
    foreach ($field in @("customer_need", "customer_objective", "customer_value_drivers", "buyer_priorities")) {
        if (-not [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.$field))) { $score += 6 }
    }
    if (-not [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.budget_band)) -or
        -not [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.budget_signal))) { $score += 8 }
    if (-not [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.likely_competitors)) -or
        -not [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.substitute_options))) { $score += 10 }

    $big4Count = @(@(
        (Get-BossKeyString -Value $KnowledgeContext.big4_technical),
        (Get-BossKeyString -Value $KnowledgeContext.big4_management),
        (Get-BossKeyString -Value $KnowledgeContext.big4_past_performance),
        (Get-BossKeyString -Value $KnowledgeContext.big4_cost_price)
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    $score += ($big4Count.Count * 4)
    $score += [math]::Round(((Get-BossKeyDecimal -Value $KnowledgeContext.confidence) / 100) * 12, 0)
    $score += [math]::Round((Get-BossKeyReliabilityScore -Value $KnowledgeContext.source_reliability) * 8, 0)
    if ($Stage -eq "opportunity-analysis") { $score += 7 }
    if ($score -gt 92) { $score = 92 }
    if ($score -lt 25) { $score = 25 }
    return [int]$score
}

function Resolve-BossKeyEntryOffer {
    param(
        [pscustomobject]$PrimaryOffer,
        [object[]]$PriceBook,
        [pscustomobject]$KnowledgeContext,
        [int]$Confidence,
        [string]$Stage
    )

    $budget = Get-BossKeyBudgetContext -BudgetBand $KnowledgeContext.budget_band -BudgetSignal $KnowledgeContext.budget_signal
    $entryOffer = $PrimaryOffer
    $expansionOfferName = Get-BossKeyString -Value $PrimaryOffer.expansion_offer_name

    if ($PrimaryOffer.starter_strategy_allowed -eq "yes" -and
        -not [string]::IsNullOrWhiteSpace($PrimaryOffer.starter_offer_name) -and
        $PrimaryOffer.starter_offer_name -ne $PrimaryOffer.offer_name) {
        $starterOffer = Get-BossKeyOfferContext -OfferName $PrimaryOffer.starter_offer_name -PriceBook $PriceBook
        $shouldDownshift =
            $Stage -eq "market-assessment" -or
            $Confidence -lt 70 -or
            ($budget.maximum -gt 0 -and $PrimaryOffer.base_price -gt $budget.maximum) -or
            ((Get-BossKeyString -Value $KnowledgeContext.substitute_options).Length -gt 0) -or
            ((Get-BossKeyString -Value $KnowledgeContext.buyer_priorities).ToLowerInvariant() -match 'quick|low-risk|proof|pilot')

        if ($shouldDownshift -and $starterOffer.base_price -gt 0) {
            $entryOffer = $starterOffer
            if ([string]::IsNullOrWhiteSpace($expansionOfferName)) {
                $expansionOfferName = $PrimaryOffer.offer_name
            }
        }
    }

    if ([string]::IsNullOrWhiteSpace($expansionOfferName) -and $entryOffer.offer_name -ne $PrimaryOffer.offer_name) {
        $expansionOfferName = $PrimaryOffer.offer_name
    }

    return [pscustomobject]@{
        entry_offer = $entryOffer
        expansion_offer = $expansionOfferName
        budget_context = $budget
    }
}

function Get-BossKeyPtwPricing {
    param(
        [pscustomobject]$Relationship,
        [pscustomobject]$OfferContext,
        [pscustomobject]$KnowledgeContext,
        [pscustomobject]$BudgetContext,
        [int]$Confidence,
        [string]$Stage,
        [object[]]$ModifierRows
    )

    $basePrice = [decimal]$OfferContext.base_price
    $marketAnchor = if ($BudgetContext.midpoint -gt 0 -and $BudgetContext.midpoint -lt $basePrice) { [decimal]$BudgetContext.midpoint } else { $basePrice }
    if ($marketAnchor -le 0 -and $BudgetContext.midpoint -gt 0) { $marketAnchor = [decimal]$BudgetContext.midpoint }

    $competitorCount = (Split-BossKeyList -Value $KnowledgeContext.likely_competitors).Count
    $substituteCount = (Split-BossKeyList -Value $KnowledgeContext.substitute_options).Count
    $incumbent = (Get-BossKeyString -Value $KnowledgeContext.incumbent_status).ToLowerInvariant()
    $valueDrivers = (Get-BossKeyString -Value $KnowledgeContext.customer_value_drivers).ToLowerInvariant()
    $differentiation = (Get-BossKeyString -Value $KnowledgeContext.differentiation_hypothesis).ToLowerInvariant()

    $pressurePct = ($competitorCount * 3) + ($substituteCount * 3)
    if ($incumbent -match 'yes|incumbent|strong') { $pressurePct += 5 }
    if ($Confidence -lt 60) { $pressurePct += 3 }

    $valueLiftPct = 0
    if ($valueDrivers -match 'speed|owner time|reduce admin|protect incumbent|low drag') { $valueLiftPct += 2 }
    if ($differentiation -match 'diagnostic|faster|clarity|signal|operator') { $valueLiftPct += 2 }

    $priceToCompete = 0
    if ($marketAnchor -gt 0) {
        $priceToCompete = Round-BossKeyPrice -Value ([decimal]($marketAnchor * (1 - (($pressurePct - $valueLiftPct) / 100))))
        if ($BudgetContext.maximum -gt 0 -and $priceToCompete -gt $BudgetContext.maximum) {
            $priceToCompete = Round-BossKeyPrice -Value ([decimal]($BudgetContext.maximum * 0.98))
        }
        if ($OfferContext.maximum_price -gt 0 -and $priceToCompete -gt $OfferContext.maximum_price) {
            $priceToCompete = [decimal]$OfferContext.maximum_price
        }
    }

    $secondaryAdjustment =
        (Get-BossKeyModifierPercent -ModifierName "urgency_level" -Level (Get-BossKeyString -Value $Relationship.urgency_level) -ModifierRows $ModifierRows) +
        (Get-BossKeyModifierPercent -ModifierName "scope_breadth" -Level (Get-BossKeyString -Value $Relationship.scope_breadth) -ModifierRows $ModifierRows) +
        (Get-BossKeyModifierPercent -ModifierName "stakeholder_complexity" -Level (Get-BossKeyString -Value $Relationship.stakeholder_complexity) -ModifierRows $ModifierRows) +
        (Get-BossKeyModifierPercent -ModifierName "research_load" -Level (Get-BossKeyString -Value $Relationship.research_load) -ModifierRows $ModifierRows) +
        (Get-BossKeyModifierPercent -ModifierName "delivery_intensity" -Level (Get-BossKeyString -Value $Relationship.delivery_intensity) -ModifierRows $ModifierRows)

    $bottomUpPrice = 0
    if ($basePrice -gt 0) {
        $bottomUpPrice = Round-BossKeyPrice -Value ([decimal]($basePrice * (1 + (($secondaryAdjustment * 0.35) / 100))))
    }

    $priceToWin = 0
    if ($Stage -eq "opportunity-analysis" -and $priceToCompete -gt 0 -and $bottomUpPrice -gt 0) {
        $blend = [math]::Max(0.35, [math]::Min(0.7, ($Confidence / 100)))
        $weighted = [decimal](($priceToCompete * (1 - $blend)) + ($bottomUpPrice * $blend))
        if ($BudgetContext.maximum -gt 0 -and $weighted -gt $BudgetContext.maximum) {
            $weighted = [decimal]($BudgetContext.maximum * 0.99)
        }
        if ($OfferContext.maximum_price -gt 0 -and $weighted -gt $OfferContext.maximum_price) {
            $weighted = [decimal]$OfferContext.maximum_price
        }
        $priceToWin = Round-BossKeyPrice -Value $weighted
    }

    return [pscustomobject]@{
        price_to_compete = $priceToCompete
        price_to_win = $priceToWin
        secondary_adjustment_percent = [int][math]::Round($secondaryAdjustment, 0)
        pricing_basis = "Competitive PTW anchored to the external market position first and blended with a lighter internal delivery adjustment only when opportunity-analysis evidence exists."
        pricing_rationale = @(
            ("Market anchor: " + $(if ($marketAnchor -gt 0) { "$" + ([int]$marketAnchor).ToString("N0") } else { "not available" })),
            ("Budget posture: " + (Get-BossKeyString -Value $BudgetContext.label -Fallback "unknown")),
            ("Likely competitors: " + (Get-BossKeyString -Value $KnowledgeContext.likely_competitors -Fallback "not yet mapped")),
            ("Differentiation: " + (Get-BossKeyString -Value $KnowledgeContext.differentiation_hypothesis -Fallback "still being shaped"))
        ) -join " "
    }
}

function Get-BossKeyPursueRecommendation {
    param(
        [pscustomobject]$OfferContext,
        [pscustomobject]$KnowledgeContext,
        [decimal]$PriceToCompete,
        [decimal]$PriceToWin,
        [int]$Confidence
    )

    $floor = [decimal]$OfferContext.minimum_price
    $hasDifferentiation = -not [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.differentiation_hypothesis))
    $hasBudgetSignal = -not [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.budget_band)) -or
        -not [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.budget_signal))

    if (($PriceToCompete -gt 0 -and $floor -gt 0 -and $PriceToCompete -lt $floor) -and (-not $hasDifferentiation -or $Confidence -lt 55)) {
        return "no-bid"
    }
    if ($Confidence -lt 60 -or -not $hasBudgetSignal) { return "pursue-cautiously" }
    if ($PriceToWin -gt 0 -and $floor -gt 0 -and $PriceToWin -lt $floor) { return "pursue-cautiously" }
    return "pursue"
}

function Get-BossKeyPtwStatus {
    param(
        [pscustomobject]$KnowledgeContext,
        [pscustomobject]$OfferContext,
        [decimal]$PriceToCompete,
        [decimal]$PriceToWin,
        [string]$Stage,
        [string]$PursueRecommendation
    )

    $missingFields = New-Object System.Collections.Generic.List[string]
    if ([string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.customer_need))) { $missingFields.Add("customer_need") }
    if ([string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.differentiation_hypothesis))) { $missingFields.Add("differentiation_hypothesis") }
    if ([string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.budget_band)) -and
        [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.budget_signal))) { $missingFields.Add("budget_signal_or_band") }
    if ([string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.likely_competitors)) -and
        [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.substitute_options))) { $missingFields.Add("competitive_context") }
    if ([string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.source_quality_notes)) -and
        [string]::IsNullOrWhiteSpace((Get-BossKeyString -Value $KnowledgeContext.source_summary))) { $missingFields.Add("source_quality_notes") }

    $status = "pending-ptw-review"
    if ($missingFields.Count -gt 0 -and $PriceToCompete -le 0) {
        $status = "needs-ptw-input"
    } elseif ($PursueRecommendation -eq "no-bid") {
        $status = "no-bid"
    } elseif ($OfferContext.minimum_price -gt 0 -and (
            ($PriceToCompete -gt 0 -and $PriceToCompete -lt $OfferContext.minimum_price) -or
            ($PriceToWin -gt 0 -and $PriceToWin -lt $OfferContext.minimum_price)
        )) {
        $status = "owner-escalation-required"
    } elseif ($Stage -eq "market-assessment" -or $PriceToWin -le 0) {
        $status = "market-assessment-only"
    }

    return [pscustomobject]@{
        status = $status
        missing_fields = $missingFields.ToArray()
    }
}

function Get-BossKeyPtwDraftText {
    param(
        [pscustomobject]$Relationship,
        [pscustomobject]$PtwRecord
    )

    $competeLine = if ((Get-BossKeyDecimal -Value $PtwRecord.price_to_compete_usd) -gt 0) {
        "$" + ([int](Get-BossKeyDecimal -Value $PtwRecord.price_to_compete_usd)).ToString("N0")
    } else {
        "Need more market evidence before a credible top-down price can be set."
    }
    $winLine = if ((Get-BossKeyDecimal -Value $PtwRecord.price_to_win_usd) -gt 0) {
        "$" + ([int](Get-BossKeyDecimal -Value $PtwRecord.price_to_win_usd)).ToString("N0")
    } else {
        "Pending opportunity-analysis refinement."
    }
    $floorLine = if ((Get-BossKeyDecimal -Value $PtwRecord.minimum_acceptable_price_usd) -gt 0) {
        "$" + ([int](Get-BossKeyDecimal -Value $PtwRecord.minimum_acceptable_price_usd)).ToString("N0")
    } else {
        "No floor configured."
    }

    $lines = @()
    $lines += "# $($Relationship.company_name) | Competitive PTW brief"
    $lines += ""
    $lines += "Status: Pending owner approval before any proposal is send-ready."
    $lines += ""
    $lines += "## PTW posture"
    $lines += "- Stage: $($PtwRecord.ptw_stage)"
    $lines += "- Pursue recommendation: $($PtwRecord.pursue_recommendation)"
    $lines += "- Confidence: $($PtwRecord.data_confidence)%"
    $lines += "- Recommended entry offer: $($PtwRecord.recommended_entry_offer)"
    $lines += "- Expansion path: $($PtwRecord.expansion_offer)"
    $lines += ""
    $lines += "## Customer objective and need"
    $lines += "- Objective: $($PtwRecord.customer_objective)"
    $lines += "- Need / pain: $($PtwRecord.customer_need)"
    $lines += "- Value drivers: $($PtwRecord.customer_value_drivers)"
    $lines += "- Buyer priorities: $($PtwRecord.buyer_priorities)"
    $lines += "- Evaluation priorities: $($PtwRecord.evaluation_priorities)"
    $lines += "- Buying behavior: $($PtwRecord.buying_behavior)"
    $lines += ""
    $lines += "## Likely scope"
    $lines += "- Delivery context: $($PtwRecord.delivery_context)"
    $lines += "- Timing context: $($PtwRecord.timing_context)"
    $lines += ""
    $lines += "## Budget and competition"
    $lines += "- Budget signal: $($PtwRecord.budget_signal)"
    $lines += "- Budget band: $($PtwRecord.budget_band)"
    $lines += "- Budget confidence: $($PtwRecord.budget_confidence)%"
    $lines += "- Likely competitors: $($PtwRecord.likely_competitors)"
    $lines += "- Incumbent status: $($PtwRecord.incumbent_status)"
    $lines += "- Substitute options: $($PtwRecord.substitute_options)"
    $lines += ""
    $lines += "## PTW band"
    $lines += "- Price to compete: $competeLine"
    $lines += "- Price to win: $winLine"
    $lines += "- Minimum acceptable price: $floorLine"
    $lines += ""
    $lines += "## Evidence and assumptions"
    $lines += "- Evidence summary: $($PtwRecord.evidence_summary)"
    $lines += "- Source summary: $($PtwRecord.source_summary)"
    $lines += "- Source quality notes: $($PtwRecord.source_quality_notes)"
    foreach ($item in (Split-BossKeyList -Value $PtwRecord.assumptions)) { $lines += "- Assumption: $item" }
    $lines += ""
    return ($lines -join "`n").Trim() + "`n"
}
