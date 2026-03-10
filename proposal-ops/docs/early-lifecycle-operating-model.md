# Boss Key Pursuit OS - Early-Lifecycle Operating Model

## Purpose

This repo exists to support Boss Key's consulting model:

```text
Policy Intelligence
-> Opportunity Forecasting
-> Capture Strategy
-> Proposal Execution
```

The goal is to codify the firm's operating discipline in software and reusable artifacts without pretending the firm is a SaaS platform.

## What The System Must Do

### 1. Support earlier market visibility
- Track public-sector signals before formal solicitations exist
- Translate signals into opportunity hypotheses and watchlists
- Preserve source provenance and analyst judgment

### 2. Make capture work concrete
- Turn likely opportunities into named actions, stakeholder maps, and qualification decisions
- Link upstream intelligence to contractor strategy and commercial planning
- Keep human approval in the loop at every material decision point

### 3. Carry context into proposal execution
- Avoid losing intelligence and capture context once the solicitation is released
- Preserve a single operating chain from forecast to proposal
- Produce exportable deliverables, not platform lock-in

## Current Product Wedge

The first implemented wedge is:
- region: Mid-Atlantic
- market: state and local
- vertical: janitorial / facilities services

This wedge is intentional. It gives Boss Key a concrete operating environment while the broader early-lifecycle model is codified.

## Lifecycle To Product Mapping

| Lifecycle stage | Advisory activity | Current software support |
| --- | --- | --- |
| Policy / procurement intelligence | budgets, agendas, legislation, program interpretation, signal tracking | documented target state; manual and service-led today |
| Opportunity forecasting | account watchlists, contract radar, likely buying events, timing hypotheses | implemented in `janitorial_os` market radar and dashboard workflows |
| Capture strategy | qualification, contractor strategy, touchpoints, intelligence notes, capture actions, commercials | implemented in `janitorial_os` and linked opportunity workflows |
| Proposal execution | intake, compliance framing, content planning, review, submission readiness | partially implemented in `opportunity_intake` and downstream proposal modules |

## Design Principles

- Internal-first: optimize for operator usefulness before client-facing polish
- Human-gated: no silent workflow changes, no autonomous bid decisions
- Artifact-first: outputs must be reusable in consulting delivery
- Additive verticalization: build reusable foundations, then layer sector packs
- Privacy-aware: store structured metadata where possible, avoid unnecessary content capture
- Non-lobbying boundary: public information analysis and capture discipline only

## Near-Term Product Requirements

### Procurement intelligence foundation
- source registry for budgets, agendas, policy documents, and procurement feeds
- agency and account watchlists
- signal event records with provenance
- opportunity-hypothesis records connected to source signals

### Cross-vertical generalization
- keep janitorial entities as the first wedge
- generalize watchlist, forecast, and capture patterns for healthcare, education, municipal services, nonprofits, and public-sector technology

### Client artifact packaging
- reusable signal brief
- forecast memo
- capture brief
- stakeholder map
- pursuit recommendation memo

## Non-Goals

- not a lobbying CRM
- not a passive surveillance or replay platform
- not a generalized ERP for government contractors
- not a productized AI proposal writer with no operator judgment

## Operating Standard

Every feature should make one of these outcomes clearer:
- what the market is signaling
- which opportunities are worth attention
- what should happen before the RFP
- how proposal execution inherits that context cleanly
