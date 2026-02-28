const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');

test('draft/create canonical join page (write-gated)', async ({ page, context }) => {
  test.skip(!writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 to enable write actions.');

  const adminBase = adminBaseUrl();
  const pageTitle = env('JWBLNG_JOIN_PAGE_TITLE', 'Join JWBLNG');
  const artifactsDir = ensureArtifactsDir();

  console.log('[join-flow] Open dashboard');
  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');

  // Kajabi may redirect/open flows into a different tab; use the active page.
  const activePage = context.pages().at(-1) || page;
  if (activePage.isClosed()) {
    throw new Error('Active Kajabi admin page is closed before write actions.');
  }
  async function clickFirstVisible(candidates, timeoutMs = 15000) {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      for (const candidate of candidates) {
        if (await candidate.isVisible().catch(() => false)) {
          await candidate.click();
          return true;
        }
      }
      await activePage.waitForTimeout(250);
    }
    return false;
  }

  // Navigate via visible UI controls only. Avoid hardcoded deep routes.
  console.log('[join-flow] Navigate to Website/Pages via UI');
  const mainNav = activePage.getByRole('navigation', { name: /main navigation/i });

  const openedWebsite = await clickFirstVisible([
    mainNav.getByRole('link', { name: /^website$/i }).first(),
    mainNav.getByRole('button', { name: /^website$/i }).first(),
    mainNav.locator('li:has-text("Website")').first(),
  ]);
  if (!openedWebsite) {
    throw new Error(`Could not open Website section from sidebar. URL: ${activePage.url()}`);
  }
  await activePage.waitForLoadState('domcontentloaded');

  // Fail early with useful context if we land on not found/unauthorized state.
  const bodyText = await activePage.locator('body').innerText();
  if (/doesn'?t exist|not found|unauthorized|forbidden/i.test(bodyText)) {
    throw new Error(`Kajabi pages screen unavailable. URL: ${activePage.url()}`);
  }

  // Some Kajabi variants surface create actions directly under Website.
  const createLink = activePage.getByRole('link', { name: /new website page/i }).first();
  let createButton = activePage
    .locator('a:has-text("New Website Page"):visible, button:has-text("New Page"):visible, button:has-text("Create Page"):visible')
    .first();
  const hasCreateAction =
    (await createLink.isVisible({ timeout: 3000 }).catch(() => false)) ||
    (await createButton.isVisible({ timeout: 3000 }).catch(() => false));

  if (!hasCreateAction) {
    const openedPages = await clickFirstVisible([
      mainNav.getByRole('link', { name: /website pages|landing pages|pages/i }).first(),
      mainNav.getByRole('button', { name: /website pages|landing pages|pages/i }).first(),
      mainNav.locator('li:has-text("Website Pages"), li:has-text("Landing Pages"), li:has-text("Pages")').first(),
    ]);
    if (!openedPages) {
      throw new Error(`Website opened, but Pages entry was not clickable. URL: ${activePage.url()}`);
    }
    await activePage.waitForLoadState('domcontentloaded');
    await expect(activePage.getByRole('heading', { name: /^Pages$/i })).toBeVisible({ timeout: 10000 });
    createButton = activePage
      .locator('a:has-text("New Website Page"):visible, button:has-text("New Page"):visible, button:has-text("Create Page"):visible')
      .first();
  }

  // Broad text selectors tolerate minor Kajabi UI label changes.
  console.log('[join-flow] Look for page create button');
  await expect(activePage.getByRole('heading', { name: /^Pages$/i })).toBeVisible({ timeout: 10000 });
  if (await createLink.isVisible().catch(() => false)) {
    await createLink.click();
  } else {
    await expect(createButton).toBeVisible({ timeout: 15000 });
    await createButton.click();
  }
  console.log('[join-flow] Create flow opened');

  // Kajabi Help flow: enter Name, then Customize Page.
  const nameInput = activePage.getByRole('textbox', { name: /^Name$/i });
  await expect(nameInput).toBeVisible({ timeout: 10000 });
  await nameInput.fill(pageTitle);

  const customizeButton = activePage.getByRole('button', { name: /customize page/i });
  await expect(customizeButton).toBeEnabled({ timeout: 10000 });

  await activePage.screenshot({
    path: path.join(artifactsDir, 'join-page-draft-before-customize.png'),
    fullPage: true,
  });

  await customizeButton.click();
  await activePage.waitForLoadState('domcontentloaded');
  await activePage.waitForTimeout(1500);

  // Do not assume editor internals/field names across Kajabi variants.
  // This skeleton step confirms page-creation flow reached builder context.
  await expect(activePage).toHaveURL(/theme_files|website_pages|landing_pages|admin\/themes/i);

  await activePage.screenshot({
    path: path.join(artifactsDir, 'join-page-draft-after-customize.png'),
    fullPage: true,
  });
});
