import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { operatorWorkspaceStateSchema } from "../src/domain/operatorWorkspace";
import {
  buildPackagedPromotedConceptSheet,
  renderShareableConceptSheetHtml,
  renderWorkingStoryBriefMarkdown,
} from "../src/deliverables/promotedConceptSheetPackaging";

interface CliOptions {
  statePath: string;
  slug: string | null;
  title: string | null;
  date: string | null;
  deliverablesRoot: string | null;
  skipPdf: boolean;
}

interface BundleManifest {
  createdAt: string;
  bundleRoot: string;
  bundleSlug: string;
  bundleTitle: string;
  sourceStatePath: string;
  promotedVariantName: string;
  exportedFiles: {
    html: string;
    shareableHtml: string;
    pdf: string | null;
    briefMarkdown: string;
    packagePayload: string;
    workspaceState: string;
    opportunity: string;
  };
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-{2,}/g, "-");
}

function parseArgs(argv: string[]): CliOptions {
  const options: CliOptions = {
    statePath: "inputs/demo-workspace-state.json",
    slug: null,
    title: null,
    date: null,
    deliverablesRoot: null,
    skipPdf: false,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const nextArg = argv[index + 1];

    if (arg === "--state" && nextArg) {
      options.statePath = nextArg;
      index += 1;
      continue;
    }

    if (arg === "--slug" && nextArg) {
      options.slug = nextArg;
      index += 1;
      continue;
    }

    if (arg === "--title" && nextArg) {
      options.title = nextArg;
      index += 1;
      continue;
    }

    if (arg === "--date" && nextArg) {
      options.date = nextArg;
      index += 1;
      continue;
    }

    if (arg === "--deliverables-root" && nextArg) {
      options.deliverablesRoot = nextArg;
      index += 1;
      continue;
    }

    if (arg === "--skip-pdf") {
      options.skipPdf = true;
    }
  }

  return options;
}

function findAncestor(
  startDirectory: string,
  matcher: (candidate: string) => boolean,
): string {
  let currentDirectory = startDirectory;

  while (true) {
    if (matcher(currentDirectory)) {
      return currentDirectory;
    }

    const parentDirectory = dirname(currentDirectory);
    if (parentDirectory === currentDirectory) {
      throw new Error(`Unable to resolve required project path from ${startDirectory}.`);
    }

    currentDirectory = parentDirectory;
  }
}

function getDateStamp(explicitDate: string | null): string {
  if (explicitDate) {
    return explicitDate;
  }

  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/New_York",
  }).format(new Date());
}

function toAbsolutePath(projectRoot: string, candidatePath: string): string {
  return resolve(projectRoot, candidatePath);
}

function createBundleRoot(
  repoRoot: string,
  bundleSlug: string,
  bundleTitle: string,
  dateStamp: string,
  deliverablesRoot: string,
): string {
  const bootstrapScript = join(repoRoot, "scripts", "new-deliverable-bundle.ps1");
  const bootstrap = spawnSync(
    "powershell",
    [
      "-NoLogo",
      "-NoProfile",
      "-ExecutionPolicy",
      "Bypass",
      "-File",
      bootstrapScript,
      "-Slug",
      bundleSlug,
      "-Title",
      bundleTitle,
      "-Date",
      dateStamp,
      "-DeliverablesRoot",
      deliverablesRoot,
    ],
    {
      cwd: repoRoot,
      encoding: "utf8",
    },
  );

  if (bootstrap.status !== 0) {
    throw new Error(
      bootstrap.stderr || bootstrap.stdout || "Failed to create the deliverable bundle scaffold.",
    );
  }

  const match = bootstrap.stdout.match(/Created deliverable bundle at (.+)$/m);

  if (!match) {
    throw new Error(`Unable to read bundle path from bootstrap output: ${bootstrap.stdout}`);
  }

  return match[1].trim();
}

function selectBrowserExecutable(): string | null {
  const candidates = [
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
  ];

  return candidates.find((candidate) => existsSync(candidate)) ?? null;
}

async function createPdfFromHtml(
  repoRoot: string,
  htmlPath: string,
  pdfPath: string,
): Promise<void> {
  const browserExecutable = selectBrowserExecutable();

  if (!browserExecutable) {
    throw new Error("No local Chrome or Edge executable was found for PDF export.");
  }

  const playwrightModulePath = join(
    repoRoot,
    "node_modules",
    "playwright",
    "index.mjs",
  );

  if (!existsSync(playwrightModulePath)) {
    const browserProfileDirectory = join(
      repoRoot,
      "outputs",
      "scratch",
      "browser-pdf-profile",
    );
    await mkdir(browserProfileDirectory, { recursive: true });

    const exportProcess = spawnSync(
      browserExecutable,
      [
        "--headless=new",
        `--user-data-dir=${browserProfileDirectory}`,
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-sync",
        "--no-pdf-header-footer",
        `--print-to-pdf=${pdfPath}`,
        pathToFileURL(htmlPath).href,
      ],
      {
        cwd: repoRoot,
        encoding: "utf8",
      },
    );

    if (exportProcess.status !== 0) {
      throw new Error(
        exportProcess.stderr ||
          exportProcess.stdout ||
          `Browser PDF export failed for ${htmlPath}.`,
      );
    }

    await rm(browserProfileDirectory, { recursive: true, force: true });

    return;
  }

  const playwrightModule = (await import(
    pathToFileURL(playwrightModulePath).href
  )) as {
    chromium: {
      launch(options: {
        executablePath: string;
        headless: boolean;
      }): Promise<{
        newPage(): Promise<{
          goto(url: string, options: { waitUntil: "networkidle" }): Promise<void>;
          emulateMedia(options: { media: "screen" }): Promise<void>;
          pdf(options: {
            path: string;
            format: "Letter";
            printBackground: boolean;
            margin: {
              top: string;
              right: string;
              bottom: string;
              left: string;
            };
          }): Promise<void>;
        }>;
        close(): Promise<void>;
      }>;
    };
  };

  const browser = await playwrightModule.chromium.launch({
    executablePath: browserExecutable,
    headless: true,
  });

  try {
    const page = await browser.newPage();
    await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "networkidle" });
    await page.emulateMedia({ media: "screen" });
    await page.pdf({
      path: pdfPath,
      format: "Letter",
      printBackground: true,
      margin: {
        top: "0.5in",
        right: "0.5in",
        bottom: "0.5in",
        left: "0.5in",
      },
    });
  } finally {
    await browser.close();
  }
}

function buildBundleReadme(manifest: BundleManifest): string {
  return `# ${manifest.bundleTitle}

Date: ${manifest.createdAt}

## Contents

- \`source/workspace-state.json\`: structured workspace state used to assemble the package
- \`source/opportunity.json\`: standalone opportunity input for the packaged pursuit
- \`source/package-payload.json\`: resolved promoted concept, snapshot summary, and supporting data
- \`source/working-story-brief.md\`: internal working-story memo used to shape the concept
- \`export/${manifest.exportedFiles.html}\`: default shareable HTML entry point
- \`export/${manifest.exportedFiles.shareableHtml}\`: named HTML concept sheet handoff
${manifest.exportedFiles.pdf ? `- \`export/${manifest.exportedFiles.pdf}\`: portable PDF fallback generated from the shareable HTML` : "- PDF fallback was skipped for this package run"}

## Handoff Notes

- Promoted variant: ${manifest.promotedVariantName}
- Source state: ${manifest.sourceStatePath}
- The HTML handoff is the primary shareable artifact.
- The PDF is the portable fallback for email, print, or attachment workflows.

## Verification

- Package bundle created under \`${manifest.bundleRoot}\`
- HTML export written successfully
- Deliverable scaffold created with \`scripts/new-deliverable-bundle.ps1\`
${manifest.exportedFiles.pdf ? "- PDF export generated with Playwright using a locally installed browser" : "- PDF export intentionally skipped"}

## Assumptions

- This package was assembled from structured pursuit state, not a live browser session dump.
- Internal strategy notes live in \`source/\`; only \`export/\` is intended for broad sharing.
`;
}

async function main(): Promise<void> {
  const options = parseArgs(process.argv.slice(2));
  const scriptDirectory = dirname(fileURLToPath(import.meta.url));
  const projectRoot = findAncestor(scriptDirectory, (candidate) =>
    existsSync(join(candidate, "package.json")),
  );
  const repoRoot = findAncestor(projectRoot, (candidate) =>
    existsSync(join(candidate, "outputs")) && existsSync(join(candidate, ".agents")),
  );
  const sourceStatePath = toAbsolutePath(projectRoot, options.statePath);
  const rawState = await readFile(sourceStatePath, "utf8");
  const workspaceState = operatorWorkspaceStateSchema.parse(JSON.parse(rawState));
  const packagedConceptSheet = buildPackagedPromotedConceptSheet(workspaceState);
  const dateStamp = getDateStamp(options.date);
  const bundleSlug = slugify(options.slug ?? packagedConceptSheet.bundleSlug);
  const bundleTitle = options.title ?? packagedConceptSheet.bundleTitle;
  const deliverablesRoot = options.deliverablesRoot
    ? resolve(projectRoot, options.deliverablesRoot)
    : join(repoRoot, "outputs", "deliverables");
  const bundleRoot = createBundleRoot(
    repoRoot,
    bundleSlug,
    bundleTitle,
    dateStamp,
    deliverablesRoot,
  );
  const sourceDirectory = join(bundleRoot, "source");
  const exportDirectory = join(bundleRoot, "export");
  const htmlFileName = "index.html";
  const shareableHtmlFileName = `${bundleSlug}.html`;
  const pdfFileName = `${bundleSlug}.pdf`;
  const htmlPath = join(exportDirectory, htmlFileName);
  const shareableHtmlPath = join(exportDirectory, shareableHtmlFileName);
  const pdfPath = join(exportDirectory, pdfFileName);
  const workingStoryPath = join(sourceDirectory, "working-story-brief.md");
  const packagePayloadPath = join(sourceDirectory, "package-payload.json");
  const workspaceStatePath = join(sourceDirectory, "workspace-state.json");
  const opportunityPath = join(sourceDirectory, "opportunity.json");

  await mkdir(sourceDirectory, { recursive: true });
  await mkdir(exportDirectory, { recursive: true });

  await writeFile(
    workspaceStatePath,
    `${JSON.stringify(workspaceState, null, 2)}\n`,
    "utf8",
  );
  await writeFile(
    opportunityPath,
    `${JSON.stringify(packagedConceptSheet.opportunity, null, 2)}\n`,
    "utf8",
  );
  await writeFile(
    packagePayloadPath,
    `${JSON.stringify(packagedConceptSheet, null, 2)}\n`,
    "utf8",
  );
  await writeFile(
    workingStoryPath,
    renderWorkingStoryBriefMarkdown(packagedConceptSheet),
    "utf8",
  );
  await writeFile(
    htmlPath,
    renderShareableConceptSheetHtml(packagedConceptSheet),
    "utf8",
  );
  await writeFile(
    shareableHtmlPath,
    renderShareableConceptSheetHtml(packagedConceptSheet),
    "utf8",
  );

  if (!options.skipPdf) {
    await createPdfFromHtml(repoRoot, htmlPath, pdfPath);
  }

  const manifest: BundleManifest = {
    createdAt: packagedConceptSheet.generatedAt,
    bundleRoot,
    bundleSlug,
    bundleTitle,
    sourceStatePath,
    promotedVariantName: packagedConceptSheet.promotedVariant.name,
    exportedFiles: {
      html: htmlFileName,
      shareableHtml: shareableHtmlFileName,
      pdf: options.skipPdf ? null : pdfFileName,
      briefMarkdown: "working-story-brief.md",
      packagePayload: "package-payload.json",
      workspaceState: "workspace-state.json",
      opportunity: "opportunity.json",
    },
  };

  await writeFile(join(bundleRoot, "README.md"), buildBundleReadme(manifest), "utf8");

  process.stdout.write(
    [
      `Created deliverable bundle: ${bundleRoot}`,
      `Source state: ${sourceStatePath}`,
      `HTML export: ${htmlPath}`,
      `Named HTML export: ${shareableHtmlPath}`,
      options.skipPdf ? "PDF export skipped." : `PDF export: ${pdfPath}`,
    ].join("\n"),
  );
}

main().catch((error: unknown) => {
  const message =
    error instanceof Error ? error.stack ?? error.message : String(error);
  process.stderr.write(`${message}\n`);
  process.exitCode = 1;
});
