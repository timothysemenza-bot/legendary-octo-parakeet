import fs from "node:fs/promises";
import path from "node:path";
import readline from "node:readline/promises";
import { stdin as input, stdout as output } from "node:process";
import { chromium } from "@playwright/test";

const cwd = process.cwd();
const defaultBaseUrl = "https://apmp.helpjuice.com/study-guide-v4/foundation-study-guide-version4";
const defaultScopePrefix = "https://apmp.helpjuice.com/";
const dateStamp = new Date().toISOString().slice(0, 10);
const defaultOutputDir = path.join(cwd, "outputs", "generated", `apmp-helpjuice-export-${dateStamp}`);
const defaultProfileDir = path.join(cwd, ".tmp", "apmp-helpjuice-profile");
const defaultMaxPages = 250;

function getArg(flag, fallback = "") {
  const index = process.argv.indexOf(flag);
  if (index === -1 || index === process.argv.length - 1) {
    return fallback;
  }
  return process.argv[index + 1];
}

function hasFlag(flag) {
  return process.argv.includes(flag);
}

function getNumberArg(flag, fallback) {
  const raw = getArg(flag, "");
  if (!raw) {
    return fallback;
  }
  const parsed = Number.parseInt(raw, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "page";
}

async function ensureDir(dirPath) {
  await fs.mkdir(dirPath, { recursive: true });
}

async function waitForEnter(promptText) {
  const rl = readline.createInterface({ input, output });
  try {
    await rl.question(promptText);
  } finally {
    rl.close();
  }
}

function normalizeUrl(rawUrl) {
  try {
    const parsed = new URL(rawUrl);
    parsed.hash = "";
    if (parsed.pathname.endsWith("/") && parsed.pathname !== "/") {
      parsed.pathname = parsed.pathname.replace(/\/+$/, "");
    }
    return parsed.toString();
  } catch {
    return "";
  }
}

function shouldCrawlUrl(rawUrl, scopePrefix) {
  const normalized = normalizeUrl(rawUrl);
  if (!normalized) {
    return false;
  }
  if (!normalized.startsWith(scopePrefix)) {
    return false;
  }

  const blockedPatterns = [
    /\/sign[-_]?(in|out)\b/i,
    /\/login\b/i,
    /\/logout\b/i,
    /\/create-account\b/i,
    /\/cart\b/i,
    /\/checkout\b/i,
  ];

  return !blockedPatterns.some((pattern) => pattern.test(normalized));
}

function getSafeFileStem(rawUrl, index) {
  const parsed = new URL(rawUrl);
  const pathPart = parsed.pathname.split("/").filter(Boolean).join("-");
  const queryPart = parsed.search ? `-${parsed.searchParams.toString().replace(/[^a-z0-9]+/gi, "-")}` : "";
  const base = slugify(`${pathPart}${queryPart}` || `page-${index + 1}`);
  return `${String(index + 1).padStart(3, "0")}-${base}`;
}

async function collectScopedLinks(page, scopePrefix) {
  return page.evaluate((prefix) => {
    const urls = new Set();
    for (const anchor of document.querySelectorAll("a[href]")) {
      const href = anchor.href;
      if (!href.startsWith(prefix)) {
        continue;
      }
      urls.add(href.split("#")[0]);
    }
    return [...urls];
  }, scopePrefix);
}

async function extractPageData(page) {
  return page.evaluate(() => {
    const title = document.title || "";
    const bodyText = document.body?.innerText || "";
    const headings = [...document.querySelectorAll("h1, h2, h3")]
      .map((node) => node.textContent?.trim())
      .filter(Boolean);
    const canonical = document.querySelector("link[rel='canonical']")?.href || "";
    return {
      title,
      bodyText,
      headings,
      canonical,
    };
  });
}

async function main() {
  const baseUrl = getArg("--url", defaultBaseUrl);
  const scopePrefix = getArg("--scope-prefix", defaultScopePrefix);
  const outputDir = getArg("--output-dir", defaultOutputDir);
  const profileDir = getArg("--profile-dir", defaultProfileDir);
  const headless = hasFlag("--headless");
  const maxPages = getNumberArg("--max-pages", defaultMaxPages);

  await ensureDir(outputDir);
  await ensureDir(profileDir);

  const context = await chromium.launchPersistentContext(profileDir, {
    headless,
    viewport: { width: 1440, height: 1024 },
  });

  try {
    const page = context.pages()[0] ?? (await context.newPage());
    await page.goto(baseUrl, { waitUntil: "domcontentloaded" });

    console.log("");
    console.log("APMP Helpjuice export");
    console.log(`Base URL: ${baseUrl}`);
    console.log(`Scope prefix: ${scopePrefix}`);
    console.log(`Max pages: ${maxPages}`);
    console.log(`Output directory: ${outputDir}`);
    console.log("");
    console.log("1. Log in in the opened browser window if needed.");
    console.log("2. Navigate to the broadest APMP Helpjuice index page you want to start from.");
    console.log("3. Expand collapsed sections and scroll if links are lazy-loaded.");
    console.log("4. Return here and press Enter to begin export.");
    console.log("");

    await waitForEnter("Press Enter after the logged-in study guide page is visible...");

    await page.waitForLoadState("domcontentloaded");
    const startUrl = normalizeUrl(page.url());
    if (!shouldCrawlUrl(startUrl, scopePrefix)) {
      throw new Error(`The current page is outside the crawl scope. Current page: ${startUrl}`);
    }

    const manifest = [];
    const pagesDir = path.join(outputDir, "pages");
    await ensureDir(pagesDir);

    const queue = [startUrl];
    const seen = new Set();
    const discoveredFrom = new Map([[startUrl, "manual-start"]]);

    console.log(`Starting recursive crawl from ${startUrl}`);

    while (queue.length > 0 && manifest.length < maxPages) {
      const url = queue.shift();
      if (!url || seen.has(url)) {
        continue;
      }
      seen.add(url);

      console.log(`[${manifest.length + 1}] ${url}`);
      await page.goto(url, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(500);

      const html = await page.content();
      const extracted = await extractPageData(page);
      const links = await collectScopedLinks(page, scopePrefix);

      for (const discoveredUrl of links) {
        const normalized = normalizeUrl(discoveredUrl);
        if (!shouldCrawlUrl(normalized, scopePrefix)) {
          continue;
        }
        if (!seen.has(normalized) && !queue.includes(normalized)) {
          queue.push(normalized);
          discoveredFrom.set(normalized, url);
        }
      }

      const safeName = getSafeFileStem(url, manifest.length);

      const htmlPath = path.join(pagesDir, `${safeName}.html`);
      const jsonPath = path.join(pagesDir, `${safeName}.json`);

      await fs.writeFile(htmlPath, html, "utf8");
      await fs.writeFile(
        jsonPath,
        JSON.stringify(
          {
            url,
            exportedAt: new Date().toISOString(),
            discoveredFrom: discoveredFrom.get(url) ?? "",
            ...extracted,
          },
          null,
          2
        ),
        "utf8"
      );

      manifest.push({
        index: manifest.length + 1,
        url,
        title: extracted.title,
        discoveredFrom: discoveredFrom.get(url) ?? "",
        linksDiscovered: links.length,
        file: path.relative(outputDir, htmlPath).replaceAll("\\", "/"),
        metaFile: path.relative(outputDir, jsonPath).replaceAll("\\", "/"),
      });
    }

    if (manifest.length === 0) {
      throw new Error("No pages were exported. Make sure you started from a logged-in page inside the requested scope.");
    }

    const manifestPath = path.join(outputDir, "manifest.json");
    await fs.writeFile(
      manifestPath,
      JSON.stringify(
        {
          baseUrl,
          startUrl,
          scopePrefix,
          maxPages,
          exportedAt: new Date().toISOString(),
          pageCount: manifest.length,
          queuedButNotVisited: queue.length,
          pages: manifest,
        },
        null,
        2
      ),
      "utf8"
    );

    console.log("");
    console.log(`Export complete. Manifest: ${manifestPath}`);
    if (queue.length > 0) {
      console.log(`Stopped after ${manifest.length} pages because the max page limit was reached. Increase --max-pages to continue.`);
    }
    console.log("Keep the export local. Do not redistribute member-only APMP content.");
  } finally {
    await context.close();
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
