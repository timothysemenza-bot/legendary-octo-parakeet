# Boss Key Pricing Model

This file explains how the review-first Growth OS now prices proposals with Competitive Price to Win logic.

## Pricing philosophy

The system no longer treats pricing as a simple internal `base price + modifier` exercise.

It now follows a competitive PTW structure:

- externally focused first
- customer and competitor aware
- separate from internal cost-plus thinking
- refined over time as discovery improves

Internal delivery modifiers still exist, but they are now secondary adjustments inside a PTW band instead of the main pricing engine.

## The PTW band

Each qualified opportunity can now produce up to three commercial numbers:

- `price_to_compete_usd`
  - early top-down view of where Boss Key likely needs to land to stay commercially viable in the market
- `price_to_win_usd`
  - later bottom-up refinement once buyer priorities, evaluation posture, and likely competitor behavior are clearer
- `minimum_acceptable_price_usd`
  - internal floor from the private price book

The proposal queue mirrors `price_to_win_usd` into `recommended_price_usd` for the outbound draft when that number exists.

## APMP-aligned evidence factors

The PTW layer looks at:

- customer need and desired outcome
- budget signal or budget band
- likely competitors and substitutes
- incumbent pressure
- buyer priorities and evaluation posture
- Boss Key differentiation
- the APMP-style Big 4 framing:
  - technical
  - management
  - past performance
  - cost / price

## Offer shaping

Starter-first is the default commercial posture.

If a narrower first move is more likely to win than the original offer hypothesis, the system:

- recommends the narrower `recommended_entry_offer`
- keeps the original or larger follow-on motion as `expansion_offer`
- writes both into the PTW brief and proposal packet

That is why a relationship can start with `Opportunity Foresight Sprint` even when the original offer hypothesis was a larger engagement.

## Price-book fields

The private price book now carries:

- `base_price_usd`
- `minimum_price_usd`
- `maximum_price_usd`
- `starter_strategy_allowed`
- `starter_offer_name`
- `expansion_offer_name`
- `owner_confirmation_required`

The price book remains internal only.

## Working anchors

- `Opportunity Foresight Sprint`
  - working base: `$5,500`
  - floor / ceiling currently configured in the private price book
- `Procurement Intelligence Retainer`
  - working base: `$6,000/month`
- `Capture Strategy Engagement`
  - working base: `$9,500`
- `Proposal Execution Support`
  - working base: `$12,500`

## Status behavior

The PTW layer can leave a proposal in one of these states:

- `needs-ptw-input`
  - too little evidence for a credible PTW view
- `market-assessment-only`
  - enough evidence for `price_to_compete`, not enough for a credible `price_to_win`
- `owner-escalation-required`
  - likely winning price falls below the configured floor
- `no-bid`
  - current commercial shape is not attractive enough to pursue
- `owner-confirmation-required`
  - viable PTW output exists, but final send still needs owner approval

## Knowledge base and calibration

Competitive context is stored in:

- `marketing-agents/data/boss_key_competitive_kb.csv`
- `marketing-agents/data/boss_key_ptw_outcomes.csv`

Generated PTW model rows are written back for continuity, but only direct evidence rows are treated as primary market evidence on later runs. Outcome rows help calibrate future PTW recommendations by comparing prior PTW estimates against actual quoted or awarded prices.

## What to update next

When you want to tune the commercial model, edit:

- `marketing-agents/data/boss_key_private_price_book.csv`

That lets you adjust:

- base price
- floor
- ceiling
- starter / expansion rules
- notes and positioning anchors

without changing the scripts.
