const path = require("path");
const { defineConfig } = require("@playwright/test");

const baseURL = process.env.BOSSKEY_DEMO_BASE_URL || "http://127.0.0.1:8010";
const slowMo = Number(process.env.BOSSKEY_PW_SLOWMO || "50");
const viewport = { width: 1920, height: 1080 };

module.exports = defineConfig({
  testDir: path.join(__dirname, "tests", "e2e"),
  timeout: 360_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  workers: 1,
  reporter: [
    ["list"],
    ["html", { outputFolder: path.join(__dirname, "playwright-report"), open: "never" }],
  ],
  outputDir: path.join(__dirname, "test-results"),
  use: {
    baseURL,
    headless: process.env.BOSSKEY_PW_HEADLESS !== "0",
    trace: "on",
    screenshot: "only-on-failure",
    video: { mode: "on", size: viewport },
    viewport,
    screen: viewport,
    launchOptions: {
      slowMo,
      args: [`--window-size=${viewport.width},${viewport.height}`],
    },
  },
  webServer: {
    command: "powershell -NoProfile -ExecutionPolicy Bypass -File .\\tools\\start-playwright-demo-server.ps1",
    cwd: __dirname,
    url: `${baseURL}/dashboard`,
    reuseExistingServer: false,
    timeout: 180_000,
  },
  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
});
