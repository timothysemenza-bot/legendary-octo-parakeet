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

  const hasApplyButton = await page.getByRole('link', { name: /join|apply|membership|get started/i }).first().isVisible().catch(() => false);
  const hasMenu = await page.locator('nav').first().isVisible().catch(() => false);

  await page.screenshot({
    path: path.join(artifactsDir, 'public-home.png'),
    fullPage: true,
  });

  if (hasApplyButton) {
    const joinLink = page.getByRole('link', { name: /join|apply|membership|get started/i }).first();
    await joinLink.click();
    await page.waitForLoadState('domcontentloaded');

    await page.screenshot({
      path: path.join(artifactsDir, 'public-join-path.png'),
      fullPage: true,
    });
  }

  expect(hasMenu).toBeTruthy();
});
