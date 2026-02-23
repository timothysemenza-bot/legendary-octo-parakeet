# Boss Key Website Launch Guide

## 1) Domain Shortlist

Prioritize short, clear, and local-intent names. Check these first:

1. `bosskeyllc.com`
2. `bosskeynj.com`
3. `bosskeyproposals.com`
4. `bosskeyconsulting.com`
5. `bosskeysj.com`
6. `bosskeybidsupport.com`
7. `bosskeysolutions.co`
8. `bosskeygroup.co`

If your top `.com` is unavailable, use `.co` before longer/hyphenated `.com`.

## 2) Registrar Choice

Recommended order:

1. Cloudflare Registrar: low markup, clean DNS UI.
2. Porkbun: usually low first-year and renewal pricing.

During checkout, enable:

- WHOIS privacy (free if offered)
- Auto-renew
- 2FA on account

Do not buy add-ons you do not need (site builder, email bundles, SSL upsells).

## 3) Hosting Choice

Best simple option: Cloudflare Pages (free tier).

Alternative options:

1. Netlify
2. Vercel

This site is static, so all three work well.

## 4) Files to Deploy

Upload or publish:

- `boss-key-website/index.html`

## 5) DNS Records

Use one platform only for hosting. Apply records for your chosen platform.

### Cloudflare Pages

1. Connect repo or drag/drop `index.html`.
2. Add custom domain.
3. DNS records:
   - `CNAME` `www` -> `<your-pages-subdomain>.pages.dev`
   - `CNAME` `@` -> `<your-pages-subdomain>.pages.dev` (Cloudflare supports CNAME flattening)

### Netlify

1. Deploy static site.
2. Add custom domain.
3. DNS records:
   - `CNAME` `www` -> `<your-site>.netlify.app`
   - `A` `@` -> `75.2.60.5`
   - `A` `@` -> `99.83.190.102`

### Vercel

1. Import project or drag/drop deploy.
2. Add custom domain.
3. DNS records:
   - `A` `@` -> `76.76.21.21`
   - `CNAME` `www` -> `cname.vercel-dns.com`

## 6) Email Setup (Optional, Recommended)

If using Google Workspace or Microsoft 365 later, add MX records after web DNS is stable.

Suggested sender addresses:

1. `tim@yourdomain`
2. `hello@yourdomain`

## 7) Final Go-Live Checklist

1. Domain purchased and auto-renew enabled.
2. Site live on both `yourdomain` and `www.yourdomain`.
3. HTTPS active.
4. Contact email in `index.html` updated to your real domain email.
5. Test on phone and desktop.
