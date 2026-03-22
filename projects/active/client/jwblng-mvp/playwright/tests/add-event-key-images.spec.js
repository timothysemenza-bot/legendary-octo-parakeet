const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');
const { getActivePage, clickFirstVisible, escapeRegex } = require('../utils/kajabi-ui');

const EVENT_PAGES = ['Speaker Series', 'Book Club', 'Halacha Circle'];

async function openWebsitePages(activePage) {
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
}

async function openBuilderForPage(activePage, pageTitle) {
  const rowNameRegex = new RegExp(`^${escapeRegex(pageTitle)}$`, 'i');
  const row = activePage
    .getByRole('listitem')
    .filter({ has: activePage.getByRole('link', { name: rowNameRegex }) })
    .first();
  await expect(row).toBeVisible({ timeout: 10000 });
  const customizeControl = row.getByRole('link', { name: /customize/i }).first();
  const titleLink = row.getByRole('link', { name: rowNameRegex }).first();
  const openEditorControl = (await customizeControl.isVisible().catch(() => false)) ? customizeControl : titleLink;
  await openEditorControl.click();
  await activePage.waitForURL(/theme_files|admin\/themes|settings\/edit|\/edit/i, { timeout: 20000 });
  await activePage.waitForLoadState('domcontentloaded');
  await activePage.waitForTimeout(800);
}

async function ensureImageSection(activePage) {
  await clickFirstVisible(
    activePage,
    [
      activePage.getByRole('tab', { name: /sections/i }).first(),
      activePage.locator('[role="tab"]:has-text("Sections")').first(),
    ],
    3000,
  ).catch(() => false);

  const imageSectionLink = activePage.getByRole('link', { name: /^image$/i }).first();
  if (await imageSectionLink.isVisible({ timeout: 1500 }).catch(() => false)) {
    return { added: false };
  }

  const addSection = activePage.getByRole('link', { name: /add section/i }).first();
  if (!(await addSection.isVisible({ timeout: 3000 }).catch(() => false))) {
    return { added: false, reason: 'add_section_not_visible' };
  }
  await addSection.click();
  await activePage.waitForTimeout(700);

  const pickImage = await clickFirstVisible(
    activePage,
    [
      activePage.getByRole('link', { name: /^image$/i }).first(),
      activePage.getByRole('button', { name: /^image$/i }).first(),
      activePage.locator('a:has-text("Image"), button:has-text("Image")').first(),
    ],
    4000,
  );

  if (!pickImage) {
    return { added: false, reason: 'image_section_picker_not_found' };
  }

  await activePage.waitForTimeout(800);
  return { added: true };
}

test('add key image section to scoped event pages (write-gated)', async ({ page, context }) => {
  test.setTimeout(240000);
  const runMode = env('JWBLNG_RUN_MODE', 'apply').toLowerCase();
  const isPlanMode = runMode === 'plan';
  test.skip(!isPlanMode && !writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 or run JWBLNG_RUN_MODE=plan.');

  const adminBase = adminBaseUrl();
  const artifactsDir = ensureArtifactsDir();

  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');
  const activePage = await getActivePage(page, context, 'Active Kajabi admin page is closed before image-section actions.');

  await openWebsitePages(activePage);

  for (const pageTitle of EVENT_PAGES) {
    console.log(`[event-images] ensure image section on: ${pageTitle}`);
    await openBuilderForPage(activePage, pageTitle);

    let result = { added: false, reason: 'plan_mode' };
    if (!isPlanMode) {
      result = await ensureImageSection(activePage);
    }
    console.log(`[event-images] ${pageTitle} added:${result.added} reason:${result.reason || 'n/a'}`);

    const saveButton = activePage
      .locator('button:has-text("Save"), button:has-text("Update"), [role="button"]:has-text("Save"), [role="button"]:has-text("Update")')
      .first();
    if (!isPlanMode && (await saveButton.isVisible().catch(() => false)) && (await saveButton.isEnabled().catch(() => false))) {
      await saveButton.click();
      await activePage.waitForTimeout(900);
    }

    const preview = activePage.frameLocator('iframe').first();
    const contentImageCount = await preview.locator('main img').count().catch(() => 0);
    console.log(`[event-images] ${pageTitle} main-img-count:${contentImageCount}`);

    await activePage.screenshot({
      path: path.join(artifactsDir, `event-images-${pageTitle.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.png`),
      fullPage: true,
    });

    const backToPages = activePage.getByRole('link', { name: /back to pages/i }).first();
    if (await backToPages.isVisible({ timeout: 4000 }).catch(() => false)) {
      await backToPages.click();
      await expect(activePage.getByRole('heading', { name: /^pages$/i })).toBeVisible({ timeout: 15000 });
    } else {
      await activePage.goto(`${adminBase}/website_pages`, { waitUntil: 'domcontentloaded' });
      await expect(activePage.getByRole('heading', { name: /^pages$/i })).toBeVisible({ timeout: 15000 });
    }
  }
});

