require('dotenv').config();

const path = require('path');
const readline = require('readline');
const fs = require('fs');
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

async function fillFirstVisible(page, candidates, value) {
  if (!value) return false;
  for (const candidate of candidates) {
    if (await candidate.isVisible().catch(() => false)) {
      const tag = await candidate.evaluate((el) => el.tagName.toLowerCase()).catch(() => '');
      if (tag === 'input' || tag === 'textarea') {
        await candidate.fill(value);
        return true;
      }
      const contentEditable = await candidate
        .evaluate((el) => el.getAttribute('contenteditable') === 'true')
        .catch(() => false);
      if (contentEditable) {
        await candidate.fill(value);
        return true;
      }
    }
  }
  return false;
}

async function chooseTimezone(page, value) {
  if (!value) return false;

  const timezoneCombobox = page.getByRole('combobox', { name: /time.?zone|zone/i }).first();
  if (!(await timezoneCombobox.isVisible().catch(() => false))) return false;

  const preferred = new RegExp(value, 'i');
  const options = await timezoneCombobox.locator('option').all().catch(() => []);

  for (const option of options) {
    const label = (await option.innerText().catch(() => '')).trim();
    const val = await option.getAttribute('value').catch(() => null);
    if (label && val && preferred.test(label)) {
      await timezoneCombobox.selectOption(val);
      return true;
    }
  }

  await timezoneCombobox.selectOption({ label: value }).catch(() => {});
  return true;
}

function normalizeOccursAt(datePart, timePart) {
  if (!datePart) return '';
  let normalizedDate = datePart.trim();
  const mdy = normalizedDate.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (mdy) {
    const mm = mdy[1].padStart(2, '0');
    const dd = mdy[2].padStart(2, '0');
    const yyyy = mdy[3];
    normalizedDate = `${yyyy}-${mm}-${dd}`;
  }

  if (!timePart) return normalizedDate;
  const normalizedTime = timePart.trim().toUpperCase();
  return `${normalizedDate} ${normalizedTime}`;
}

async function runEventFlow(page) {
  const adminBase = adminBaseUrl();
  const eventTitle = env('JWBLNG_EVENT_TITLE', `JWBLNG Event Draft ${new Date().toISOString().slice(0, 10)}`);
  const eventDate = env('JWBLNG_EVENT_DATE', '');
  const eventTime = env('JWBLNG_EVENT_TIME', '');
  const eventTimezone = env('JWBLNG_EVENT_TIMEZONE', '');
  const eventDescription = env('JWBLNG_EVENT_DESCRIPTION', '');
  const artifactsDir = ensureArtifactsDir();

  console.log('[event-flow] Open dashboard');
  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });

  const mainNav = page.getByRole('navigation', { name: /main navigation/i });

  console.log('[event-flow] Navigate to Marketing/Events via UI');
  const openedMarketing = await clickFirstVisible(page, [
    mainNav.getByRole('link', { name: /^marketing$/i }).first(),
    mainNav.getByRole('button', { name: /^marketing$/i }).first(),
    mainNav.locator('li:has-text("Marketing")').first(),
  ]);

  if (!openedMarketing) throw new Error(`Could not open Marketing section from sidebar. URL: ${page.url()}`);

  const openedEvents = await clickFirstVisible(page, [
    mainNav.getByRole('link', { name: /^events$/i }).first(),
    mainNav.getByRole('link', { name: /events/i }).first(),
    mainNav.locator('li:has-text("Events")').first(),
  ]);

  if (!openedEvents) throw new Error(`Marketing opened, but Events navigation was not clickable. URL: ${page.url()}`);

  await page.waitForLoadState('domcontentloaded');
  await page.screenshot({ path: path.join(artifactsDir, 'event-flow-events-screen.png'), fullPage: true });

  console.log('[event-flow] Open create event flow');
  const createEventControl = page
    .locator('a:has-text("New Event"):visible, a:has-text("Create Event"):visible, button:has-text("New Event"):visible, button:has-text("Create Event"):visible, button:has-text("Add Event"):visible')
    .first();

  if (!(await createEventControl.isVisible({ timeout: 15000 }).catch(() => false))) {
    throw new Error(`Could not find visible event create control. URL: ${page.url()}`);
  }

  await createEventControl.click();
  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(1000);

  const visibleLabels = await page.locator('label:visible').allTextContents().catch(() => []);
  console.log(`[event-flow] Visible labels: ${visibleLabels.join(' | ')}`);

  const titleCandidates = [
    page.getByRole('textbox', { name: /title|event name|name/i }).first(),
    page.locator('input[name*="title" i], input[placeholder*="title" i], input[name*="name" i]').first(),
  ];

  let filledTitle = false;
  for (const field of titleCandidates) {
    if (await field.isVisible().catch(() => false)) {
      await field.fill(eventTitle);
      filledTitle = true;
      break;
    }
  }
  if (!filledTitle) throw new Error(`Could not find a visible Event Title/Name input. URL: ${page.url()}`);

  const filledDate = await fillFirstVisible(
    page,
    [
      page.getByRole('textbox', { name: /when does this event occur|occurs at|start/i }).first(),
      page.getByLabel(/when does this event occur|occurs at|start/i).first(),
      page.locator('input[type="date"]:visible, input[name*="date" i], input[placeholder*="date" i], input[placeholder*="mm" i]').first(),
    ],
    normalizeOccursAt(eventDate, eventTime),
  );

  const filledTime = Boolean(eventTime) && filledDate;
  const selectedTimezone = await chooseTimezone(page, eventTimezone);

  const filledDescription = await fillFirstVisible(
    page,
    [
      page.getByRole('textbox', { name: /description|details|about/i }).first(),
      page.getByLabel(/description|details|about/i).first(),
      page.locator('textarea[name*="description" i], textarea[placeholder*="description" i], textarea[placeholder*="details" i], [contenteditable="true"]').first(),
    ],
    eventDescription,
  );

  console.log(
    `[event-flow] Filled fields => title:${filledTitle} date:${filledDate} time:${filledTime} timezone:${selectedTimezone} description:${filledDescription}`,
  );

  await page.screenshot({ path: path.join(artifactsDir, 'event-flow-create-dialog.png'), fullPage: true });
}

async function runApproveFlow(page) {
  const adminBase = adminBaseUrl();
  const emailFilter = env('JWBLNG_CONTACT_EMAIL_FILTER', '').trim();
  const approvalTag = env('JWBLNG_APPROVAL_TAG', 'approved-member').trim();
  const artifactsDir = ensureArtifactsDir();

  if (!emailFilter) throw new Error('JWBLNG_CONTACT_EMAIL_FILTER is required for safe contact approval runs.');

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
  if (!openedContactsGroup) throw new Error(`Could not open Contacts section from sidebar. URL: ${page.url()}`);

  const allContactsLink = mainNav.getByRole('link', { name: /^all contacts$/i }).first();
  if (!(await allContactsLink.isVisible({ timeout: 10000 }).catch(() => false))) {
    throw new Error(`Contacts section opened, but 'All Contacts' link was not visible. URL: ${page.url()}`);
  }

  await Promise.all([page.waitForURL(/\/contacts(\?|$)/, { timeout: 15000 }), allContactsLink.click()]);

  await clickFirstVisible(
    page,
    [
      page.getByRole('link', { name: /pending-review/i }).first(),
      page.getByRole('button', { name: /pending-review/i }).first(),
    ],
    2000,
  ).catch(() => false);

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
  if (!searchInput) throw new Error(`Could not find contacts search input. URL: ${page.url()}`);

  await searchInput.fill(emailFilter);
  await searchInput.press('Enter').catch(() => {});
  await page.waitForTimeout(1200);

  const escapedEmail = emailFilter.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const contactRow = page.getByRole('row', { name: new RegExp(escapedEmail, 'i') }).first();
  if (!(await contactRow.isVisible({ timeout: 10000 }).catch(() => false))) {
    throw new Error(`No visible contact row found for '${emailFilter}'.`);
  }

  await page.screenshot({ path: path.join(artifactsDir, 'contact-flow-before-open.png'), fullPage: true });

  let openedDetail = false;
  const openContactCandidates = [
    contactRow.getByRole('button', { name: new RegExp(`^(?!.*options).+`, 'i') }).first(),
    contactRow.getByRole('link', { name: new RegExp(`^(?!.*options).+`, 'i') }).first(),
    contactRow.locator('button:not(:has-text("Options"))').first(),
  ];
  for (const candidate of openContactCandidates) {
    if (await candidate.isVisible().catch(() => false)) {
      await candidate.click();
      openedDetail = true;
      break;
    }
  }
  if (!openedDetail) await contactRow.click();

  await page.waitForLoadState('domcontentloaded');
  await page.waitForTimeout(1000);

  // Kajabi may keep /contacts URL while opening a side-panel detail view.
  // Continue to tag-control discovery rather than hard-failing on URL shape.

  console.log(`[contact-flow] Apply tag: ${approvalTag}`);
  const detailRoot = page.locator('main, aside, [role="dialog"]').first();
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
  if (!openedTagControl) throw new Error('Could not open tag editor controls on contact page.');

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
  if (!tagInput) throw new Error('Could not find tag input after opening tag controls.');

  await tagInput.fill(approvalTag);
  await page.waitForTimeout(500);

  const tagOption = page.getByRole('option', { name: new RegExp(approvalTag, 'i') }).first();
  if (await tagOption.isVisible().catch(() => false)) {
    await tagOption.click();
  } else {
    await tagInput.press('Enter');
  }

  const saved = await clickFirstVisible(page, [page.getByRole('button', { name: /save|update|apply/i }).first()], 2000);
  await page.screenshot({ path: path.join(artifactsDir, 'contact-flow-after-tag.png'), fullPage: true });
  console.log(`[contact-flow] Tag applied candidate:${approvalTag} saveClicked:${saved}`);
}

async function main() {
  if (!writesAllowed()) {
    console.error('ALLOW_KAJABI_WRITES is not set to 1. Refusing to run write flow.');
    process.exit(1);
  }

  let mode = (process.argv[2] || 'event').trim().toLowerCase();
  if (!['event', 'approve'].includes(mode)) mode = 'event';

  const context = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    viewport: null,
  });

  const page = context.pages()[0] || (await context.newPage());

  console.log('Persistent Kajabi runner started.');
  console.log(`Current mode: ${mode}`);
  console.log('Commands: r=run, mode event, mode approve, report, q=quit');

  const printReportHints = () => {
    const artifactsDir = ensureArtifactsDir();
    const reportDir = path.join(__dirname, '..', 'playwright-report');
    const resultsDir = path.join(__dirname, '..', 'test-results');

    const files = fs
      .readdirSync(artifactsDir, { withFileTypes: true })
      .filter((d) => d.isFile())
      .map((d) => {
        const full = path.join(artifactsDir, d.name);
        const stat = fs.statSync(full);
        return { name: d.name, mtime: stat.mtimeMs };
      })
      .sort((a, b) => b.mtime - a.mtime)
      .slice(0, 10);

    console.log('--- Report Hints ---');
    console.log(`Artifacts: ${artifactsDir}`);
    if (files.length) {
      console.log('Latest artifact files:');
      for (const f of files) console.log(` - ${f.name}`);
    } else {
      console.log('No artifact files found yet.');
    }
    console.log(`Playwright HTML report dir (test-runner only): ${reportDir}`);
    console.log(`Playwright test-results dir (test-runner only): ${resultsDir}`);
    console.log('To open HTML report (after npm run pw:... commands):');
    console.log('  npx.cmd playwright show-report jwblng-mvp\\\\playwright\\\\playwright-report');
  };

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
      if (mode === 'approve') {
        await runApproveFlow(page);
      } else {
        await runEventFlow(page);
      }
      console.log(`Run completed for mode=${mode}. Press r to run again, q to quit.`);
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
    if (cmd === 'mode event') {
      mode = 'event';
      console.log('Mode switched to event. Press r to run.');
      return;
    }
    if (cmd === 'mode approve') {
      mode = 'approve';
      console.log('Mode switched to approve. Press r to run.');
      return;
    }
    if (cmd === 'report') {
      printReportHints();
      return;
    }
    console.log('Unknown command. Use r, mode event, mode approve, report, q.');
  });
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
