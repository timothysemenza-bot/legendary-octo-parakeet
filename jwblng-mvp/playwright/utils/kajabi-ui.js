async function getActivePage(page, context, closedErrorMessage) {
  const activePage = context.pages().at(-1) || page;
  if (activePage.isClosed()) {
    throw new Error(closedErrorMessage || 'Active Kajabi admin page is closed before actions.');
  }
  return activePage;
}

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

async function fillFirstEditable(candidates, value) {
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

async function chooseTimezone(page, value) {
  if (!value) return false;
  const timezoneCombobox = page.getByRole('combobox', { name: /time.?zone|zone/i }).first();
  if (await timezoneCombobox.isVisible().catch(() => false)) {
    const preferred = new RegExp(value, 'i');
    const optionByLabel = page.getByRole('option', { name: preferred }).first();
    if (await optionByLabel.isVisible({ timeout: 2000 }).catch(() => false)) {
      const optionValue = await optionByLabel.getAttribute('value');
      if (optionValue) {
        await timezoneCombobox.selectOption(optionValue);
        return true;
      }
    }

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
    const timezoneOption = page.getByRole('option', { name: new RegExp(value, 'i') }).first();
    if (await timezoneOption.isVisible({ timeout: 4000 }).catch(() => false)) {
      await timezoneOption.click();
      return true;
    }
    return false;
  }

  const timezoneInputs = [
    page.getByLabel(/time.?zone|zone/i).first(),
    page.locator('input[name*="zone" i], input[placeholder*="zone" i], input[placeholder*="eastern" i]').first(),
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

function escapeRegex(text) {
  return String(text || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

async function findContactRowByEmail(page, email, timeoutMs = 10000) {
  const escapedEmail = escapeRegex(email);
  const row = page.getByRole('row', { name: new RegExp(escapedEmail, 'i') }).first();
  const visible = await row.isVisible({ timeout: timeoutMs }).catch(() => false);
  return visible ? row : null;
}

async function openContactDetailFromRow(page, contactRow) {
  const openContactCandidates = [
    contactRow.getByRole('button', { name: new RegExp('^(?!.*options).+', 'i') }).first(),
    contactRow.getByRole('link', { name: new RegExp('^(?!.*options).+', 'i') }).first(),
    contactRow.locator('button:not(:has-text("Options"))').first(),
  ];

  for (const candidate of openContactCandidates) {
    if (await candidate.isVisible().catch(() => false)) {
      await candidate.click();
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(800);
      return true;
    }
  }

  if (await contactRow.isVisible().catch(() => false)) {
    await contactRow.click();
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(800);
    return true;
  }

  return false;
}

async function applyTagToOpenContact(page, approvalTag) {
  const escapedTag = escapeRegex(approvalTag);
  const existingTag = page.locator(`text=/^\\s*${escapedTag}\\s*$/i`).first();
  if (await existingTag.isVisible().catch(() => false)) {
    return { success: true, saved: false, alreadyPresent: true };
  }

  const detailRoots = [
    page.locator('[role="dialog"]:visible').first(),
    page.locator('aside:visible').first(),
    page.locator('main:visible').first(),
  ];

  let openedTagControl = false;
  let chosenRoot = null;

  for (const root of detailRoots) {
    if (!(await root.isVisible().catch(() => false))) continue;
    const controls = [
      root.getByRole('button', { name: /add tag|tags/i }).first(),
      root.getByRole('link', { name: /^add tag$/i }).first(),
      root.locator('a[href="#add-tag"]').first(),
      root.locator('button:has-text("Add Tag"), button:has-text("Tags")').first(),
      root.locator('a:has-text("Add tag")').first(),
    ];
    for (const control of controls) {
      if (await control.isVisible().catch(() => false)) {
        await control.click();
        openedTagControl = true;
        chosenRoot = root;
        break;
      }
    }
    if (openedTagControl) break;
  }

  if (!openedTagControl) {
    // Fallback: drawer action links can render outside expected root semantics.
    const globalAddTagControl = page
      .locator('a[href="#add-tag"]:visible, a:has-text("Add tag"):visible, button:has-text("Add tag"):visible')
      .first();
    if (await globalAddTagControl.isVisible({ timeout: 2000 }).catch(() => false)) {
      await globalAddTagControl.click();
      openedTagControl = true;
    }
  }

  if (!openedTagControl) {
    return { success: false, reason: 'tag_control_not_found' };
  }

  // Tag picker often opens in dialog; fall back to chosen root.
  const inputScopes = [
    page.locator('[role="dialog"]:visible').first(),
    chosenRoot || page.locator('main:visible').first(),
  ];

  let tagInput = null;
  for (const scope of inputScopes) {
    if (!(await scope.isVisible().catch(() => false))) continue;
    const candidates = [
      scope.getByRole('combobox', { name: /tag/i }).first(),
      scope.getByRole('textbox', { name: /tag/i }).first(),
      scope.locator('input[placeholder*="tag" i], input[name*="tag" i]').first(),
    ];
    for (const candidate of candidates) {
      if (await candidate.isVisible({ timeout: 4000 }).catch(() => false)) {
        tagInput = candidate;
        break;
      }
    }
    if (tagInput) break;
  }

  if (!tagInput) {
    // Kajabi drawer variant: "Add a Tag" modal + "Select tags" picker (no direct text input).
    const selectTagsButton = page
      .locator('button:has-text("Select tags"):visible, [role="button"]:has-text("Select tags"):visible')
      .first();
    if (await selectTagsButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await selectTagsButton.click();
      await page.waitForTimeout(400);

      const option = page.getByRole('option', { name: new RegExp(escapedTag, 'i') }).first();
      if (await option.isVisible({ timeout: 3000 }).catch(() => false)) {
        await option.click();
      } else {
        const checkbox = page.getByRole('checkbox', { name: new RegExp(escapedTag, 'i') }).first();
        if (await checkbox.isVisible({ timeout: 2000 }).catch(() => false)) {
          await checkbox.check().catch(async () => {
            await checkbox.click();
          });
        } else {
          return { success: false, reason: 'tag_input_not_found' };
        }
      }

      const modalSave = page
        .locator('[role="dialog"] button:has-text("Save"):visible, button:has-text("Save"):visible')
        .first();
      if (await modalSave.isVisible({ timeout: 2000 }).catch(() => false)) {
        if (await modalSave.isEnabled().catch(() => false)) {
          await modalSave.click();
          return { success: true, saved: true };
        }
        // If still disabled, tag may already be selected by default.
        return { success: true, saved: false, alreadyPresent: true };
      }

      return { success: true, saved: false };
    }

    return { success: false, reason: 'tag_input_not_found' };
  }

  await tagInput.fill(approvalTag);
  await page.waitForTimeout(500);

  const tagOption = page.getByRole('option', { name: new RegExp(escapeRegex(approvalTag), 'i') }).first();
  if (await tagOption.isVisible().catch(() => false)) {
    await tagOption.click();
  } else {
    await tagInput.press('Enter');
  }

  const saved = await clickFirstVisible(
    page,
    [page.getByRole('button', { name: /save|update|apply/i }).first()],
    2000,
  ).catch(() => false);

  return { success: true, saved };
}

module.exports = {
  getActivePage,
  clickFirstVisible,
  fillFirstEditable,
  normalizeOccursAt,
  chooseTimezone,
  escapeRegex,
  findContactRowByEmail,
  openContactDetailFromRow,
  applyTagToOpenContact,
};
