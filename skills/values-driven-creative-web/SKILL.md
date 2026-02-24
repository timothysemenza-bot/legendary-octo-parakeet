---
name: values-driven-creative-web
description: Build websites where brand values, audience psychology, UX structure, and Creative Cloud production are aligned. Use when creating or redesigning a site for an organization and you need concrete creative direction, visual language, and Adobe asset workflow.
---

# Values-Driven Creative Web

Use this skill when a client asks for a site that reflects values, audience, and leadership persona, not generic templates.

## Workflow

1. Gather inputs:
- Organization mission and values (3-6 words)
- Audience segments (primary + secondary)
- Trust signals (credentials, outcomes, proof)
- Conversion goals (top 1-2 actions)

2. Select a style archetype:
- Use [references/style-archetypes.md](references/style-archetypes.md)
- Pick exactly one primary archetype and one supporting archetype.

3. Generate creative brief:
- Run `scripts/generate-creative-brief.ps1`
- Output includes:
  - tone and messaging voice
  - typography pair guidance
  - visual motifs
  - UX priorities and page blocks
  - Creative Cloud asset production plan

4. Produce Adobe assets:
- Follow [references/adobe-production-workflow.md](references/adobe-production-workflow.md)
- Build and export:
  - hero stills/videos
  - iconography
  - lottie motion
  - image treatment presets

5. Integrate and validate:
- Inject exported assets into HTML/CSS/JS
- Verify mobile and desktop rendering
- Confirm aesthetics and UX match audience expectations and brand values.

## Script

Create a reusable brief:

```powershell
powershell -ExecutionPolicy Bypass -File .\skills\values-driven-creative-web\scripts\generate-creative-brief.ps1 `
  -OrgName "JWBLNG" `
  -Values "Torah values, leadership, integrity, growth, community" `
  -Audience "Orthodox Jewish businesswomen; nonprofit stakeholders" `
  -Goals "Join membership, register events, donate" `
  -OutputPath ".\creative-brief-jwblng.md"
```
