require('dotenv').config();

const path = require('path');
const readline = require('readline');
const { chromium } = require('@playwright/test');
const { env, adminBaseUrl, ensureArtifactsDir, writesAllowed } = require('../utils/env');

const profileDir = path.join(__dirname, '..', '.profile');

async function clickFirstVisible(page, candidates, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    for (const candidate of candidates) {
      if (await candidate.isVisible().catch(() => false)) {
        await candidate.click();
        return true;
      }
    }
    await page.waitForTimeout(250);
  }
  return false;
}

async function runApprovalFlow(page) {
  const adminBase = adminBaseUrl();
  const emailFilter = env('JWBLNG_CONTACT_EMAIL_FILTER', '').trim();
  const approvalTag = env('JWBLNG_APPROVAL_TAG', 'approved-member').trim();
  const artifactsDir = ensureArtifactsDir();

  if (!emailFilter) {
    throw new Error('JWBLNG_CONTACT_EMAIL_FILTER is required for safe contact approval runs.');
  }

  console.log('[contact-flow] Open dashboard');
  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');

  const mainNav = page.getByRole('navigation', { name: /main navigation/i });

  console.log('[contact-flow] Navigate to Contacts via UI');
  const openedContactsGroup = await clickFirstVisible(page, [
    mainNav.getByRole('link', { name: /^contacts$/i }).first(),
    mainNav.getByRole('button', { name: /^contacts$/i }).first(),
    mainNav.locator('li:has-text("Contacts")').first(),
  ]);

  if (!openedContactsGroup) {
    throw new Error(`Could not open Contacts section from sidebar. URL: ${page.url()}`);
  }

  const allContactsLink = mainNav.getByRole('link', { name: /^all contacts$/i }).first();
  if (!(await allContactsLink.isVisible({ timeout: 10000 }).catch(() => false))) {
    throw new Error(`Contacts section opened, but 'All Contacts' link was not visible. URL: ${page.url()}`);
  }

  await Promise.all([
    page.waitForURL(/\/contacts(\?|$)/, { timeout: 15000 }),
    allContactsLink.click(),
  ]);

  // Optional segment shortcut if present.
  await clickFirstVisible(page, [
    page.getByRole('link', { name: /pending-review/i }).first(),
    page.getByRole('button', { name: /pending-review/i }).first(),
  ], 2000).catch(() => false);

  console.log(`[contact-flow] Search contact: ${emailFilter}`);
  const searchCandidates = [
    page.getByRole('searchbox', { name: /search/i }).first(),
    page.getByRole('textbox', { name: /search/i }).first(),
    page.locator('input[placeholder*="search" i]').first(),
  ];

  let searchInput = null;
  for (const candidate of searchCandidates) {
    if (await candidate.isVisible().catch(() => false)) {
      searchInput = candidate;
      break;
    }
  }

  if (!searchInput) {
    throw new Error(`Could not find contacts search input. URL: ${page.url()}`);
  }

  await searchInput.fill(emailFilter);
  await searchInput.press('Enter').catch(() => {});
  await page.waitForTimeout(1200);

  const escapedEmail = emailFilter.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const contactRow = page.getByRole('row', { name: new RegExp(escapedEmail, 'i') }).first();
  if (!(await contactRow.isVisible({ timeout: 10000 }).catch(() => false))) {
    throw new Error(`No visible contact row found for '${emailFilter}'.`);
  }

  await page.screenshot({
    path: path.join(artifactsDir, 'contact-flow-before-open.png'),
    fullPage: true,
  });

  let openedDetail = false;
  const openContactCandidates = [
    contactRow.getByRole('button', { name: /timmy|semenza/i }).first(),
    contactRow.getByRole('button', { name: new RegExp(escapedEmail, 'i') }).first(),
    contactRow.getByRole('button').nth(1),
  ];
  for (const candidate of openContactCandidates) {
    if (await candidate.isVisible().catch(() => false)) {
      await candidate.click();
      openedDetail = true;
      break;
    }
  }
  if (!openedDetail) {
    await contactRow.click();
  }

  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(1000);

  if (/\/contacts(\?|$)|\/contact_tags(\/|$)/.test(page.url())) {
    throw new Error('Did not open contact detail view; still on contacts list/tag management page.');
  }

  console.log(`[contact-flow] Apply tag: ${approvalTag}`);
  const detailRoot = page.locator('main').first();
  const tagControls = [
    detailRoot.getByRole('button', { name: /add tag|tags/i }).first(),
    detailRoot.getByRole('link', { name: /add tag|tags/i }).first(),
    detailRoot.locator('button:has-text("Add Tag"), button:has-text("Tags"), a:has-text("Add Tag")').first(),
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
    detailRoot.getByRole('combobox', { name: /tag/i }).first(),
    detailRoot.getByRole('textbox', { name: /tag/i }).first(),
    detailRoot.locator('input[placeholder*="tag" i], input[name*="tag" i]').first(),
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
  await page.waitForTimeout(500);

  const tagOption = page.getByRole('option', { name: new RegExp(approvalTag, 'i') }).first();
  if (await tagOption.isVisible().catch(() => false)) {
    await tagOption.click();
  } else {
    await tagInput.press('Enter');
  }

  const saved = await clickFirstVisible(page, [
    page.getByRole('button', { name: /save|update|apply/i }).first(),
  ], 2000);

  await page.screenshot({
    path: path.join(artifactsDir, 'contact-flow-after-tag.png'),
    fullPage: true,
  });

  console.log(`[contact-flow] Tag applied candidate:${approvalTag} saveClicked:${saved}`);
}

async function main() {
  if (!writesAllowed()) {
    console.error('ALLOW_KAJABI_WRITES is not set to 1. Refusing to run write flow.');
    process.exit(1);
  }

  const context = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    viewport: null,
  });

  const page = context.pages()[0] || (await context.newPage());

  console.log('Persistent Kajabi contact runner started.');
  console.log('Commands: r = run contact approval flow, q = quit');

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  let running = false;

  const runOnce = async () => {
    if (running) {
      console.log('Run already in progress...');
      return;
    }
    running = true;
    try {
      await runApprovalFlow(page);
      console.log('Run completed. Press r to run again, q to quit.');
    } catch (err) {
      console.error('Run failed:', err.message);
    } finally {
      running = false;
    }
  };

  await runOnce();

  rl.on('line', async (line) => {
    const cmd = String(line || '').trim().toLowerCase();
    if (cmd === 'q' || cmd === 'quit' || cmd === 'exit') {
      await context.close();
      rl.close();
      process.exit(0);
    }
    if (cmd === 'r' || cmd === 'run') {
      await runOnce();
      return;
    }
    console.log('Unknown command. Use r to rerun, q to quit.');
  });
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
