const fs = require("fs");
const path = require("path");

const REQUIRED_LIBRARY_KEYS = ["industryGraphics", "geography", "serviceLevel", "siteType", "risk", "coverage", "capabilities"];
const FIELD_KEYS = ["summary", "description", "scopeBullets", "timeline", "exclusions", "body"];

function toSlug(value = "") {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "")
    .replace(/--+/g, "-");
}

function isPlainObject(value) {
  return !!value && typeof value === "object" && !Array.isArray(value);
}

function isReadableReference(value) {
  if (typeof value !== "string") return false;
  const text = value.trim();
  return text.startsWith("content:") || text.startsWith("file:") || /^https?:\/\//i.test(text) || text.startsWith("/");
}

function normalizeArray(value) {
  if (Array.isArray(value)) return value;
  if (typeof value === "string") {
    return value
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);
  }
  return [];
}

function formatResource(value) {
  if (Array.isArray(value)) return value.filter(Boolean).join("\n");
  if (value === null || value === undefined) return "";
  return String(value);
}

function safeRel(baseDir, sections) {
  return path.join(baseDir, ...sections).replace(/\\/g, "/");
}

function readJson(filePath) {
  const raw = fs.readFileSync(filePath, "utf8");
  return JSON.parse(raw);
}

function parseArgs(argv) {
  const options = {
    source: "content-library.json",
    manifest: "content-library.manifest.json",
    contentDir: "sample-content",
  };
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (!arg.startsWith("--") || i === argv.length - 1) continue;
    const key = arg.slice(2);
    options[key] = argv[i + 1];
    i += 1;
  }
  return options;
}

function writeContentFile(baseDir, relPath, content) {
  const absolute = path.resolve(baseDir, relPath);
  const dir = path.dirname(absolute);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(absolute, formatResource(content), "utf8");
  return relPath.replace(/\\/g, "/");
}

function migrateSection(section, collectionType, sectionKey, optionKey, targetDir, outSection) {
  if (!isPlainObject(section)) return section;
  const sectionOut = { ...section };
  const safeSectionKey = sectionKey || "default";
  const safeOptionKey = optionKey || "default";

  for (const field of FIELD_KEYS) {
    if (!(field in sectionOut)) continue;
    const value = sectionOut[field];
    if (isReadableReference(value)) continue;
    if (typeof value === "string") {
      if (!value.trim()) continue;
      if (value.length < 140 && !value.includes("\n")) continue;
      const rel = safeRel(collectionType, safeSectionKey, safeOptionKey, `${field}.md`);
      sectionOut[field] = `content:${writeContentFile(targetDir, rel, value)}`;
      continue;
    }
    if (Array.isArray(value) && value.length > 0) {
      const rel = safeRel(collectionType, safeSectionKey, safeOptionKey, `${field}.md`);
      const rendered = value.filter((item) => typeof item === "string").map((item) => item.toString()).join("\n");
      sectionOut[field] = `content:${writeContentFile(targetDir, rel, rendered)}`;
      continue;
    }
  }

  return { ...outSection, ...sectionOut };
}

function validateLibrary(payload) {
  if (!isPlainObject(payload)) return false;
  if (!isPlainObject(payload.industryGraphics)) return false;
  for (const key of REQUIRED_LIBRARY_KEYS.slice(1)) {
    if (!isPlainObject(payload[key])) return false;
  }
  return Object.values(payload.industryGraphics).every((value) => Array.isArray(value));
}

function run() {
  const options = parseArgs(process.argv);
  const sourcePath = path.resolve(process.cwd(), options.source);
  const manifestPath = path.resolve(process.cwd(), options.manifest);
  const contentDir = path.resolve(process.cwd(), options.contentDir);

  const source = readJson(sourcePath);
  if (!validateLibrary(source)) {
    console.error("Source content library is not in the expected shape.");
    process.exit(1);
  }

  const nextLibrary = {};
  if (!isPlainObject(nextLibrary.industryGraphics)) nextLibrary.industryGraphics = {};
  nextLibrary.industryGraphics = {};

  for (const mapKey of REQUIRED_LIBRARY_KEYS) {
    if (mapKey === "industryGraphics") {
      const rawMap = source.industryGraphics || {};
      const nextIndustryMap = {};
      for (const [industry, optionsList] of Object.entries(rawMap)) {
        if (!Array.isArray(optionsList)) continue;
        const safeIndustry = toSlug(industry);
        const migrated = [];
        for (const option of optionsList) {
          if (!isPlainObject(option)) {
            migrated.push(option);
            continue;
          }
          const optionKey = toSlug(option.id || option.title || "option");
          const sectionOut = {};
          for (const field of FIELD_KEYS) {
            if (!(field in option)) continue;
            const value = option[field];
            if (typeof value === "string" && !isReadableReference(value)) {
              if (value.length >= 140 || value.includes("\n")) {
                const rel = safeRel("industryGraphics", safeIndustry, optionKey, `${field}.md`);
                sectionOut[field] = `content:${writeContentFile(contentDir, rel, value)}`;
              } else {
                sectionOut[field] = value;
              }
            } else if (Array.isArray(value) && value.length > 0) {
              const rel = safeRel("industryGraphics", safeIndustry, optionKey, `${field}.md`);
              sectionOut[field] = `content:${writeContentFile(contentDir, rel, value.filter(Boolean).join("\n"))}`;
            } else {
              sectionOut[field] = value;
            }
          }
          migrated.push({
            ...option,
            ...sectionOut,
          });
        }
        nextLibrary.industryGraphics[industry] = migrated;
      }
      continue;
    }

    const rawMap = source[mapKey] || {};
    const outputMap = {};
    for (const [sectionKey, sectionValue] of Object.entries(rawMap)) {
      outputMap[sectionKey] = migrateSection(sectionValue, mapKey, toSlug(sectionKey), "entry", contentDir, sectionValue);
    }
    nextLibrary[mapKey] = outputMap;
  }

  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
  fs.writeFileSync(manifestPath, JSON.stringify(nextLibrary, null, 2), "utf8");
  console.log(`Wrote manifest: ${manifestPath}`);
  console.log(`Wrote content files: ${contentDir}`);
}

run();
