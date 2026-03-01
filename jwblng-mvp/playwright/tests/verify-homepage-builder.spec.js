const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, adminBaseUrl, ensureArtifactsDir } = require('../utils/env');
const { getActivePage, clickFirstVisible, escapeRegex } = require('../utils/kajabi-ui');

test('verify homepage content in Kajabi builder preview', async ({ page, context }) => {
  const artifactsDir = ensureArtifactsDir();
  const adminBase = adminBaseUrl();
  const homepageName = env('JWBLNG_HOMEPAGE_NAME', 'Home').trim();

  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');
  const activePage = await getActivePage(page, context, 'Active Kajabi admin page is closed before homepage verification.');

  const mainNav = activePage.getByRole('navigation', { name: /main navigation/i });
  await clickFirstVisible(activePage, [
    mainNav.getByRole('link', { name: /^website$/i }).first(),
    mainNav.getByRole('button', { name: /^website$/i }).first(),
    mainNav.locator('li:has-text("Website")').first(),
  ]);
  await clickFirstVisible(
    activePage,
    [
      mainNav.getByRole('link', { name: /website pages|pages/i }).first(),
      mainNav.getByRole('button', { name: /website pages|pages/i }).first(),
      mainNav.locator('li:has-text("Website Pages"), li:has-text("Pages")').first(),
    ],
    8000,
  );

  await expect(activePage.getByRole('heading', { name: /^pages$/i })).toBeVisible({ timeout: 15000 });
  const rowNameRegex = new RegExp(`^${escapeRegex(homepageName)}$`, 'i');
  const homepageRow = activePage.getByRole('listitem').filter({ has: activePage.getByRole('link', { name: rowNameRegex }) }).first();
  await expect(homepageRow).toBeVisible({ timeout: 10000 });

  const customizeControl = homepageRow.getByRole('link', { name: /customize/i }).first();
  const titleLink = homepageRow.getByRole('link', { name: rowNameRegex }).first();
  const openEditorControl = (await customizeControl.isVisible().catch(() => false)) ? customizeControl : titleLink;
  await openEditorControl.click();

  await activePage.waitForURL(/theme_files|admin\/themes|settings\/edit|\/edit/i, { timeout: 20000 });
  await activePage.waitForLoadState('domcontentloaded');

  const preview = activePage.frameLocator('iframe').first();
  const hasJoinSurface =
    (await preview.getByRole('button', { name: /join|member|become/i }).first().isVisible().catch(() => false)) ||
    (await preview.getByRole('link', { name: /join|member|become/i }).first().isVisible().catch(() => false));
  const hasEventsSurface = await preview.getByRole('link', { name: /events/i }).first().isVisible().catch(() => false);
  const hasHeroHeading = await preview
    .getByRole('heading', { name: /orthodox jewish women|business|jwblng|lead/i })
    .first()
    .isVisible()
    .catch(() => false);

  await activePage.screenshot({
    path: path.join(artifactsDir, 'homepage-builder-preview-check.png'),
    fullPage: true,
  });

  expect(hasJoinSurface, 'Expected join/membership CTA in homepage preview.').toBeTruthy();
  expect(hasEventsSurface, 'Expected events link in homepage preview.').toBeTruthy();
  expect(hasHeroHeading, 'Expected hero heading in homepage preview.').toBeTruthy();
});

