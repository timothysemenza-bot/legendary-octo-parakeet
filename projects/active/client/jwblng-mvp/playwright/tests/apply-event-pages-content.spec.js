const { test, expect } = require('@playwright/test');
const path = require('path');
const { canonicalJoinHref, env, adminBaseUrl, writesAllowed, ensureArtifactsDir } = require('../utils/env');
const { getActivePage, clickFirstVisible, escapeRegex } = require('../utils/kajabi-ui');

function slugify(input) {
  return String(input || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

const PAGE_CONTENT_DEFAULTS = [
  {
    title: 'Speaker Series',
    heading: 'Speaker Series',
    subheading: 'Conversations with founders, executives, and experts who lead with purpose.',
    ctaText: 'Register for Speaker Series',
    ctaLink: canonicalJoinHref(),
  },
  {
    title: 'Book Club',
    heading: 'Book Club',
    subheading: 'Practical learning rooted in Torah values and real business application.',
    ctaText: 'Register for Book Club',
    ctaLink: canonicalJoinHref(),
  },
  {
    title: 'Halacha Circle',
    heading: 'Halacha Circle',
    subheading: 'Live Q&A for business questions through a halachic and values-driven lens.',
    ctaText: 'Join the Halacha Circle',
    ctaLink: canonicalJoinHref(),
  },
];

async function fillFirstMatchingField(candidates, value) {
  if (!value) return false;
  for (const candidate of candidates) {
    if (await candidate.isVisible().catch(() => false)) {
      const filled = await candidate.fill(value).then(() => true).catch(() => false);
      if (filled) return true;
    }
  }
  return false;
}

async function applyHeuristicTextboxEdits(page, pageConfig) {
  let edits = 0;
  const textboxes = page.getByRole('textbox');
  const count = await textboxes.count().catch(() => 0);
  for (let i = 0; i < count; i += 1) {
    const box = textboxes.nth(i);
    if (!(await box.isVisible().catch(() => false))) continue;
    const meta = await box
      .evaluate((el) => ({
        name: (el.getAttribute('aria-label') || '').toLowerCase(),
        placeholder: (el.getAttribute('placeholder') || '').toLowerCase(),
        value: 'value' in el ? String(el.value || '') : '',
      }))
      .catch(() => ({ name: '', placeholder: '', value: '' }));
    const signature = `${meta.name} ${meta.placeholder} ${meta.value}`.toLowerCase();

    if (/heading|headline|title|all the tools|successful online business/.test(signature)) {
      await box.fill(pageConfig.heading);
      edits += 1;
      continue;
    }
    if (/description|body|text|lorem ipsum/.test(signature)) {
      await box.fill(pageConfig.subheading);
      edits += 1;
      continue;
    }
    if (/button.*text|cta.*text|button label|label/.test(signature)) {
      await box.fill(pageConfig.ctaText);
      edits += 1;
      continue;
    }
    if (/button.*link|cta.*link|url|link/.test(signature)) {
      await box.fill(pageConfig.ctaLink);
      edits += 1;
    }
  }
  return edits;
}

async function applyHeuristicContentEditableEdits(page, pageConfig) {
  let edits = 0;
  const editable = page.locator('[contenteditable="true"]:visible');
  const count = await editable.count().catch(() => 0);
  for (let i = 0; i < count; i += 1) {
    const field = editable.nth(i);
    if (!(await field.isVisible().catch(() => false))) continue;
    if (i === 0) {
      const ok = await field.fill(pageConfig.heading).then(() => true).catch(() => false);
      if (ok) edits += 1;
      continue;
    }
    if (i === 1) {
      const ok = await field.fill(pageConfig.subheading).then(() => true).catch(() => false);
      if (ok) edits += 1;
      continue;
    }
  }
  return edits;
}

async function openPagesScreen(activePage) {
  const mainNav = activePage.getByRole('navigation', { name: /main navigation/i });
  const openedWebsite = await clickFirstVisible(activePage, [
    mainNav.getByRole('link', { name: /^website$/i }).first(),
    mainNav.getByRole('button', { name: /^website$/i }).first(),
    mainNav.locator('li:has-text("Website")').first(),
  ]);
  if (!openedWebsite) {
    throw new Error(`Could not open Website section from sidebar. URL: ${activePage.url()}`);
  }

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
  if (!(await row.isVisible({ timeout: 10000 }).catch(() => false))) {
    return false;
  }

  const customizeControl = row.getByRole('link', { name: /customize/i }).first();
  const titleLink = row.getByRole('link', { name: rowNameRegex }).first();
  const openEditorControl = (await customizeControl.isVisible().catch(() => false)) ? customizeControl : titleLink;
  await openEditorControl.click();
  await activePage.waitForURL(/theme_files|admin\/themes|settings\/edit|\/edit/i, { timeout: 20000 });
  await activePage.waitForLoadState('domcontentloaded');
  await activePage.waitForTimeout(900);
  return true;
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
      activePage.locator('a:has-text("Text & Image")').first(),
    ],
    4000,
  ).catch(() => false);

  const textBlockCandidates = [
    activePage.locator('a[href*="/blocks/"]:has-text("Text")').first(),
    activePage.getByRole('link', { name: /^text$/i }).first(),
    activePage.locator('a:has-text("Text")').first(),
  ];
  let clicked = false;
  for (const candidate of textBlockCandidates) {
    if (await candidate.isVisible().catch(() => false)) {
      await candidate.click();
      clicked = true;
      break;
    }
  }

  if (!clicked) return false;
  await activePage.waitForTimeout(800);

  const onTextBlockHeading = await activePage
    .getByRole('heading', { name: /^text$/i })
    .first()
    .isVisible()
    .catch(() => false);
  const onBlockUrl = /\/blocks\//i.test(activePage.url());
  return onTextBlockHeading || onBlockUrl;
}

async function applyTinyMceEdits(activePage, pageConfig) {
  const brandedHtml = `
    <section style="padding:30px;border-radius:16px;border:1px solid currentColor;">
      <h2 style="margin:0 0 10px 0;letter-spacing:0.2px;">${pageConfig.heading}</h2>
      <p style="margin:0;line-height:1.7;font-size:17px;">${pageConfig.subheading}</p>
      <p style="margin:16px 0 0 0;">
        <a href="${pageConfig.ctaLink}" style="display:inline-block;padding:10px 16px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:600;">
          ${pageConfig.ctaText}
        </a>
        <a href="/events" style="display:inline-block;margin-left:10px;padding:10px 16px;border-radius:999px;border:1px solid currentColor;text-decoration:none;font-weight:600;">
          Back to Events
        </a>
      </p>
    </section>
  `;

  let result = await activePage
    .evaluate(({ html }) => {
      const tiny = window.tinymce;
      if (!tiny || !Array.isArray(tiny.editors) || tiny.editors.length === 0) return 0;
      let changed = 0;
      for (const editor of tiny.editors) {
        if (!editor || editor.removed) continue;
        editor.setContent(html);
        editor.fire('change');
        changed += 1;
      }
      return changed;
    }, { html: brandedHtml })
    .catch(() => 0);

  result = Number(result) || 0;
  if (result > 0) return result;

  const frames = activePage.frames();
  for (const frame of frames) {
    const edited = await frame
      .evaluate(({ html }) => {
        const body = document.querySelector('body[contenteditable="true"]');
        if (!body) return 0;
        body.innerHTML = html;
        body.dispatchEvent(new Event('input', { bubbles: true }));
        return 1;
      }, { html: brandedHtml })
      .catch(() => 0);
    if (edited) {
      result += Number(edited) || 0;
      break;
    }
  }

  return result;
}

test('apply scoped event page content in Kajabi builder (write-gated)', async ({ page, context }) => {
  test.setTimeout(240000);
  const runMode = env('JWBLNG_RUN_MODE', 'apply').toLowerCase();
  const isPlanMode = runMode === 'plan';
  test.skip(!isPlanMode && !writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 or run JWBLNG_RUN_MODE=plan.');

  const adminBase = adminBaseUrl();
  const artifactsDir = ensureArtifactsDir();
  const activeContent = PAGE_CONTENT_DEFAULTS;
  const pagesWithoutEditableControls = [];

  console.log('[event-pages] Open dashboard');
  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');
  const activePage = await getActivePage(page, context, 'Active Kajabi admin page is closed before event page content actions.');

  await openPagesScreen(activePage);

  for (const pageConfig of activeContent) {
    console.log(`[event-pages] Update page: ${pageConfig.title}`);
    const found = await openBuilderForPage(activePage, pageConfig.title);
    if (!found) {
      throw new Error(`Scoped event page not found in Website Pages list: ${pageConfig.title}`);
    }

    let editsApplied = 0;

    await clickFirstVisible(
      activePage,
      [
        activePage.getByRole('link', { name: /^hero$/i }).first(),
        activePage.getByRole('link', { name: /text & image/i }).first(),
        activePage.getByRole('link', { name: /^image$/i }).first(),
        activePage.locator('a:has-text("Hero")').first(),
        activePage.locator('a:has-text("Text & Image")').first(),
      ],
      3000,
    ).catch(() => false);
    await clickFirstVisible(
      activePage,
      [
        activePage.getByRole('link', { name: /^text$/i }).first(),
        activePage.locator('a:has-text("Text")').first(),
        activePage.locator('a[href*="/blocks/"]:has-text("Text")').first(),
      ],
      3000,
    ).catch(() => false);
    const openedBlockEditor = await openTextBlockEditor(activePage);
    console.log(`[event-pages] ${pageConfig.title} text block editor opened:${openedBlockEditor} url:${activePage.url()}`);

    const textboxes = activePage.getByRole('textbox');
    const textboxCount = await textboxes.count().catch(() => 0);
    const textboxDebug = [];
    for (let i = 0; i < textboxCount; i += 1) {
      const box = textboxes.nth(i);
      if (!(await box.isVisible().catch(() => false))) continue;
      const meta = await box
        .evaluate((el) => ({
          aria: el.getAttribute('aria-label') || '',
          placeholder: el.getAttribute('placeholder') || '',
          tag: el.tagName,
        }))
        .catch(() => ({ aria: '', placeholder: '', tag: '' }));
      textboxDebug.push(`${meta.tag}:${meta.aria || meta.placeholder || 'unnamed'}`);
    }
    console.log(`[event-pages] ${pageConfig.title} visible textboxes => ${textboxDebug.join(' | ')}`);
    const editableCount = await activePage.locator('[contenteditable="true"]:visible').count().catch(() => 0);
    console.log(`[event-pages] ${pageConfig.title} visible contenteditable => ${editableCount}`);

    if (
      await fillFirstMatchingField(
        [
          activePage.getByRole('textbox', { name: /^heading$|headline|hero title|title/i }).first(),
          activePage.getByLabel(/^heading$|headline|hero title|title/i).first(),
          activePage.locator('input[name*="headline" i], input[name*="heading" i], input[name*="title" i], textarea[name*="heading" i]').first(),
        ],
        pageConfig.heading,
      )
    ) {
      editsApplied += 1;
    }
    if (
      await fillFirstMatchingField(
        [
          activePage.getByRole('textbox', { name: /^subheading$|subtitle|description|body|content|text/i }).first(),
          activePage.getByLabel(/^subheading$|subtitle|description|body|content|text/i).first(),
          activePage.locator('textarea[name*="description" i], textarea[name*="content" i], input[name*="subheading" i], textarea[name*="text" i]').first(),
        ],
        pageConfig.subheading,
      )
    ) {
      editsApplied += 1;
    }
    editsApplied += await applyHeuristicTextboxEdits(activePage, pageConfig);
    editsApplied += await applyHeuristicContentEditableEdits(activePage, pageConfig);
    editsApplied += await applyTinyMceEdits(activePage, pageConfig);

    const saveSectionButton = activePage.getByRole('button', { name: /save section/i }).first();
    if (!isPlanMode && (await saveSectionButton.isVisible().catch(() => false)) && (await saveSectionButton.isEnabled().catch(() => false))) {
      await saveSectionButton.click();
      await activePage.waitForTimeout(500);
    }

    await clickFirstVisible(
      activePage,
      [
        activePage.getByRole('link', { name: /call to action/i }).first(),
        activePage.locator('a:has-text("Call to Action")').first(),
      ],
      3000,
    ).catch(() => false);

    if (
      await fillFirstMatchingField(
        [
          activePage.getByRole('textbox', { name: /button.*text|cta.*text|button label|label/i }).first(),
          activePage.getByLabel(/button.*text|cta.*text|button label|label/i).first(),
          activePage.locator('input[name*="button_text" i], input[name*="cta_text" i], input[name*="buttonlabel" i], input[name*="label" i]').first(),
        ],
        pageConfig.ctaText,
      )
    ) {
      editsApplied += 1;
    }
    if (
      await fillFirstMatchingField(
        [
          activePage.getByRole('textbox', { name: /button.*link|cta.*link|button.*url|url/i }).first(),
          activePage.getByLabel(/button.*link|cta.*link|button.*url|url/i).first(),
          activePage.locator('input[name*="button_link" i], input[name*="cta_link" i], input[name*="url" i]').first(),
        ],
        pageConfig.ctaLink,
      )
    ) {
      editsApplied += 1;
    }

    console.log(`[event-pages] ${pageConfig.title} edits applied:${editsApplied}`);

    const saveButton = activePage
      .locator('button:has-text("Save"), button:has-text("Update"), [role="button"]:has-text("Save"), [role="button"]:has-text("Update")')
      .first();
    const hasGlobalSave = await saveButton.isVisible({ timeout: 3000 }).catch(() => false);
    if (hasGlobalSave && !isPlanMode && (await saveButton.isEnabled().catch(() => false))) {
      await saveButton.click();
      await Promise.race([
        activePage.getByText(/saved|updated|changes saved/i).first().waitFor({ state: 'visible', timeout: 8000 }).catch(() => null),
        activePage.waitForTimeout(1000),
      ]);
    } else if (!hasGlobalSave && !/\/sections\//i.test(activePage.url()) && !/\/blocks\//i.test(activePage.url())) {
      // Some Kajabi editor variants autosave and do not expose a global Save button.
      console.log(`[event-pages] ${pageConfig.title} global save not visible; continuing with autosave-compatible flow.`);
      await activePage.waitForTimeout(900);
    }

    const preview = activePage.frameLocator('iframe').first();
    if (editsApplied > 0) {
      const hasExpectedHeading = await preview
        .getByRole('heading', { name: new RegExp(escapeRegex(pageConfig.title), 'i') })
        .first()
        .isVisible()
        .catch(() => false);
      const hasTemplateHeading = await preview
        .getByRole('heading', { name: /all the tools you need to build a successful online business/i })
        .first()
        .isVisible()
        .catch(() => false);
      if (!hasExpectedHeading && hasTemplateHeading) {
        throw new Error(`Builder preview missing expected heading for ${pageConfig.title}.`);
      }
    } else {
      pagesWithoutEditableControls.push(pageConfig.title);
    }

    await activePage.screenshot({
      path: path.join(artifactsDir, `event-pages-${slugify(pageConfig.title)}-after-save.png`),
      fullPage: true,
    });

    if (/\/sections\//i.test(activePage.url()) || /\/blocks\//i.test(activePage.url())) {
      const backInEditor = activePage.getByRole('button', { name: /back/i }).first();
      if (await backInEditor.isVisible({ timeout: 2000 }).catch(() => false)) {
        await backInEditor.click();
        await activePage.waitForLoadState('domcontentloaded');
      } else {
        await activePage.goto(`${adminBase}/website_pages`, { waitUntil: 'domcontentloaded' });
      }
    } else {
      const backToPages = activePage.getByRole('link', { name: /back to pages/i }).first();
      if (!(await backToPages.isVisible({ timeout: 10000 }).catch(() => false))) {
        throw new Error(`Could not find Back to Pages in builder for ${pageConfig.title}. URL: ${activePage.url()}`);
      }
      await backToPages.click();
    }
    await expect(activePage.getByRole('heading', { name: /^pages$/i })).toBeVisible({ timeout: 15000 });
  }

  if (pagesWithoutEditableControls.length) {
    console.log(`[event-pages] No editable controls detected for: ${pagesWithoutEditableControls.join(', ')}`);
  }
});
