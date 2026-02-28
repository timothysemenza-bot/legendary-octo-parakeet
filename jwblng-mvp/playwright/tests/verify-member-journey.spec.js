const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, requireEnv, ensureArtifactsDir } = require('../utils/env');

test('verify public member journey baseline', async ({ page }) => {
  const artifactsDir = ensureArtifactsDir();
  const publicUrl = env('JWBLNG_PUBLIC_URL', '');
  const kajabiBase = requireEnv('KAJABI_BASE_URL');

  const startUrl = publicUrl || kajabiBase;
  await page.goto(startUrl, { waitUntil: 'domcontentloaded' });
  await expect(page).toHaveURL(/https?:\/\//);

  const nav = page.locator('nav').first();
  const joinLink = page.getByRole('link', { name: /join|apply|membership|get started/i }).first();
  const comingSoonHeading = page.getByRole('heading', { name: /coming soon/i });

  const hasMenu = await nav.isVisible().catch(() => false);
  const hasApplyButton = await joinLink.isVisible().catch(() => false);
  const hasComingSoon = await comingSoonHeading.isVisible().catch(() => false);

  await page.screenshot({
    path: path.join(artifactsDir, 'public-home.png'),
    fullPage: true,
  });

  if (hasMenu && hasApplyButton) {
    await joinLink.click();
    await page.waitForLoadState('domcontentloaded');

    await page.screenshot({
      path: path.join(artifactsDir, 'public-join-path.png'),
      fullPage: true,
    });
  }

  // Accept either full navigation shell or intentional maintenance shell.
  expect(hasMenu || hasComingSoon).toBeTruthy();
});
