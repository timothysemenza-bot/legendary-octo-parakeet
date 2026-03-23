# Los Angeles County Sheriff's Department concept sheet

Date: 2026-03-23T21:26:44.464Z

## Contents

- `source/workspace-state.json`: structured workspace state used to assemble the package
- `source/opportunity.json`: standalone opportunity input for the packaged pursuit
- `source/package-payload.json`: resolved promoted concept, snapshot summary, and supporting data
- `source/working-story-brief.md`: internal working-story memo used to shape the concept
- `export/index.html`: default shareable HTML entry point
- `export/los-angeles-county-sheriff-s-department-concept-sheet.html`: named HTML concept sheet handoff
- `export/los-angeles-county-sheriff-s-department-concept-sheet.pdf`: portable PDF fallback generated from the shareable HTML

## Handoff Notes

- Promoted variant: Region 4 operating control
- Source state: C:\Users\timot\Documents\Proposal-Microsite\projects\pipeline\boss-key\bosc-pursuit-os\inputs\demo-workspace-state.json
- The HTML handoff is the primary shareable artifact.
- The PDF is the portable fallback for email, print, or attachment workflows.

## Verification

- Package bundle created under `C:\Users\timot\Documents\Proposal-Microsite\outputs\deliverables\los-angeles-county-sheriff-s-department-concept-sheet-2026-03-23`
- HTML export written successfully
- Deliverable scaffold created with `scripts/new-deliverable-bundle.ps1`
- PDF export generated with Playwright using a locally installed browser

## Assumptions

- This package was assembled from structured pursuit state, not a live browser session dump.
- Internal strategy notes live in `source/`; only `export/` is intended for broad sharing.
