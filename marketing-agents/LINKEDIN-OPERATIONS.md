# LinkedIn Operations (Human-in-the-Loop)

Use this process to keep outbound and relationship management active while preserving owner control.

## System Behavior (Current)

- LinkedIn profile/company research links and message drafts are generated into `marketing-agents/data/linkedin_outreach_queue.csv`.
- Messages are `review-first` only. Nothing is auto-sent.
- Queue rows with status `queued` should be reviewed, lightly edited, and then sent manually inside LinkedIn.
- Public profile/company details can be captured in the queue and pipeline notes after review.

## Weekly Rhythm

1. Add priorities:
- Update account priorities and relationship targets.
- Add any new interactions to `marketing-agents/data/linkedin_inbox_log.csv`.

2. Run Agent 5:
- Use prompt: `marketing-agents/prompts/05_linkedin_operator.md`.
- Provide current week themes and CSV contents.

3. Review approval sheet:
- Mark each draft `approve`, `revise`, or `hold`.
- Update `marketing-agents/data/linkedin_post_queue.csv`.
- Review `marketing-agents/data/linkedin_outreach_queue.csv` and set `owner_decision` + `status`:
  - `approve` + `ready-to-send`
  - `revise` + `needs-edit`
  - `hold` + `on-hold`

4. Publish/send:
- Approved content is published manually or through your approved automation stack.
- Log posted/sent timestamps.
- For direct outreach, send from LinkedIn manually and update `status=sent` with notes.

5. Relationship follow-through:
- Use Owner Brief to prioritize who gets in-person follow-up.

## Suggested Weekly Targets

- 2 to 3 posts per week.
- 5 to 10 thoughtful comments on target operators' content.
- 10 to 20 direct interactions (connection follow-ups, replies, check-ins).

## Message Quality Rules

- Lead with operator realities, not tech language.
- Use one concrete example or operational signal per post.
- Keep tone local, practical, and accountable.
- Always end with a useful CTA (question, invite, short call offer).

## Safety/Compliance Notes

- Agent prepares drafts and digests; owner approves before any publish/send action.
- Avoid sharing confidential client details.
- Do not misrepresent automation as direct personal authorship when disclosure is required by policy.
