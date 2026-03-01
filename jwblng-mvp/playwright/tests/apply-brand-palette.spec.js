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

async function fillFirstColorField(activePage, labelRegex, hex) {
  const candidates = [
    activePage.getByRole('textbox', { name: labelRegex }).first(),
    activePage.getByLabel(labelRegex).first(),
    activePage.locator('input[type="text"][name*="color" i]').filter({ hasText: '' }).first(),
  ];
  for (const c of candidates) {
    if (await c.isVisible().catch(() => false)) {
      const ok = await c.fill(hex).then(() => true).catch(() => false);
      if (ok) {
        await c.press('Enter').catch(() => {});
        return true;
      }
    }
  }
  return false;
}

async function applyPaletteToStyleGuideInputs(activePage, palette) {
  const paletteRing = [palette.primary, palette.dark, palette.accent, palette.soft, palette.text, palette.primary, palette.accent, palette.dark];
  return activePage
    .evaluate((ring) => {
      const isVisible = (el) => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && window.getComputedStyle(el).visibility !== 'hidden';
      };
      const isHex = (v) => /^#[0-9a-f]{6}$/i.test((v || '').trim());
      const inputs = [...document.querySelectorAll('input')]
        .filter((el) => {
          const name = (el.getAttribute('name') || '').toLowerCase();
          const aria = (el.getAttribute('aria-label') || '').toLowerCase();
          const val = (el.value || '').trim();
          return isHex(val) || name.includes('color') || aria.includes('color');
        });
      let changed = 0;
      for (let i = 0; i < inputs.length && i < ring.length; i += 1) {
        const el = inputs[i];
        const next = ring[i];
        if (!next) continue;
        el.value = next;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        changed += 1;
      }
      return changed;
    }, paletteRing)
    .catch(() => 0);
}

async function applyPaletteViaColorRows(activePage, palette) {
  const targets = [
    { row: /^primary$/i, hex: palette.primary },
    { row: /^text$/i, hex: palette.dark },
    { row: /^body$/i, hex: palette.text },
    { row: /^secondary$/i, hex: palette.accent },
    { row: /^placeholder$/i, hex: palette.accent },
    { row: /^background$/i, hex: palette.soft },
  ];
  let changed = 0;
  for (const t of targets) {
    const row = activePage.getByText(t.row).first();
    if (!(await row.isVisible().catch(() => false))) continue;
    await row.click().catch(() => {});
    await activePage.waitForTimeout(250);
    const colorInput = activePage
      .locator('input[value^="#"]:visible, input[aria-label*="hex" i]:visible, input[name*="color" i]:visible')
      .last();
    if (await colorInput.isVisible().catch(() => false)) {
      const before = await colorInput.inputValue().catch(() => '');
      const ok = await colorInput.fill(t.hex).then(() => true).catch(() => false);
      if (ok) {
        await colorInput.press('Enter').catch(() => {});
        const after = await colorInput.inputValue().catch(() => '');
        if (before !== after) changed += 1;
      }
    }
  }
  return changed;
}

async function applyPaletteViaSwatchPicker(activePage, palette) {
  const targets = [
    { row: /^primary$/i, hex: palette.primary },
    { row: /^text$/i, hex: palette.dark },
    { row: /^body$/i, hex: palette.text },
    { row: /^secondary$/i, hex: palette.accent },
    { row: /^background$/i, hex: palette.soft },
  ];
  let changed = 0;
  for (const t of targets) {
    const rowText = activePage.getByText(t.row).first();
    if (!(await rowText.isVisible().catch(() => false))) continue;
    await rowText.click().catch(() => {});
    await activePage.waitForTimeout(250);

    const hexInput = activePage
      .locator('input[placeholder*="#" i]:visible, input[value^="#"]:visible, input[aria-label*="hex" i]:visible')
      .first();
    if (await hexInput.isVisible().catch(() => false)) {
      const ok = await hexInput.fill(t.hex).then(() => true).catch(() => false);
      if (ok) {
        await hexInput.press('Enter').catch(() => {});
        changed += 1;
      }
      continue;
    }

    const anyTextbox = activePage.getByRole('textbox').filter({ hasText: '' }).first();
    if (await anyTextbox.isVisible().catch(() => false)) {
      const ok = await anyTextbox.fill(t.hex).then(() => true).catch(() => false);
      if (ok) {
        await anyTextbox.press('Enter').catch(() => {});
        changed += 1;
      }
    }
  }
  return changed;
}

test('apply JWBLNG brand palette in Kajabi theme settings (write-gated)', async ({ page, context }) => {
  test.setTimeout(180000);
  const runMode = env('JWBLNG_RUN_MODE', 'apply').toLowerCase();
  const isPlanMode = runMode === 'plan';
  test.skip(!isPlanMode && !writesAllowed(), 'Set ALLOW_KAJABI_WRITES=1 or run JWBLNG_RUN_MODE=plan.');

  const adminBase = adminBaseUrl();
  const artifactsDir = ensureArtifactsDir();
  const homepageName = env('JWBLNG_HOMEPAGE_NAME', 'Home').trim();

  const palette = {
    primary: env('JWBLNG_BRAND_PRIMARY', '#833D87').trim(),
    dark: env('JWBLNG_BRAND_DARK', '#722C7B').trim(),
    accent: env('JWBLNG_BRAND_ACCENT', '#BFA4C6').trim(),
    soft: env('JWBLNG_BRAND_SOFT', '#EDE2F3').trim(),
    text: env('JWBLNG_BRAND_TEXT', '#2F1E36').trim(),
  };

  await page.goto(`${adminBase}/dashboard`, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');
  const activePage = await getActivePage(page, context, 'Active Kajabi admin page is closed before brand palette apply.');

  await openWebsitePages(activePage);
  await openBuilderForPage(activePage, homepageName);

  const previewHref =
    (await activePage.getByRole('link', { name: /^preview$/i }).first().getAttribute('href').catch(() => '')) || '';
  console.log(`[brand-palette] Preview URL: ${previewHref}`);

  await clickFirstVisible(
    activePage,
    [
      activePage.getByRole('tab', { name: /settings/i }).first(),
      activePage.locator('[role="tab"]:has-text("Settings")').first(),
    ],
    4000,
  );

  await clickFirstVisible(
    activePage,
    [
      activePage.getByRole('button', { name: /colors/i }).first(),
      activePage.getByRole('link', { name: /colors/i }).first(),
      activePage.locator('button:has-text("Colors"), a:has-text("Colors"), div:has-text("Colors")').first(),
    ],
    3000,
  ).catch(() => false);

  const styleGuideLink = activePage.getByRole('link', { name: /style guide/i }).first();
  if (await styleGuideLink.isVisible({ timeout: 3000 }).catch(() => false)) {
    await styleGuideLink.click();
    await activePage.waitForLoadState('domcontentloaded');
    await activePage.waitForTimeout(700);
  }

  if (isPlanMode) {
    await activePage.screenshot({
      path: path.join(artifactsDir, 'brand-palette-plan.png'),
      fullPage: true,
    });
    return;
  }

  let changed = 0;
  const colorInputStats = await activePage
    .evaluate(() => {
      const all = [...document.querySelectorAll('input')].filter((el) => {
        const name = (el.getAttribute('name') || '').toLowerCase();
        const aria = (el.getAttribute('aria-label') || '').toLowerCase();
        const val = (el.value || '').trim();
        return /^#[0-9a-f]{3,8}$/i.test(val) || name.includes('color') || aria.includes('color');
      });
      const visible = all.filter((el) => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden';
      });
      return { all: all.length, visible: visible.length };
    })
    .catch(() => ({ all: 0, visible: 0 }));
  console.log(`[brand-palette] color-inputs all:${colorInputStats.all} visible:${colorInputStats.visible}`);

  if (await fillFirstColorField(activePage, /primary|brand primary|button|accent/i, palette.primary)) changed += 1;
  if (await fillFirstColorField(activePage, /secondary|link|hover|dark/i, palette.dark)) changed += 1;
  if (await fillFirstColorField(activePage, /accent|highlight/i, palette.accent)) changed += 1;
  if (await fillFirstColorField(activePage, /background|surface|canvas/i, palette.soft)) changed += 1;
  if (await fillFirstColorField(activePage, /text|body|paragraph|heading/i, palette.text)) changed += 1;
  if (changed === 0) {
    changed += await applyPaletteViaColorRows(activePage, palette);
  }
  if (changed === 0) {
    changed += await applyPaletteViaSwatchPicker(activePage, palette);
  }
  if (changed === 0) {
    changed += await applyPaletteToStyleGuideInputs(activePage, palette);
  }

  const saveButton = activePage
    .locator('button:has-text("Save"), button:has-text("Update"), [role="button"]:has-text("Save"), [role="button"]:has-text("Update")')
    .first();
  if (await saveButton.isVisible().catch(() => false)) {
    if (await saveButton.isEnabled().catch(() => false)) {
      await saveButton.click();
      await activePage.waitForTimeout(1000);
    }
  }

  await activePage.screenshot({
    path: path.join(artifactsDir, 'brand-palette-after.png'),
    fullPage: true,
  });

  console.log(`[brand-palette] changed:${changed} primary:${palette.primary} dark:${palette.dark} accent:${palette.accent}`);
  if (changed === 0) {
    throw new Error('No theme color fields were matched in Settings. Need theme-specific color selectors.');
  }
});
