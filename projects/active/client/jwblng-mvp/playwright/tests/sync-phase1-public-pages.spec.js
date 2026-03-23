const { test, expect } = require('@playwright/test');
const path = require('path');
const { canonicalJoinHref, env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');
const { getActivePage, clickFirstVisible, escapeRegex } = require('../utils/kajabi-ui');

const joinFormUrl = canonicalJoinHref();
const joinBridgeUrl = '/join';

function slugify(input) {
  return String(input || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

const PAGE_CONFIGS = [
  {
    title: 'About',
    artifactSlug: 'about',
    html: `
      <section style="padding:32px;border-radius:18px;border:1px solid currentColor;">
        <h1 style="margin:0 0 12px 0;">About JWBLNG</h1>
        <p style="margin:0 0 16px 0;line-height:1.75;font-size:17px;">
          Pronounced "JEW-Bling," JWBLNG exists to support Orthodox Jewish women who are building careers,
          businesses, and leadership paths without leaving Torah values at the door.
        </p>
        <h2 style="margin:0 0 10px 0;">Why JWBLNG exists</h2>
        <p style="margin:0 0 16px 0;line-height:1.75;">
          As more women enter entrepreneurship, ownership, leadership, and corporate life, they face questions
          about workplace culture, business halacha, travel, yichud, dress, and values-based decision making.
          JWBLNG was built so those women do not have to navigate that alone.
        </p>
        <p style="margin:0 0 16px 0;line-height:1.75;">
          Our mission is to provide support, education, and community so Jewish women can bring G-d, Torah,
          and Jewish values with them into the workplace, with the courage, protection, and confidence that comes
          from knowing they are not alone.
        </p>
        <h2 style="margin:0 0 10px 0;">What members find here</h2>
        <ul style="margin:0 0 18px 20px;line-height:1.8;">
          <li>Speaker Series conversations with founders, executives, and expert operators.</li>
          <li>Book Club, business halacha, and learning rooted in Torah values and real business application.</li>
          <li>A supportive peer network for women growing businesses, careers, and communal impact.</li>
          <li>Professional development and practical guidance for real workplace challenges.</li>
          <li>Support, input, and encouragement to stay strong and balanced in environments that can challenge Torah beliefs and values.</li>
        </ul>
        <p style="margin:0 0 18px 0;line-height:1.75;">
          Together we are building a community where like-minded Jewish women can take their full selves to work
          and return each day with the same Torah values and lifestyle they brought in.
        </p>
        <p style="margin:0 0 18px 0;line-height:1.75;"><strong>Connect - Grow - Succeed!</strong></p>
        <p style="margin:0;">
          <a href="/events" style="display:inline-block;padding:10px 16px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:700;">View Upcoming Events</a>
          <a href="${joinBridgeUrl}" style="display:inline-block;margin-left:10px;padding:10px 16px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:700;">Join JWBLNG</a>
        </p>
      </section>
    `,
  },
  {
    title: 'Contact',
    artifactSlug: 'contact',
    html: `
      <section style="padding:32px;border-radius:18px;border:1px solid currentColor;">
        <h1 style="margin:0 0 12px 0;">Contact JWBLNG</h1>
        <p style="margin:0 0 16px 0;line-height:1.75;font-size:17px;">
          Questions about membership, programming, speaking, partnerships, support, or business halacha? We would love to hear from you.
        </p>
        <p style="margin:0 0 16px 0;line-height:1.75;">
          We are here to answer questions of business halacha, provide support in difficult work situations,
          learn together, and help women get connected to the right JWBLNG next step.
        </p>
        <ul style="margin:0 0 18px 20px;line-height:1.8;">
          <li>Email us at <a href="mailto:info@jwblng.org" style="font-weight:700;">info@jwblng.org</a>.</li>
          <li>Call or text us at <strong>347.335.9599</strong>.</li>
          <li>Use this page for community access questions, speaker ideas, collaboration requests, workplace support, and partnership conversations.</li>
          <li>Registered charity number: <strong>92-2391852</strong>.</li>
          <li>If you are waiting on approval or unsure whether to join again or log in, contact us before submitting a second request.</li>
        </ul>
        <p style="margin:0;">
          <a href="mailto:info@jwblng.org" style="display:inline-block;padding:10px 16px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:700;">Email JWBLNG</a>
          <a href="/support-jwblng" style="display:inline-block;margin-left:10px;padding:10px 16px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:700;">Support JWBLNG</a>
        </p>
      </section>
    `,
  },
  {
    title: 'Events',
    pathHint: '/events',
    artifactSlug: 'events',
    html: `
      <section style="padding:32px;border-radius:18px;border:1px solid currentColor;">
        <h1 style="margin:0 0 12px 0;">Upcoming Events</h1>
        <p style="margin:0 0 16px 0;line-height:1.75;font-size:17px;">
          Explore JWBLNG programs, choose the format that fits where you are right now, and use the join path to request community access for registration details and follow-up.
        </p>
        <p style="margin:0 0 16px 0;line-height:1.75;">
          JWBLNG programming is designed to strengthen Orthodox Jewish women in business through professional development,
          Torah perspective, practical support, and live community connection.
        </p>
        <div style="display:grid;gap:12px;margin:0 0 18px 0;">
          <a href="/speaker-series" style="display:block;padding:14px 16px;border-radius:14px;border:1px solid currentColor;text-decoration:none;color:inherit;">
            <strong style="display:block;font-size:18px;">Speaker Series</strong>
            <span style="display:block;margin-top:6px;line-height:1.7;">Conversations with founders, executives, and expert operators focused on values-aligned leadership and professional growth.</span>
          </a>
          <a href="/book-club" style="display:block;padding:14px 16px;border-radius:14px;border:1px solid currentColor;text-decoration:none;color:inherit;">
            <strong style="display:block;font-size:18px;">Book Club</strong>
            <span style="display:block;margin-top:6px;line-height:1.7;">Practical learning rooted in Torah values and real business application, with guided discussion and implementation prompts.</span>
          </a>
          <a href="/halacha-circle" style="display:block;padding:14px 16px;border-radius:14px;border:1px solid currentColor;text-decoration:none;color:inherit;">
            <strong style="display:block;font-size:18px;">Halacha Circle</strong>
            <span style="display:block;margin-top:6px;line-height:1.7;">Live Q&amp;A for business questions through a halachic and values-driven lens, with member questions shaping the conversation.</span>
          </a>
        </div>
        <p style="margin:0 0 18px 0;line-height:1.75;">
          New here? Join JWBLNG first. Approved members can log in for access details, follow-up, and member-only logistics.
        </p>
        <p style="margin:0;">
          <a href="${joinBridgeUrl}" style="display:inline-block;padding:10px 16px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:700;">Join JWBLNG</a>
          <a href="/support-jwblng" style="display:inline-block;margin-left:10px;padding:10px 16px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:700;">Support JWBLNG</a>
        </p>
      </section>
    `,
  },
  {
    title: 'Support JWBLNG',
    pathHint: '/support-jwblng',
    artifactSlug: 'support',
    html: `
      <section style="padding:32px;border-radius:18px;border:1px solid currentColor;">
        <h1 style="margin:0 0 12px 0;">Support Jewish Women in Business Leadership</h1>
        <p style="margin:0 0 16px 0;line-height:1.75;font-size:17px;">
          Your support helps JWBLNG sustain speaker series conversations, book club learning, business halacha, and a stronger network for Orthodox Jewish women building with integrity.
        </p>
        <div style="display:grid;gap:12px;margin:0 0 18px 0;">
          <div style="padding:14px 16px;border-radius:14px;border:1px solid currentColor;">
            <strong style="display:block;font-size:18px;">Donate online</strong>
            <span style="display:block;margin-top:6px;line-height:1.7;">Give securely through Zeffy to support current programming, community-building, and practical resources for Jewish women in business.</span>
          </div>
          <div style="padding:14px 16px;border-radius:14px;border:1px solid currentColor;">
            <strong style="display:block;font-size:18px;">Prefer to give by check?</strong>
            <span style="display:block;margin-top:6px;line-height:1.7;">Email <a href="mailto:info@jwblng.org" style="font-weight:700;">info@jwblng.org</a> or call/text <strong>347.335.9599</strong> for the current mailing details and check-giving guidance.</span>
          </div>
          <div style="padding:14px 16px;border-radius:14px;border:1px solid currentColor;">
            <strong style="display:block;font-size:18px;">Questions about giving?</strong>
            <span style="display:block;margin-top:6px;line-height:1.7;">Reach out for donation questions, sponsorship conversations, or help choosing the right giving path.</span>
          </div>
          <div style="padding:14px 16px;border-radius:14px;border:1px solid currentColor;">
            <strong style="display:block;font-size:18px;">Charity details</strong>
            <span style="display:block;margin-top:6px;line-height:1.7;">Registered charity number: <strong>92-2391852</strong>. You can also reach JWBLNG at <a href="mailto:info@jwblng.org" style="font-weight:700;">info@jwblng.org</a>.</span>
          </div>
        </div>
        <p style="margin:0;">
          <a href="https://www.zeffy.com/en-US/donation-form/91c61b76-8899-4a47-ac53-2226da71bc05" style="display:inline-block;padding:10px 16px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:700;">Donate via Zeffy</a>
          <a href="mailto:info@jwblng.org" style="display:inline-block;margin-left:10px;padding:10px 16px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:700;">Email JWBLNG</a>
        </p>
      </section>
    `,
  },
  {
    title: 'Join',
    pathHint: '/join',
    artifactSlug: 'join',
    html: `
      <section style="padding:32px;border-radius:18px;border:1px solid currentColor;">
        <h1 style="margin:0 0 12px 0;">Join JWBLNG</h1>
        <p style="margin:0 0 16px 0;line-height:1.75;font-size:17px;">
          Membership requests begin on the JWBLNG homepage form. Use the button below to go straight to the Phase 1 join form and request free community access there.
        </p>
        <p style="margin:0 0 18px 0;line-height:1.75;">
          This page is only a bridge so there is one consistent public join path. After approval, returning members should use the site-wide Log In control instead of submitting a second request.
        </p>
        <p style="margin:0 0 18px 0;line-height:1.75;">
          Waiting on approval or not sure whether you should join again or log in? Contact JWBLNG at <a href="mailto:info@jwblng.org" style="font-weight:700;">info@jwblng.org</a> or <strong>347.335.9599</strong> for help.
        </p>
        <p style="margin:0;">
          <a href="${joinFormUrl}" style="display:inline-block;padding:10px 16px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:700;">Go to the Join Form</a>
          <a href="/events" style="display:inline-block;margin-left:10px;padding:10px 16px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:700;">View Upcoming Events</a>
        </p>
      </section>
    `,
  },
];

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

async function findPageRow(activePage, pageTitle) {
  const rowNameRegex = new RegExp(`^${escapeRegex(pageTitle)}$`, 'i');
  return activePage
    .getByRole('listitem')
    .filter({ has: activePage.getByRole('link', { name: rowNameRegex }) })
    .first();
}

async function ensurePage(activePage, pageConfig) {
  let row = await findPageRow(activePage, pageConfig.title);
  const exists = await row.isVisible({ timeout: 2000 }).catch(() => false);
  if (exists) return { row, created: false };

  const createControl = activePage
    .locator('a:has-text("New Website Page"):visible, button:has-text("New Website Page"):visible, a:has-text("New Page"):visible, button:has-text("New Page"):visible')
    .first();
  if (!(await createControl.isVisible({ timeout: 8000 }).catch(() => false))) {
    throw new Error(`Could not find create page control while creating '${pageConfig.title}'. URL: ${activePage.url()}`);
  }
  await createControl.click();

  const nameInput = activePage.getByRole('textbox', { name: /^name$/i }).first();
  await nameInput.waitFor({ state: 'visible', timeout: 10000 });
  await nameInput.fill(pageConfig.title);

  const pathInput = activePage
    .locator('input[name*="path" i], input[name*="slug" i], input[placeholder*="path" i], input[placeholder*="slug" i]')
    .first();
  if (pageConfig.pathHint && (await pathInput.isVisible().catch(() => false))) {
    await pathInput.fill(pageConfig.pathHint);
  }

  const customizeButton = activePage.getByRole('button', { name: /customize page/i }).first();
  await expect(customizeButton).toBeEnabled({ timeout: 10000 });
  await customizeButton.click();
  await activePage.waitForLoadState('domcontentloaded');
  await activePage.waitForTimeout(1000);

  const duplicateNameError = await activePage
    .getByText(/name has already been taken/i)
    .first()
    .isVisible()
    .catch(() => false);
  if (duplicateNameError) {
    throw new Error(`Kajabi reported duplicate page title '${pageConfig.title}'. Create or rename it manually, then rerun.`);
  }

  await activePage.waitForURL(/theme_files|admin\/themes|settings\/edit|\/edit/i, { timeout: 20000 });
  return { row: null, created: true };
}

async function openBuilderForPage(activePage, pageTitle) {
  const rowNameRegex = new RegExp(`^${escapeRegex(pageTitle)}$`, 'i');
  const row = activePage
    .getByRole('listitem')
    .filter({ has: activePage.getByRole('link', { name: rowNameRegex }) })
    .first();
  await expect(row).toBeVisible({ timeout: 10000 });
  const editControl =
    (await row.getByRole('link', { name: /edit|customize/i }).first().isVisible().catch(() => false))
      ? row.getByRole('link', { name: /edit|customize/i }).first()
      : row.getByRole('link', { name: rowNameRegex }).first();
  await editControl.click();
  await activePage.waitForURL(/theme_files|admin\/themes|settings\/edit|\/edit/i, { timeout: 20000 });
  await activePage.waitForLoadState('domcontentloaded');
  await activePage.waitForTimeout(800);
}

async function openTextBlockEditor(activePage) {
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

  const textBlockCandidates = [
    activePage.locator('a[href*="/blocks/"]:has-text("Text")').first(),
    activePage.getByRole('link', { name: /^text$/i }).first(),
    activePage.locator('a:has-text("Text")').first(),
  ];
  for (const candidate of textBlockCandidates) {
    if (await candidate.isVisible().catch(() => false)) {
      await candidate.click();
      await activePage.waitForTimeout(700);
      if (/\/blocks\//i.test(activePage.url())) {
        return true;
      }
    }
  }

  const firstBlockHref = await activePage
    .locator('a[href*="/blocks/"]')
    .first()
    .getAttribute('href')
    .catch(() => null);
  if (firstBlockHref) {
    const nextUrl = new URL(firstBlockHref, activePage.url()).toString();
    await activePage.goto(nextUrl, { waitUntil: 'domcontentloaded' });
    await activePage.waitForTimeout(700);
    return /\/blocks\//i.test(activePage.url());
  }

  return /\/blocks\//i.test(activePage.url());
}

async function applyHtmlContent(activePage, html) {
  let changed = await activePage
    .evaluate(({ nextHtml }) => {
      const tiny = window.tinymce;
      if (!tiny || !Array.isArray(tiny.editors) || tiny.editors.length === 0) return 0;
      let edits = 0;
      for (const editor of tiny.editors) {
        if (!editor || editor.removed) continue;
        editor.setContent(nextHtml);
        editor.fire('change');
        edits += 1;
      }
      return edits;
    }, { nextHtml: html })
    .catch(() => 0);

  if (changed) return changed;

  const frames = activePage.frames();
  for (const frame of frames) {
    const frameEdits = await frame
      .evaluate(({ nextHtml }) => {
        const body = document.body || document.querySelector('body[contenteditable="true"]');
        if (!body) return 0;
        body.innerHTML = nextHtml;
        body.dispatchEvent(new Event('input', { bubbles: true }));
        body.dispatchEvent(new Event('change', { bubbles: true }));
        return 1;
      }, { nextHtml: html })
      .catch(() => 0);
    if (frameEdits) {
      changed += frameEdits;
      break;
    }
  }

  return changed;
}

async function saveBuilder(activePage) {
  const saveSectionButton = activePage.getByRole('button', { name: /save section/i }).first();
  if ((await saveSectionButton.isVisible().catch(() => false)) && (await saveSectionButton.isEnabled().catch(() => false))) {
    await saveSectionButton.click();
    await activePage.waitForTimeout(500);
  }

  const saveButton = activePage
    .locator('button:has-text("Save"), button:has-text("Update"), [role="button"]:has-text("Save"), [role="button"]:has-text("Update")')
    .first();
  if ((await saveButton.isVisible().catch(() => false)) && (await saveButton.isEnabled().catch(() => false))) {
    await saveButton.click();
    await Promise.race([
      activePage.getByText(/saved|updated|changes saved/i).first().waitFor({ state: 'visible', timeout: 8000 }).catch(() => null),
      activePage.waitForTimeout(1000),
    ]);
  }

  const publishButton = activePage
    .locator('button:has-text("Publish"), [role="button"]:has-text("Publish")')
    .first();
  if ((await publishButton.isVisible().catch(() => false)) && (await publishButton.isEnabled().catch(() => false))) {
    await publishButton.click();
    await activePage.waitForTimeout(1200);
  }
}

async function returnToPages(activePage, adminBase) {
  const backToPages = activePage.getByRole('link', { name: /back to pages/i }).first();
  if (await backToPages.isVisible({ timeout: 4000 }).catch(() => false)) {
    await backToPages.click();
  } else {
    await activePage.goto(`${adminBase}/website_pages`, { waitUntil: 'domcontentloaded' });
  }
  await expect(activePage.getByRole('heading', { name: /^pages$/i })).toBeVisible({ timeout: 15000 });
}

test('sync JWBLNG phase 1 public pages in Kajabi (write-gated)', async ({ page, context }) => {
  test.setTimeout(300000);
  const runMode = env('JWBLNG_RUN_MODE', 'apply').toLowerCase();
  const isPlanMode = runMode === 'plan';
  test.skip(!isPlanMode && !writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 or run JWBLNG_RUN_MODE=plan.');

  const adminBase = adminBaseUrl();
  const artifactsDir = ensureArtifactsDir();

  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');
  const activePage = await getActivePage(page, context, 'Active Kajabi admin page is closed before phase 1 page sync.');
  const requestedTitles = env('JWBLNG_PHASE1_PAGE_TITLES', '')
    .split('|')
    .map((value) => value.trim())
    .filter(Boolean);
  const pageConfigs = requestedTitles.length
    ? PAGE_CONFIGS.filter((config) => requestedTitles.some((title) => new RegExp(`^${escapeRegex(title)}$`, 'i').test(config.title)))
    : PAGE_CONFIGS;

  await openWebsitePages(activePage);

  for (const pageConfig of pageConfigs) {
    console.log(`[phase1-pages] Sync page: ${pageConfig.title}`);
    let created = false;
    if (isPlanMode) {
      const row = await findPageRow(activePage, pageConfig.title);
      const exists = await row.isVisible({ timeout: 2000 }).catch(() => false);
      console.log(`[phase1-pages] plan mode ${pageConfig.title} exists:${exists}`);
      continue;
    }

    const ensured = await ensurePage(activePage, pageConfig);
    created = ensured.created;
    if (!created) {
      await openBuilderForPage(activePage, pageConfig.title);
    }

    await openTextBlockEditor(activePage).catch(() => false);
    const editsApplied = await applyHtmlContent(activePage, pageConfig.html);
    if (!editsApplied) {
      throw new Error(`Could not find editable HTML context for ${pageConfig.title}. URL: ${activePage.url()}`);
    }

    await saveBuilder(activePage);

    await activePage.screenshot({
      path: path.join(artifactsDir, `phase1-page-${slugify(pageConfig.artifactSlug)}.png`),
      fullPage: true,
    });

    await returnToPages(activePage, adminBase);
  }
});
