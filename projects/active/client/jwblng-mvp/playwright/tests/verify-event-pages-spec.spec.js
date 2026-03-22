const { test, expect } = require('@playwright/test');
const path = require('path');
const { canonicalJoinUrl, env, requireEnv, ensureArtifactsDir } = require('../utils/env');

function resolvedPathHash(href, baseUrl) {
  const url = new URL(href, baseUrl);
  return `${url.pathname}${url.hash}`;
}

async function firstVisible(...locators) {
  for (const locator of locators) {
    if (await locator.isVisible().catch(() => false)) return locator;
  }
  return null;
}

test('verify three event pages against JWBLNG scope', async ({ page }) => {
  const artifactsDir = ensureArtifactsDir();
  const publicUrl = env('JWBLNG_PUBLIC_URL', '') || requireEnv('KAJABI_BASE_URL');
  const joinUrl = canonicalJoinUrl();
  const allowedJoinPaths = new Set([joinUrl, '/join']);

  const pages = [
    { slug: '/speaker-series', title: /speaker/i },
    { slug: '/book-club', title: /book club/i },
    { slug: '/halacha-circle', title: /halacha/i },
  ];

  for (const eventPage of pages) {
    const url = `${publicUrl.replace(/\/$/, '')}${eventPage.slug}`;
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await expect(page).toHaveURL(/https?:\/\//);
    await expect(page.getByRole('heading', { name: eventPage.title }).first()).toBeVisible();

    const registrationCta = await firstVisible(
      page.locator('a[href*="/join"], a[href*="#block-1772192187104_0"]').first(),
      page.getByRole('link', { name: /register|reserve|join/i }).first(),
      page.getByRole('button', { name: /register|reserve|join/i }).first(),
    );
    expect(registrationCta).toBeTruthy();

    const joinCta = await firstVisible(
      page.getByRole('link', { name: /join jwblng|join/i }).first(),
      page.getByRole('button', { name: /join jwblng|join/i }).first(),
      registrationCta,
    );
    expect(joinCta).toBeTruthy();
    const joinHref = await joinCta.getAttribute('href').catch(() => null);
    if (joinHref) {
      expect(allowedJoinPaths.has(resolvedPathHash(joinHref, url))).toBeTruthy();
    }

    const donateCta = page.getByRole('link', { name: /donat|support/i }).first();
    await expect(donateCta).toBeVisible();

    const fileSlug = eventPage.slug.replace(/[\/]/g, '-').replace(/^-+/, '');
    await page.screenshot({
      path: path.join(artifactsDir, `public-${fileSlug}-scope-check.png`),
      fullPage: true,
    });
  }
});
