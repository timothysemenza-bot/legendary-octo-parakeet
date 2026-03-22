# SAM Registration Checklist

Use this checklist before opening the live SAM.gov registration flow.

Official references:

- [SAM entity registration](https://sam.gov/entity-registration)
- [SAM entity registration checklist PDF](https://sam.gov/sites/default/files/2024-11/entity-checklist.pdf)
- [SBA basic requirements for federal contracting](https://www.sba.gov/federal-contracting/contracting-guide/basic-requirements)

## Recommended registration path

- Register for `All Awards`, not `Unique Entity ID only`.
- Make the entity publicly visible in SAM search results.
- Use `541611` as the primary NAICS unless you decide to lead with a stronger web or systems-design posture.
- Add secondary NAICS for management consulting and digital-services work.

## Documents already on file in the repo

- `projects/internal/admin/boss-key-llc-admin/BusinessRegistrationCertificate.pdf`
- `projects/internal/admin/boss-key-llc-admin/irs/ein/IRS-EIN-Confirmation-CP575G.pdf`
- `projects/internal/admin/boss-key-llc-admin/vendor-packet/W9-Boss-Key-LLC_signed.pdf`
- `projects/internal/admin/boss-key-llc-admin/certifications/nj-sbe/NJ-SBE-Certificate-2026-03-18.pdf`

## Information to confirm before starting

### Entity basics

- Legal business name exactly as registered
- Physical address used for entity validation
- Mailing address, if different
- Organization start date
- State of incorporation or formation
- Fiscal year end date
- Business website URL
- U.S. business phone number

### Tax and banking

- TIN or EIN
- Taxpayer name and address for IRS consent
- EFT routing number
- EFT account number
- Remittance address

### Ownership and business facts

- Entity structure
- Profit structure
- Organization factors such as LLC
- Whether there is an immediate owner or predecessor entity
- Socioeconomic categories that are true today and can be supported

### Points of contact

- Accounts Receivable POC
- Electronic Business POC
- Government Business POC
- Optional alternate POCs if you want redundancy

## Recommended NAICS stack for Boss Key

- Primary: `541611`
- Secondary: `541618`
- Secondary: `541512`
- Secondary: `541511`
- Secondary: `541519`

## Section-by-section prep

### Unique Entity ID

- Use the exact legal business name and physical address from the registration record.
- If SAM validation fails, stop and fix validation rather than improvising.

### Core Data

- Confirm company start date and fiscal year end before entering anything.
- Use a real website URL, even if it is a simple company site or landing page.
- If there is no CAGE code yet, SAM will assign one after submission for a U.S. entity.

### Assertions and Reps and Certs

- Read carefully and answer conservatively.
- Do not claim a socioeconomic or certification status unless it is true and supportable today.
- If a section is unclear, capture the question and resolve it before submitting.

### SBA supplemental page

- Complete the profile because buyers and prime contractors use SBA Small Business Search for market research.
- Use the narrative and keyword draft in `small-business-search-profile-draft.md`.

### Points of contact

- Use an email address you will monitor consistently.
- Keep government-business and electronic-business contacts current.

## Done criteria

- SAM registration submitted
- UEI assigned
- Registration status becomes `Active`
- CAGE code assigned and recorded
- SBA supplemental page completed
- Small Business Search profile reviewed for clarity and keywords

## After activation

- Save the UEI, CAGE, activation date, and renewal date in this folder.
- Add a short registration record note so the repo becomes the source of truth.
