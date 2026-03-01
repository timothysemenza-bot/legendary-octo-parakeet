const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');
const {
  getActivePage,
  clickFirstVisible,
  fillFirstEditable,
  normalizeOccursAt,
  chooseTimezone,
} = require('../utils/kajabi-ui');

test('draft/create event template flow (write-gated)', async ({ page, context }) => {
  const runMode = env('JWBLNG_RUN_MODE', 'apply').toLowerCase();
  const isPlanMode = runMode === 'plan';
  test.skip(!isPlanMode && !writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 or run JWBLNG_RUN_MODE=plan.');

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

  const activePage = await getActivePage(page, context, 'Active Kajabi admin page is closed before event actions.');

  const mainNav = activePage.getByRole('navigation', { name: /main navigation/i });

  console.log('[event-flow] Navigate to Marketing/Events via UI');
  const openedMarketing = await clickFirstVisible(activePage, [
    mainNav.getByRole('link', { name: /^marketing$/i }).first(),
    mainNav.getByRole('button', { name: /^marketing$/i }).first(),
    mainNav.locator('li:has-text("Marketing")').first(),
  ]);

  if (!openedMarketing) {
    throw new Error(`Could not open Marketing section from sidebar. URL: ${activePage.url()}`);
  }

  const openedEvents = await clickFirstVisible(activePage, [
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

  if (isPlanMode) {
    console.log('[event-flow] Plan mode: validated Events screen and create control visibility only.');
    const createEventControlPlan = activePage
      .locator('a:has-text("New Event"):visible, a:has-text("Create Event"):visible, button:has-text("New Event"):visible, button:has-text("Create Event"):visible, button:has-text("Add Event"):visible')
      .first();
    await expect(createEventControlPlan).toBeVisible({ timeout: 15000 });
    await activePage.screenshot({
      path: path.join(artifactsDir, 'event-flow-plan-ready.png'),
      fullPage: true,
    });
    return;
  }

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

  const filledDate = await fillFirstEditable(
    [
      activePage.getByRole('textbox', { name: /when does this event occur|occurs at|start/i }).first(),
      activePage.getByLabel(/when does this event occur|occurs at|start/i).first(),
      activePage.locator('input[type="date"]:visible, input[name*="date" i], input[placeholder*="date" i], input[placeholder*="mm" i]').first(),
    ],
    normalizeOccursAt(eventDate, eventTime),
  );

  // Kajabi commonly combines date+time in one "When does this event occur?" field.
  const filledTime = Boolean(eventTime) && filledDate;

  const selectedTimezone = await chooseTimezone(activePage, eventTimezone);

  const filledDescription = await fillFirstEditable(
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

  console.log('[event-flow] Save draft event');
  const saveButton = activePage.getByRole('button', { name: /^save$/i }).first();
  await expect(saveButton).toBeVisible({ timeout: 10000 });
  await expect(saveButton).toBeEnabled({ timeout: 10000 });
  await saveButton.click();

  const landedOnEventsList = await activePage
    .waitForURL(/\/events(\?|$)/, { timeout: 15000 })
    .then(() => true)
    .catch(() => false);

  if (!landedOnEventsList) {
    const createHeadingVisible = await activePage
      .getByRole('heading', { name: /create an event/i })
      .first()
      .isVisible()
      .catch(() => false);
    const invalidFieldCount = await activePage
      .locator('[aria-invalid="true"], .field_with_errors, .sage-input--invalid, .error')
      .count()
      .catch(() => 0);
    if (createHeadingVisible) {
      throw new Error(
        `Event save did not leave create form. Potential validation issues: ${invalidFieldCount}. URL: ${activePage.url()}`,
      );
    }
  }

  await activePage.screenshot({
    path: path.join(artifactsDir, 'event-flow-after-save.png'),
    fullPage: true,
  });
});
