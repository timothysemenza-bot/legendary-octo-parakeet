# MVP Backlog (Initial)

## Epic 1: Intake and Qualification

- User story: As a salesperson, I can upload/paste an RFP and get an initial recommendation quickly.
- Acceptance: Intake persists `rfp_submission`, parser supports PDF/DOCX/TXT, and qualification output includes rationale + missing data.

## Epic 2: Decision Governance

- User story: As a proposal lead, I can apply gate checks and weighted scoring before committing bid resources.
- Acceptance: Gate statuses and score sliders drive recommendation, and decision save writes audit entry.

## Epic 3: Red-Team Drafting

- User story: As a proposal manager, I can generate and iterate an initial draft with source citations.
- Acceptance: Draft versions are created, locked sections persist on regenerate, reviewer notes are captured.

## Epic 4: Commercialization Artifacts

- User story: As a JV leadership team, we can pitch with clear pricing and scope.
- Acceptance: Offer sheet, SOW template, roadmap, storyboard, and margin calculator are complete.

## Defect Policy

- Severity 1: Flow-breaking bug in intake/decision/draft path, fix same day.
- Severity 2: Incorrect scoring/recommendation behavior, fix next sprint day.
- Severity 3: Cosmetic/reporting issues, backlog for next sprint.
