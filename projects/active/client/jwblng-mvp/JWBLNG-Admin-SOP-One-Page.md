# JWBLNG Admin SOP (One Page)
Owner: JWBLNG Admin Team (Jessica / Marcy)
Prepared by: Timmy Semenza, Boss Key LLC
Updated: 2026-03-17

Purpose: Run the Phase 1 public site, member-approval, event, and email workflows safely and consistently in Kajabi.

## 1) Approve Contact (Grant Free Community Access Only)
When to use: A new homepage join-form request is legitimate and should be admitted to free JWBLNG community access.

1. Go to `Contacts`.
2. Open the `pending-review` saved filter or segment.
3. Open the contact record.
4. Confirm basic legitimacy:
- name
- email
- interest selection
- any notes or referral context
5. Add tag `approved-member`.
6. Confirm the contact receives only the intended free community-access offer.
7. Confirm `pending-review` is cleared if the automation is set to remove it.

Manual fallback:
- If the welcome/approval automation does not fire, send the approved welcome draft manually from Kajabi Email Campaigns.

Guardrail:
- Never grant Insider or paid-access offers during Phase 1 unless there is an explicit written instruction to do so.

## 2) Hold or Reject Contact
When to use: The submission is incomplete, unclear, suspicious, or needs follow-up first.

1. Go to `Contacts` -> `pending-review`.
2. Open the contact record.
3. Do not add `approved-member`.
4. Add one status tag:
- `needs-follow-up`, or
- `declined`
5. Send a manual clarification email only if needed.

Result:
- No offer is granted.
- The contact stays outside gated/member-only areas.

## 3) Update or Publish Event
When to use: A new event or program page needs to go live or an existing event needs an update.

1. Go to the event or page inside Kajabi.
2. Confirm:
- title
- date/time/timezone
- short description
- visibility level
- any RSVP or follow-up details
3. Keep public discovery pages public.
4. Keep gated details or member-only follow-up behind the existing approval/login flow.
5. Confirm the event/program join CTA routes to `/join` or the approved homepage join path.
6. Save and verify the public page after the update.

## 4) Send a Communication
When to use: Approval, reminder, or monthly community update.

1. Go to `Email Campaigns`.
2. Start from the approved draft or template:
- Welcome / approval
- Event reminder
- Monthly digest
3. Select the correct audience.
4. Send an internal seed test first.
5. Check:
- subject line
- sender identity
- CTA links
- mobile rendering
- public/member link separation
6. Send or schedule the campaign.

Rule:
- Do not place private WhatsApp links, Zoom details, or member-only links on public pages or in broad public sends.

## 5) Join-Flow Reference
- Canonical join target: `/#block-1772192187104_0`
- Secondary-page compatibility bridge: `/join`
- Homepage form fields:
  - `name`
  - `email`
  - `interest`

If a public join CTA looks wrong, verify those three items before changing anything else.

## Guardrails (Always On)
1. Never approve by email reply alone. Always use the Kajabi tag workflow.
2. Never create a second public signup funnel alongside the homepage join form.
3. Never grant Insider access by mistake.
4. Keep tags consistent: `pending-review`, `approved-member`, `needs-follow-up`, `declined`.
5. If unsure, hold the contact and escalate internally before approving.
