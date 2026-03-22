# JWBLNG Homepage Implementation Spec
Date: 2026-03-17
Scope tie-in:
- `JWBLNG-Donated-Scope-One-Pager.md`
- `JWBLNG-Creative-Brief.md`
- `notes/meeting-notes-2026-03-17-jessica-follow-up.md`
- `transcripts/jwblng-meeting-2026-03-16-transcript-extract.md`

Use this as the current homepage target and QA reference.

## Goal
Create a clear public homepage that:
1. Explains what JWBLNG is before asking for gated action
2. Captures join interest through the homepage form
3. Routes visitors into events and donation paths without creating duplicate join funnels

## Current Section Blueprint
1. Header/Nav
- Logo
- `About Us`
- `Events`
- `Donate`
- Kajabi `Log In`

2. Hero
- Headline: `Support, education, and community for Orthodox Jewish women in business.`
- Supporting copy: speaker series, book club, business halacha, peer network
- Primary CTA: `Join JWBLNG`

3. Join Form
- Same page as the hero
- Required fields:
  - `name`
  - `email`
  - `interest`

4. Program Highlights
- `Speaker Series`
- `Book Club`
- `Classes & Learning`
- Events CTA

5. Values Section
- Professional growth with integrity
- Supportive peer network
- Actionable guidance for real business challenges

6. Membership CTA
- `Membership is free`
- CTA returns visitors into the same approved join path

## CTA Targets
- Homepage join CTAs -> `/#block-1772192187104_0`
- Secondary-page join CTAs -> `/join` when Kajabi strips homepage hash anchors
- Events CTA -> `/events`
- Donation CTA -> `/support-jwblng` and approved Zeffy destination

## Acceptance Criteria
- Homepage renders cleanly on desktop and mobile.
- The explanatory story appears above or alongside the form.
- The homepage keeps one canonical join path only.
- Events CTA is visible and valid.
- Public copy matches the Phase 1 story approved from the transcript/notes.

## QA Command
After implementing in Kajabi, run:
```powershell
npm run pw:jwblng:homeqa
```
