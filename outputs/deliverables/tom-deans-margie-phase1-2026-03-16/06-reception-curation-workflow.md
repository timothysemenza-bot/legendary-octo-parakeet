# March 31 Reception Curation Workflow

## Purpose
Use the Margie tribute outreach as a live operational pilot that produces two outputs at once:

1. A reception-ready packet of approved memories and well-wishes for March 31.
2. A reusable alumni-response record for later phase 2 work.

## Inputs
- `05-writing-center-alumni-tracker.csv`
- Tom's initial outreach sent March 24
- One reminder sent March 26 or March 27 morning
- Alumni replies received by Thursday, March 27 at 5:00 PM ET
- Optional approved invitees from the supplemental intake page at `boss-key-website/writing-center-alumni-tribute.html`

## Intake Rules
Treat the project as two distinct intake paths.

### 1. Direct email replies from Tom's outreach
For each reply, update one tracker row only.

- Set `outreach_status` to `replied`
- Fill `date_replied`
- Copy a short usable excerpt into `memory_excerpt`
- Fill `name_role_for_display` using the alum's preference
- Update `current_email`, `alternate_contact`, `current_role_org`, and `linkedin_url` if the reply provides better data

### 2. Public interest intake plus invite-only tribute submission
- The public intake page should collect identity, contact information, graduation year, and verification context first.
- Review those interest records internally before anyone receives the actual tribute prompt.
- Only approved contacts should receive the private tribute link.
- If an approved person is not already in the tracker, add one tracker row before the tribute is processed.
- Once the actual tribute note, selfie, or video arrives through the private link, update the matching tracker row using the same reply rules above.

## Permission Rules
Use these exact values in `share_permission`:

- `yes`
  Alum clearly says Tom may share the note at the reception.
- `no`
  Alum clearly says the note is private or internal only.
- `unclear`
  Alum replies but does not clearly say whether the note may be shared.

Default rule:

- Any `unclear` reply stays internal only.
- Any `no` reply stays internal only.
- Only `yes` replies can move to the shareable reception packet.

## Packet Assembly
Build two outputs for Tom.

### 1. Reception packet
- 10-15 strong, clearly approved excerpts
- each excerpt paired with the alum's approved name and current role
- ordered for easy reading aloud or selective quotation

### 2. Internal appendix
- all additional `yes` replies that do not make the short packet
- all `no` and `unclear` replies grouped separately for Tom's private reference

## Tracker Rules For Packet Inclusion
Use `include_in_reception_packet` this way:

- `yes`
  Approved and selected for the short packet
- `no`
  Approved but intentionally left out of the short packet, or explicitly private
- `hold`
  Waiting on permission clarification, cleanup, or Tom's final review

## Quality Check Before March 31
- No row with `share_permission=unclear` appears in the shareable packet
- No row with `share_permission=no` appears in the shareable packet
- Every quote in the shareable packet has a matching `name_role_for_display`
- Every reply used publicly has a clear audit trail in the tracker

## Phase 2 Carryforward
After the reception:

- keep all valid alumni rows for later follow-up
- use `phase2_follow_up=yes` for anyone who should remain in the alumni-network build
- treat the tribute campaign as the first verified response layer, not the end state of the alumni project
