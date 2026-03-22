# Sensitive Data Handoff Checklist

Use this page to keep the SAM and SBA work moving without writing sensitive data into the repo.

## Never store in the repo

- Login.gov username or password
- MFA backup codes
- SSN or date of birth
- driver's license or identity-proofing answers
- EFT routing number
- EFT account number
- online-banking credentials
- any image of a voided check or bank letter

## Repo-safe inputs that can be prepared ahead of time

- legal business name
- entity type
- formation state and date
- physical and mailing address
- website URL
- business email
- final NAICS ordering
- business description and capability narrative
- POC names and roles
- remittance-address choice if it matches the mailing address

## Live-entry handoff items

Enter these only in the browser during the real submission:

1. Login.gov sign-in and MFA
2. identity validation prompts
3. EFT routing and account details
4. banking-contact confirmation
5. any ownership or socioeconomic representation that depends on private personal facts
6. any final certifications or affirmations that require direct user acknowledgment

## Working rule

If a field is not needed for repo planning, leave it out of version control and record only a status note such as `entered live` or `confirmed outside repo`.
