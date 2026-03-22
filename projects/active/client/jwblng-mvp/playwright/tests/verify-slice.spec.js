const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, adminBaseUrl, ensureArtifactsDir } = require('../utils/env');
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

async function openBuilderByPageTitle(activePage, pageTitle) {
  const rowNameRegex = new RegExp(`^${escapeRegex(pageTitle)}$`, 'i');
  const row = activePage.getByRole('listitem').filter({ has: activePage.getByRole('link', { name: rowNameRegex }) }).first();
  await expect(row).toBeVisible({ timeout: 10000 });
  const customizeControl = row.getByRole('link', { name: /customize/i }).first();
  const titleLink = row.getByRole('link', { name: rowNameRegex }).first();
  const openEditorControl = (await customizeControl.isVisible().catch(() => false)) ? customizeControl : titleLink;
  await openEditorControl.click();
  await activePage.waitForURL(/theme_files|admin\/themes|settings\/edit|\/edit/i, { timeout: 20000 });
  await activePage.waitForLoadState('domcontentloaded');
}

test('verify one agile slice in Kajabi', async ({ page, context }) => {
  const sliceId = env('JWBLNG_SLICE_ID', 'home-cta').trim().toLowerCase();
  const adminBase = adminBaseUrl();
  const artifactsDir = ensureArtifactsDir();
  const homepageName = env('JWBLNG_HOMEPAGE_NAME', 'Home').trim();

  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');
  const activePage = await getActivePage(page, context, 'Active Kajabi admin page is closed before slice verification.');
  await openWebsitePages(activePage);

  const eventSlicePageMap = {
    'event-speaker': 'Speaker Series',
    'event-book': 'Book Club',
    'event-halacha': 'Halacha Circle',
  };

  if (sliceId === 'home-hero' || sliceId === 'home-cta') {
    await openBuilderByPageTitle(activePage, homepageName);
    const preview = activePage.frameLocator('iframe').first();

    if (sliceId === 'home-hero') {
      const hero = await preview
        .getByRole('heading', { name: /orthodox jewish women|business|jwblng|lead/i })
        .first()
        .isVisible()
        .catch(() => false);
      expect(hero, 'Expected homepage hero heading in builder preview.').toBeTruthy();
    }

    if (sliceId === 'home-cta') {
      const hasJoin =
        (await preview.getByRole('button', { name: /join|member|become/i }).first().isVisible().catch(() => false)) ||
        (await preview.getByRole('link', { name: /join|member|become/i }).first().isVisible().catch(() => false));
      const hasEvents = await preview.getByRole('link', { name: /events/i }).first().isVisible().catch(() => false);
      expect(hasJoin, 'Expected homepage join CTA in builder preview.').toBeTruthy();
      expect(hasEvents, 'Expected homepage events link in builder preview.').toBeTruthy();
    }
  } else if (eventSlicePageMap[sliceId]) {
    const pageTitle = eventSlicePageMap[sliceId];
    await openBuilderByPageTitle(activePage, pageTitle);
    const selectedPage = await activePage.locator('select option:checked').first().innerText().catch(() => '');
    const selectedLooksRight = new RegExp(escapeRegex(pageTitle), 'i').test(selectedPage || '');
    expect(selectedLooksRight, `Expected builder page selector to target '${pageTitle}'.`).toBeTruthy();
  } else {
    throw new Error(`Unsupported JWBLNG_SLICE_ID '${sliceId}'.`);
  }

  await activePage.screenshot({
    path: path.join(artifactsDir, `slice-verify-${sliceId}.png`),
    fullPage: true,
  });
});

