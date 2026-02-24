# Cloudflare Pages Deploy (One Command)

Use this to publish `boss-key-website` without manual dashboard upload.

## One-time setup

1. Create Cloudflare API token with:
- `Account - Cloudflare Pages:Edit`
- `Zone - DNS:Edit` (optional, only needed if domain bindings/DNS change)

2. Set environment variables in PowerShell:

```powershell
$env:CLOUDFLARE_API_TOKEN = "YOUR_TOKEN"
$env:CLOUDFLARE_ACCOUNT_ID = "f411849ae73dcab46e0b99e6f2c90bc8"
```

## Deploy

```powershell
powershell -ExecutionPolicy Bypass -File .\marketing-agents\scripts\deploy-bosskey-pages.ps1
```

Default target:
- Project: `boss-key-website`
- Folder: `boss-key-website`
- Branch tag: `main`

## Notes

- This does not change domain DNS unless you explicitly do that in Cloudflare.
- Keep token private.
