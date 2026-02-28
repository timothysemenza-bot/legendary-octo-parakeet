const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');

test('approve contact by email filter (write-gated)', async ({ page, context }) => {
  test.skip(!writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 to enable write actions.');

  const adminBase = adminBaseUrl();
  const emailFilter = env('JWBLNG_CONTACT_EMAIL_FILTER', '').trim();
  const approvalTag = env('JWBLNG_APPROVAL_TAG', 'approved-member').trim();
  const artifactsDir = ensureArtifactsDir();

  if (!emailFilter) {
    throw new Error('JWBLNG_CONTACT_EMAIL_FILTER is required for safe contact approval runs.');
  }

  const activePage = context.pages().at(-1) || page;

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

  console.log('[contact-flow] Open dashboard');
  await activePage.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await activePage.waitForLoadState('domcontentloaded');

  const mainNav = activePage.getByRole('navigation', { name: /main navigation/i });

  console.log('[contact-flow] Navigate to Contacts via UI');
  const openedContacts = await clickFirstVisible([
    mainNav.getByRole('link', { name: /^contacts$/i }).first(),
    mainNav.getByRole('button', { name: /^contacts$/i }).first(),
    mainNav.locator('li:has-text("Contacts")').first(),
  ]);

  if (!openedContacts) {
    throw new Error(`Could not open Contacts section from sidebar. URL: ${activePage.url()}`);
  }

  await activePage.waitForLoadState('domcontentloaded');
  await expect(activePage).toHaveURL(/contacts/);

  // Optional segment shortcut if present.
  await clickFirstVisible([
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

  const contactRow = activePage.getByRole('link', { name: new RegExp(emailFilter.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i') }).first();
  if (!(await contactRow.isVisible({ timeout: 10000 }).catch(() => false))) {
    throw new Error(`No visible contact row found for '${emailFilter}'.`);
  }

  await activePage.screenshot({
    path: path.join(artifactsDir, 'contact-flow-before-open.png'),
    fullPage: true,
  });

  await contactRow.click();
  await activePage.waitForLoadState('domcontentloaded');
  await activePage.waitForTimeout(1000);

  console.log(`[contact-flow] Apply tag: ${approvalTag}`);
  const tagControls = [
    activePage.getByRole('button', { name: /add tag|tags|manage tags/i }).first(),
    activePage.getByRole('link', { name: /add tag|tags|manage tags/i }).first(),
    activePage.locator('button:has-text("Add Tag"), button:has-text("Tags"), a:has-text("Add Tag")').first(),
  ];

  let openedTagControl = false;
  for (const control of tagControls) {
    if (await control.isVisible().catch(() => false)) {
      await control.click();
      openedTagControl = true;
      break;
    }
  }

  if (!openedTagControl) {
    throw new Error('Could not open tag editor controls on contact page.');
  }

  const tagInputCandidates = [
    activePage.getByRole('combobox', { name: /tag/i }).first(),
    activePage.getByRole('textbox', { name: /tag/i }).first(),
    activePage.locator('input[placeholder*="tag" i], input[name*="tag" i]').first(),
  ];

  let tagInput = null;
  for (const candidate of tagInputCandidates) {
    if (await candidate.isVisible({ timeout: 5000 }).catch(() => false)) {
      tagInput = candidate;
      break;
    }
  }

  if (!tagInput) {
    throw new Error('Could not find tag input after opening tag controls.');
  }

  await tagInput.fill(approvalTag);
  await activePage.waitForTimeout(500);

  const tagOption = activePage.getByRole('option', { name: new RegExp(approvalTag, 'i') }).first();
  if (await tagOption.isVisible().catch(() => false)) {
    await tagOption.click();
  } else {
    await tagInput.press('Enter');
  }

  // Save/update if explicit button exists.
  const saved = await clickFirstVisible([
    activePage.getByRole('button', { name: /save|update|apply/i }).first(),
  ], 2000);

  await activePage.screenshot({
    path: path.join(artifactsDir, 'contact-flow-after-tag.png'),
    fullPage: true,
  });

  console.log(`[contact-flow] Tag applied candidate:${approvalTag} saveClicked:${saved}`);
});
