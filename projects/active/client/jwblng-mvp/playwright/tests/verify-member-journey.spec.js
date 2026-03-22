const { test, expect } = require('@playwright/test');
const path = require('path');
const { canonicalJoinUrl, env, requireEnv, ensureArtifactsDir } = require('../utils/env');

function resolvedPathHash(href, baseUrl) {
  const url = new URL(href, baseUrl);
  return `${url.pathname}${url.hash}`;
}

async function firstVisible(locatorA, locatorB) {
  if (await locatorA.isVisible().catch(() => false)) return locatorA;
  if (await locatorB.isVisible().catch(() => false)) return locatorB;
  return null;
}

test('verify public member journey baseline', async ({ page }) => {
  const artifactsDir = ensureArtifactsDir();
  const publicUrl = env('JWBLNG_PUBLIC_URL', '');
  const kajabiBase = requireEnv('KAJABI_BASE_URL');

  const startUrl = publicUrl || kajabiBase;
  const joinUrl = canonicalJoinUrl();
  const canonicalAnchor = '/#block-1772192187104_0';
  await page.goto(startUrl, { waitUntil: 'domcontentloaded' });
  await expect(page).toHaveURL(/https?:\/\//);

  const nav = page.locator('nav').first();
  const headerShell = page.locator('header, [role="banner"], .header').first();
  const aboutLink = page.getByRole('link', { name: /about/i }).first();
  const eventsLink = page.getByRole('link', { name: /events/i }).first();
  const joinLink = page.getByRole('link', { name: /join|apply|membership|get started/i }).first();
  const joinButton = page.getByRole('button', { name: /join|apply|membership|get started/i }).first();
  const comingSoonHeading = page.getByRole('heading', { name: /coming soon/i });

  const hasMenu =
    (await nav.isVisible().catch(() => false)) ||
    (await headerShell.isVisible().catch(() => false)) ||
    ((await aboutLink.isVisible().catch(() => false)) && (await eventsLink.isVisible().catch(() => false)));
  const hasApplyButton = (await joinLink.isVisible().catch(() => false)) || (await joinButton.isVisible().catch(() => false));
  const hasComingSoon = await comingSoonHeading.isVisible().catch(() => false);

  await page.screenshot({
    path: path.join(artifactsDir, 'public-home.png'),
    fullPage: true,
  });

  if (hasMenu && hasApplyButton) {
    const joinSurface = await firstVisible(joinLink, joinButton);
    expect(joinSurface).toBeTruthy();
    const href = await joinSurface.getAttribute('href').catch(() => null);
    if (href) {
      const actualJoinPathHash = resolvedPathHash(href, startUrl);
      const acceptedJoinTargets = new Set([
        resolvedPathHash(joinUrl || canonicalAnchor, startUrl),
        resolvedPathHash(canonicalAnchor, startUrl),
      ]);
      expect(acceptedJoinTargets.has(actualJoinPathHash)).toBeTruthy();
    }
    await joinSurface.click();
    await page.waitForTimeout(1000);

    const joinForm = page.locator('form[action*="forms/2148877767/form_submissions"]').first();
    await expect(joinForm).toBeVisible();
    await expect(joinForm.locator('input[name="form_submission[name]"]').first()).toBeVisible();
    await expect(joinForm.locator('input[name="form_submission[email]"]').first()).toBeVisible();

    await page.screenshot({
      path: path.join(artifactsDir, 'public-join-path.png'),
      fullPage: true,
    });
  }

  // Accept either full navigation shell or intentional maintenance shell.
  expect(hasMenu || hasComingSoon).toBeTruthy();
});
