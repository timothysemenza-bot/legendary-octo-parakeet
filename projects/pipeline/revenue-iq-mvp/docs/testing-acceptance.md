# Testing and Acceptance Scenarios

## Functional

1. Upload a complete RFP and return recommendation with rationale in under 10 minutes.
2. Upload partial/noisy text and populate `missing_data[]` without fabricated fields.
3. Set `No-Go` and confirm draft generation is blocked with audit entry.
4. Set `Go` or `Conditional` and generate `proposal_draft_v1` with visible citations.
5. Lock one section, regenerate, and verify locked content is preserved.
6. Add reviewer note and verify note appears in history and state export.
7. Open weekly report and validate metrics + audit rows.

## UAT Exit

- Non-technical salesperson can complete intake, review, and draft generation flow without prompt engineering.
- Two live simulation runs complete with no flow-breaking errors.
