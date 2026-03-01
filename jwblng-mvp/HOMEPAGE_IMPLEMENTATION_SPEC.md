# JWBLNG Homepage Implementation Spec
Date: 2026-02-28
Scope tie-in:
- `JWBLNG-Donated-Scope-One-Pager.md`
- `JWBLNG-Creative-Brief.md`

Use this as the exact homepage build target in Kajabi.

## Goal
Create a clear public homepage that drives:
1. Membership join
2. Event discovery/registration
3. Donation path awareness

## Section Blueprint
1. Header/Nav
- Brand: JWBLNG logo + `JWBLNG`
- Links:
  - Programs
  - Experience
  - Upcoming Events
  - Portal
- Primary CTA: `Join JWBLNG`

2. Hero
- Headline: `A professional home for Orthodox Jewish women in business.`
- Supporting copy: leadership, practical learning, trusted network.
- Primary button: `Join JWBLNG` -> canonical join URL
- Secondary button: `View Events` -> events section/page

3. Value Rail (right-side or stacked on mobile)
- Block: `Built for Your Growth`
- Block: `What Members Receive`
- Block: `This Month at JWBLNG`
- Include recurring-program proof points (free membership, recurring programming, etc.)

4. Programs Section
- Heading: `Programs`
- Cards:
  - Speaker Series
  - Book Club
  - Learning Hub

5. Experience / Journey Section
- Heading: `How It Works`
- Ordered flow:
  - Join
  - Get Started
  - Participate
  - Stay Connected

6. Upcoming Events Section
- Heading: `Upcoming Events`
- Three links:
  - Speaker Series
  - Monthly Book Club
  - Business Halacha Circle

7. Donation CTA
- Mode approved: external Zeffy link.
- Place at least one clear donation CTA on homepage footer or support section.

## CTA Targets
- Join CTA -> canonical join path (single URL only)
- Events CTA -> upcoming events section/page
- Portal CTA -> member portal mock
- Donation CTA -> approved external Zeffy URL

## Acceptance Criteria
- Homepage renders cleanly on mobile and desktop.
- One unambiguous primary CTA (`Join JWBLNG`) above the fold.
- Programs + journey + events sections are visible and readable.
- Event links are valid and route to intended event pages.
- Donation CTA is present and routes to Zeffy without redirect errors.

## QA Command
After implementing in Kajabi, run:
```powershell
npm.cmd run pw:jwblng:homeqa
```
