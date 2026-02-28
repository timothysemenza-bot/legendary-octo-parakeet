const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');

test('draft/create event template flow (write-gated)', async ({ page, context }) => {
  test.skip(!writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 to enable write actions.');

  const adminBase = adminBaseUrl();
  const eventTitle = env('JWBLNG_EVENT_TITLE', `JWBLNG Event Draft ${new Date().toISOString().slice(0, 10)}`);
  const eventDate = env('JWBLNG_EVENT_DATE', '');
  const eventTime = env('JWBLNG_EVENT_TIME', '');
  const eventTimezone = env('JWBLNG_EVENT_TIMEZONE', '');
  const eventDescription = env('JWBLNG_EVENT_DESCRIPTION', '');
  const artifactsDir = ensureArtifactsDir();

  console.log('[event-flow] Open dashboard');
  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');

  const activePage = context.pages().at(-1) || page;
  if (activePage.isClosed()) {
    throw new Error('Active Kajabi admin page is closed before event actions.');
  }

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

  async function fillFirstVisible(candidates, value) {
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
        // Non-fillable element (e.g., select): skip.
        continue;
      }
    }
    return false;
  }

  async function chooseTimezone(value) {
    if (!value) return false;
    const timezoneCombobox = activePage.getByRole('combobox', { name: /time.?zone|zone/i }).first();
    if (await timezoneCombobox.isVisible().catch(() => false)) {
      const preferred = new RegExp(value, 'i');
      const optionByLabel = activePage.getByRole('option', { name: preferred }).first();
      if (await optionByLabel.isVisible({ timeout: 2000 }).catch(() => false)) {
        const optionValue = await optionByLabel.getAttribute('value');
        if (optionValue) {
          await timezoneCombobox.selectOption(optionValue);
          return true;
        }
      }

      // Fallback: select by matching visible option label.
      const options = await timezoneCombobox.locator('option').all().catch(() => []);
      for (const option of options) {
        const label = (await option.innerText().catch(() => '')).trim();
        const val = await option.getAttribute('value').catch(() => null);
        if (label && val && preferred.test(label)) {
          await timezoneCombobox.selectOption(val);
          return true;
        }
      }

      // Last-resort exact value set (if caller passed full option value).
      await timezoneCombobox.selectOption({ label: value }).catch(() => {});
      const timezoneOption = activePage.getByRole('option', { name: new RegExp(value, 'i') }).first();
      if (await timezoneOption.isVisible({ timeout: 4000 }).catch(() => false)) {
        await timezoneOption.click();
        return true;
      }
      return false;
    }
    const timezoneInputs = [
      activePage.getByLabel(/time.?zone|zone/i).first(),
      activePage.locator('input[name*="zone" i], input[placeholder*="zone" i], input[placeholder*="eastern" i]').first(),
    ];
    for (const input of timezoneInputs) {
      if (await input.isVisible().catch(() => false)) {
        await input.fill(value);
        await input.press('Enter').catch(() => {});
        return true;
      }
    }
    return false;
  }

  const mainNav = activePage.getByRole('navigation', { name: /main navigation/i });

  console.log('[event-flow] Navigate to Marketing/Events via UI');
  const openedMarketing = await clickFirstVisible([
    mainNav.getByRole('link', { name: /^marketing$/i }).first(),
    mainNav.getByRole('button', { name: /^marketing$/i }).first(),
    mainNav.locator('li:has-text("Marketing")').first(),
  ]);

  if (!openedMarketing) {
    throw new Error(`Could not open Marketing section from sidebar. URL: ${activePage.url()}`);
  }

  const openedEvents = await clickFirstVisible([
    mainNav.getByRole('link', { name: /^events$/i }).first(),
    mainNav.getByRole('link', { name: /events/i }).first(),
    mainNav.locator('li:has-text("Events")').first(),
  ]);

  if (!openedEvents) {
    throw new Error(`Marketing opened, but Events navigation was not clickable. URL: ${activePage.url()}`);
  }

  await activePage.waitForLoadState('domcontentloaded');
  await expect(activePage).toHaveURL(/events/);

  await activePage.screenshot({
    path: path.join(artifactsDir, 'event-flow-events-screen.png'),
    fullPage: true,
  });

  console.log('[event-flow] Open create event flow');
  const createEventControl = activePage
    .locator('a:has-text("New Event"):visible, a:has-text("Create Event"):visible, button:has-text("New Event"):visible, button:has-text("Create Event"):visible, button:has-text("Add Event"):visible')
    .first();

  await expect(createEventControl).toBeVisible({ timeout: 15000 });
  await createEventControl.click();
  await activePage.waitForLoadState('domcontentloaded');
  await activePage.waitForTimeout(1000);

  const visibleLabels = await activePage
    .locator('label:visible')
    .allTextContents()
    .catch(() => []);
  console.log(`[event-flow] Visible labels: ${visibleLabels.join(' | ')}`);

  // Fill core draft fields if exposed by this Kajabi event form.
  const titleCandidates = [
    activePage.getByRole('textbox', { name: /title|event name|name/i }).first(),
    activePage.locator('input[name*="title" i], input[placeholder*="title" i], input[name*="name" i]').first(),
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
    throw new Error(`Could not find a visible Event Title/Name input. URL: ${activePage.url()}`);
  }

  const filledDate = await fillFirstVisible(
    [
      activePage.getByRole('textbox', { name: /when does this event occur|occurs at|start/i }).first(),
      activePage.getByLabel(/when does this event occur|occurs at|start/i).first(),
      activePage.locator('input[type="date"]:visible, input[name*="date" i], input[placeholder*="date" i], input[placeholder*="mm" i]').first(),
    ],
    eventTime ? `${eventDate} ${eventTime}` : eventDate,
  );

  // Kajabi commonly combines date+time in one "When does this event occur?" field.
  const filledTime = Boolean(eventTime) && filledDate;

  const selectedTimezone = await chooseTimezone(eventTimezone);

  const filledDescription = await fillFirstVisible(
    [
      activePage.getByRole('textbox', { name: /description|details|about/i }).first(),
      activePage.getByLabel(/description|details|about/i).first(),
      activePage.locator('textarea[name*="description" i], textarea[placeholder*="description" i], textarea[placeholder*="details" i], [contenteditable="true"]').first(),
    ],
    eventDescription,
  );

  console.log(
    `[event-flow] Filled fields => title:${filledTitle} date:${filledDate} time:${filledTime} timezone:${selectedTimezone} description:${filledDescription}`,
  );

  await activePage.screenshot({
    path: path.join(artifactsDir, 'event-flow-create-dialog.png'),
    fullPage: true,
  });
});
