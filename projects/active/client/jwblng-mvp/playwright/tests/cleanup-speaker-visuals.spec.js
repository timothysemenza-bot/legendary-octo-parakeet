const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');
const { getActivePage, clickFirstVisible, escapeRegex } = require('../utils/kajabi-ui');

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
  await activePage.waitForTimeout(700);
}

async function deleteSectionByName(activePage, nameRegex) {
  const sectionLink = activePage.getByRole('link', { name: nameRegex }).first();
  if (!(await sectionLink.isVisible().catch(() => false))) return false;
  await sectionLink.click();
  await activePage.waitForTimeout(500);
  const deleteLink = activePage.getByRole('link', { name: /delete this section/i }).first();
  if (!(await deleteLink.isVisible({ timeout: 2000 }).catch(() => false))) return false;
  await deleteLink.click();
  const confirmDelete = activePage.getByRole('button', { name: /delete|remove/i }).first();
  if (await confirmDelete.isVisible({ timeout: 2000 }).catch(() => false)) {
    await confirmDelete.click();
  }
  await activePage.waitForTimeout(700);
  return true;
}

async function rewriteTextBlock(activePage, heading, subheading) {
  await clickFirstVisible(
    activePage,
    [
      activePage.getByRole('link', { name: /text & image/i }).first(),
      activePage.locator('a:has-text("Text & Image")').first(),
    ],
    4000,
  ).catch(() => false);

  const textBlockLink = activePage
    .locator('a[href*="/blocks/"]:has-text("Text"), a[href*="/blocks/"][href*="_0"]')
    .first();
  if (!(await textBlockLink.isVisible({ timeout: 3000 }).catch(() => false))) return false;
  await textBlockLink.click();
  await activePage.waitForTimeout(800);

  const changedViaTiny = await activePage
    .evaluate(({ h, s }) => {
      const tiny = window.tinymce;
      if (!tiny || !Array.isArray(tiny.editors) || tiny.editors.length === 0) return 0;
      let changed = 0;
      for (const editor of tiny.editors) {
        if (!editor || editor.removed) continue;
        editor.setContent(`<h2>${h}</h2><p>${s}</p>`);
        editor.fire('change');
        changed += 1;
      }
      return changed;
    }, { h: heading, s: subheading })
    .catch(() => 0);

  const saveSection = activePage.getByRole('button', { name: /save section/i }).first();
  if (await saveSection.isVisible().catch(() => false)) {
    if (await saveSection.isEnabled().catch(() => false)) {
      await saveSection.click();
      await activePage.waitForTimeout(700);
    }
  }

  return Number(changedViaTiny) > 0;
}

test('cleanup scoped event page visuals (write-gated)', async ({ page, context }) => {
  test.setTimeout(180000);
  const runMode = env('JWBLNG_RUN_MODE', 'apply').toLowerCase();
  const isPlanMode = runMode === 'plan';
  test.skip(!isPlanMode && !writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 or run JWBLNG_RUN_MODE=plan.');

  const adminBase = adminBaseUrl();
  const artifactsDir = ensureArtifactsDir();
  const pageTitle = env('JWBLNG_CLEANUP_PAGE_TITLE', 'Speaker Series').trim();
  const heading = env('JWBLNG_CLEANUP_HEADING', pageTitle).trim();
  const subheading = env(
    'JWBLNG_CLEANUP_SUBHEADING',
    'Conversations with founders, executives, and experts who lead with purpose.',
  ).trim();

  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');
  const activePage = await getActivePage(page, context, 'Active Kajabi admin page is closed before speaker cleanup.');

  await openWebsitePages(activePage);
  await openBuilderForPage(activePage, pageTitle);

  const previewHref =
    (await activePage.getByRole('link', { name: /^preview$/i }).first().getAttribute('href').catch(() => '')) || '';
  console.log(`[speaker-cleanup] Preview URL: ${previewHref}`);

  if (isPlanMode) {
    await activePage.screenshot({
      path: path.join(artifactsDir, 'speaker-cleanup-plan.png'),
      fullPage: true,
    });
    return;
  }

  await clickFirstVisible(
    activePage,
    [
      activePage.getByRole('tab', { name: /sections/i }).first(),
      activePage.locator('[role="tab"]:has-text("Sections")').first(),
    ],
    3000,
  ).catch(() => false);

  const removedImage = await deleteSectionByName(activePage, /^image$/i);
  const rewritten = await rewriteTextBlock(activePage, heading, subheading);

  const saveButton = activePage
    .locator('button:has-text("Save"), button:has-text("Update"), [role="button"]:has-text("Save"), [role="button"]:has-text("Update")')
    .first();
  if (await saveButton.isVisible().catch(() => false)) {
    if (await saveButton.isEnabled().catch(() => false)) {
      await saveButton.click();
      await activePage.waitForTimeout(800);
    }
  }

  const preview = activePage.frameLocator('iframe').first();
  const hasOldHeading = await preview
    .getByRole('heading', { name: /all the tools you need to build a successful online business/i })
    .first()
    .isVisible()
    .catch(() => false);

  await activePage.screenshot({
    path: path.join(artifactsDir, 'speaker-cleanup-after.png'),
    fullPage: true,
  });

  if (hasOldHeading) {
    throw new Error(`${pageTitle} page still shows template heading after cleanup pass.`);
  }

  console.log(`[speaker-cleanup] page:${pageTitle} removedImage:${removedImage} rewritten:${rewritten}`);
});
