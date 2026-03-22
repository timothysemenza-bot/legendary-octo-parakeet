---
name: nj-business-registration-agent
description: Plan and execute New Jersey state business registration for new or existing businesses. Use when forming an NJ LLC/corporation/nonprofit, registering a foreign entity in NJ, completing NJ tax registration (NJ-REG), preparing annual report compliance, or building a filing-ready checklist of required information and documents.
---

# NJ Business Registration Agent

Use this skill to produce a filing-ready, step-by-step registration plan for New Jersey.

This skill is process guidance only, not legal or tax advice. Verify filing requirements on official New Jersey and IRS sites before submission.

## Workflow

1. Collect intake data:
- Use [references/required-inputs.md](references/required-inputs.md).
- Confirm entity type, ownership, registered agent, NAICS, and start date.

2. Build the filing path:
- Use [references/filing-playbook.md](references/filing-playbook.md).
- Choose one path: domestic entity, foreign qualification, or sole proprietor.

3. Generate a personalized execution checklist:
- Run `scripts/generate-nj-registration-checklist.ps1`.
- Review each generated step with the user before filing.

4. Execute registrations:
- Complete entity formation/qualification filing.
- Complete NJ tax registration (`NJ-REG`) for tax and employer accounts.
- Complete any local/industry licensing that applies.

5. Set compliance cadence:
- Track annual report deadline and registered agent continuity.
- Track tax filing cadence and payroll obligations if employees exist.

## Script

```powershell
powershell -ExecutionPolicy Bypass -File .\.agents\skills\nj-business-registration-agent\scripts\generate-nj-registration-checklist.ps1 `
  -BusinessName "Boss Key LLC" `
  -EntityType "llc" `
  -HasEmployees `
  -OutputPath ".\nj-registration-checklist.md"
```
