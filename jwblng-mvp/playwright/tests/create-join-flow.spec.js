const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, requireEnv, writesAllowed, ensureArtifactsDir } = require('../utils/env');

test('draft/create canonical join page (write-gated)', async ({ page }) => {
  test.skip(!writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 to enable write actions.');

  const baseUrl = requireEnv('KAJABI_BASE_URL');
  const pageTitle = env('JWBLNG_JOIN_PAGE_TITLE', 'Join JWBLNG');
  const pagePath = env('JWBLNG_JOIN_PAGE_PATH', '/join');
  const ctaText = env('JWBLNG_JOIN_PAGE_CTA', 'Apply Now');
  const artifactsDir = ensureArtifactsDir();

  await page.goto(`${baseUrl}/admin/website/pages`, { waitUntil: 'domcontentloaded' });

  // These selectors are intentionally broad to tolerate Kajabi UI changes.
  await page.getByRole('button', { name: /new page|create page|add page/i }).first().click();

  const titleInput = page.locator('input[name*="title" i], input[placeholder*="title" i]').first();
  await expect(titleInput).toBeVisible();
  await titleInput.fill(pageTitle);

  const pathInput = page.locator('input[name*="slug" i], input[name*="path" i], input[placeholder*="path" i]').first();
  if (await pathInput.count()) {
    await pathInput.fill(pagePath);
  }

  const bodyField = page.locator('[contenteditable="true"]').first();
  if (await bodyField.count()) {
    await bodyField.fill('Welcome to JWBLNG. Start here for community access and upcoming events.');
  }

  const ctaField = page.locator('input[name*="button" i], input[placeholder*="button" i]').first();
  if (await ctaField.count()) {
    await ctaField.fill(ctaText);
  }

  await page.screenshot({
    path: path.join(artifactsDir, 'join-page-draft-before-save.png'),
    fullPage: true,
  });

  await page.getByRole('button', { name: /save|publish|update/i }).first().click();
  await page.waitForTimeout(1500);

  await page.screenshot({
    path: path.join(artifactsDir, 'join-page-draft-after-save.png'),
    fullPage: true,
  });
});
