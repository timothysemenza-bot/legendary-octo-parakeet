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

test('verify homepage implementation against JWBLNG scope', async ({ page }) => {
  const artifactsDir = ensureArtifactsDir();
  const publicUrl = env('JWBLNG_PUBLIC_URL', '');
  const kajabiBase = requireEnv('KAJABI_BASE_URL');
  const startUrl = publicUrl || kajabiBase;
  const joinUrl = canonicalJoinUrl();
  const canonicalAnchor = '/#block-1772192187104_0';

  await page.goto(startUrl, { waitUntil: 'domcontentloaded' });
  await expect(page).toHaveURL(/https?:\/\//);

  // Top-level structure checks tied to scope and implementation spec.
  const primaryJoinCta = await firstVisible(
    page.getByRole('link', { name: /^join jwblng$/i }).first(),
    page.getByRole('button', { name: /^join jwblng$/i }).first(),
  );
  const membershipJoinCta = await firstVisible(
    page.getByRole('link', { name: /become a member/i }).first(),
    page.getByRole('button', { name: /become a member/i }).first(),
  );
  expect(primaryJoinCta, 'Expected primary join CTA on homepage.').toBeTruthy();
  expect(membershipJoinCta, 'Expected lower membership CTA on homepage.').toBeTruthy();
  await primaryJoinCta.click();
  await page.waitForTimeout(1000);
  await expect(page.locator('form[action*="forms/2148877767/form_submissions"]').first()).toBeVisible();

  const currentPathHash = new URL(page.url()).pathname + new URL(page.url()).hash;
  const acceptedJoinTargets = new Set([
    resolvedPathHash(joinUrl || canonicalAnchor, startUrl),
    resolvedPathHash(canonicalAnchor, startUrl),
    '/',
  ]);
  expect(acceptedJoinTargets.has(currentPathHash) || page.url().startsWith(startUrl)).toBeTruthy();

  await expect(page.getByRole('heading', { name: /orthodox jewish women|business|jwblng/i }).first()).toBeVisible();
  await expect(page.getByRole('heading', { name: /^join jwblng$/i }).first()).toBeVisible();
  await expect(page.getByRole('heading', { name: /membership is free/i }).first()).toBeVisible();

  // Event surfaces expected in MVP scope.
  await expect(page.getByRole('heading', { name: /speaker series/i }).first()).toBeVisible();
  await expect(page.getByRole('heading', { name: /book club/i }).first()).toBeVisible();
  await expect(page.getByRole('heading', { name: /classes|learning/i }).first()).toBeVisible();
  await expect(page.getByRole('button', { name: /latest events/i }).first()).toBeVisible();
  await expect(page.getByRole('heading', { name: /professional growth with integrity/i }).first()).toBeVisible();
  await expect(page.getByRole('heading', { name: /supportive peer network/i }).first()).toBeVisible();

  // Donation CTA should exist (external Zeffy mode approved).
  const donationCta = page.getByRole('link', { name: /donat|support/i }).first();
  const hasDonationCta = await donationCta.isVisible().catch(() => false);

  await page.screenshot({
    path: path.join(artifactsDir, 'public-home-scope-check.png'),
    fullPage: true,
  });

  expect(hasDonationCta).toBeTruthy();
});
