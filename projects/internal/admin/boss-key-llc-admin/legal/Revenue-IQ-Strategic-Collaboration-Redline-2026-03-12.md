# Revenue-IQ Strategic Collaboration Agreement Redline Notes

Reviewed on March 12, 2026 against:

- `C:\Users\timot\Downloads\DRAFT Master Strategic Collaboration and Intellectual Property Protection Agreement.pdf`
- the current `Proposal-Microsite` repo, including `proposal-ops`, `docs`, `projects/internal/admin/boss-key-llc-admin`, and `projects/pipeline/revenue-iq-mvp`

This is a business redline memo, not legal advice. If this deal matters, send the revised draft to counsel before signing.

## Bottom line

This draft is too aggressive on IP, too vague on commercial scope, and too loose on operational details.

The biggest problem is structural: it reads like a one-sided methodology lockup, but the repo shows a broader prime/sub pilot build with reusable Boss Key tooling, commercialization artifacts, and a likely continuing platform. That mismatch creates avoidable ownership and restraint-of-trade risk.

Best path:

1. Replace this with a short mutual NDA plus an MSA/SOW package.
2. If they insist on this agreement, narrow it hard and attach a pilot SOW.

## Highest-priority redlines

### 1. Purpose and structure

Problem:

- The draft describes a collaboration, but it does not include scope, fees, payment timing, acceptance, change control, termination convenience, expense handling, or an attached SOW.
- The repo already contains a pilot SOW template and commercialization materials for this exact concept.

Redline:

- Add an effective date and correct legal names.
- State that the parties are independent contractors and that nothing creates a partnership, joint venture, fiduciary relationship, agency, or exclusivity arrangement.
- Add a sentence that project-specific work is governed by one or more signed SOWs.
- Attach a pilot SOW covering deliverables, acceptance, timeline, commercials, security, and support boundaries.

### 2. Background IP and methodology license

Problem:

- Section 2 is directionally right, but not specific enough to protect your existing platform, workflow, prompts, templates, schemas, and generalized proposal operating methods.
- The repo already states that `proposal-ops` is an internal consulting toolkit and that the repo remains the master system for reusable methodology and workflow.

Redline:

- Define `Developer Background IP` broadly.
- State that Developer Background IP includes software, source code, system architecture, prompts, prompt libraries, schemas, connectors, automations, templates, workflows, evaluation harnesses, tests, documentation, analytics, and improvements, whether or not used in the project.
- Limit the Consultant methodology license to identified Consultant materials actually provided under the engagement.
- Add an explicit carve-out for independently developed materials, residual know-how, and generalized lessons learned that do not disclose Consultant Confidential Information.

Suggested replacement:

`Each party retains all right, title, and interest in its Background IP. Developer Background IP includes Developer's software, code, architecture, prompts, templates, workflows, schemas, connectors, evaluation tools, documentation, analytics, improvements, and generalized know-how existing before or developed outside the Services. Consultant grants Developer a limited, non-exclusive, non-transferable license to use Consultant Materials solely as necessary to perform an applicable SOW. No restriction applies to Developer's independently developed materials, residual know-how, or generalized methods that do not disclose Consultant Confidential Information.`

### 3. AI training, fine-tuned models, and deletion

Problem:

- Section 3 is too broad and technically sloppy.
- It gives Consultant ownership of any model "fine-tuned or customized" using its data, then requires deletion of the fine-tuned model and all associated databases within 10 days.
- That wording can swallow project-specific indexes, prompts, scoring logic, tooling layers, and potentially any persistent workspace touched by their materials.
- It also ignores backups, legal retention, audit logs, and security records.

Redline:

- Ban use of Consultant Confidential Information for training public or shared models without written consent.
- If a project-specific model, retrieval index, or dataset is built solely for Consultant from Consultant data, define ownership narrowly and only for that project artifact.
- Preserve Developer ownership of platform code, orchestration, prompts, evaluation logic, security tooling, logs, backups, and de-identified telemetry.
- Require deletion only of Consultant Confidential Information and project-specific artifacts in Developer-controlled systems, with carve-outs for ordinary-course backups, immutable logs, legal retention, and security evidence.
- Make deletion certification due on written request, on a commercially reasonable timetable.

Suggested replacement:

`Developer will not use Consultant Confidential Information to train or fine-tune any public or shared AI model. Any project-specific model weights, retrieval indexes, or datasets created exclusively from Consultant Confidential Information for a signed SOW will, upon full payment, be treated as Consultant project artifacts. Developer retains all rights in Developer Background IP, including platform software, prompts, workflows, schemas, evaluation assets, logs, backups, security records, and de-identified performance telemetry. Upon termination or written request, Developer will delete Consultant Confidential Information and project-specific artifacts in its active systems within a commercially reasonable period, excluding ordinary-course backups, immutable logs, and records required by law or security policy.`

### 4. Non-circumvention and referral fee

Problem:

- Section 4 is the most legally sensitive clause.
- The Washington framing is not comforting. The Washington Attorney General says customer non-solicits and clauses that directly or indirectly bar acceptance of business can count as non-competes, and Washington L&I states non-compete enforceability is limited and threshold-driven.
- A 24-month restriction, recurring 25% revenue skim for two years, and 100% revenue liquidated damages clause is overreaching.
- Your own Boss Key strategy materials use much narrower partner economics: 10% of first contract value for a referral partner and 15%-20% for a selling/channel partner.

Redline:

- Change this from a non-circumvention/non-compete style clause into a narrow non-solicit.
- Limit it to named clients first introduced by Consultant, with whom Developer had direct material contact through the project.
- Limit duration to 6-12 months.
- Exclude general advertising, responses to public RFPs, pre-existing relationships, and independent inbound contact not caused by misuse of Consultant Confidential Information.
- If they insist on a referral payment, make it a one-time fee tied to first-contract fees actually received, not a recurring override.
- Delete the 100% revenue liquidated damages clause.

Suggested replacement:

`During the Term and for 12 months thereafter, Developer will not knowingly solicit, for substantially similar services, any client first introduced by Consultant and with whom Developer had direct material contact through the Services, except for general advertising, public procurement responses, pre-existing relationships, or independent inbound opportunities not caused by misuse of Consultant Confidential Information. If Consultant expressly authorizes a direct engagement, Developer will pay Consultant a one-time referral fee equal to 10% of fees actually received during the first six months of that engagement.`

### 5. Non-solicitation of staff

Problem:

- The staff clause is too blunt.
- It applies to employees and contractors, lasts 12 months, and imposes a full annual salary recruitment fee.

Redline:

- Limit to active solicitation of employees or long-term dedicated contractors with material involvement in the project.
- Exclude general recruiting, public postings, and unsolicited approaches.
- Replace the full-salary penalty with a reasonable, pre-agreed fee or actual documented recruiting costs.

### 6. Ownership of outputs

Problem:

- Section 6 is too vague on what `Outputs` means.
- It should not allow Consultant to claim ownership over your platform, prompts, workflows, templates, or reusable draft-generation logic.
- It also needs third-party and open-source carve-outs.

Redline:

- Define Outputs as client-specific deliverables actually prepared for Consultant or Consultant's client under a signed SOW.
- State that Consultant owns those deliverables upon payment.
- State that Developer retains all Background IP and tools used to create them.
- Clarify that open-source components, third-party licensed materials, and pre-existing Developer materials remain under their existing licenses.

Suggested replacement:

`Consultant will own the final client-specific proposals, reports, and other deliverables expressly identified in an applicable SOW upon full payment for the applicable Services. Developer retains all rights in Developer Background IP and all tools, software, prompts, workflows, templates, schemas, connectors, libraries, evaluation assets, and improvements used to produce such deliverables. No ownership transfer applies to open-source software, third-party licensed materials, or pre-existing Developer materials except to the extent expressly stated in a signed SOW.`

### 7. Accuracy, indemnity, and liability

Problem:

- Section 7 makes you review-gated on hallucinations but still gives them a broad technical indemnity if the AI causes a breach or infringes a patent or copyright.
- Patent indemnity is especially dangerous in AI deals.
- The clause has no liability cap, no exclusion of consequential damages, and no reciprocal indemnity from Consultant for its data, templates, or claims.

Redline:

- Keep human review responsibility on Consultant for client-facing content approval.
- Limit your indemnity to third-party claims arising from Developer-created deliverables that infringe IP rights, excluding claims caused by Consultant materials, Consultant instructions, third-party models required by Consultant, modifications by others, or use outside the agreed scope.
- Exclude patent indemnity unless counsel specifically approves it.
- Add a mutual liability cap, ideally tied to fees paid under the SOW, with exclusion of indirect, incidental, special, consequential, and punitive damages.
- Add a Consultant indemnity for rights in the data, templates, and materials it supplies.

### 8. Governing law, venue, and dispute mechanics

Problem:

- Washington-only law and in-person executive meeting/mediation in Washington is burdensome for a New Jersey company.
- The draft also cites Washington law for the customer restriction even though you are not a Washington entity.

Redline:

- Push for New Jersey law and venue, or a neutral forum.
- At minimum, make executive escalation and mediation remote or in a mutually agreed location.
- Add prevailing language around emergency injunctive relief for confidentiality/IP issues only.

## Missing clauses you should add

- Confidentiality definition, exclusions, and survival
- Return/destruction clause with backup and legal-retention carve-outs
- Payment terms and late fees
- SOW precedence and change-order process
- Acceptance criteria
- Term and termination, including termination for convenience
- Post-termination transition obligations, if any
- Independent contractor status
- No partnership, joint venture, or fiduciary relationship
- No exclusivity
- Security addendum / data handling schedule
- Approved subprocessors or provider approval process
- Limitation of liability
- Mutual representations on authority to sign
- Assignment rule
- Notices

## Repo-specific conflicts and leverage points

These are the main repo facts that support a narrower draft:

- `proposal-ops/README.md` says the repo is an internal consulting toolkit for reusable client-deliverable workflows and remains the master system for reusable methodology and workflow.
- `docs/boss-key-early-lifecycle-strategy.md` says Boss Key keeps scope, pricing, and delivery ownership, and that the proposal stack is the existing proposal and AI-assisted workflow under Partner 1.
- `projects/pipeline/revenue-iq-mvp/docs/01-offer-sheet.md` and `projects/pipeline/revenue-iq-mvp/docs/04-pilot-sow-template.md` already frame this as a prime/sub pilot with human-supervised AI workflow automation, defined deliverables, exclusions, and shared responsibilities.
- `projects/pipeline/revenue-iq-mvp/docs/03-sprint-roadmap.md` identifies Chris Arlen as prime product owner and Timothy Semenza as technical product owner and delivery lead. That supports a scoped commercial arrangement, not a blanket IP capture.
- `projects/pipeline/revenue-iq-mvp/docs/05-margin-calculator.csv` shows a shared commercial model and hours split, which again points toward a negotiated SOW and fee schedule.
- `proposal-ops/app/modules/janitorial_os/service.py` already contains a data-minimization rule: do not store confidential procurement information.
- `boss-key-website/trust/security-policy.html` says data retention and deletion follow contractual terms and applicable law, personnel with client access sign confidentiality obligations, and the legal package should include NDA, MSA/SOW, and DPA where applicable.
- `projects/internal/admin/boss-key-llc-admin/legal/Mutual-NDA-Boss-Key-St-Moritz-REVIEW.md` already uses more balanced AI restrictions: no training public/shared models, return/destroy on request, backup carve-out, and no implied license.

## Internal cleanup note

If you want the final deal paper to say there is no joint venture, avoid internal shorthand that says `JV leadership team` in `projects/pipeline/revenue-iq-mvp/docs/06-mvp-backlog.md`. That phrase is probably harmless internally, but it is unnecessary noise if this relationship ever becomes contentious.

## Practical fallback positions

If Chris refuses a full rewrite, the minimum changes I would insist on are:

1. Add a broad Developer Background IP definition and carve-out.
2. Replace the model-ownership/deletion clause with a no-public-training plus project-artifact clause.
3. Replace Section 4 with a narrow 12-month non-solicit and one-time referral fee.
4. Limit output ownership to client-specific deliverables upon payment.
5. Add liability cap, consequential-damages waiver, and remove patent indemnity.
6. Attach a signed pilot SOW.
7. Add no-partnership/no-JV language.

## Sources

- Washington State Department of Labor & Industries, non-compete agreements: https://www.lni.wa.gov/workers-rights/workplace-policies/non-compete-agreements
- Washington Attorney General, labor and antitrust guidance: https://www.atg.wa.gov/labor-and-antitrust
