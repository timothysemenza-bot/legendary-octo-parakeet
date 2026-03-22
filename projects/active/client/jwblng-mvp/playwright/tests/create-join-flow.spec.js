const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');
const { getActivePage, clickFirstVisible } = require('../utils/kajabi-ui');

test('draft/create join compatibility page (write-gated)', async ({ page, context }) => {
  const runMode = env('JWBLNG_RUN_MODE', 'apply').toLowerCase();
  const isPlanMode = runMode === 'plan';
  test.skip(!isPlanMode && !writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 or run JWBLNG_RUN_MODE=plan.');

  const adminBase = adminBaseUrl();
  const pageTitle = env('JWBLNG_JOIN_PAGE_TITLE', 'Join JWBLNG');
  const pagePath = env('JWBLNG_JOIN_PAGE_PATH', '/join');
  const artifactsDir = ensureArtifactsDir();
  const uniqueSuffix = new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0, 12);

  console.log('[join-flow] Open dashboard');
  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');

  // Kajabi may redirect/open flows into a different tab; use the active page.
  const activePage = await getActivePage(page, context, 'Active Kajabi admin page is closed before write actions.');

  // Navigate via visible UI controls only. Avoid hardcoded deep routes.
  console.log('[join-flow] Navigate to Website/Pages via UI');
  const mainNav = activePage.getByRole('navigation', { name: /main navigation/i });

  const openedWebsite = await clickFirstVisible(activePage, [
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
  const createActionCandidates = [
    activePage.getByRole('link', { name: /^new website page$/i }).first(),
    activePage.getByRole('button', { name: /^new website page$/i }).first(),
    activePage.getByRole('link', { name: /new website page|new page|create page/i }).first(),
    activePage.getByRole('button', { name: /new website page|new page|create page/i }).first(),
    activePage
      .locator('a:has-text("New Website Page"):visible, button:has-text("New Website Page"):visible, button:has-text("New Page"):visible, button:has-text("Create Page"):visible')
      .first(),
  ];

  let createAction = null;
  for (const candidate of createActionCandidates) {
    if (await candidate.isVisible({ timeout: 3000 }).catch(() => false)) {
      createAction = candidate;
      break;
    }
  }

  if (!createAction) {
    const openedPages = await clickFirstVisible(activePage, [
      mainNav.getByRole('link', { name: /website pages|landing pages|pages/i }).first(),
      mainNav.getByRole('button', { name: /website pages|landing pages|pages/i }).first(),
      mainNav.locator('li:has-text("Website Pages"), li:has-text("Landing Pages"), li:has-text("Pages")').first(),
    ]);
    if (!openedPages) {
      throw new Error(`Website opened, but Pages entry was not clickable. URL: ${activePage.url()}`);
    }
    await activePage.waitForLoadState('domcontentloaded');
    await expect(activePage.getByRole('heading', { name: /^Pages$/i })).toBeVisible({ timeout: 10000 });

    for (const candidate of createActionCandidates) {
      if (await candidate.isVisible({ timeout: 3000 }).catch(() => false)) {
        createAction = candidate;
        break;
      }
    }
  }

  // Broad text selectors tolerate minor Kajabi UI label changes.
  console.log('[join-flow] Look for page create button');
  await expect(activePage.getByRole('heading', { name: /^Pages$/i })).toBeVisible({ timeout: 10000 });
  if (!createAction) {
    throw new Error(`Could not find visible create-page control on Pages screen. URL: ${activePage.url()}`);
  }

  if (isPlanMode) {
    console.log('[join-flow] Plan mode: validated Pages screen and create control only.');
    await activePage.screenshot({
      path: path.join(artifactsDir, 'join-page-draft-plan-ready.png'),
      fullPage: true,
    });
    return;
  }

  await createAction.click();
  console.log('[join-flow] Create flow opened');

  // Kajabi variants:
  // 1) "Add new website page" modal -> Name -> Customize Page
  // 2) Direct navigation into page builder
  const addPageHeading = activePage.getByRole('heading', { name: /add new website page|create.*website page/i }).first();
  const nameInputHint = activePage.getByRole('textbox', { name: /^name$/i }).first();

  // Deterministic branch selection: wait until either modal is visible or URL moves to builder/edit context.
  await Promise.race([
    addPageHeading.waitFor({ state: 'visible', timeout: 15000 }).catch(() => null),
    nameInputHint.waitFor({ state: 'visible', timeout: 15000 }).catch(() => null),
    activePage.waitForURL(/theme_files|admin\/themes|website_pages\/\d+|landing_pages\/\d+|\/edit/i, { timeout: 15000 }).catch(() => null),
  ]);

  let onAddPageModal =
    (await addPageHeading.isVisible().catch(() => false)) ||
    (await nameInputHint.isVisible().catch(() => false));

  // If initial click did not open modal/builder, retry create click once with explicit "New Website Page" control.
  if (!onAddPageModal && !/theme_files|admin\/themes|website_pages\/\d+|landing_pages\/\d+|\/edit/i.test(activePage.url())) {
    const explicitCreate = activePage.getByRole('link', { name: /^new website page$/i }).first();
    if (await explicitCreate.isVisible({ timeout: 2000 }).catch(() => false)) {
      await explicitCreate.click();
      await Promise.race([
        addPageHeading.waitFor({ state: 'visible', timeout: 8000 }).catch(() => null),
        nameInputHint.waitFor({ state: 'visible', timeout: 8000 }).catch(() => null),
        activePage.waitForURL(/theme_files|admin\/themes|website_pages\/\d+|landing_pages\/\d+|\/edit/i, { timeout: 8000 }).catch(() => null),
      ]);
      onAddPageModal =
        (await addPageHeading.isVisible().catch(() => false)) ||
        (await nameInputHint.isVisible().catch(() => false));
    }
  }

  if (onAddPageModal) {
    const nameInputCandidates = [
      activePage.getByRole('textbox', { name: /^name$/i }).first(),
      activePage.getByRole('textbox', { name: /name|title/i }).first(),
      activePage.locator('input[placeholder*="page name" i], input[name*="name" i], input[name*="title" i]').first(),
    ];

    let nameInput = null;
    for (const candidate of nameInputCandidates) {
      if (await candidate.isVisible({ timeout: 5000 }).catch(() => false)) {
        nameInput = candidate;
        break;
      }
    }

    if (!nameInput) {
      throw new Error(`Create modal opened, but Name input was not found. URL: ${activePage.url()}`);
    }
    await nameInput.fill(pageTitle);

    const pathInputCandidates = [
      activePage.getByRole('textbox', { name: /path|slug|url/i }).first(),
      activePage.locator('input[name*="path" i], input[name*="slug" i], input[placeholder*="path" i], input[placeholder*="slug" i]').first(),
    ];
    for (const candidate of pathInputCandidates) {
      if (await candidate.isVisible().catch(() => false)) {
        await candidate.fill(pagePath);
        break;
      }
    }

    const customizeButton = activePage.getByRole('button', { name: /customize page/i }).first();
    await expect(customizeButton).toBeEnabled({ timeout: 15000 });

    await activePage.screenshot({
      path: path.join(artifactsDir, 'join-page-draft-before-customize.png'),
      fullPage: true,
    });

    await customizeButton.click();
    await activePage.waitForLoadState('domcontentloaded');
    await activePage.waitForTimeout(1200);

    // Kajabi may reject duplicate page names and keep the modal open.
    const duplicateNameErrorVisible = await activePage
      .getByText(/name has already been taken/i)
      .first()
      .isVisible()
      .catch(() => false);

    if (duplicateNameErrorVisible) {
      const uniqueTitle = `${pageTitle} ${uniqueSuffix}`;
      console.log(`[join-flow] Duplicate page name detected; retrying with unique title: ${uniqueTitle}`);
      await nameInput.fill(uniqueTitle);
      await customizeButton.click();
      await activePage.waitForLoadState('domcontentloaded');
      await activePage.waitForTimeout(1200);
    }
  }

  // Ensure we actually moved past list/create-entry and into editable context.
  const reachedBuilderContext =
    (await activePage
      .waitForURL(/theme_files|admin\/themes|website_pages\/\d+|landing_pages\/\d+|\/edit/i, { timeout: 15000 })
      .then(() => true)
      .catch(() => false)) ||
    (await activePage.getByRole('button', { name: /save|update/i }).first().isVisible().catch(() => false));

  if (!reachedBuilderContext) {
    throw new Error(`Join page flow did not reach builder context after create/customize. URL: ${activePage.url()}`);
  }

  await activePage.screenshot({
    path: path.join(artifactsDir, 'join-page-draft-after-customize.png'),
    fullPage: true,
  });

  // Minimal deterministic edit in builder context.
  let editedField = false;
  const editableCandidates = [
    activePage.getByRole('textbox', { name: /title|page title|name/i }).first(),
    activePage.locator('input[name*="title" i], input[placeholder*="title" i]').first(),
  ];
  for (const candidate of editableCandidates) {
    if (await candidate.isVisible().catch(() => false)) {
      await candidate.fill(pageTitle);
      editedField = true;
      break;
    }
  }

  console.log(`[join-flow] Builder edit applied: ${editedField}`);

  await activePage.screenshot({
    path: path.join(artifactsDir, 'join-page-draft-before-save.png'),
    fullPage: true,
  });

  const saveCandidates = [
    activePage.getByRole('button', { name: /^save$/i }).first(),
    activePage.getByRole('button', { name: /update/i }).first(),
    activePage.locator('button:has-text("Save"), button:has-text("Update")').first(),
  ];

  let saveButton = null;
  for (const candidate of saveCandidates) {
    if (await candidate.isVisible({ timeout: 3000 }).catch(() => false)) {
      saveButton = candidate;
      break;
    }
  }

  if (!saveButton) {
    throw new Error(`Reached builder context but no visible Save/Update control was found. URL: ${activePage.url()}`);
  }

  if (await saveButton.isEnabled().catch(() => false)) {
    await saveButton.click();
  }

  // Non-blocking success checks across Kajabi variants.
  await Promise.race([
    activePage.waitForURL(/theme_files|admin\/themes|website_pages|landing_pages/i, { timeout: 8000 }).catch(() => null),
    activePage.getByText(/saved|updated|changes saved/i).first().waitFor({ state: 'visible', timeout: 8000 }).catch(() => null),
    activePage.waitForTimeout(1200),
  ]);

  await activePage.screenshot({
    path: path.join(artifactsDir, 'join-page-draft-after-save.png'),
    fullPage: true,
  });
});
