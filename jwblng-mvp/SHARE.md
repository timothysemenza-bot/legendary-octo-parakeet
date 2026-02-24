# JWBLNG Mockup Share Commands

## Fastest option (recommended)

Run one command:

```powershell
powershell -ExecutionPolicy Bypass -File .\run-share.ps1
```

This starts:
- local site server on `http://localhost:5500`
- a temporary Cloudflare tunnel window that prints the public URL

## Manual option

## 1) Serve locally from this folder

```powershell
cd C:\Users\timot\Documents\Proposal-Microsite\jwblng-mvp
python -m http.server 5500
```

Site URL locally:
- http://localhost:5500/index.html
- http://localhost:5500/dashboard.html
- http://localhost:5500/proposal.html

## 2) Expose via temporary Cloudflare tunnel (new terminal)

```powershell
cloudflared tunnel --url http://localhost:5500
```

Share the generated `https://*.trycloudflare.com` URL with Jessica and Marcy.

## 3) Stop when done

- In each terminal, press `Ctrl + C`.
