const { test, expect } = require('@playwright/test');
const path = require('path');
const { canonicalJoinHref, env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');
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
  await activePage.waitForTimeout(800);
}

async function rewriteHeroText(activePage, heading, subheading) {
  const joinUrl = canonicalJoinHref();
  await clickFirstVisible(
    activePage,
    [
      activePage.getByRole('tab', { name: /sections/i }).first(),
      activePage.locator('[role="tab"]:has-text("Sections")').first(),
    ],
    3000,
  ).catch(() => false);
  await clickFirstVisible(
    activePage,
    [
      activePage.getByRole('link', { name: /^hero$/i }).first(),
      activePage.locator('a:has-text("Hero")').first(),
    ],
    3000,
  ).catch(() => false);
  await clickFirstVisible(
    activePage,
    [
      activePage.locator('a[href*="/blocks/"]:has-text("Text")').first(),
      activePage.getByRole('link', { name: /^text$/i }).first(),
      activePage.locator('a:has-text("Text")').first(),
    ],
    3000,
  ).catch(() => false);

  const styledHtml = `
    <section style="padding:34px;border-radius:18px;border:1px solid currentColor;">
      <h1 style="margin:0 0 12px 0;line-height:1.2;">${heading}</h1>
      <p style="margin:0 0 18px 0;line-height:1.7;font-size:18px;">${subheading}</p>
      <p style="margin:0;">
        <a href="${joinUrl}" style="display:inline-block;padding:11px 18px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:700;">Join JWBLNG</a>
        <a href="/events" style="display:inline-block;margin-left:10px;padding:11px 18px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:700;">View Events</a>
      </p>
    </section>
  `;

  const edited = await activePage
    .evaluate(({ html }) => {
      const tiny = window.tinymce;
      if (!tiny || !Array.isArray(tiny.editors) || tiny.editors.length === 0) return 0;
      let changed = 0;
      for (const editor of tiny.editors) {
        if (!editor || editor.removed) continue;
        editor.setContent(html);
        editor.fire('change');
        changed += 1;
      }
      return changed;
    }, { html: styledHtml })
    .catch(() => 0);

  const saveSection = activePage.getByRole('button', { name: /save section/i }).first();
  if (await saveSection.isVisible().catch(() => false)) {
    if (await saveSection.isEnabled().catch(() => false)) {
      await saveSection.click();
      await activePage.waitForTimeout(700);
    }
  }
  return Number(edited) > 0;
}

test('cleanup homepage visuals (write-gated)', async ({ page, context }) => {
  test.setTimeout(180000);
  const runMode = env('JWBLNG_RUN_MODE', 'apply').toLowerCase();
  const isPlanMode = runMode === 'plan';
  test.skip(!isPlanMode && !writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 or run JWBLNG_RUN_MODE=plan.');

  const adminBase = adminBaseUrl();
  const artifactsDir = ensureArtifactsDir();
  const pageTitle = env('JWBLNG_HOMEPAGE_NAME', 'Home').trim();
  const heading = env('JWBLNG_HOMEPAGE_HEADLINE', 'A Professional Home for Jewish Business Leaders').trim();
  const subheading = env(
    'JWBLNG_HOMEPAGE_SUBHEAD',
    'Grow with trusted peers, practical Torah-grounded business wisdom, and clear next steps.',
  ).trim();

  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');
  const activePage = await getActivePage(page, context, 'Active Kajabi admin page is closed before homepage cleanup.');

  await openWebsitePages(activePage);
  await openBuilderForPage(activePage, pageTitle);

  const previewHref =
    (await activePage.getByRole('link', { name: /^preview$/i }).first().getAttribute('href').catch(() => '')) || '';
  console.log(`[home-cleanup] Preview URL: ${previewHref}`);

  if (!isPlanMode) {
    const rewritten = await rewriteHeroText(activePage, heading, subheading);
    console.log(`[home-cleanup] rewritten:${rewritten}`);
  }

  const saveButton = activePage
    .locator('button:has-text("Save"), button:has-text("Update"), [role="button"]:has-text("Save"), [role="button"]:has-text("Update")')
    .first();
  if (await saveButton.isVisible().catch(() => false)) {
    if (!isPlanMode && (await saveButton.isEnabled().catch(() => false)) ) {
      await saveButton.click();
      await activePage.waitForTimeout(800);
    }
  }

  const preview = activePage.frameLocator('iframe').first();
  const hasOldTemplateHeading = await preview
    .getByRole('heading', { name: /all the tools you need to build a successful online business/i })
    .first()
    .isVisible()
    .catch(() => false);

  await activePage.screenshot({
    path: path.join(artifactsDir, 'home-cleanup-after.png'),
    fullPage: true,
  });

  if (hasOldTemplateHeading) {
    throw new Error('Homepage still shows template heading after cleanup pass.');
  }
});
