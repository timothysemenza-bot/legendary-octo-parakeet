require('dotenv').config();
const { defineConfig, devices } = require('@playwright/test');
const path = require('path');

module.exports = defineConfig({
  testDir: path.join(__dirname, 'tests'),
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  retries: 0,
  workers: 1,
  reporter: [['list'], ['html', { outputFolder: path.join(__dirname, 'playwright-report') }]],
  outputDir: path.join(__dirname, 'test-results'),
  use: {
    headless: process.env.HEADLESS === '1',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    storageState: process.env.KAJABI_STORAGE_STATE || path.join(__dirname, '.auth', 'kajabi-admin.json'),
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
