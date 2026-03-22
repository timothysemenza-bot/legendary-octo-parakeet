---
name: apmp-review-cycle
description: Run structured review operations for content-development reviews, Pink/Red/Gold reviews, proofread readiness, and action-log consolidation. Use when a run needs to prepare, conduct, or close a proposal review cycle.
---

# APMP Review Cycle

## Purpose

Manage proposal reviews as structured quality-improvement events with usable outputs and clear follow-up actions.

## When to use it

- when a proposal draft is approaching a formal or informal review checkpoint
- when reviewer comments need to be consolidated into a clean issue log
- when a recurring run should determine readiness for Pink, Red, Gold, or proofreading

## Required inputs

- current draft status or draft location
- next milestone or review date, if known
- any existing review agendas, comments, or issue logs
- schedule constraints and known reviewer availability if available

## Expected outputs

- review readiness decision
- review agenda or scope note
- consolidated issue log with owners and due dates
- rework priorities and proofread/production guardrails

## Step-by-step instructions

1. Read `docs/apmp-automation-reference-map.md`, then use the review-management and scheduling sources listed there.
2. Determine the right review type for the draft maturity. Do not substitute a late review for an early one or vice versa.
3. Build or refresh the review scope, participants, timing, and exit criteria.
4. Consolidate comments into action-oriented guidance. Each issue should have an owner, disposition, and timing expectation.
5. Protect proofreading and production time. Do not let review churn erase the final quality-control window.
6. If the review is premature, say so and identify what must be completed first.
7. End with the next handoff: draft rework, final production, or lessons-learned harvest.

## Scripts and resources

- Read `docs/apmp-automation-reference-map.md`.
- Open the pinned export pages for review management and scheduling.
- Use `.\scripts\review-change-scope.ps1` only when the review work overlaps with code or document packaging changes tracked in git and you need a scoped diff summary.
