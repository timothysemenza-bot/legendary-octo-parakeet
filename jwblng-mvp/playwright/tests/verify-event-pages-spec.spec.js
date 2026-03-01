const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, requireEnv, ensureArtifactsDir } = require('../utils/env');

test('verify three event pages against JWBLNG scope', async ({ page }) => {
  const artifactsDir = ensureArtifactsDir();
  const publicUrl = env('JWBLNG_PUBLIC_URL', '') || requireEnv('KAJABI_BASE_URL');

  const pages = [
    { slug: '/events/speaker-series', title: /speaker/i },
    { slug: '/events/book-club', title: /book club/i },
    { slug: '/events/halacha-circle', title: /halacha/i },
  ];

  for (const eventPage of pages) {
    const url = `${publicUrl.replace(/\/$/, '')}${eventPage.slug}`;
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/https?:\/\//);
    await expect(page.getByRole('heading', { name: eventPage.title }).first()).toBeVisible();

    const joinCta = page.getByRole('link', { name: /join jwblng|join/i }).first();
    await expect(joinCta).toBeVisible();

    const registrationCta = page.getByRole('link', { name: /register|reserve/i }).first();
    await expect(registrationCta).toBeVisible();

    const donateCta = page.getByRole('link', { name: /donat|support/i }).first();
    await expect(donateCta).toBeVisible();

    const fileSlug = eventPage.slug.replace(/[\/]/g, '-').replace(/^-+/, '');
    await page.screenshot({
      path: path.join(artifactsDir, `public-${fileSlug}-scope-check.png`),
      fullPage: true,
    });
  }
});
