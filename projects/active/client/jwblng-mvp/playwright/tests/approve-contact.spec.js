const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');
const {
  getActivePage,
  clickFirstVisible,
  findContactRowByEmail,
  openContactDetailFromRow,
  applyTagToOpenContact,
} = require('../utils/kajabi-ui');

test('approve contact by email filter (write-gated)', async ({ page, context }) => {
  const runMode = env('JWBLNG_RUN_MODE', 'apply').toLowerCase();
  const isPlanMode = runMode === 'plan';
  test.skip(!isPlanMode && !writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 or run JWBLNG_RUN_MODE=plan.');

  const adminBase = adminBaseUrl();
  const emailFilter = env('JWBLNG_CONTACT_EMAIL_FILTER', '').trim();
  const approvalTag = env('JWBLNG_APPROVAL_TAG', 'approved-member').trim();
  const artifactsDir = ensureArtifactsDir();

  if (!emailFilter) {
    throw new Error('JWBLNG_CONTACT_EMAIL_FILTER is required for safe contact approval runs.');
  }

  const activePage = await getActivePage(page, context, 'Active Kajabi admin page is closed before contact actions.');

  console.log('[contact-flow] Open dashboard');
  await activePage.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await activePage.waitForLoadState('domcontentloaded');

  const mainNav = activePage.getByRole('navigation', { name: /main navigation/i });

  console.log('[contact-flow] Navigate to Contacts via UI');
  const openedContactsGroup = await clickFirstVisible(activePage, [
    mainNav.getByRole('link', { name: /^contacts$/i }).first(),
    mainNav.getByRole('button', { name: /^contacts$/i }).first(),
    mainNav.locator('li:has-text("Contacts")').first(),
  ]);

  if (!openedContactsGroup) {
    throw new Error(`Could not open Contacts section from sidebar. URL: ${activePage.url()}`);
  }

  const allContactsLink = mainNav.getByRole('link', { name: /^all contacts$/i }).first();
  if (!(await allContactsLink.isVisible({ timeout: 10000 }).catch(() => false))) {
    throw new Error(`Contacts section opened, but 'All Contacts' link was not visible. URL: ${activePage.url()}`);
  }

  await Promise.all([
    activePage.waitForURL(/\/contacts(\?|$)/, { timeout: 15000 }),
    allContactsLink.click(),
  ]);
  await expect(activePage).toHaveURL(/\/contacts(\?|$)/);

  // Optional segment shortcut if present.
  await clickFirstVisible(activePage, [
    activePage.getByRole('link', { name: /pending-review/i }).first(),
    activePage.getByRole('button', { name: /pending-review/i }).first(),
  ], 2000).catch(() => false);

  console.log(`[contact-flow] Search contact: ${emailFilter}`);
  const searchCandidates = [
    activePage.getByRole('searchbox', { name: /search/i }).first(),
    activePage.getByRole('textbox', { name: /search/i }).first(),
    activePage.locator('input[placeholder*="search" i]').first(),
  ];

  let searchInput = null;
  for (const candidate of searchCandidates) {
    if (await candidate.isVisible().catch(() => false)) {
      searchInput = candidate;
      break;
    }
  }

  if (!searchInput) {
    throw new Error(`Could not find contacts search input. URL: ${activePage.url()}`);
  }

  await searchInput.fill(emailFilter);
  await searchInput.press('Enter').catch(() => {});
  await activePage.waitForTimeout(1200);

  const contactRow = await findContactRowByEmail(activePage, emailFilter, 10000);
  if (!contactRow) {
    throw new Error(`No visible contact row found for '${emailFilter}'.`);
  }

  await activePage.screenshot({
    path: path.join(artifactsDir, 'contact-flow-before-open.png'),
    fullPage: true,
  });

  if (isPlanMode) {
    console.log('[contact-flow] Plan mode: validated contact discovery only, no tag mutation applied.');
    await activePage.screenshot({
      path: path.join(artifactsDir, 'contact-flow-plan-ready.png'),
      fullPage: true,
    });
    return;
  }

  const openedDetail = await openContactDetailFromRow(activePage, contactRow);
  if (!openedDetail) {
    throw new Error('Did not open contact detail view; still on contacts list/tag management page.');
  }

  console.log(`[contact-flow] Apply tag: ${approvalTag}`);
  const tagResult = await applyTagToOpenContact(activePage, approvalTag);
  if (!tagResult.success) {
    throw new Error(`Could not apply tag '${approvalTag}' (${tagResult.reason}).`);
  }

  await activePage.screenshot({
    path: path.join(artifactsDir, 'contact-flow-after-tag.png'),
    fullPage: true,
  });

  console.log(`[contact-flow] Tag applied candidate:${approvalTag} saveClicked:${Boolean(tagResult.saved)}`);
});
