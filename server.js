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
const WRITING_CENTER_TRIBUTES_DIR = path.resolve(
  __dirname,
  process.env.WRITING_CENTER_TRIBUTES_DIR || "projects/shared/data/writing-center-tributes"
);
const WRITING_CENTER_TRIBUTES_FILE = path.join(WRITING_CENTER_TRIBUTES_DIR, "submissions.csv");
const WRITING_CENTER_TRIBUTES_JSON_FILE = path.join(WRITING_CENTER_TRIBUTES_DIR, "submissions.json");
const WRITING_CENTER_TRIBUTE_VIDEO_DIR = path.join(WRITING_CENTER_TRIBUTES_DIR, "videos");
const WRITING_CENTER_TRIBUTE_SELFIE_DIR = path.join(WRITING_CENTER_TRIBUTES_DIR, "selfies");
const WRITING_CENTER_TRIBUTE_VIDEO_MAX_BYTES =
  Number(process.env.WRITING_CENTER_TRIBUTE_VIDEO_MAX_BYTES) || 18 * 1024 * 1024;
const WRITING_CENTER_TRIBUTE_SELFIE_MAX_BYTES =
  Number(process.env.WRITING_CENTER_TRIBUTE_SELFIE_MAX_BYTES) || 8 * 1024 * 1024;
const WRITING_CENTER_TRIBUTE_PAYLOAD_MAX_BYTES =
  Number(process.env.WRITING_CENTER_TRIBUTE_PAYLOAD_MAX_BYTES) || 28 * 1024 * 1024;
const WRITING_CENTER_TRIBUTE_PUBLIC_DIR = path.resolve(
  __dirname,
  process.env.WRITING_CENTER_TRIBUTE_PUBLIC_DIR || "boss-key-website/data"
);
const WRITING_CENTER_TRIBUTE_PUBLIC_MEDIA_DIR = path.join(
  WRITING_CENTER_TRIBUTE_PUBLIC_DIR,
  "writing-center-tribute-media"
);
const WRITING_CENTER_TRIBUTE_PUBLIC_FEED_FILE = path.join(
  WRITING_CENTER_TRIBUTE_PUBLIC_DIR,
  "writing-center-tribute-display.json"
);
const WRITING_CENTER_ADMIN_TOKEN = String(process.env.WRITING_CENTER_ADMIN_TOKEN || "").trim();
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
function ensureWritingCenterTributesFile() {
  ensureParentDir(WRITING_CENTER_TRIBUTES_FILE);
  if (!fs.existsSync(WRITING_CENTER_TRIBUTE_VIDEO_DIR)) {
    fs.mkdirSync(WRITING_CENTER_TRIBUTE_VIDEO_DIR, { recursive: true });
  }
  if (!fs.existsSync(WRITING_CENTER_TRIBUTE_SELFIE_DIR)) {
    fs.mkdirSync(WRITING_CENTER_TRIBUTE_SELFIE_DIR, { recursive: true });
  }
  if (!fs.existsSync(WRITING_CENTER_TRIBUTES_FILE)) {
    const header = getWritingCenterTributeHeaders().join(",");
    fs.writeFileSync(WRITING_CENTER_TRIBUTES_FILE, `${header}\n`, "utf8");
  }
  if (!fs.existsSync(WRITING_CENTER_TRIBUTES_JSON_FILE)) {
    fs.writeFileSync(WRITING_CENTER_TRIBUTES_JSON_FILE, "[]\n", "utf8");
  }
  if (!fs.existsSync(WRITING_CENTER_TRIBUTE_PUBLIC_MEDIA_DIR)) {
    fs.mkdirSync(WRITING_CENTER_TRIBUTE_PUBLIC_MEDIA_DIR, { recursive: true });
  }
  if (!fs.existsSync(WRITING_CENTER_TRIBUTE_PUBLIC_FEED_FILE)) {
    ensureParentDir(WRITING_CENTER_TRIBUTE_PUBLIC_FEED_FILE);
    fs.writeFileSync(
      WRITING_CENTER_TRIBUTE_PUBLIC_FEED_FILE,
      JSON.stringify({ updatedAt: "", items: [] }, null, 2),
      "utf8"
    );
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

function parseBody(req, limit = 1e6) {
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (chunk) => {
      data += chunk;
      if (data.length > limit) {
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

function cleanSingleLine(value, maxLength = 300) {
  return String(value ?? "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, maxLength);
}

function cleanMultiline(value, maxLength = 5000) {
  return String(value ?? "")
    .replace(/\r\n/g, "\n")
    .trim()
    .slice(0, maxLength);
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(email || "").trim());
}

function toYesNo(value, fallback = "no") {
  const normalized = cleanSingleLine(value, 8).toLowerCase();
  if (["yes", "true", "1", "on"].includes(normalized)) return "yes";
  if (["no", "false", "0", "off"].includes(normalized)) return "no";
  return fallback;
}

function detectVideoType(mediaType) {
  const normalized = String(mediaType || "").toLowerCase();
  if (!normalized.startsWith("video/")) return null;
  if (normalized.includes("video/webm")) return { ext: "webm", contentType: "video/webm" };
  if (normalized.includes("video/mp4")) return { ext: "mp4", contentType: "video/mp4" };
  if (normalized.includes("video/quicktime")) return { ext: "mov", contentType: "video/quicktime" };
  if (normalized.includes("video/ogg")) return { ext: "ogv", contentType: "video/ogg" };
  return null;
}

function saveWritingCenterVideo(videoPayload, submissionId) {
  if (!videoPayload || typeof videoPayload !== "object") return null;
  const dataUrl = typeof videoPayload.data_url === "string" ? videoPayload.data_url : videoPayload.dataUrl;
  if (!dataUrl) return null;
  const decoded = decodeDataUriValue(dataUrl);
  if (!decoded || !decoded.data || decoded.data.length === 0) {
    throw new Error("The video upload could not be decoded");
  }
  const detectedType = detectVideoType(decoded.mediaType || videoPayload.mime_type || videoPayload.mimeType);
  if (!detectedType) {
    throw new Error("Only MP4, WebM, MOV, or OGG video uploads are supported");
  }
  if (decoded.data.length > WRITING_CENTER_TRIBUTE_VIDEO_MAX_BYTES) {
    throw new Error("Video uploads must be 18 MB or smaller");
  }
  const fileName = `${submissionId}.${detectedType.ext}`;
  const filePath = path.join(WRITING_CENTER_TRIBUTE_VIDEO_DIR, fileName);
  fs.writeFileSync(filePath, decoded.data);
  return {
    filename: fileName,
    storagePath: path.relative(__dirname, filePath).replace(/\\/g, "/"),
    mimeType: detectedType.contentType,
    sizeBytes: decoded.data.length,
  };
}

function detectImageType(mediaType) {
  const normalized = String(mediaType || "").toLowerCase();
  if (!normalized.startsWith("image/")) return null;
  if (normalized.includes("image/jpeg") || normalized.includes("image/jpg")) {
    return { ext: "jpg", contentType: "image/jpeg" };
  }
  if (normalized.includes("image/png")) return { ext: "png", contentType: "image/png" };
  if (normalized.includes("image/webp")) return { ext: "webp", contentType: "image/webp" };
  if (normalized.includes("image/gif")) return { ext: "gif", contentType: "image/gif" };
  return null;
}

function saveWritingCenterSelfie(imagePayload, submissionId) {
  if (!imagePayload || typeof imagePayload !== "object") return null;
  const dataUrl = typeof imagePayload.data_url === "string" ? imagePayload.data_url : imagePayload.dataUrl;
  if (!dataUrl) return null;
  const decoded = decodeDataUriValue(dataUrl);
  if (!decoded || !decoded.data || decoded.data.length === 0) {
    throw new Error("The selfie upload could not be decoded");
  }
  const detectedType = detectImageType(decoded.mediaType || imagePayload.mime_type || imagePayload.mimeType);
  if (!detectedType) {
    throw new Error("Only JPG, PNG, WEBP, or GIF selfie uploads are supported");
  }
  if (decoded.data.length > WRITING_CENTER_TRIBUTE_SELFIE_MAX_BYTES) {
    throw new Error("Selfie uploads must be 8 MB or smaller");
  }
  const fileName = `${submissionId}-selfie.${detectedType.ext}`;
  const filePath = path.join(WRITING_CENTER_TRIBUTE_SELFIE_DIR, fileName);
  fs.writeFileSync(filePath, decoded.data);
  return {
    filename: fileName,
    storagePath: path.relative(__dirname, filePath).replace(/\\/g, "/"),
    mimeType: detectedType.contentType,
    sizeBytes: decoded.data.length,
  };
}

function readJsonArray(filePath) {
  try {
    const raw = fs.readFileSync(filePath, "utf8");
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (_error) {
    return [];
  }
}

function writeJsonFile(filePath, payload) {
  ensureParentDir(filePath);
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

function loadWritingCenterTributes() {
  return readJsonArray(WRITING_CENTER_TRIBUTES_JSON_FILE);
}

function toRepoAssetUrl(storagePath) {
  const clean = String(storagePath || "").replace(/\\/g, "/").replace(/^\/+/, "");
  return clean ? `/${clean}` : "";
}

function getWritingCenterTributeHeaders() {
  return [
    "submission_id",
    "interest_submitted_at",
    "full_name",
    "email",
    "graduation_year",
    "current_role_org",
    "linkedin_url",
    "best_contact_method",
    "network_interest",
    "connection_path",
    "verification_context",
    "future_contact_ok",
    "interest_status",
    "interest_reviewed_at",
    "interest_review_notes",
    "vetting_score",
    "vetting_status",
    "vetting_summary",
    "vetting_positive_signals",
    "vetting_caution_signals",
    "vetting_review_notes",
    "invite_token",
    "invite_status",
    "invite_created_at",
    "invite_sent_at",
    "tribute_submitted_at",
    "preferred_display_name",
    "written_note",
    "video_link",
    "video_filename",
    "video_storage_path",
    "video_mime_type",
    "video_size_bytes",
    "selfie_filename",
    "selfie_storage_path",
    "selfie_mime_type",
    "selfie_size_bytes",
    "share_permission",
    "display_permission",
    "review_status",
    "review_updated_at",
    "review_notes",
    "published_display_name",
    "published_role_org",
    "published_note",
    "publish_to_screen",
    "display_order",
    "interest_source_page",
    "tribute_source_page",
    "referrer",
    "user_agent",
    "ip_hash",
    "spam_score",
    "spam_flag",
    "spam_reasons",
  ];
}

function writeWritingCenterTributesCsv(records) {
  const header = getWritingCenterTributeHeaders();
  const lines = [header.join(",")];
  records.forEach((row) => {
    const assessment = buildWritingCenterVettingAssessment(row);
    const derived = {
      vetting_score: String(assessment.score),
      vetting_status: assessment.statusLabel,
      vetting_summary: assessment.summary,
      vetting_positive_signals: assessment.positiveSignals.join(" | "),
      vetting_caution_signals: assessment.cautionSignals.join(" | "),
      vetting_review_notes: row.vetting_review_notes || "",
    };
    const line = header.map((key) => csvEscape(derived[key] ?? row[key] ?? "")).join(",");
    lines.push(line);
  });
  fs.writeFileSync(WRITING_CENTER_TRIBUTES_FILE, `${lines.join("\n")}\n`, "utf8");
}

function exportPublicSelfie(record) {
  if (!record.selfie_storage_path) return "";
  const sourcePath = path.resolve(__dirname, record.selfie_storage_path);
  if (!fs.existsSync(sourcePath)) return "";
  ensureParentDir(path.join(WRITING_CENTER_TRIBUTE_PUBLIC_MEDIA_DIR, "placeholder"));
  const ext = path.extname(sourcePath) || ".jpg";
  const fileName = `${record.submission_id}${ext}`;
  const destPath = path.join(WRITING_CENTER_TRIBUTE_PUBLIC_MEDIA_DIR, fileName);
  fs.copyFileSync(sourcePath, destPath);
  return `./data/writing-center-tribute-media/${fileName}`;
}

function buildWritingCenterPublicFeed(records) {
  const items = records
    .filter((record) => {
      return (
        String(record.review_status || "") === "approved" &&
        String(record.publish_to_screen || "") === "yes" &&
        String(record.share_permission || "") === "yes" &&
        String(record.display_permission || "") === "yes"
      );
    })
    .sort((a, b) => {
      const aOrder = Number(a.display_order || 999999);
      const bOrder = Number(b.display_order || 999999);
      if (aOrder !== bOrder) return aOrder - bOrder;
      return String(a.tribute_submitted_at || a.interest_submitted_at || "").localeCompare(
        String(b.tribute_submitted_at || b.interest_submitted_at || "")
      );
    })
    .map((record, index) => ({
      id: record.submission_id,
      index: index + 1,
      name: record.published_display_name || record.preferred_display_name || record.full_name,
      roleOrg: record.published_role_org || record.current_role_org || "",
      graduationYear: record.graduation_year || "",
      note: record.published_note || record.written_note || "",
      selfieUrl: exportPublicSelfie(record),
      hasVideo: !!(record.video_filename || record.video_link),
      updatedAt: record.review_updated_at || record.tribute_submitted_at || record.interest_submitted_at || "",
    }));
  const payload = {
    updatedAt: new Date().toISOString(),
    itemCount: items.length,
    items,
  };
  writeJsonFile(WRITING_CENTER_TRIBUTE_PUBLIC_FEED_FILE, payload);
  return payload;
}

function saveWritingCenterTributes(records) {
  writeJsonFile(WRITING_CENTER_TRIBUTES_JSON_FILE, records);
  writeWritingCenterTributesCsv(records);
  return buildWritingCenterPublicFeed(records);
}

function isLocalAdminRequest(req) {
  const host = String(req.headers.host || "").toLowerCase();
  const ip = getClientIp(req);
  if (host.includes("localhost") || host.includes("127.0.0.1")) return true;
  return ip === "::1" || ip === "127.0.0.1" || ip.startsWith("::ffff:127.0.0.1");
}

function authorizeWritingCenterAdmin(req) {
  if (!WRITING_CENTER_ADMIN_TOKEN) {
    if (isLocalAdminRequest(req)) return { ok: true, mode: "local" };
    return { ok: false, status: 503, error: "WRITING_CENTER_ADMIN_TOKEN is not configured" };
  }
  const authHeader = String(req.headers.authorization || "");
  const bearer = authHeader.startsWith("Bearer ") ? authHeader.slice(7).trim() : "";
  const headerToken = cleanSingleLine(req.headers["x-admin-token"] || "", 240);
  const token = headerToken || bearer;
  if (!token || token !== WRITING_CENTER_ADMIN_TOKEN) {
    return { ok: false, status: 401, error: "Invalid admin token" };
  }
  return { ok: true, mode: "token" };
}

function makeWritingCenterInviteToken() {
  return crypto.randomBytes(18).toString("hex");
}

const WRITING_CENTER_DISPOSABLE_EMAIL_DOMAINS = new Set([
  "10minutemail.com",
  "dispostable.com",
  "fakeinbox.com",
  "guerrillamail.com",
  "maildrop.cc",
  "mailinator.com",
  "tempmail.com",
  "trashmail.com",
  "yopmail.com",
]);

const WRITING_CENTER_VETTING_TERMS = [
  { label: "Writing Center", regex: /\bwriting center\b/i },
  { label: "tutor", regex: /\btutor(?:ed|ing|s)?\b/i },
  { label: "consultant", regex: /\bconsultant(?:s)?\b/i },
  { label: "ENGL 296", regex: /\bengl\s*296\b/i },
  { label: "ENGL 3082", regex: /\bengl\s*3082\b/i },
  { label: "practicum", regex: /\bpracticum\b/i },
  { label: "Margie", regex: /\bmargie\b|\bouimette\b/i },
  { label: "Tom", regex: /\btom\b|\bdeans\b/i },
  { label: "UConn", regex: /\buconn\b|\buniversity of connecticut\b/i },
  { label: "Nexus", regex: /\bnexus\b/i },
  { label: "front office", regex: /\bfront office\b/i },
];

function getEmailDomain(value) {
  const email = String(value || "").trim().toLowerCase();
  const atIndex = email.lastIndexOf("@");
  return atIndex >= 0 ? email.slice(atIndex + 1) : "";
}

function getMatchedWritingCenterTerms(text) {
  const source = String(text || "");
  return WRITING_CENTER_VETTING_TERMS.filter((entry) => entry.regex.test(source)).map((entry) => entry.label);
}

function buildWritingCenterVettingAssessment(record = {}) {
  const positives = [];
  const cautions = [];
  let score = 20;

  const fullName = String(record.full_name || "").trim();
  const nameParts = fullName.split(/\s+/).filter(Boolean);
  if (nameParts.length >= 2) {
    score += 4;
    positives.push("Submitted a full name instead of a single-handle identity.");
  } else if (fullName) {
    score -= 6;
    cautions.push("Name field is thin and may need a quick identity check.");
  } else {
    score -= 12;
    cautions.push("Missing a usable full name.");
  }

  const graduationYear = Number(record.graduation_year || 0);
  const currentYear = new Date().getFullYear();
  if (Number.isInteger(graduationYear) && graduationYear >= 1980 && graduationYear <= currentYear + 1) {
    score += 8;
    positives.push(`Includes a plausible graduation year (${graduationYear}).`);
  } else {
    score -= 10;
    cautions.push("Graduation year is missing or falls outside the expected range.");
  }

  const connectionPath = String(record.connection_path || "").trim();
  const normalizedPath = connectionPath.toLowerCase();
  if (["tom", "kathleen", "nikki"].includes(normalizedPath)) {
    score += 12;
    positives.push(`Came through a known relationship path (${connectionPath}).`);
  } else if (["linkedin", "social"].includes(normalizedPath)) {
    score += 5;
    positives.push(`Came through a traceable outreach path (${connectionPath}).`);
  } else if (normalizedPath === "other") {
    score += 2;
    cautions.push("Connection path is generic, so the context should be reviewed more closely.");
  } else if (!connectionPath) {
    score -= 6;
    cautions.push("Connection path is missing.");
  }

  const verificationContext = String(record.verification_context || "").trim();
  if (verificationContext.length >= 120) {
    score += 12;
    positives.push("Provides detailed verification context.");
  } else if (verificationContext.length >= 60) {
    score += 8;
    positives.push("Provides enough verification context to evaluate the claim.");
  } else if (verificationContext.length >= 25) {
    score += 3;
    positives.push("Provides some verification context.");
  } else {
    score -= 14;
    cautions.push("Verification context is brief and may not be enough on its own.");
  }

  const evidenceText = `${verificationContext} ${String(record.written_note || "").trim()}`.trim();
  const matchedTerms = getMatchedWritingCenterTerms(evidenceText);
  if (matchedTerms.length >= 3) {
    score += 14;
    positives.push(`References multiple Writing Center-specific details: ${matchedTerms.join(", ")}.`);
  } else if (matchedTerms.length >= 1) {
    score += 8;
    positives.push(`References recognizable Writing Center details: ${matchedTerms.join(", ")}.`);
  } else {
    score -= 12;
    cautions.push("Does not mention recognizable Writing Center-specific details yet.");
  }

  const emailDomain = getEmailDomain(record.email);
  if (emailDomain && WRITING_CENTER_DISPOSABLE_EMAIL_DOMAINS.has(emailDomain)) {
    score -= 24;
    cautions.push(`Uses a disposable-looking email domain (${emailDomain}).`);
  } else if (emailDomain.endsWith(".edu")) {
    score += 4;
    positives.push(`Uses an academic email domain (${emailDomain}).`);
  } else if (emailDomain) {
    score += 2;
    positives.push(`Provides a direct contact email (${emailDomain}).`);
  } else {
    score -= 10;
    cautions.push("Email domain could not be evaluated.");
  }

  const linkedinUrl = String(record.linkedin_url || "").trim();
  if (linkedinUrl) {
    if (/linkedin\.com/i.test(linkedinUrl)) {
      score += 6;
      positives.push("Includes a LinkedIn profile that can be corroborated.");
    } else {
      score += 2;
      positives.push("Includes an external profile link for corroboration.");
    }
  } else {
    score -= 4;
    cautions.push("No LinkedIn or profile link was provided.");
  }

  if (String(record.current_role_org || "").trim()) {
    score += 3;
    positives.push("Shares a current role or organization.");
  } else {
    score -= 3;
    cautions.push("No current role or organization was provided.");
  }

  if (String(record.network_interest || "").trim() || String(record.future_contact_ok || "").toLowerCase() === "yes") {
    score += 2;
    positives.push("Seems open to ongoing alumni contact beyond this one tribute.");
  }

  if (String(record.tribute_submitted_at || "").trim()) {
    const writtenNote = String(record.written_note || "").trim();
    if (writtenNote.length >= 80) {
      score += 5;
      positives.push("Tribute note includes enough detail to compare tone and context.");
    } else if (writtenNote.length > 0) {
      score += 2;
      positives.push("Tribute note adds a little more direct evidence.");
    }
    if (String(record.selfie_filename || "").trim()) {
      score += 3;
      positives.push("Submitted a current selfie that can help with recognition.");
    }
    if (String(record.video_filename || record.video_link || "").trim()) {
      score += 3;
      positives.push("Submitted a video artifact that can be manually reviewed.");
    }
  }

  const spamScore = Number(record.spam_score || 0);
  if (String(record.spam_flag || "").toLowerCase() === "yes") {
    score -= 40;
    cautions.push("Submission was flagged by the spam filter and should be independently verified.");
  } else if (Number.isFinite(spamScore) && spamScore >= 25) {
    score -= 18;
    cautions.push(`Spam score is elevated (${spamScore}).`);
  }

  score = Math.max(0, Math.min(100, score));

  let status = "investigate";
  let statusLabel = "Needs Investigation";
  let summary = "The submission does not yet have enough specific support to be treated as confirmed without follow-up.";
  if (score >= 82) {
    status = "high_confidence";
    statusLabel = "High Confidence";
    summary = "Submitted details strongly suggest a real Writing Center connection.";
  } else if (score >= 68) {
    status = "credible";
    statusLabel = "Credible";
    summary = "Submitted details look plausible, with enough support for a light-touch human review.";
  } else if (score >= 52) {
    status = "needs_review";
    statusLabel = "Needs Review";
    summary = "Some signals look real, but the record would benefit from extra verification.";
  }

  return {
    score,
    status,
    statusLabel,
    summary,
    positiveSignals: positives,
    cautionSignals: cautions,
  };
}

function buildWritingCenterWorkflowStage(record) {
  if (String(record.review_status || "") === "approved" && String(record.publish_to_screen || "") === "yes") {
    return "approved_for_display";
  }
  if (String(record.invite_status || "") === "tribute_submitted") {
    return String(record.review_status || "") === "approved" ? "tribute_approved" : "needs_content_review";
  }
  if (String(record.interest_status || "") === "approved") {
    if (String(record.invite_status || "") === "sent") return "awaiting_tribute";
    return "approved_ready_to_invite";
  }
  if (String(record.interest_status || "") === "hold") return "interest_hold";
  if (String(record.interest_status || "") === "rejected") return "rejected";
  return "needs_interest_review";
}

function shapeWritingCenterReviewRecord(record) {
  const assessment = buildWritingCenterVettingAssessment(record);
  return {
    ...record,
    vetting_score: assessment.score,
    vetting_status: assessment.status,
    vetting_status_label: assessment.statusLabel,
    vetting_summary: assessment.summary,
    vetting_positive_signals: assessment.positiveSignals,
    vetting_caution_signals: assessment.cautionSignals,
    vetting_review_notes: record.vetting_review_notes || "",
    selfie_preview_url: toRepoAssetUrl(record.selfie_storage_path),
    video_preview_url: toRepoAssetUrl(record.video_storage_path),
    workflow_stage: buildWritingCenterWorkflowStage(record),
  };
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

function normalizeWritingCenterInterest(body = {}, req) {
  const submissionId = `tribute-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const fullName = cleanSingleLine(body.full_name || body.fullName, 120);
  const email = cleanSingleLine(body.email, 160).toLowerCase();
  const currentRoleOrg = cleanSingleLine(body.current_role_org || body.currentRoleOrg, 180);
  const linkedinUrl = cleanSingleLine(body.linkedin_url || body.linkedinUrl, 300);
  const bestContactMethod = cleanSingleLine(body.best_contact_method || body.bestContactMethod, 40).toLowerCase();
  const networkInterest = cleanMultiline(body.network_interest || body.networkInterest, 1200);
  const connectionPath = cleanSingleLine(body.connection_path || body.connectionPath, 80);
  const verificationContext = cleanMultiline(body.verification_context || body.verificationContext, 1200);
  const futureContactOk = toYesNo(body.future_contact_ok || body.futureContactOk, "no");
  const graduationYear = String(body.graduation_year || body.graduationYear || "").trim();

  if (!fullName) throw new Error("Full name is required");
  if (!isValidEmail(email)) throw new Error("A valid email is required");
  if (!/^\d{4}$/.test(graduationYear)) throw new Error("Graduation year must be a four-digit year");

  const parsedYear = Number(graduationYear);
  const currentYear = new Date().getFullYear();
  if (parsedYear < 1980 || parsedYear > currentYear + 1) {
    throw new Error(`Graduation year must fall between 1980 and ${currentYear + 1}`);
  }

  if (!connectionPath) throw new Error("Please tell us how you are connected to the Writing Center");
  if (verificationContext.length < 8) {
    throw new Error("Please include a little more context so we can verify your connection");
  }
  if (bestContactMethod && !["email", "linkedin", "either"].includes(bestContactMethod)) {
    throw new Error("Best contact method must be email, LinkedIn, or either");
  }

  const inboundEvent = normalizeInboundEvent(
    {
      channel: "contact",
      context: `${fullName} ${networkInterest || verificationContext}`.trim(),
      source_page: body.source_page || body.pageUrl || body.page_url || "",
      honeypot: body.website || body.honeypot || "",
      referrer: body.referrer || "",
      user_agent: body.user_agent || "",
    },
    req
  );
  const spam = scoreSpam(inboundEvent);
  if (spam.isSpam) {
    throw new Error("This submission was flagged as spam. Please email Tom directly instead.");
  }

  return {
    submission_id: submissionId,
    interest_submitted_at: new Date().toISOString(),
    full_name: fullName,
    email,
    graduation_year: String(parsedYear),
    current_role_org: currentRoleOrg,
    linkedin_url: linkedinUrl,
    best_contact_method: bestContactMethod || "email",
    network_interest: networkInterest,
    connection_path: connectionPath,
    verification_context: verificationContext,
    future_contact_ok: futureContactOk,
    interest_status: "pending",
    interest_reviewed_at: "",
    interest_review_notes: "",
    vetting_review_notes: "",
    invite_token: "",
    invite_status: "not_ready",
    invite_created_at: "",
    invite_sent_at: "",
    tribute_submitted_at: "",
    preferred_display_name: "",
    written_note: "",
    video_link: "",
    video_filename: "",
    video_storage_path: "",
    video_mime_type: "",
    video_size_bytes: "",
    selfie_filename: "",
    selfie_storage_path: "",
    selfie_mime_type: "",
    selfie_size_bytes: "",
    share_permission: "",
    display_permission: "",
    review_status: "not_submitted",
    review_updated_at: "",
    review_notes: "",
    published_display_name: "",
    published_role_org: currentRoleOrg,
    published_note: "",
    publish_to_screen: "no",
    display_order: "",
    interest_source_page: inboundEvent.sourcePage,
    tribute_source_page: "",
    referrer: inboundEvent.referrer,
    user_agent: inboundEvent.userAgent,
    ip_hash: inboundEvent.ipHash,
    spam_score: String(spam.score),
    spam_flag: spam.isSpam ? "yes" : "no",
    spam_reasons: spam.reasons.join("|"),
  };
}

function applyWritingCenterTributeSubmission(record, body = {}, req) {
  const preferredDisplayName = cleanSingleLine(body.preferred_display_name || body.preferredDisplayName || record.full_name, 120);
  const updatedRoleOrg = cleanSingleLine(body.current_role_org || body.currentRoleOrg || record.current_role_org, 180);
  const writtenNote = cleanMultiline(body.written_note || body.writtenNote, 5000);
  const videoLink = cleanSingleLine(body.video_link || body.videoLink, 300);
  const sharePermissionRaw = cleanSingleLine(body.share_permission || body.sharePermission, 12).toLowerCase();
  const displayPermissionRaw = cleanSingleLine(body.display_permission || body.displayPermission, 12).toLowerCase();
  const sharePermission = ["yes", "no"].includes(sharePermissionRaw) ? sharePermissionRaw : "unclear";
  const displayPermission = ["yes", "no"].includes(displayPermissionRaw) ? displayPermissionRaw : "no";
  const hasVideoUpload = !!(body.video && (body.video.data_url || body.video.dataUrl));
  if (!writtenNote && !videoLink && !hasVideoUpload) {
    throw new Error("Please include a written note, a short video, or a video link");
  }

  const inboundEvent = normalizeInboundEvent(
    {
      channel: "contact",
      context: `${record.full_name} ${writtenNote || videoLink}`.trim(),
      source_page: body.source_page || body.pageUrl || body.page_url || "",
      honeypot: body.website || body.honeypot || "",
      referrer: body.referrer || "",
      user_agent: body.user_agent || "",
    },
    req
  );
  const spam = scoreSpam(inboundEvent);
  if (spam.isSpam) {
    throw new Error("This tribute submission was flagged as spam. Please contact Tom directly instead.");
  }

  const videoMeta = saveWritingCenterVideo(body.video, record.submission_id);
  const selfieMeta = saveWritingCenterSelfie(body.selfie, record.submission_id);

  record.current_role_org = updatedRoleOrg;
  record.preferred_display_name = preferredDisplayName;
  record.written_note = writtenNote;
  record.video_link = videoLink;
  if (videoMeta) {
    record.video_filename = videoMeta.filename;
    record.video_storage_path = videoMeta.storagePath;
    record.video_mime_type = videoMeta.mimeType;
    record.video_size_bytes = String(videoMeta.sizeBytes);
  }
  if (selfieMeta) {
    record.selfie_filename = selfieMeta.filename;
    record.selfie_storage_path = selfieMeta.storagePath;
    record.selfie_mime_type = selfieMeta.mimeType;
    record.selfie_size_bytes = String(selfieMeta.sizeBytes);
  }
  record.share_permission = sharePermission;
  record.display_permission = displayPermission;
  record.tribute_submitted_at = new Date().toISOString();
  record.invite_status = "tribute_submitted";
  record.review_status = "pending";
  record.review_updated_at = "";
  record.review_notes = "";
  record.published_display_name = preferredDisplayName || record.full_name;
  record.published_role_org = updatedRoleOrg;
  record.published_note = writtenNote;
  record.publish_to_screen = "no";
  record.display_order = "";
  record.tribute_source_page = inboundEvent.sourcePage;
  return record;
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

  if (pathname === "/api/writing-center-tributes/published" && method === "GET") {
    try {
      const feed = fs.existsSync(WRITING_CENTER_TRIBUTE_PUBLIC_FEED_FILE)
        ? JSON.parse(fs.readFileSync(WRITING_CENTER_TRIBUTE_PUBLIC_FEED_FILE, "utf8"))
        : { updatedAt: "", itemCount: 0, items: [] };
      return sendJson(res, feed);
    } catch (error) {
      return sendJson(res, { error: error.message }, 500);
    }
  }

  if (pathname === "/api/writing-center-tributes/review" && method === "GET") {
    const auth = authorizeWritingCenterAdmin(req);
    if (!auth.ok) {
      return sendJson(res, { error: auth.error }, auth.status);
    }
    const items = loadWritingCenterTributes()
      .sort((a, b) =>
        String(b.tribute_submitted_at || b.interest_submitted_at || "").localeCompare(
          String(a.tribute_submitted_at || a.interest_submitted_at || "")
        )
      )
      .map(shapeWritingCenterReviewRecord);
    return sendJson(res, {
      items,
      admin_mode: auth.mode,
      feed_path: "boss-key-website/data/writing-center-tribute-display.json",
      invite_page_path: "boss-key-website/writing-center-alumni-tribute-compose.html",
    });
  }

  if (pathname === "/api/writing-center-interest" && method === "POST") {
    try {
      const body = await parseBody(req, WRITING_CENTER_TRIBUTE_PAYLOAD_MAX_BYTES);
      const submission = normalizeWritingCenterInterest(body, req);
      const records = loadWritingCenterTributes();
      records.push(submission);
      saveWritingCenterTributes(records);
      return sendJson(
        res,
        {
          ok: true,
          submission_id: submission.submission_id,
        },
        201
      );
    } catch (error) {
      return sendJson(res, { error: error.message }, 400);
    }
  }

  const writingCenterInviteViewMatch = pathname.match(/^\/api\/writing-center-invites\/([^/]+)$/);
  if (writingCenterInviteViewMatch && method === "GET") {
    const inviteToken = writingCenterInviteViewMatch[1];
    const record = loadWritingCenterTributes().find((item) => item.invite_token === inviteToken);
    if (!record || String(record.interest_status || "") !== "approved") {
      return sendJson(res, { error: "Invitation not found or no longer active" }, 404);
    }
    return sendJson(res, {
      ok: true,
      full_name: record.full_name,
      preferred_display_name: record.preferred_display_name || record.full_name,
      email: record.email,
      graduation_year: record.graduation_year,
      current_role_org: record.current_role_org,
      network_interest: record.network_interest || "",
      tribute_submitted: String(record.invite_status || "") === "tribute_submitted",
      display_permission: record.display_permission || "no",
      share_permission: record.share_permission || "yes",
    });
  }

  const writingCenterInviteSubmitMatch = pathname.match(/^\/api\/writing-center-invites\/([^/]+)\/tribute$/);
  if (writingCenterInviteSubmitMatch && method === "POST") {
    try {
      const inviteToken = writingCenterInviteSubmitMatch[1];
      const body = await parseBody(req, WRITING_CENTER_TRIBUTE_PAYLOAD_MAX_BYTES);
      const records = loadWritingCenterTributes();
      const target = records.find((item) => item.invite_token === inviteToken);
      if (!target || String(target.interest_status || "") !== "approved") {
        return sendJson(res, { error: "Invitation not found or no longer active" }, 404);
      }
      applyWritingCenterTributeSubmission(target, body, req);
      saveWritingCenterTributes(records);
      return sendJson(
        res,
        {
          ok: true,
          submission_id: target.submission_id,
          stored_video: !!target.video_filename,
          stored_selfie: !!target.selfie_filename,
        },
        201
      );
    } catch (error) {
      return sendJson(res, { error: error.message }, 400);
    }
  }

  const writingCenterTributeMatch = pathname.match(/^\/api\/writing-center-tributes\/([^/]+)$/);
  if (writingCenterTributeMatch && method === "PUT") {
    const auth = authorizeWritingCenterAdmin(req);
    if (!auth.ok) {
      return sendJson(res, { error: auth.error }, auth.status);
    }
    try {
      const submissionId = writingCenterTributeMatch[1];
      const body = await parseBody(req);
      const records = loadWritingCenterTributes();
      const target = records.find((record) => record.submission_id === submissionId);
      if (!target) {
        return sendJson(res, { error: "Submission not found" }, 404);
      }

      const nextInterestStatus = cleanSingleLine(body.interest_status || body.interestStatus || target.interest_status, 20).toLowerCase();
      if (!["pending", "approved", "hold", "rejected"].includes(nextInterestStatus)) {
        return sendJson(res, { error: "Invalid interest status" }, 400);
      }

      const nextInviteStatus = cleanSingleLine(body.invite_status || body.inviteStatus || target.invite_status, 24).toLowerCase();
      if (!["not_ready", "generated", "sent", "tribute_submitted"].includes(nextInviteStatus)) {
        return sendJson(res, { error: "Invalid invite status" }, 400);
      }

      const nextReviewStatus = cleanSingleLine(body.review_status || body.reviewStatus || target.review_status, 20).toLowerCase();
      if (!["not_submitted", "pending", "approved", "hold", "rejected"].includes(nextReviewStatus)) {
        return sendJson(res, { error: "Invalid review status" }, 400);
      }

      const nextPublishToScreen = toYesNo(body.publish_to_screen || body.publishToScreen || target.publish_to_screen, "no");
      const nextDisplayOrder = cleanSingleLine(body.display_order || body.displayOrder || target.display_order, 12);
      if (nextDisplayOrder && !/^\d+$/.test(nextDisplayOrder)) {
        return sendJson(res, { error: "Display order must be a whole number" }, 400);
      }

      target.interest_status = nextInterestStatus;
      target.interest_reviewed_at = new Date().toISOString();
      target.interest_review_notes = cleanMultiline(
        body.interest_review_notes || body.interestReviewNotes || target.interest_review_notes,
        1600
      );
      target.vetting_review_notes = cleanMultiline(
        body.vetting_review_notes || body.vettingReviewNotes || target.vetting_review_notes,
        1600
      );
      target.best_contact_method = cleanSingleLine(
        body.best_contact_method || body.bestContactMethod || target.best_contact_method,
        40
      ).toLowerCase();
      target.current_role_org = cleanSingleLine(
        body.current_role_org || body.currentRoleOrg || target.current_role_org,
        180
      );
      target.linkedin_url = cleanSingleLine(body.linkedin_url || body.linkedinUrl || target.linkedin_url, 300);
      target.network_interest = cleanMultiline(
        body.network_interest || body.networkInterest || target.network_interest,
        1200
      );

      if (nextInterestStatus === "approved" && !target.invite_token) {
        target.invite_token = makeWritingCenterInviteToken();
        target.invite_created_at = new Date().toISOString();
      }

      if (nextInterestStatus !== "approved") {
        target.invite_status = "not_ready";
      } else {
        target.invite_status = nextInviteStatus === "not_ready" ? "generated" : nextInviteStatus;
      }
      if (target.invite_status === "generated" && !target.invite_created_at) {
        target.invite_created_at = new Date().toISOString();
      }
      if (target.invite_status === "sent" && !target.invite_sent_at) {
        target.invite_sent_at = new Date().toISOString();
      }

      target.review_status = nextReviewStatus;
      target.review_updated_at = nextReviewStatus === "not_submitted" ? "" : new Date().toISOString();
      target.review_notes = cleanMultiline(body.review_notes || body.reviewNotes || target.review_notes, 1600);
      target.published_display_name = cleanSingleLine(
        body.published_display_name || body.publishedDisplayName || target.published_display_name || target.preferred_display_name || target.full_name,
        120
      );
      target.published_role_org = cleanSingleLine(
        body.published_role_org || body.publishedRoleOrg || target.published_role_org || target.current_role_org,
        180
      );
      target.published_note = cleanMultiline(
        body.published_note || body.publishedNote || target.published_note || target.written_note,
        5000
      );
      target.publish_to_screen = nextPublishToScreen;
      target.display_order = nextDisplayOrder;

      saveWritingCenterTributes(records);
      return sendJson(res, { ok: true, item: shapeWritingCenterReviewRecord(target) });
    } catch (error) {
      return sendJson(res, { error: error.message }, 400);
    }
  }

  if (
    pathname === "/api/writing-center-tributes" ||
    pathname === "/api/writing-center-interest" ||
    pathname.startsWith("/api/writing-center-invites/")
  ) {
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
    : ext === ".mp4"
    ? "video/mp4"
    : ext === ".webm"
    ? "video/webm"
    : ext === ".mov"
    ? "video/quicktime"
    : ext === ".csv"
    ? "text/csv"
    : ext === ".md" || ext === ".txt"
    ? "text/plain"
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
    pathname === "/api/writing-center-interest" ||
    pathname.startsWith("/api/writing-center-invites") ||
    pathname.startsWith("/api/writing-center-tributes") ||
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
  ensureWritingCenterTributesFile();
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
















