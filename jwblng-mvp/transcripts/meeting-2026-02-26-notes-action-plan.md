# JWBLNG Meeting Notes + Action Plan
Date: February 26, 2026  
Participants: Marcy Fried, Timmy Semenza  
Source recording: `C:\Users\timot\Videos\Captures\Meet - JWBLNG & Boss Key - Website development discussion and 5 more pages - Personal - Microsoft​ Edge 2026-02-26 12-01-04.mp4`

## Transcript Output
- Timestamped transcript (SRT): `c:\Users\timot\Documents\Proposal-Microsite\jwblng-mvp\transcripts\jwblng-meeting-2026-02-26.srt`
- Plain text transcript: `c:\Users\timot\Documents\Proposal-Microsite\jwblng-mvp\transcripts\jwblng-meeting-2026-02-26.txt`

Note: This is machine transcription and contains minor recognition errors (for example "Zeffy" and "JWBLNG" may be misheard in some lines).

## What Was Agreed
1. Strategic direction: prioritize Kajabi consolidation, not a full custom-platform rebuild in Phase 1.
2. Wix direction: likely retire Wix after equivalent Kajabi pages/flows are in place.
3. Domain direction: keep `jwblng.org` as the public URL; point it to Kajabi experience.
4. Donations: keep Zeffy in the flow; embed/link cleanly from Kajabi onboarding and event paths.
5. Membership model: free membership, with optional paid/upsell programs later.
6. Priority concerns: security, access control, and a very simple member experience for non-technical users.
7. Operations goal: make event posting, reminders, communications, and login paths straightforward.
8. Immediate enablement: Jessica/Marcy to provide access for Kajabi, Wix, GoDaddy, Zoom, Zeffy.
9. Time box: three-week constrained implementation is considered feasible.

## Key Requirements Captured
1. Reduce friction in join/login flow (especially password and first-visit usability).
2. Capture member interest and segment users by program/learning-group intent.
3. Maintain brand identity on the public-facing experience (`jwblng.org`), not "Kajabi-looking" URLs in member comms.
4. Preserve safety/security controls while avoiding over-complex steps for members.
5. Ensure future monetization options (courses/professional offerings) can layer on top of free membership.

## Risks To Manage Early
1. DNS and email changes can accidentally interrupt service.
2. Platform confusion from dual systems (Wix + Kajabi) can persist unless cutover is explicit.
3. Non-technical operators need SOP-level workflows, not technical runbooks.
4. Time zone friction for MFA/login codes (Marcy is 7 hours ahead) can stall setup work.

## First 72 Hours: Immediate Action Plan
1. Credential intake and validation (Owner: Timmy, Support: Jessica/Marcy)
- Collect logins for Kajabi, Wix, GoDaddy, Zoom, Zeffy.
- Verify access immediately and note any MFA dependencies.
- Confirm who receives security codes and best overlap window for live auth.

2. Baseline audit (Owner: Timmy)
- Document current page map in Kajabi and Wix.
- Identify all active forms, offers, pipelines, automations, and event flows.
- Capture DNS/email current-state records before touching anything.

3. Decision lock (Owner: Marcy + Jessica)
- Confirm "Kajabi-first, Wix-retire" as Phase 1 direction.
- Confirm that domain remains owned where it is today, with pointing/cutover only.
- Confirm exact donation path behavior (embed vs external link for Zeffy).

4. Phase 1 definition freeze (Owner: Timmy)
- Finalize constrained deliverables list and out-of-scope list.
- Share one-page implementation plan and approval checkpoint.

## 3-Week Execution Plan
### Week 1: Architecture + Journey
1. Define canonical member journey (home -> join -> onboarding -> events -> updates).
2. Remove/replace fragile free-membership workarounds (coupon-based confusion).
3. Simplify navigation and establish one clear primary CTA path.

### Week 2: Build + Automation
1. Build core public and member-facing Kajabi pages.
2. Configure event flow templates (publish, RSVP, reminder, follow-up).
3. Configure communication templates (welcome, newsletter base, update notices).
4. Wire Zoom/Zeffy touchpoints.

### Week 3: QA + Cutover + Handover
1. End-to-end QA with test users for join/login/event experience.
2. DNS/domain cutover checklist and launch window.
3. Admin SOP for Jessica + backup owner; live walkthrough and sign-off.

## Deliverables (Phase 1)
1. Consolidated Kajabi information architecture.
2. Clear free-member onboarding path with segmentation touchpoints.
3. Repeatable event + communication operating flow.
4. Domain-routing/cutover checklist and launch support.
5. Admin SOP and handoff session.

## Open Questions To Resolve Before Build
1. Which pages from Wix are mandatory to preserve as-is?
2. Should member directory/community feed be emphasized in Phase 1 or deferred?
3. Preferred method for Zeffy donations in onboarding: inline embed or external page?
4. Who is backup admin if Jessica or Marcy is unavailable?
5. What minimum security controls are required for membership access screening?

## Suggested Client Update Message (Copy/Paste)
We completed discovery and aligned on a constrained Phase 1 focused on Kajabi consolidation. The immediate goal is to simplify member onboarding, event operations, and communications while preserving security and reducing administrative burden.  
Next step is credential/access validation and a locked 3-week implementation plan, followed by phased build, QA, and cutover of `jwblng.org` to the streamlined Kajabi experience.
