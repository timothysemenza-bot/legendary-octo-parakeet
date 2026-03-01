const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');
const { getActivePage, clickFirstVisible, escapeRegex } = require('../utils/kajabi-ui');

function slugify(input) {
  return String(input || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

async function openPagesScreen(activePage) {
  const mainNav = activePage.getByRole('navigation', { name: /main navigation/i });
  const openedWebsite = await clickFirstVisible(activePage, [
    mainNav.getByRole('link', { name: /^website$/i }).first(),
    mainNav.getByRole('button', { name: /^website$/i }).first(),
    mainNav.locator('li:has-text("Website")').first(),
  ]);
  if (!openedWebsite) {
    throw new Error(`Could not open Website section from sidebar. URL: ${activePage.url()}`);
  }

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
}

async function findPageRow(activePage, pageTitle) {
  const rowNameRegex = new RegExp(`^${escapeRegex(pageTitle)}$`, 'i');
  return activePage
    .getByRole('listitem')
    .filter({ has: activePage.getByRole('link', { name: rowNameRegex }) })
    .first();
}

test('apply/create scoped JWBLNG event pages in Kajabi (write-gated)', async ({ page, context }) => {
  test.setTimeout(180000);
  const runMode = env('JWBLNG_RUN_MODE', 'apply').toLowerCase();
  const isPlanMode = runMode === 'plan';
  test.skip(!isPlanMode && !writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 or run JWBLNG_RUN_MODE=plan.');

  const adminBase = adminBaseUrl();
  const artifactsDir = ensureArtifactsDir();
  const configuredTitles = env('JWBLNG_SCOPE_PAGE_TITLES', 'Speaker Series|Book Club|Halacha Circle')
    .split('|')
    .map((x) => x.trim())
    .filter(Boolean);
  const uniqueSuffix = new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0, 12);

  console.log('[scope-pages] Open dashboard');
  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');
  const activePage = await getActivePage(page, context, 'Active Kajabi admin page is closed before scoped page actions.');

  await openPagesScreen(activePage);
  const missing = [];

  for (const pageTitle of configuredTitles) {
    console.log(`[scope-pages] Ensure page: ${pageTitle}`);
    let row = await findPageRow(activePage, pageTitle);
    const exists = await row.isVisible({ timeout: 2000 }).catch(() => false);

    if (!exists) {
      if (isPlanMode) {
        missing.push(pageTitle);
        continue;
      }

      const createControl = activePage
        .locator('a:has-text("New Website Page"):visible, button:has-text("New Website Page"):visible, a:has-text("New Page"):visible, button:has-text("New Page"):visible')
        .first();
      if (!(await createControl.isVisible({ timeout: 8000 }).catch(() => false))) {
        throw new Error(`Could not find create page control while creating '${pageTitle}'. URL: ${activePage.url()}`);
      }
      await createControl.click();

      const addPageHeading = activePage.getByRole('heading', { name: /add new website page|create.*website page/i }).first();
      const nameInput = activePage.getByRole('textbox', { name: /^name$/i }).first();
      await Promise.race([
        addPageHeading.waitFor({ state: 'visible', timeout: 10000 }).catch(() => null),
        nameInput.waitFor({ state: 'visible', timeout: 10000 }).catch(() => null),
      ]);

      if (!(await nameInput.isVisible({ timeout: 3000 }).catch(() => false))) {
        throw new Error(`Create modal opened but Name input was not visible for '${pageTitle}'. URL: ${activePage.url()}`);
      }
      await nameInput.fill(pageTitle);

      const pathInput = activePage
        .locator('input[name*="path" i], input[name*="slug" i], input[placeholder*="path" i], input[placeholder*="slug" i]')
        .first();
      if (await pathInput.isVisible().catch(() => false)) {
        await pathInput.fill(`/events/${slugify(pageTitle)}`);
      }

      const customizeButton = activePage.getByRole('button', { name: /customize page/i }).first();
      await expect(customizeButton).toBeEnabled({ timeout: 10000 });
      await customizeButton.click();
      await activePage.waitForLoadState('domcontentloaded');
      await activePage.waitForTimeout(1000);

      const duplicateNameError = await activePage
        .getByText(/name has already been taken/i)
        .first()
        .isVisible()
        .catch(() => false);
      if (duplicateNameError) {
        const uniqueTitle = `${pageTitle} ${uniqueSuffix}`;
        await nameInput.fill(uniqueTitle);
        await customizeButton.click();
        await activePage.waitForLoadState('domcontentloaded');
        await activePage.waitForTimeout(1000);
      }

      await activePage.waitForURL(/theme_files|admin\/themes|settings\/edit|\/edit/i, { timeout: 20000 });
      await activePage.screenshot({
        path: path.join(artifactsDir, `scope-pages-${slugify(pageTitle)}-builder.png`),
        fullPage: true,
      });

      const backToPages = activePage.getByRole('link', { name: /back to pages/i }).first();
      if (!(await backToPages.isVisible({ timeout: 8000 }).catch(() => false))) {
        throw new Error(`Created '${pageTitle}' but could not find Back to Pages link in builder. URL: ${activePage.url()}`);
      }
      await backToPages.click();
      await expect(activePage.getByRole('heading', { name: /^pages$/i })).toBeVisible({ timeout: 15000 });
      row = await findPageRow(activePage, pageTitle);
    }

    const rowVisible = await row.isVisible({ timeout: 5000 }).catch(() => false);
    if (!rowVisible) {
      missing.push(pageTitle);
      continue;
    }
  }

  await activePage.screenshot({
    path: path.join(artifactsDir, 'scope-pages-summary.png'),
    fullPage: true,
  });

  if (missing.length) {
    throw new Error(`Missing scoped pages: ${missing.join(', ')}`);
  }
});
