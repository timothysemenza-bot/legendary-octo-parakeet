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

Publish the full static site directory, not just the homepage:

- `boss-key-website/index.html`
- `boss-key-website/janitorial-intelligence.html` (legacy redirect to homepage)
- `boss-key-website/dungeon-crawler.html`
- `boss-key-website/insights/`
- `boss-key-website/about.html`
- `boss-key-website/services.html`
- `boss-key-website/coaching.html`
- `boss-key-website/engagements.html`
- `boss-key-website/proof.html`
- `boss-key-website/faq.html`
- `boss-key-website/contact.html`
- `boss-key-website/assets/`
- `boss-key-website/client/`
- `boss-key-website/trust/`

The primary published experience is now the single anchored homepage at `index.html`. Legacy subpages may remain in the folder, but the homepage no longer depends on multi-page navigation. Longform microsites under `boss-key-website/insights/` are part of the live site surface and should deploy with the RSS feed.

Shared brand assets now live under `boss-key-website/assets/css/` and `boss-key-website/assets/js/`, so do not deploy HTML files without the updated assets folder.

## 5) DNS Records

Use one platform only for hosting. Apply records for your chosen platform.

### Cloudflare Pages

1. Connect repo or deploy the full `boss-key-website` folder as the site root.
2. Add custom domain.
3. DNS records:
   - `CNAME` `www` -> `<your-pages-subdomain>.pages.dev`
   - `CNAME` `@` -> `<your-pages-subdomain>.pages.dev` (Cloudflare supports CNAME flattening)

### Netlify

1. Deploy the full `boss-key-website` folder as the publish directory.
2. Add custom domain.
3. DNS records:
   - `CNAME` `www` -> `<your-site>.netlify.app`
   - `A` `@` -> `75.2.60.5`
   - `A` `@` -> `99.83.190.102`

### Vercel

1. Import project or deploy the full `boss-key-website` folder.
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
4. Homepage anchor links work for `Who`, `Problems`, `How`, `Sprint`, `Insights`, `Ethics`, `Play`, and `Contact`.
5. Contact email flow is updated to your real domain email.
6. Insights routes and `insights/feed.xml` load correctly.
7. The public dungeon crawler route loads from `dungeon-crawler.html`.
8. Test on phone and desktop.
