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

async function runEventFlow(page) {
  const adminBase = adminBaseUrl();
  const eventTitle = env('JWBLNG_EVENT_TITLE', `JWBLNG Event Draft ${new Date().toISOString().slice(0, 10)}`);
  const eventDate = env('JWBLNG_EVENT_DATE', '');
  const eventTime = env('JWBLNG_EVENT_TIME', '');
  const eventTimezone = env('JWBLNG_EVENT_TIMEZONE', '');
  const eventDescription = env('JWBLNG_EVENT_DESCRIPTION', '');
  const artifactsDir = ensureArtifactsDir();

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

  console.log('[event-flow] Open dashboard');
  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });

  const mainNav = page.getByRole('navigation', { name: /main navigation/i });

  console.log('[event-flow] Navigate to Marketing/Events via UI');
  const openedMarketing = await clickFirstVisible(page, [
    mainNav.getByRole('link', { name: /^marketing$/i }).first(),
    mainNav.getByRole('button', { name: /^marketing$/i }).first(),
    mainNav.locator('li:has-text("Marketing")').first(),
  ]);

  if (!openedMarketing) {
    throw new Error(`Could not open Marketing section from sidebar. URL: ${page.url()}`);
  }

  const openedEvents = await clickFirstVisible(page, [
    mainNav.getByRole('link', { name: /^events$/i }).first(),
    mainNav.getByRole('link', { name: /events/i }).first(),
    mainNav.locator('li:has-text("Events")').first(),
  ]);

  if (!openedEvents) {
    throw new Error(`Marketing opened, but Events navigation was not clickable. URL: ${page.url()}`);
  }

  await page.waitForLoadState('domcontentloaded');
  await page.screenshot({
    path: path.join(artifactsDir, 'event-flow-events-screen.png'),
    fullPage: true,
  });

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
  if (!filledTitle) {
    throw new Error(`Could not find a visible Event Title/Name input. URL: ${page.url()}`);
  }

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

  await page.screenshot({
    path: path.join(artifactsDir, 'event-flow-create-dialog.png'),
    fullPage: true,
  });
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

  console.log('Persistent Kajabi runner started.');
  console.log('Commands: r = run event flow, q = quit');
  console.log('Tip: log in once if needed; session is kept in jwblng-mvp/playwright/.profile');

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
      await runEventFlow(page);
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
