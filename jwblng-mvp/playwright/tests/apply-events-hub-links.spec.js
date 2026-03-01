const { test, expect } = require('@playwright/test');
const path = require('path');
const { env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');
const { getActivePage, clickFirstVisible, escapeRegex } = require('../utils/kajabi-ui');

async function openWebsitePages(activePage) {
  const mainNav = activePage.getByRole('navigation', { name: /main navigation/i });
  await clickFirstVisible(activePage, [
    mainNav.getByRole('link', { name: /^website$/i }).first(),
    mainNav.getByRole('button', { name: /^website$/i }).first(),
    mainNav.locator('li:has-text("Website")').first(),
  ]);
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
}

async function openBuilderForPage(activePage, pageTitle) {
  const rowNameRegex = new RegExp(`^${escapeRegex(pageTitle)}$`, 'i');
  const row = activePage
    .getByRole('listitem')
    .filter({ has: activePage.getByRole('link', { name: rowNameRegex }) })
    .first();
  await expect(row).toBeVisible({ timeout: 10000 });
  const customizeControl = row.getByRole('link', { name: /customize/i }).first();
  const titleLink = row.getByRole('link', { name: rowNameRegex }).first();
  const openEditorControl = (await customizeControl.isVisible().catch(() => false)) ? customizeControl : titleLink;
  await openEditorControl.click();
  await activePage.waitForURL(/theme_files|admin\/themes|settings\/edit|\/edit/i, { timeout: 20000 });
  await activePage.waitForLoadState('domcontentloaded');
  await activePage.waitForTimeout(700);
}

async function rewriteHubTextBlock(activePage) {
  await clickFirstVisible(
    activePage,
    [
      activePage.getByRole('tab', { name: /sections/i }).first(),
      activePage.locator('[role="tab"]:has-text("Sections")').first(),
    ],
    3000,
  ).catch(() => false);

  await clickFirstVisible(
    activePage,
    [
      activePage.getByRole('link', { name: /text & image/i }).first(),
      activePage.getByRole('link', { name: /^hero$/i }).first(),
      activePage.locator('a:has-text("Text & Image"), a:has-text("Hero")').first(),
    ],
    4000,
  ).catch(() => false);

  await clickFirstVisible(
    activePage,
    [
      activePage.locator('a[href*="/blocks/"]:has-text("Text")').first(),
      activePage.getByRole('link', { name: /^text$/i }).first(),
      activePage.locator('a:has-text("Text")').first(),
    ],
    3000,
  ).catch(() => false);

  const html = `
    <section style="padding:28px;border-radius:14px;border:1px solid currentColor;">
      <h1 style="margin:0 0 10px 0;">JWBLNG Events</h1>
      <p style="margin:0 0 16px 0;line-height:1.6;">Choose a program and register through the canonical JWBLNG journey.</p>
      <ul style="margin:0 0 18px 18px;line-height:1.8;">
        <li><a href="/speaker-series" style="font-weight:600;">Speaker Series</a></li>
        <li><a href="/book-club" style="font-weight:600;">Book Club</a></li>
        <li><a href="/halacha-circle" style="font-weight:600;">Halacha Circle</a></li>
      </ul>
      <p style="margin:0;">
        <a href="/join" style="display:inline-block;padding:10px 16px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:600;">Join JWBLNG</a>
      </p>
    </section>
  `;

  const changed = await activePage
    .evaluate((content) => {
      const tiny = window.tinymce;
      if (!tiny || !Array.isArray(tiny.editors) || tiny.editors.length === 0) return 0;
      let n = 0;
      for (const editor of tiny.editors) {
        if (!editor || editor.removed) continue;
        editor.setContent(content);
        editor.fire('change');
        n += 1;
      }
      return n;
    }, html)
    .catch(() => 0);

  const saveSection = activePage.getByRole('button', { name: /save section/i }).first();
  if (await saveSection.isVisible().catch(() => false)) {
    if (await saveSection.isEnabled().catch(() => false)) {
      await saveSection.click();
      await activePage.waitForTimeout(700);
    }
  }
  return Number(changed) > 0;
}

async function rewriteFeatureCardBlocks(activePage) {
  const cards = [
    {
      title: 'Speaker Series',
      description: 'Leadership conversations with founders and experts.',
      buttonText: 'View Speaker Series',
      link: '/speaker-series',
    },
    {
      title: 'Book Club',
      description: 'Practical learning rooted in values and business application.',
      buttonText: 'View Book Club',
      link: '/book-club',
    },
    {
      title: 'Halacha Circle',
      description: 'Business halacha Q&A and implementation guidance.',
      buttonText: 'View Halacha Circle',
      link: '/halacha-circle',
    },
  ];

  await clickFirstVisible(
    activePage,
    [
      activePage.getByRole('link', { name: /3 feature cards/i }).first(),
      activePage.locator('a:has-text("3 Feature Cards")').first(),
    ],
    4000,
  ).catch(() => false);

  const blockHrefs = await activePage
    .evaluate(() => [...document.querySelectorAll('a[href*="/blocks/"]')].map((a) => a.getAttribute('href')).filter(Boolean))
    .catch(() => []);
  if (!blockHrefs.length) return false;

  let changed = 0;
  for (let i = 0; i < cards.length && i < blockHrefs.length; i += 1) {
    const url = new URL(blockHrefs[i], activePage.url()).toString();
    await activePage.goto(url, { waitUntil: 'domcontentloaded' });
    await activePage.waitForLoadState('domcontentloaded');
    await activePage.waitForTimeout(300);

    const didSet = await activePage
      .evaluate((card) => {
        const fields = [...document.querySelectorAll('input, textarea')];
        let wrote = 0;
        for (const el of fields) {
          const sig = `${el.getAttribute('name') || ''} ${el.getAttribute('id') || ''} ${el.getAttribute('placeholder') || ''} ${el.getAttribute('aria-label') || ''}`
            .toLowerCase();
          if (/title|heading|name/.test(sig)) {
            el.value = card.title;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            wrote += 1;
            continue;
          }
          if (/description|summary|text|body|content/.test(sig)) {
            el.value = card.description;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            wrote += 1;
            continue;
          }
          if (/button.*text|label|cta/.test(sig)) {
            el.value = card.buttonText;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            wrote += 1;
            continue;
          }
          if (/link|url|href/.test(sig)) {
            el.value = card.link;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            wrote += 1;
          }
        }
        return wrote;
      }, cards[i])
      .catch(() => 0);
    if (didSet > 0) changed += 1;
  }

  const saveSection = activePage.getByRole('button', { name: /save section/i }).first();
  if (await saveSection.isVisible().catch(() => false)) {
    if (await saveSection.isEnabled().catch(() => false)) {
      await saveSection.click();
      await activePage.waitForTimeout(700);
    }
  }
  return changed > 0;
}

test('apply events hub links in Kajabi builder (write-gated)', async ({ page, context }) => {
  test.setTimeout(180000);
  const runMode = env('JWBLNG_RUN_MODE', 'apply').toLowerCase();
  const isPlanMode = runMode === 'plan';
  test.skip(!isPlanMode && !writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 or run JWBLNG_RUN_MODE=plan.');

  const adminBase = adminBaseUrl();
  const artifactsDir = ensureArtifactsDir();
  const hubPageTitle = env('JWBLNG_EVENTS_HUB_PAGE_TITLE', 'Events').trim();

  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');
  const activePage = await getActivePage(page, context, 'Active Kajabi admin page is closed before events hub actions.');

  await openWebsitePages(activePage);
  await openBuilderForPage(activePage, hubPageTitle);

  const previewHref = await activePage.getByRole('link', { name: /^preview$/i }).first().getAttribute('href').catch(() => '');
  console.log(`[events-hub] Preview URL: ${previewHref || ''}`);

  let rewritten = false;
  let featureCardsUpdated = false;
  if (!isPlanMode) {
    rewritten = await rewriteHubTextBlock(activePage);
    featureCardsUpdated = await rewriteFeatureCardBlocks(activePage);
  }

  const saveButton = activePage
    .locator('button:has-text("Save"), button:has-text("Update"), [role="button"]:has-text("Save"), [role="button"]:has-text("Update")')
    .first();
  if (!isPlanMode && (await saveButton.isVisible().catch(() => false)) && (await saveButton.isEnabled().catch(() => false))) {
    await saveButton.click();
    await activePage.waitForTimeout(900);
  }

  const preview = activePage.frameLocator('iframe').first();
  const hasSpeakerLink = await preview.getByRole('link', { name: /speaker series/i }).first().isVisible().catch(() => false);
  const hasBookLink = await preview.getByRole('link', { name: /book club/i }).first().isVisible().catch(() => false);
  const hasHalachaLink = await preview.getByRole('link', { name: /halacha circle/i }).first().isVisible().catch(() => false);

  await activePage.screenshot({
    path: path.join(artifactsDir, 'events-hub-links-after.png'),
    fullPage: true,
  });

  console.log(
    `[events-hub] rewritten:${rewritten} featureCardsUpdated:${featureCardsUpdated} links speaker:${hasSpeakerLink} book:${hasBookLink} halacha:${hasHalachaLink}`,
  );
  expect(hasSpeakerLink && hasBookLink && hasHalachaLink).toBeTruthy();
});
