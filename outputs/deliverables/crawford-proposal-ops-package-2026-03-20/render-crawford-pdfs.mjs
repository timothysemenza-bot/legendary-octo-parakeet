import { chromium } from "playwright";
import path from "node:path";
import { pathToFileURL } from "node:url";

const baseDir = path.resolve("workspace/deliverables/crawford-proposal-ops-package-2026-03-20");

const jobs = [
  {
    html: "crawford-proposal-ops-modernization-branded.html",
    pdf: "crawford-proposal-ops-modernization-branded.pdf",
  },
  {
    html: "crawford-executive-summary-branded.html",
    pdf: "crawford-executive-summary-branded.pdf",
  },
];

const browser = await chromium.launch({ headless: true });

try {
  for (const job of jobs) {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(path.join(baseDir, job.html)).href, {
      waitUntil: "networkidle",
    });
    await page.pdf({
      path: path.join(baseDir, job.pdf),
      format: "Letter",
      printBackground: true,
      margin: {
        top: "0.35in",
        right: "0.35in",
        bottom: "0.35in",
        left: "0.35in",
      },
      preferCSSPageSize: true,
    });
    await page.close();
    console.log(`rendered ${job.pdf}`);
  }
} finally {
  await browser.close();
}
