const { test, expect } = require('@playwright/test');
const path = require('path');
const { canonicalJoinHref, env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');
const { getActivePage, clickFirstVisible, escapeRegex } = require('../utils/kajabi-ui');

async function fillFirstMatchingField(candidates, value) {
  if (!value) return false;
  for (const candidate of candidates) {
    if (await candidate.isVisible().catch(() => false)) {
      await candidate.fill(value);
      return true;
    }
  }
  return false;
}

test('apply homepage content in Kajabi editor (write-gated)', async ({ page, context }) => {
  const runMode = env('JWBLNG_RUN_MODE', 'apply').toLowerCase();
  const isPlanMode = runMode === 'plan';
  test.skip(!isPlanMode && !writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 or run JWBLNG_RUN_MODE=plan.');

  const adminBase = adminBaseUrl();
  const artifactsDir = ensureArtifactsDir();

  const homepageName = env('JWBLNG_HOMEPAGE_NAME', 'Home').trim();
  const heroHeadline = env(
    'JWBLNG_HOMEPAGE_HEADLINE',
    'Support, education, and community for Orthodox Jewish women in business.',
  ).trim();
  const heroSubhead = env(
    'JWBLNG_HOMEPAGE_SUBHEAD',
    'JWBLNG helps women bring Torah values to work with confidence through speaker series, book club, business halacha, and a trusted peer network.',
  ).trim();
  const primaryCtaText = env('JWBLNG_HOMEPAGE_PRIMARY_CTA_TEXT', 'Join JWBLNG').trim();
  const primaryCtaLink = env('JWBLNG_HOMEPAGE_PRIMARY_CTA_LINK', canonicalJoinHref()).trim();
  const secondaryCtaText = env('JWBLNG_HOMEPAGE_SECONDARY_CTA_TEXT', 'View Events').trim();
  const secondaryCtaLink = env('JWBLNG_HOMEPAGE_SECONDARY_CTA_LINK', '/events').trim();
  const donationLink = env('JWBLNG_HOMEPAGE_DONATION_LINK', '').trim();

  console.log('[homepage-flow] Open dashboard');
  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');
  const activePage = await getActivePage(page, context, 'Active Kajabi admin page is closed before homepage actions.');

  const mainNav = activePage.getByRole('navigation', { name: /main navigation/i });

  console.log('[homepage-flow] Navigate to Website/Pages via UI');
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
  const nameRegex = new RegExp(`^${escapeRegex(homepageName)}$`, 'i');
  const homepageRow = activePage.getByRole('listitem').filter({ has: activePage.getByRole('link', { name: nameRegex }) }).first();
  if (!(await homepageRow.isVisible({ timeout: 10000 }).catch(() => false))) {
    throw new Error(`Could not find homepage row '${homepageName}'. Set JWBLNG_HOMEPAGE_NAME if your page label differs.`);
  }

  await activePage.screenshot({
    path: path.join(artifactsDir, 'homepage-flow-pages-list.png'),
    fullPage: true,
  });

  if (isPlanMode) {
    const customizeVisible = await homepageRow.getByRole('link', { name: /customize/i }).first().isVisible().catch(() => false);
    console.log(`[homepage-flow] Plan mode: homepage row found; customize visible:${customizeVisible}`);
    await activePage.screenshot({
      path: path.join(artifactsDir, 'homepage-flow-plan-ready.png'),
      fullPage: true,
    });
    return;
  }

  console.log('[homepage-flow] Open customize editor for homepage');
  const customizeControl = homepageRow.getByRole('link', { name: /customize/i }).first();
  const titleLink = homepageRow.getByRole('link', { name: nameRegex }).first();
  const openEditorControl = (await customizeControl.isVisible().catch(() => false)) ? customizeControl : titleLink;
  await openEditorControl.click();

  const builderUrlMatched = await activePage
    .waitForURL(/theme_files|admin\/themes|settings\/edit|\/edit/i, { timeout: 20000 })
    .then(() => true)
    .catch(() => false);

  if (!builderUrlMatched) {
    throw new Error(`Did not reach homepage builder context. URL: ${activePage.url()}`);
  }

  await activePage.waitForLoadState('domcontentloaded');
  await activePage.waitForTimeout(1200);

  let editsApplied = 0;
  await clickFirstVisible(
    activePage,
    [
      activePage.getByRole('link', { name: /^hero$/i }).first(),
      activePage.locator('a:has-text("Hero")').first(),
    ],
    3000,
  ).catch(() => false);

  if (
    await fillFirstMatchingField(
      [
        activePage.getByRole('textbox', { name: /^heading$|headline|hero title|title/i }).first(),
        activePage.getByLabel(/^heading$|headline|hero title|title/i).first(),
        activePage.locator('input[name*="headline" i], input[name*="heading" i], input[name*="title" i], textarea[name*="heading" i]').first(),
      ],
      heroHeadline,
    )
  ) {
    editsApplied += 1;
  }
  if (
    await fillFirstMatchingField(
      [
        activePage.getByRole('textbox', { name: /^subheading$|subtitle|description|body|content|text/i }).first(),
        activePage.getByLabel(/^subheading$|subtitle|description|body|content|text/i).first(),
        activePage.locator('textarea[name*="description" i], textarea[name*="content" i], input[name*="subheading" i], textarea[name*="text" i]').first(),
      ],
      heroSubhead,
    )
  ) {
    editsApplied += 1;
  }

  await clickFirstVisible(
    activePage,
    [
      activePage.getByRole('link', { name: /call to action/i }).first(),
      activePage.locator('a:has-text("Call to Action")').first(),
    ],
    3000,
  ).catch(() => false);

  if (
    await fillFirstMatchingField(
      [
        activePage.getByRole('textbox', { name: /primary.*button.*text|button.*text|cta.*text|button label|label/i }).first(),
        activePage.getByLabel(/primary.*button.*text|button.*text|cta.*text|button label|label/i).first(),
        activePage.locator('input[name*="button_text" i], input[name*="cta_text" i], input[name*="buttonlabel" i], input[name*="label" i]').first(),
      ],
      primaryCtaText,
    )
  ) {
    editsApplied += 1;
  }
  if (
    await fillFirstMatchingField(
      [
        activePage.getByRole('textbox', { name: /primary.*button.*link|button.*link|cta.*link|button.*url/i }).first(),
        activePage.getByLabel(/primary.*button.*link|button.*link|cta.*link|button.*url/i).first(),
        activePage.locator('input[name*="button_link" i], input[name*="cta_link" i], input[name*="url" i]').first(),
      ],
      primaryCtaLink,
    )
  ) {
    editsApplied += 1;
  }
  if (
    await fillFirstMatchingField(
      [
        activePage.getByRole('textbox', { name: /secondary.*button.*text|secondary.*cta.*text/i }).first(),
        activePage.getByLabel(/secondary.*button.*text|secondary.*cta.*text/i).first(),
        activePage.locator('input[name*="secondary" i][name*="text" i]').first(),
      ],
      secondaryCtaText,
    )
  ) {
    editsApplied += 1;
  }
  if (
    await fillFirstMatchingField(
      [
        activePage.getByRole('textbox', { name: /secondary.*button.*link|secondary.*cta.*link/i }).first(),
        activePage.getByLabel(/secondary.*button.*link|secondary.*cta.*link/i).first(),
        activePage.locator('input[name*="secondary" i][name*="link" i], input[name*="secondary" i][name*="url" i]').first(),
      ],
      secondaryCtaLink,
    )
  ) {
    editsApplied += 1;
  }
  if (
    donationLink &&
    (await fillFirstMatchingField(
      [
        activePage.getByRole('textbox', { name: /donat.*link|support.*link|zeffy/i }).first(),
        activePage.getByLabel(/donat.*link|support.*link|zeffy/i).first(),
        activePage.locator('input[name*="donat" i], input[name*="support" i], input[name*="zeffy" i]').first(),
      ],
      donationLink,
    ))
  ) {
    editsApplied += 1;
  }

  console.log(`[homepage-flow] Builder field edits applied:${editsApplied}`);

  await activePage.screenshot({
    path: path.join(artifactsDir, 'homepage-flow-before-save.png'),
    fullPage: true,
  });

  const saveButton = activePage
    .locator('button:has-text("Save"), button:has-text("Update"), [role="button"]:has-text("Save"), [role="button"]:has-text("Update")')
    .first();
  if (!(await saveButton.isVisible({ timeout: 8000 }).catch(() => false))) {
    throw new Error(`Reached builder, but Save/Update control was not visible. URL: ${activePage.url()}`);
  }

  if (await saveButton.isEnabled().catch(() => false)) {
    await saveButton.click();
  }

  await Promise.race([
    activePage.getByText(/saved|updated|changes saved/i).first().waitFor({ state: 'visible', timeout: 8000 }).catch(() => null),
    activePage.waitForTimeout(1200),
  ]);

  await activePage.screenshot({
    path: path.join(artifactsDir, 'homepage-flow-after-save.png'),
    fullPage: true,
  });

  if (!editsApplied) {
    const previewFrame = activePage.frameLocator('iframe').first();
    const hasJoinCta = await previewFrame
      .getByRole('button', { name: /join|member|become/i })
      .first()
      .isVisible()
      .catch(() => false);
    const hasEventsLink = await previewFrame
      .getByRole('link', { name: /events/i })
      .first()
      .isVisible()
      .catch(() => false);

    if (!hasJoinCta || !hasEventsLink) {
      throw new Error(
        'Reached homepage builder, but no editable fields matched and preview does not show expected join/events controls. Update selectors for this Kajabi theme.',
      );
    }
    console.log('[homepage-flow] No settings fields matched; keeping existing homepage content that already satisfies join/events baseline.');
  }
});
