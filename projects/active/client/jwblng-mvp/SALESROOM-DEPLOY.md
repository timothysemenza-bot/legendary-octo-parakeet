# JWBLNG Private Salesroom Deploy (bosskeyops.com)

This lets you publish a private proposal page for JWBLNG on your existing domain, with access restricted to approved people only.

## Page to publish

- `projects/active/client/jwblng-mvp/proposal.html`

## Recommended URL

- `https://bosskeyops.com/jwblng` (or `https://bosskeyops.com/salesroom/jwblng`)

## Deployment approach

Use Cloudflare Pages for hosting and Cloudflare Access (Zero Trust) for protection.

## 1) Deploy the page to Pages

Option A (quick and isolated):
- Create a small Pages project for this folder only.
- Source directory: `projects/active/client/jwblng-mvp`
- Entry page: `proposal.html`

Option B (if reusing existing Pages project):
- Add this page under a path in your main project (e.g., `/jwblng/index.html`).

## 2) Restrict access with Cloudflare Access

In Cloudflare Zero Trust:

1. Go to `Access` -> `Applications` -> `Add application`.
2. Type: `Self-hosted`.
3. Application domain:
- `bosskeyops.com`
4. Path:
- `/jwblng*` (or your chosen salesroom path)
5. Policy:
- `Allow` only specific emails:
  - `rabinowitzjessica@gmail.com`
  - add Marcy's preferred email
  - add your own email for testing
6. Identity provider:
- One-time PIN via email is sufficient for this use case.

## 3) Keep it temporary

After review:
- Disable Access policy OR
- Remove the route/page and republish.

## 4) Share message (copy/paste)

\"Hi Jessica and Marcy, here is your private JWBLNG proposal page.  
Please use this secure link and your email to access it: [link].\"

## Notes

- This is stronger than a PDF for live discussion and updates.
- It remains private; only approved emails can open it.
