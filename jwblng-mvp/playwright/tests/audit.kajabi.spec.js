const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');
const { requireEnv, ensureArtifactsDir } = require('../utils/env');

test('audit current Kajabi surfaces (read-only)', async ({ page }) => {
  const baseUrl = requireEnv('KAJABI_BASE_URL');
  const artifactsDir = ensureArtifactsDir();

  const targets = [
    { id: 'admin_dashboard', url: `${baseUrl}/admin/dashboard` },
    { id: 'admin_website_pages', url: `${baseUrl}/admin/website/pages` },
    { id: 'admin_people', url: `${baseUrl}/admin/people` },
    { id: 'admin_events', url: `${baseUrl}/admin/events` },
    { id: 'admin_marketing', url: `${baseUrl}/admin/marketing/email-campaigns` },
  ];

  const findings = [];

  for (const target of targets) {
    const response = await page.goto(target.url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);

    findings.push({
      id: target.id,
      url: target.url,
      status: response ? response.status() : null,
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
