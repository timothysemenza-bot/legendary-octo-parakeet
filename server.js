const fs = require("fs");
const http = require("http");
const path = require("path");
const crypto = require("crypto");
const { URL } = require("url");
const { createContentProvider, isValidLibraryPayload } = require("./content-provider");

const CONFIG_ENV_PATH = path.join(__dirname, ".env");

function loadEnvFile(filePath) {
  try {
    const raw = fs.readFileSync(filePath, "utf8");
    raw.split(/\r?\n/).forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) return;
      const equalsIndex = trimmed.indexOf("=");
      if (equalsIndex === -1) return;
      const key = trimmed.slice(0, equalsIndex).trim();
      if (!key) return;
      let value = trimmed.slice(equalsIndex + 1).trim();
      if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      if (process.env[key] === undefined) {
        process.env[key] = value;
      }
    });
  } catch (_error) {}
}

loadEnvFile(CONFIG_ENV_PATH);

const PORT = Number(process.env.PORT) || 3000;
const PUBLIC_DIR = path.resolve(process.env.PUBLIC_DIR || __dirname);
const DATA_DIR = path.resolve(__dirname, process.env.PROPOSAL_DATA_DIR || process.env.DATA_DIR || "data");
const DATA_FILE = path.resolve(DATA_DIR, "proposals.json");
const CONTACT_EVENTS_FILE = path.resolve(
  __dirname,
  process.env.CONTACT_EVENTS_FILE || "marketing-agents/data/website_contact_events.csv"
);
const LIBRARY_FILE = path.resolve(
  __dirname,
  process.env.PROPOSAL_LIBRARY_PATH || process.env.LIBRARY_FILE || "content-library.json"
);
const CONTENT_PROVIDER = String(process.env.CONTENT_PROVIDER || "json").toLowerCase();
const CONTENT_PROVIDER_SETTINGS = (() => {
  try {
    return process.env.CONTENT_PROVIDER_SETTINGS ? JSON.parse(process.env.CONTENT_PROVIDER_SETTINGS) : {};
  } catch (_error) {
    return {};
  }
})();
const APP_NAME = process.env.BRAND_NAME || "St. Moritz Security Services";
const APP_TAGLINE = process.env.BRAND_TAGLINE || "Proposal Builder";
const CLIENT_NAME_FALLBACK = process.env.CLIENT_NAME_FALLBACK || `${APP_NAME} Client`;
const WORD_IMAGES_ENABLED = process.env.WORD_IMAGES_ENABLED !== "0";
const CORS_ORIGINS = (process.env.CORS_ORIGINS || "*")
  .split(",")
  .map((origin) => origin.trim())
  .filter(Boolean);
const STORAGE = { proposals: [] };
let CONTENT_LIBRARY = {};
let CONTENT_LIBRARY_PROVIDER = null;

function isOriginAllowed(origin) {
  if (!origin) return true;
  if (CORS_ORIGINS.includes("*")) return true;
  return CORS_ORIGINS.includes(origin);
}

function resolveCorsOrigin(origin = "") {
  if (!origin || CORS_ORIGINS.includes("*")) return "*";
  return isOriginAllowed(origin) ? origin : "";
}

function ensureDataFile() {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }
  if (!fs.existsSync(DATA_FILE)) {
    fs.writeFileSync(DATA_FILE, "[]", "utf8");
  }
}

function ensureParentDir(filePath) {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function ensureContactEventsFile() {
  ensureParentDir(CONTACT_EVENTS_FILE);
  if (!fs.existsSync(CONTACT_EVENTS_FILE)) {
    const header = [
      "event_at",
      "event_date",
      "source_page",
      "context",
      "channel",
      "referrer",
      "user_agent",
      "ip_hash",
      "spam_score",
      "spam_flag",
      "spam_reasons",
    ].join(",");
    fs.writeFileSync(CONTACT_EVENTS_FILE, `${header}\n`, "utf8");
  }
}
function ensureLibraryFile() {
  if (CONTENT_PROVIDER !== "json") return;
  if (!fs.existsSync(LIBRARY_FILE)) {
    fs.writeFileSync(LIBRARY_FILE, "{}", "utf8");
  }
}

function loadStore() {
  try {
    const raw = fs.readFileSync(DATA_FILE, "utf8");
    STORAGE.proposals = JSON.parse(raw);
  } catch {
    STORAGE.proposals = [];
  }
}

function initializeContentProvider() {
  if (CONTENT_LIBRARY_PROVIDER) return;
  CONTENT_LIBRARY_PROVIDER = createContentProvider({
    provider: CONTENT_PROVIDER,
    file: LIBRARY_FILE,
    settings: CONTENT_PROVIDER_SETTINGS,
  });
}

function saveStore() {
  fs.writeFileSync(DATA_FILE, JSON.stringify(STORAGE.proposals, null, 2), "utf8");
}

async function getContentLibrary() {
  if (!CONTENT_LIBRARY_PROVIDER) {
    initializeContentProvider();
  }
  await CONTENT_LIBRARY_PROVIDER.init();
  CONTENT_LIBRARY = await CONTENT_LIBRARY_PROVIDER.getLibrary();
  return CONTENT_LIBRARY;
}

async function setContentLibrary(payload) {
  if (!CONTENT_LIBRARY_PROVIDER) {
    initializeContentProvider();
  }
  await CONTENT_LIBRARY_PROVIDER.init();
  CONTENT_LIBRARY = await CONTENT_LIBRARY_PROVIDER.saveLibrary(payload);
  return CONTENT_LIBRARY;
}

async function refreshContentLibrary() {
  if (!CONTENT_LIBRARY_PROVIDER) {
    initializeContentProvider();
  }
  await CONTENT_LIBRARY_PROVIDER.reload();
  CONTENT_LIBRARY = await CONTENT_LIBRARY_PROVIDER.getLibrary();
  return CONTENT_LIBRARY;
}

function getContentLibraryStatus() {
  if (!CONTENT_LIBRARY_PROVIDER) return { provider: CONTENT_PROVIDER, loaded: false };
  const status = CONTENT_LIBRARY_PROVIDER.getStatus();
  return {
    ...status,
    loaded: !!status.loaded,
  };
}

function sendJson(res, payload, code = 200) {
  const body = JSON.stringify(payload);
  const allowOrigin = resolveCorsOrigin(res.__origin || "");
  res.writeHead(code, {
    "Access-Control-Allow-Origin": allowOrigin,
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
    "Content-Type": "application/json",
    "Content-Length": Buffer.byteLength(body),
  });
  res.end(body);
}

function sendText(res, text, code = 200, contentType = "text/plain") {
  const allowOrigin = resolveCorsOrigin(res.__origin || "");
  res.writeHead(code, {
    "Access-Control-Allow-Origin": allowOrigin,
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
    "Content-Type": `${contentType}; charset=utf-8`,
    "Content-Length": Buffer.byteLength(text),
  });
  res.end(text);
}

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (chunk) => {
      data += chunk;
      if (data.length > 1e6) {
        req.destroy();
        reject(new Error("Payload too large"));
      }
    });
    req.on("end", () => {
      if (!data) return resolve({});
      try {
        resolve(JSON.parse(data));
      } catch {
        reject(new Error("Invalid JSON"));
      }
    });
  });
}

function csvEscape(value) {
  const str = String(value ?? "");
  if (str.includes(",") || str.includes('"') || str.includes("\n")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function hashIp(ip) {
  const raw = String(ip || "").trim();
  if (!raw) return "";
  return crypto.createHash("sha256").update(raw).digest("hex").slice(0, 16);
}

function getClientIp(req) {
  const h = req.headers || {};
  const forwarded = String(h["cf-connecting-ip"] || h["x-forwarded-for"] || "").trim();
  if (forwarded) return forwarded.split(",")[0].trim();
  return String(req.socket?.remoteAddress || "").trim();
}

function normalizeInboundEvent(body = {}, req) {
  const now = new Date();
  const eventAt = now.toISOString();
  const eventDate = eventAt.slice(0, 10);
  const channel = String(body.channel || "unknown").trim().toLowerCase().slice(0, 20);
  const context = String(body.context || "").trim().slice(0, 180);
  const sourcePage = String(body.source_page || body.page_url || "").trim().slice(0, 300);
  const referrer = String(body.referrer || req.headers.referer || "").trim().slice(0, 300);
  const userAgent = String(body.user_agent || req.headers["user-agent"] || "").trim().slice(0, 300);
  const ipHash = hashIp(getClientIp(req));
  const honeypot = String(body.website || body.honeypot || "").trim();
  return { eventAt, eventDate, channel, context, sourcePage, referrer, userAgent, ipHash, honeypot };
}

function scoreSpam(event) {
  let score = 0;
  const reasons = [];
  const ua = String(event.userAgent || "").toLowerCase();
  const context = String(event.context || "").toLowerCase();
  const channel = String(event.channel || "").toLowerCase();
  const page = String(event.sourcePage || "").toLowerCase();
  const bots = ["bot", "spider", "crawl", "headless", "python", "curl", "wget", "go-http-client", "postman"];

  if (!["call", "sms", "email", "linkedin", "contact"].includes(channel)) {
    score += 25;
    reasons.push("unknown-channel");
  }
  if (!context || context.length < 3) {
    score += 25;
    reasons.push("missing-context");
  }
  if (!page || !page.includes("boss-key")) {
    score += 10;
    reasons.push("invalid-page");
  }
  if (bots.some((b) => ua.includes(b))) {
    score += 70;
    reasons.push("bot-user-agent");
  }
  if (event.honeypot) {
    score += 80;
    reasons.push("honeypot-filled");
  }
  if (context.includes("seo") || context.includes("crypto") || context.includes("gambling") || context.includes("viagra")) {
    score += 70;
    reasons.push("spam-keywords");
  }

  return { score, isSpam: score >= 60, reasons };
}

function appendContactEvent(row) {
  const line = [
    row.event_at,
    row.event_date,
    row.source_page,
    row.context,
    row.channel,
    row.referrer,
    row.user_agent,
    row.ip_hash,
    String(row.spam_score),
    row.spam_flag,
    row.spam_reasons,
  ]
    .map(csvEscape)
    .join(",");
  fs.appendFileSync(CONTACT_EVENTS_FILE, `${line}\n`, "utf8");
}
function escapeXmlValue(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function decodeDataUriValue(dataUrl) {
  if (typeof dataUrl !== "string") return null;
  const uri = dataUrl.trim();
  const parts = uri.match(/^data:([^;,]*);base64,(.+)$/i);
  if (parts) {
    const mediaType = (parts[1] || "").toLowerCase();
    return {
      mediaType,
      data: Buffer.from(parts[2], "base64"),
    };
  }

  const plain = uri.match(/^data:([^;,]*),(.*)$/i);
  if (plain) {
    const mediaType = (plain[1] || "").toLowerCase();
    return {
      mediaType,
      data: Buffer.from(decodeURIComponent(plain[2] || ""), "utf8"),
    };
  }

  return null;
}

function detectImageMetaFromGraphic(graphic, fallbackLabel) {
  if (!graphic) return null;
  if (!WORD_IMAGES_ENABLED) return null;
  const resolved =
    typeof graphic === "string"
      ? {
          inline: graphic,
          label: fallbackLabel || "Graphic",
        }
      : {
          inline: graphic.inline || graphic.svg || graphic.html || "",
          label: graphic.label || graphic.alt || graphic.title || fallbackLabel || "Graphic",
          wordImage: graphic.wordImage || graphic.image || graphic.wordSource || graphic.dataUrl,
        };

  const inline = String(resolved.inline || "").trim();
  const graphicName = String(resolved.label || fallbackLabel || "Graphic").trim();

  const hasValidImageSignature = (data, type) => {
    if (!Buffer.isBuffer(data) || data.length < 8) return false;
    if (type === "png") return data[0] === 0x89 && data[1] === 0x50 && data[2] === 0x4e && data[3] === 0x47;
    if (type === "jpg" || type === "jpeg") return data[0] === 0xff && data[1] === 0xd8 && data[2] === 0xff;
    if (type === "gif") return data[0] === 0x47 && data[1] === 0x49 && data[2] === 0x46 && data[3] === 0x38;
    if (type === "webp")
      return (
        data.length > 12 &&
        data[0] === 0x52 &&
        data[1] === 0x49 &&
        data[2] === 0x46 &&
        data[3] === 0x46 &&
        data[8] === 0x57 &&
        data[9] === 0x45 &&
        data[10] === 0x42 &&
        data[11] === 0x50
      );
    if (type === "bmp") return data[0] === 0x42 && data[1] === 0x4d;
    return false;
  };

  const detectedTypeFromMediaType = (mediaType) => {
    if (!mediaType) return null;
    if (mediaType.includes("image/png")) return { ext: "png", contentType: "image/png" };
    if (mediaType.includes("image/jpeg") || mediaType.includes("image/jpg")) return { ext: "jpeg", contentType: "image/jpeg" };
    if (mediaType.includes("image/gif")) return { ext: "gif", contentType: "image/gif" };
    if (mediaType.includes("image/webp")) return { ext: "webp", contentType: "image/webp" };
    if (mediaType.includes("image/bmp") || mediaType.includes("image/x-ms-bmp")) return { ext: "bmp", contentType: "image/bmp" };
    return null;
  };

  if (typeof resolved.wordImage === "string" && resolved.wordImage.trim().startsWith("data:")) {
    const decoded = decodeDataUriValue(resolved.wordImage);
      if (decoded && decoded.data.length > 0) {
        const mediaType = (decoded.mediaType || "").toLowerCase();
        if (mediaType.includes("image/svg+xml")) return null;
        if (mediaType && !mediaType.startsWith("image/")) return null;
        const type = detectedTypeFromMediaType(mediaType);
        if (!type) return null;
      if (!hasValidImageSignature(decoded.data, type.ext)) {
        return null;
      }
      return {
        kind: "binary",
        ext: type.ext,
        name: graphicName,
        data: decoded.data,
        contentType: type.contentType,
      };
    }
  }

  return null;
}

function generateWordDocument(data, generated, styleSet) {
  if (!generated) {
    throw new Error("No generated proposal payload provided");
  }

  const safe = escapeXmlValue;
  const styleNames = {
    title: safe((styleSet && styleSet.title) || "SMS Title"),
    subtitle: safe((styleSet && styleSet.subtitle) || "SMS Subtitle"),
    sectionHeading: safe((styleSet && styleSet.sectionHeading) || "SMS Section Heading"),
    body: safe((styleSet && styleSet.body) || "SMS Body"),
    summary: safe((styleSet && styleSet.summary) || "SMS Summary"),
    figure: safe((styleSet && styleSet.figure) || "SMS Figure"),
  };
  const styleIds = {
    title: "sms-title",
    subtitle: "sms-subtitle",
    sectionHeading: "sms-section",
    body: "sms-body",
    summary: "sms-summary",
    figure: "sms-figure",
  };

  const safeName = data.companyName || "client";
  const facilities = Number(data.facilities || 1);
  const timelineItems = generated.timeline || [];
  const exclusions = generated.exclusions || [];
  const imageParts = [];
  let relCounter = 2;
  let drawingId = 1;
  let imageCount = 0;

  const toEmu = (value) => Math.max(1, Math.round((value || 0) * 9525));
  const paragraph = (text, style, bold = false) => {
    const safeText = safe(text);
    const boldTag = bold ? "<w:b/>" : "";
    return `\n      <w:p><w:pPr><w:pStyle w:val="${style}" /></w:pPr><w:r>${boldTag ? `<w:rPr>${boldTag}</w:rPr>` : ""}<w:t xml:space="preserve">${safeText}</w:t></w:r></w:p>`;
  };
  const sectionTitle = (title) => paragraph(title, styleIds.sectionHeading, true);
  const listItems = (items) =>
    (items || [])
      .filter(Boolean)
      .map((line) => `\n      <w:p><w:pPr><w:pStyle w:val="${styleIds.body}" /></w:pPr><w:r><w:t xml:space="preserve">- ${safe(line)}</w:t></w:r></w:p>`)
      .join("");

  const addImageGraphic = (graphic, sectionTitle) => {
    const detected = detectImageMetaFromGraphic(graphic, sectionTitle);
    if (!detected) return "";
    const graphicLabel = safe(detected.name || sectionTitle || "Graphic");

    if (!detected.data || !detected.data.length) return "";

    const mediaName = `word/media/image${++imageCount}.${detected.ext || "png"}`;
    const mediaType = detected.ext || "png";
    const relationshipId = `rId${relCounter++}`;

    const cx = toEmu(520);
    const cy = toEmu(160);

    const contentType = detected.contentType || "image/png";
    imageParts.push({
      name: mediaName,
      data: detected.data,
      contentType,
    });

    return `
      <w:p><w:pPr><w:pStyle w:val="${styleIds.figure}" /></w:pPr><w:r><w:drawing><wp:inline>
        <wp:extent cx="${cx}" cy="${cy}" />
        <wp:docPr id="${drawingId++}" name="${graphicLabel}" descr="${graphicLabel}" />
        <a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
          <pic:pic>
            <pic:nvPicPr>
              <pic:cNvPr id="${drawingId++}" name="${graphicLabel}" />
              <pic:cNvPicPr />
            </pic:nvPicPr>
            <pic:blipFill>
              <a:blip r:embed="${relationshipId}" cstate="print" />
              <a:stretch><a:fillRect /></a:stretch>
            </pic:blipFill>
            <pic:spPr>
              <a:xfrm><a:off x="0" y="0" /><a:ext cx="${cx}" cy="${cy}" /></a:xfrm>
              <a:prstGeom prst="rect"><a:avLst /></a:prstGeom>
            </pic:spPr>
          </pic:pic>
        </a:graphicData></a:graphic>
      </wp:inline></w:drawing></w:r></w:p>`;
  };

  const sectionContent = (section) => {
    const title = section.title || "Section";
    const paragraphs = (section.paragraphs || []).map((line) => paragraph(line, styleIds.body)).join("");
    const bullets = listItems(section.bullets || []);
    const graphicMarkup = section.graphic ? addImageGraphic(section.graphic, title) : "";
    const graphic = graphicMarkup ? `\n      ${paragraph(section.title || "Graphic", styleIds.figure)}${graphicMarkup}` : "";
    return `\n      ${sectionTitle(title)}${paragraphs}${bullets}${graphic}`;
  };

  const body = `
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
      <w:body>
        ${paragraph(APP_NAME, styleIds.title, true)}
        ${paragraph(`Proposal for ${safeName}`, styleIds.subtitle)}
        ${paragraph(`Primary contact: ${data.primaryContact || ""} (${data.contactEmail || ""})`, styleIds.body)}
        ${paragraph(`Location: ${data.location || "TBD"} | Sites: ${facilities}`, styleIds.body)}
        ${paragraph("Scope", styleIds.sectionHeading, true)}
        ${(generated.sections || []).map(sectionContent).join("")}
        ${paragraph("Timeline", styleIds.sectionHeading, true)}
        ${listItems(timelineItems)}
        ${paragraph("Exclusions", styleIds.sectionHeading, true)}
        ${listItems(exclusions)}
        ${paragraph("Pricing", styleIds.summary, true)}
        ${paragraph(`Monthly: $${generated.pricing?.monthly?.toLocaleString() || 0}`, styleIds.body)}
        ${paragraph(`First month onboarding: $${generated.pricing?.firstMonthInstall?.toLocaleString() || 0}`, styleIds.body)}
        ${paragraph(`Annualized total: $${generated.pricing?.yearly?.toLocaleString() || 0}`, styleIds.body)}
        <w:sectPr>
          <w:pgSz w:w="12240" w:h="15840" w:orient="portrait" />
          <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0" />
        </w:sectPr>
      </w:body>
    </w:document>`.replace(/^\s+/gm, "").trim();

  const stylesXml = `
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
      <w:docDefaults>
        <w:rPrDefault>
          <w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" /></w:rPr>
        </w:rPrDefault>
      </w:docDefaults>
      <w:style w:type="paragraph" w:styleId="${styleIds.title}">
        <w:name w:val="${styleNames.title}" />
        <w:qFormat />
        <w:basedOn w:val="Normal" />
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" />
          <w:b />
          <w:sz w:val="52" />
        </w:rPr>
      </w:style>
      <w:style w:type="paragraph" w:styleId="${styleIds.subtitle}">
        <w:name w:val="${styleNames.subtitle}" />
        <w:qFormat />
        <w:basedOn w:val="Normal" />
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" />
          <w:sz w:val="28" />
        </w:rPr>
      </w:style>
      <w:style w:type="paragraph" w:styleId="${styleIds.sectionHeading}">
        <w:name w:val="${styleNames.sectionHeading}" />
        <w:qFormat />
        <w:basedOn w:val="Normal" />
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" />
          <w:b />
          <w:sz w:val="32" />
        </w:rPr>
      </w:style>
      <w:style w:type="paragraph" w:styleId="${styleIds.body}">
        <w:name w:val="${styleNames.body}" />
        <w:qFormat />
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" />
          <w:sz w:val="22" />
        </w:rPr>
      </w:style>
      <w:style w:type="paragraph" w:styleId="${styleIds.summary}">
        <w:name w:val="${styleNames.summary}" />
        <w:qFormat />
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" />
          <w:b />
          <w:sz w:val="24" />
        </w:rPr>
      </w:style>
      <w:style w:type="paragraph" w:styleId="${styleIds.figure}">
        <w:name w:val="${styleNames.figure}" />
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" />
          <w:sz w:val="22" />
        </w:rPr>
      </w:style>
      <w:style w:type="character" w:styleId="DefaultParagraphFont">
        <w:name w:val="Default Paragraph Font" />
        <w:rPr>
          <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" />
        </w:rPr>
      </w:style>
      <w:style w:type="table" w:styleId="TableNormal">
        <w:name w:val="Normal Table" />
      </w:style>
      <w:latentStyles defLockedState="1" latentStyleCount="267" />
    </w:styles>
  `.replace(/^\s+/gm, "").trim();

  return buildDocxFromXml(body, stylesXml, imageParts);
}

function crc32(buf) {
  const table = getCrc32Table();
  let crc = 0 ^ -1;
  for (const byte of buf) {
    crc = (crc >>> 8) ^ table[(crc ^ byte) & 0xff];
  }
  return (crc ^ -1) >>> 0;
}

function getCrc32Table() {
  if (crcTable) return crcTable;
  crcTable = [];
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) {
      if (c & 1) {
        c = 0xedb88320 ^ (c >>> 1);
      } else {
        c = c >>> 1;
      }
    }
    crcTable[n] = c >>> 0;
  }
  return crcTable;
}

let crcTable;

function buildDocxFromXml(documentXml, stylesXml, imageParts = []) {
  const imageRels = imageParts
    .map((part, index) => {
      const safeName = String(part.name || "").replace(/^word\//, "");
      return `  <Relationship Id="rId${index + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="${safeName}" />`;
    })
    .join("\n");

  const documentRel = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
 <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
   <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml" />
${imageRels}
 </Relationships>`.trim();

  const rels = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
 <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
   <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml" />
 </Relationships>`.trim();

  const imageContentTypes = imageParts
    .map((part) => `  <Override PartName="/${part.name}" ContentType="${part.contentType || "image/svg+xml"}" />`)
    .join("\n");

  const contentTypes = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
 <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
   <Default Extension="svg" ContentType="image/svg+xml" />
   <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />
   <Default Extension="xml" ContentType="application/xml" />
${imageContentTypes}
   <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml" />
   <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml" />
   <Override PartName="/_rels/.rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />
 </Types>`.trim();

  const files = [
    { name: "[Content_Types].xml", data: Buffer.from(contentTypes, "utf8") },
    { name: "_rels/.rels", data: Buffer.from(rels, "utf8") },
    { name: "word/document.xml", data: Buffer.from(documentXml, "utf8") },
    { name: "word/_rels/document.xml.rels", data: Buffer.from(documentRel, "utf8") },
    { name: "word/styles.xml", data: Buffer.from(stylesXml, "utf8") },
  ];

  imageParts.forEach((part) => {
    files.push({
      name: part.name,
      data: part.data,
    });
  });

  return createZip(files);
}

function createZip(entries) {
  const localParts = [];
  const centralParts = [];
  let offset = 0;

  for (const entry of entries) {
    const name = entry.name;
    const data = Buffer.isBuffer(entry.data) ? entry.data : Buffer.from(entry.data || "", "utf8");
    const nameBuffer = Buffer.from(name, "utf8");
    const crc = crc32(data);
    const compressionMethod = 0;

    const localHeader = Buffer.alloc(30 + nameBuffer.length);
    let pos = 0;
    localHeader.writeUInt32LE(0x04034b50, pos);
    pos += 4;
    localHeader.writeUInt16LE(20, pos);
    pos += 2;
    localHeader.writeUInt16LE(0, pos);
    pos += 2;
    localHeader.writeUInt16LE(compressionMethod, pos);
    pos += 2;
    localHeader.writeUInt16LE(0, pos);
    pos += 2;
    localHeader.writeUInt16LE(0, pos);
    pos += 2;
    localHeader.writeUInt32LE(crc, pos);
    pos += 4;
    localHeader.writeUInt32LE(data.length, pos);
    pos += 4;
    localHeader.writeUInt32LE(data.length, pos);
    pos += 4;
    localHeader.writeUInt16LE(nameBuffer.length, pos);
    pos += 2;
    localHeader.writeUInt16LE(0, pos);
    pos += 2;
    nameBuffer.copy(localHeader, pos);
    localParts.push(localHeader, data);

    const centralHeader = Buffer.alloc(46 + nameBuffer.length);
    pos = 0;
    centralHeader.writeUInt32LE(0x02014b50, pos);
    pos += 4;
    centralHeader.writeUInt16LE(20, pos);
    pos += 2;
    centralHeader.writeUInt16LE(20, pos);
    pos += 2;
    centralHeader.writeUInt16LE(0, pos);
    pos += 2;
    centralHeader.writeUInt16LE(compressionMethod, pos);
    pos += 2;
    centralHeader.writeUInt16LE(0, pos);
    pos += 2;
    centralHeader.writeUInt16LE(0, pos);
    pos += 2;
    centralHeader.writeUInt32LE(crc, pos);
    pos += 4;
    centralHeader.writeUInt32LE(data.length, pos);
    pos += 4;
    centralHeader.writeUInt32LE(data.length, pos);
    pos += 4;
    centralHeader.writeUInt16LE(nameBuffer.length, pos);
    pos += 2;
    centralHeader.writeUInt16LE(0, pos);
    pos += 2;
    centralHeader.writeUInt16LE(0, pos);
    pos += 2;
    centralHeader.writeUInt32LE(0, pos);
    pos += 4;
    centralHeader.writeUInt32LE(0, pos);
    pos += 4;
    centralHeader.writeUInt32LE(offset, pos);
    pos += 4;
    nameBuffer.copy(centralHeader, pos);

    centralParts.push(centralHeader);
    offset += localHeader.length + data.length;
  }

  const centralDirectory = Buffer.concat(centralParts);
  const eocd = Buffer.alloc(22);
  let pos = 0;
  eocd.writeUInt32LE(0x06054b50, pos);
  pos += 4;
  eocd.writeUInt16LE(0, pos);
  pos += 2;
  eocd.writeUInt16LE(0, pos);
  pos += 2;
  eocd.writeUInt16LE(centralParts.length, pos);
  pos += 2;
  eocd.writeUInt16LE(centralParts.length, pos);
  pos += 2;
  eocd.writeUInt32LE(centralDirectory.length, pos);
  pos += 4;
  eocd.writeUInt32LE(offset, pos);
  pos += 4;
  eocd.writeUInt16LE(0, pos);
  pos += 2;

  return Buffer.concat([...localParts, centralDirectory, eocd]);
}

function sanitizeGeneratedPayload(generated) {
  if (!generated || typeof generated !== "object") return generated;
  const safeSections = Array.isArray(generated.sections)
    ? generated.sections
        .map((section) => {
          if (!section || typeof section !== "object") return null;
          const title = String(section.title || "");
          return {
            title,
            paragraphs: Array.isArray(section.paragraphs) ? section.paragraphs.filter((line) => typeof line === "string") : [],
            bullets: Array.isArray(section.bullets) ? section.bullets.filter((line) => typeof line === "string") : [],
            graphic: section.graphic,
          };
        })
        .filter(Boolean)
    : [];

  return {
    ...generated,
    sections: safeSections,
    timeline: Array.isArray(generated.timeline) ? generated.timeline.filter((line) => typeof line === "string") : [],
    exclusions: Array.isArray(generated.exclusions) ? generated.exclusions.filter((line) => typeof line === "string") : [],
    pricing: generated.pricing && typeof generated.pricing === "object" ? generated.pricing : {},
  };
}

function stripWordGraphicsFromGenerated(generated) {
  if (!generated || typeof generated !== "object") return generated;
  return {
    ...sanitizeGeneratedPayload(generated),
    sections: Array.isArray(generated.sections)
      ? generated.sections
          .map((section) =>
            section && typeof section === "object"
              ? {
                  ...section,
                  paragraphs: Array.isArray(section.paragraphs) ? section.paragraphs.filter((line) => typeof line === "string") : [],
                  bullets: Array.isArray(section.bullets) ? section.bullets.filter((line) => typeof line === "string") : [],
                  graphic: null,
                }
              : section
          )
          .filter(Boolean)
      : [],
  };
}

function sendBinary(res, buffer, filename = "proposal.docx") {
  res.writeHead(200, {
    "Access-Control-Allow-Origin": resolveCorsOrigin(res.__origin || ""),
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
    "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "Content-Disposition": `attachment; filename="${filename}"`,
    "Content-Length": Buffer.byteLength(buffer),
  });
  res.end(buffer);
}

function createVersion(data, generated) {
  return {
    version: 1,
    generatedAt: new Date().toISOString(),
    data,
    generated,
  };
}

function upsertVersion(existing, data, generated) {
  const nextVersion = Number(existing.currentVersion || existing.versions.length || 0) + 1;
  const version = {
    version: nextVersion,
    generatedAt: new Date().toISOString(),
    data,
    generated,
  };
  existing.versions.push(version);
  existing.currentVersion = nextVersion;
  existing.current = version;
  existing.updatedAt = new Date().toISOString();
  if (existing.versions.length > 40) {
    existing.versions = existing.versions.slice(-40);
  }
}

function sanitizeName(data) {
  const name = (data && data.companyName ? String(data.companyName) : CLIENT_NAME_FALLBACK).trim();
  return name.slice(0, 120) || CLIENT_NAME_FALLBACK;
}

function getProposalById(id) {
  return STORAGE.proposals.find((proposal) => proposal.id === id);
}

function makeId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

async function handleApiRequest(req, res, pathname, method) {
    if (pathname === "/api/contact-events" && method === "POST") {
    try {
      const body = await parseBody(req);
      const event = normalizeInboundEvent(body, req);
      const spam = scoreSpam(event);
      appendContactEvent({
        event_at: event.eventAt,
        event_date: event.eventDate,
        source_page: event.sourcePage,
        context: event.context,
        channel: event.channel,
        referrer: event.referrer,
        user_agent: event.userAgent,
        ip_hash: event.ipHash,
        spam_score: spam.score,
        spam_flag: spam.isSpam ? "yes" : "no",
        spam_reasons: spam.reasons.join("|"),
      });
      return sendJson(res, { ok: true, accepted: !spam.isSpam, spam_score: spam.score }, 201);
    } catch (error) {
      return sendJson(res, { error: error.message }, 400);
    }
  }

  if (pathname === "/api/contact-events") {
    return sendJson(res, { error: "Method not supported" }, 405);
  }
  if (pathname === "/api/library" && method === "GET") {
    await getContentLibrary();
    return sendJson(res, CONTENT_LIBRARY);
  }

  if (pathname === "/api/library" && method === "PUT") {
    try {
      const nextLibrary = await parseBody(req);
      if (!isValidLibraryPayload(nextLibrary)) {
        return sendJson(res, { error: "Invalid library payload" }, 400);
      }
      await setContentLibrary(nextLibrary);
      return sendJson(res, CONTENT_LIBRARY);
    } catch (error) {
      return sendJson(res, { error: error.message }, 400);
    }
  }

  if (pathname === "/api/library") {
    return sendJson(res, { error: "Method not supported" }, 405);
  }

  if (pathname === "/api/content/status" && method === "GET") {
    if (!CONTENT_LIBRARY_PROVIDER) {
      initializeContentProvider();
      await CONTENT_LIBRARY_PROVIDER.init();
    }
    return sendJson(res, getContentLibraryStatus());
  }

  if (pathname === "/api/content/refresh" && method === "POST") {
    try {
      await refreshContentLibrary();
      return sendJson(res, { status: "ok", ...getContentLibraryStatus() });
    } catch (error) {
      return sendJson(res, { error: error.message }, 500);
    }
  }

  if (pathname === "/api/content/resolve" && method === "POST") {
    try {
      const body = await parseBody(req);
      if (!CONTENT_LIBRARY_PROVIDER) {
        initializeContentProvider();
        await CONTENT_LIBRARY_PROVIDER.init();
      }
      const generated = await CONTENT_LIBRARY_PROVIDER.resolve(body || {});
      return sendJson(res, generated);
    } catch (error) {
      return sendJson(res, { error: error.message }, 400);
    }
  }

  if (pathname === "/api/export/docx" && method === "POST") {
    try {
      const body = await parseBody(req);
      const data = body.data || {};
      const generated = sanitizeGeneratedPayload(body.generated || null);
      const safeName = data.companyName || "client";
      const filename = `${String(safeName)
        .replace(/[^a-z0-9]+/gi, "_")
        .toLowerCase() || "proposal"}-proposal.docx`;
      const wordBinary = generateWordDocument(data, generated, body.wordStyleSet || {});
      if (!wordBinary || wordBinary.length < 4 || wordBinary[0] !== 0x50 || wordBinary[1] !== 0x4b) {
        throw new Error("DOCX generation failed; output does not appear to be a valid ZIP package.");
      }
      return sendBinary(res, wordBinary, filename);
    } catch (error) {
      return sendJson(res, { error: error.message }, 400);
    }
  }

  if (pathname === "/api/export/docx") {
    return sendJson(res, { error: "Method not supported" }, 405);
  }

  if (pathname === "/api/proposals" && method === "GET") {
    const sorted = [...STORAGE.proposals].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
    return sendJson(res, sorted);
  }

  if (pathname === "/api/proposals" && method === "POST") {
    try {
      const body = await parseBody(req);
      const data = body.data || {};
      const generated = sanitizeGeneratedPayload(body.generated || null);
      const proposal = {
        id: makeId(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        companyName: sanitizeName(data),
        primaryContact: data.primaryContact || "",
        contactEmail: data.contactEmail || "",
        status: body.status || "Draft",
        currentVersion: 0,
        versions: [],
      };
      const version = createVersion(data, generated);
      proposal.versions.push(version);
      proposal.currentVersion = version.version;
      proposal.current = version;
      STORAGE.proposals.unshift(proposal);
      saveStore();
      return sendJson(res, proposal, 201);
    } catch (error) {
      return sendJson(res, { error: error.message }, 400);
    }
  }

  const idMatch = pathname.match(/^\/api\/proposals\/([^/]+)$/);
  if (!idMatch) return sendJson(res, { error: "Not found" }, 404);
  const proposal = getProposalById(decodeURIComponent(idMatch[1]));
  if (!proposal) return sendJson(res, { error: "Proposal not found" }, 404);

  if (method === "GET") {
    return sendJson(res, proposal);
  }

  if (method === "PUT") {
    try {
      const body = await parseBody(req);
      if (!body.data) return sendJson(res, { error: "Data payload required" }, 400);
      const generated = sanitizeGeneratedPayload(body.generated || null);
      upsertVersion(proposal, body.data, generated);
      proposal.companyName = sanitizeName(body.data);
      proposal.primaryContact = body.data.primaryContact || proposal.primaryContact;
      proposal.contactEmail = body.data.contactEmail || proposal.contactEmail;
      if (body.status) proposal.status = body.status;
      saveStore();
      return sendJson(res, proposal);
    } catch (error) {
      return sendJson(res, { error: error.message }, 400);
    }
  }

  return sendJson(res, { error: "Method not supported" }, 405);
}

function serveStatic(res, pathname, reqPathname) {
  const filePath = path.join(PUBLIC_DIR, reqPathname === "/" ? "index.html" : pathname.slice(1));
  const publicRoot = path.join(PUBLIC_DIR, path.sep);
  if (!filePath.startsWith(publicRoot) && filePath !== PUBLIC_DIR) {
    return sendText(res, "Not found", 403);
  }
  if (filePath.endsWith("/")) {
    return sendText(res, "Not found", 404);
  }
  if (!fs.existsSync(filePath)) {
    return sendText(res, "Not found", 404);
  }
  const stream = fs.createReadStream(filePath);
  const ext = path.extname(filePath).toLowerCase();
  const type =
    ext === ".html"
      ? "text/html"
      : ext === ".css"
      ? "text/css"
      : ext === ".js"
      ? "application/javascript"
      : ext === ".json"
    ? "application/json"
    : ext === ".png"
    ? "image/png"
    : ext === ".jpg" || ext === ".jpeg"
    ? "image/jpeg"
    : ext === ".gif"
    ? "image/gif"
    : ext === ".webp"
    ? "image/webp"
    : ext === ".bmp"
    ? "image/bmp"
    : ext === ".svg"
    ? "image/svg+xml"
    : "application/octet-stream";
  res.writeHead(200, {
    "Access-Control-Allow-Origin": resolveCorsOrigin(res.__origin || ""),
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
    "Content-Type": `${type}; charset=utf-8`,
  });
  stream.pipe(res);
}

async function requestHandler(req, res) {
  res.__origin = req.headers.origin || "";
  if (res.__origin && !isOriginAllowed(res.__origin) && !CORS_ORIGINS.includes("*")) {
    return sendText(res, "Origin not allowed", 403);
  }
  const url = new URL(req.url, `http://localhost:${PORT}`);
  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": resolveCorsOrigin(res.__origin || ""),
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
    });
    return res.end();
  }
  const pathname = url.pathname.endsWith("/") && url.pathname.length > 1 ? url.pathname.slice(0, -1) : url.pathname;
  if (
    pathname === "/api/contact-events" ||
    pathname === "/api/library" ||
    pathname.startsWith("/api/content/") ||
    pathname === "/api/export/docx" ||
    pathname.startsWith("/api/proposals")
  ) {
    return handleApiRequest(req, res, pathname, req.method);
  }
  return serveStatic(res, pathname, pathname);
}

async function main() {
  ensureDataFile();
  ensureContactEventsFile();
  ensureLibraryFile();
  loadStore();
  initializeContentProvider();
  if (CONTENT_LIBRARY_PROVIDER) {
    await getContentLibrary();
  }
  const server = http.createServer(requestHandler);
  server.listen(PORT, () => {
    console.log(`${APP_NAME} - ${APP_TAGLINE} running at http://localhost:${PORT}`);
    console.log(`Data file: ${DATA_FILE}`);
    console.log(`Content provider: ${CONTENT_PROVIDER}`);
    console.log(`Content library source: ${LIBRARY_FILE}`);
  });
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
















