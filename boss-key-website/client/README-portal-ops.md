# Client Portal Ops Notes

Portal file:

- `boss-key-website/client/st-moritz-eric-portal.html`

## 1) Rotate access code before sharing

The portal uses a SHA-256 hash, not plaintext.

Update `CONFIG.accessCodeSha256` in the page after generating a new hash:

```powershell
$text='your-new-code-here'
$bytes=[System.Text.Encoding]::UTF8.GetBytes($text)
$sha=[System.Security.Cryptography.SHA256]::Create()
($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') }) -join ''
```

## 2) Enable true server-side confirmation capture

Set `CONFIG.webhookUrl` to a secure endpoint (Zapier, Make, Cloudflare Worker, etc.) that accepts JSON POST.

If blank, submit falls back to prefilled email draft to `CONFIG.fallbackEmail`.

## 3) Restrict access at edge (recommended)

For real access control beyond hidden URL + passcode:

1. In Cloudflare Zero Trust, create an Access Application for path `/client/*`.
2. Allow only specific emails/domains for St. Moritz stakeholders.
3. Require one-time pin or SSO.

This is the reliable way to enforce "client-only" access on a public domain.

