const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');

test('draft/create event template flow (write-gated)', async ({ page, context }) => {
  test.skip(!writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 to enable write actions.');

  const adminBase = adminBaseUrl();
  const eventTitle = env('JWBLNG_EVENT_TITLE', `JWBLNG Event Draft ${new Date().toISOString().slice(0, 10)}`);
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

  // Fill title if the form exposes it at this step.
  const titleCandidates = [
    activePage.getByRole('textbox', { name: /title|event name|name/i }).first(),
    activePage.locator('input[name*="title" i], input[placeholder*="title" i], input[name*="name" i]').first(),
  ];

  for (const field of titleCandidates) {
    if (await field.isVisible().catch(() => false)) {
      await field.fill(eventTitle);
      break;
    }
  }

  await activePage.screenshot({
    path: path.join(artifactsDir, 'event-flow-create-dialog.png'),
    fullPage: true,
  });
});
