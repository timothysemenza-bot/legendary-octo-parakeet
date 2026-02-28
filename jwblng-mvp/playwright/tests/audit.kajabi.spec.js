const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const { adminBaseUrl, ensureArtifactsDir } = require('../utils/env');

test('audit current Kajabi surfaces (read-only)', async ({ page }) => {
  const adminBase = adminBaseUrl();
  const artifactsDir = ensureArtifactsDir();

  const targets = [
    { id: 'admin_dashboard', candidates: [`${adminBase}/dashboard`] },
    { id: 'admin_website_pages', candidates: [`${adminBase}/website_pages`, `${adminBase}/landing_pages`, `${adminBase}/website/pages`] },
    { id: 'admin_contacts', candidates: [`${adminBase}/contacts`, `${adminBase}/people`] },
    { id: 'admin_events', candidates: [`${adminBase}/events`] },
    { id: 'admin_marketing', candidates: [`${adminBase}/email_campaigns`, `${adminBase}/marketing/email-campaigns`] },
  ];

  const findings = [];

  for (const target of targets) {
    let chosenUrl = null;
    let chosenStatus = null;

    for (const candidate of target.candidates) {
      const response = await page.goto(candidate, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(800);

      const status = response ? response.status() : null;
      const title = await page.title();
      const isNotFound = status === 404 || /doesn't exist|404/i.test(title);

      if (!isNotFound) {
        chosenUrl = candidate;
        chosenStatus = status;
        break;
      }

      if (!chosenUrl) {
        chosenUrl = candidate;
        chosenStatus = status;
      }
    }

    findings.push({
      id: target.id,
      url: chosenUrl,
      status: chosenStatus,
      title: await page.title(),
      finalUrl: page.url(),
    });

    await page.screenshot({
      path: path.join(artifactsDir, `${target.id}.png`),
      fullPage: true,
    });
  }

  const reportPath = path.join(artifactsDir, 'kajabi-audit.json');
  fs.writeFileSync(reportPath, JSON.stringify(findings, null, 2));

  expect(findings.length).toBe(targets.length);
  expect(findings.some((row) => row.finalUrl.includes('/login'))).toBeFalsy();
});
