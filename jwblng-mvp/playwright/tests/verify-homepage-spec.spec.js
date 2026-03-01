const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, requireEnv, ensureArtifactsDir } = require('../utils/env');

test('verify homepage implementation against JWBLNG scope', async ({ page }) => {
  const artifactsDir = ensureArtifactsDir();
  const publicUrl = env('JWBLNG_PUBLIC_URL', '');
  const kajabiBase = requireEnv('KAJABI_BASE_URL');
  const startUrl = publicUrl || kajabiBase;

  await page.goto(startUrl, { waitUntil: 'domcontentloaded' });
  await expect(page).toHaveURL(/https?:\/\//);

  // Top-level structure checks tied to scope and implementation spec.
  await expect(page.getByRole('link', { name: /join jwblng|join|membership/i }).first()).toBeVisible();
  await expect(page.getByRole('heading', { name: /professional home|jwblng/i }).first()).toBeVisible();
  await expect(page.getByRole('heading', { name: /programs/i }).first()).toBeVisible();
  await expect(page.getByRole('heading', { name: /how it works/i }).first()).toBeVisible();
  await expect(page.getByRole('heading', { name: /upcoming events/i }).first()).toBeVisible();

  // Event surfaces expected in MVP scope.
  await expect(page.getByRole('link', { name: /speaker series/i }).first()).toBeVisible();
  await expect(page.getByRole('link', { name: /book club/i }).first()).toBeVisible();
  await expect(page.getByRole('link', { name: /halacha/i }).first()).toBeVisible();

  // Donation CTA should exist (external Zeffy mode approved).
  const donationCta = page.getByRole('link', { name: /donat|support/i }).first();
  const hasDonationCta = await donationCta.isVisible().catch(() => false);

  await page.screenshot({
    path: path.join(artifactsDir, 'public-home-scope-check.png'),
    fullPage: true,
  });

  expect(hasDonationCta).toBeTruthy();
});
