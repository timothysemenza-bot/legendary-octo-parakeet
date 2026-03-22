---
name: apmp-capture-cycle
description: Plan and update opportunity/capture actions, gate decisions, and schedules for a live pursuit. Use when a run needs to qualify or advance an opportunity, refresh the capture plan, or prepare a gate-ready package.
---

# APMP Capture Cycle

## Purpose

Turn pursuit-stage information into concrete capture actions, gate decisions, and schedule-aware next steps.

## When to use it

- when the opportunity is still being shaped or qualified
- when leadership needs a gate packet or bid/no-bid recommendation
- when pursuit actions, discriminators, or resource commitments need to be refreshed
- when a recurring run should update the capture plan instead of drafting proposal content

## Required inputs

- current opportunity or account context
- known customer issues, requirements, and timeline
- competitor and teaming information, if available
- current pursuit assumptions, risks, and open actions

## Expected outputs

- gate decision brief or bid/no-bid recommendation
- capture action list with dates and accountable owners
- schedule notes and parallel-work opportunities
- updated risk and discriminator summary

## Step-by-step instructions

1. Read `docs/apmp-automation-reference-map.md`, then open the gate, scheduling, and opportunity-plan export pages listed there if needed.
2. Identify the current capture phase and the next decision gate.
3. Test the pursuit against APMP gate questions: is it real, can we win, and do we want to?
4. Convert findings into a short action-oriented capture plan. Each action should have one accountable owner, a due date or target window, and a visible reason it matters.
5. Use parallel work wherever feasible. Start long-lead items early and surface missing resources instead of hiding them.
6. If the pursuit does not justify more investment, say so clearly and recommend no-bid, defer, or re-position.
7. If the pursuit is ready to move forward, identify the clean handoff into kickoff or proposal planning.

## Scripts and resources

- Read `docs/apmp-automation-reference-map.md`.
- Open the pinned export pages for gate decisions, scheduling, and opportunity/capture plan development.
- Reuse `.\.agents\skills\proposal-manager\scripts\generate-proposal-workplan.ps1` when you need a backward-planned schedule anchored to a known deadline.
