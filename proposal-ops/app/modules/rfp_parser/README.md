# RFP Parser Module

Parses solicitation text from manual input, direct upload, or intake-time batch uploads using TXT/MD/PDF/DOCX files.

## Responsibilities
- Extract deadlines, evaluation criteria, and submission instructions
- Detect atomic requirements using deterministic heuristics
- Persist `solicitations` and `requirements`
- Trigger initial compliance matrix row generation
- Support mixed-file batch extraction for intake kickoff flows
- Persist per-file source-document manifests for drafts and confirmed solicitations
- Persist durable binary provenance for uploaded source documents
- Maintain solicitation versions and support reparsing from prior document sets without deleting history
- Compare arbitrary solicitation version pairs, including changed requirement text between versions
- Support true document-set reparse by retaining prior source documents, removing selected documents, and appending new uploaded files
- Maintain stable source-document family IDs across versions so duplicate filenames can still be compared and replaced correctly
- Let operators download stored originals and replace one retained source document while creating a new solicitation version
