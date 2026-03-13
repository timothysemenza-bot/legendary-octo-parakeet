const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const MARKETING_AGENTS_ROOT = path.join(__dirname, "..");
const REPO_ROOT = path.join(MARKETING_AGENTS_ROOT, "..");
const DATA_DIR = path.join(MARKETING_AGENTS_ROOT, "data");
const BRIEFS_DIR = path.join(MARKETING_AGENTS_ROOT, "briefs");

const PATHS = {
  config: path.join(DATA_DIR, "communication_sync_sources.json"),
  state: path.join(DATA_DIR, "communication_sync_state.json"),
  summaryJson: path.join(DATA_DIR, "communication_sync_summary.json"),
  summaryMd: path.join(BRIEFS_DIR, "communication-sync-latest.md"),
  liveSyncRoot: path.join(DATA_DIR, "engagement-inbox", "live-sync"),
  intakeScript: path.join(__dirname, "run-engagement-intake.js"),
  intakeSummary: path.join(DATA_DIR, "engagement_intake_summary.json"),
};

const FREE_EMAIL_DOMAINS = new Set([
  "gmail.com",
  "googlemail.com",
  "outlook.com",
  "hotmail.com",
  "live.com",
  "icloud.com",
  "me.com",
  "yahoo.com",
  "aol.com",
  "msn.com",
  "comcast.net",
  "verizon.net",
  "att.net",
  "proton.me",
  "protonmail.com",
]);

loadEnvFile(path.join(REPO_ROOT, ".env"));
loadEnvFile(path.join(REPO_ROOT, ".env.local"));
loadEnvFile(path.join(MARKETING_AGENTS_ROOT, ".env"));
loadEnvFile(path.join(MARKETING_AGENTS_ROOT, ".env.local"));

main().catch((error) => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 1;
});

async function main() {
  ensureDir(BRIEFS_DIR);
  ensureDir(PATHS.liveSyncRoot);

  const config = readJson(PATHS.config, { defaults: {}, sources: [] });
  const state = readJson(PATHS.state, { processed: {} });
  if (!state.processed || typeof state.processed !== "object") state.processed = {};

  const summary = createSummary();
  for (const source of config.sources || []) {
    if (!source || source.enabled !== true) continue;
    const result = await syncSource(source, config.defaults || {}, state);
    summary.sources.push(result);
    summary.captures_created += Number(result.captures_created || 0);
    summary.captures_skipped += Number(result.captures_skipped || 0);
    summary.errors += Number(result.errors || 0);
  }

  const intakeResult = runEngagementIntake();
  summary.intake = intakeResult;
  summary.last_run_at = nowIso();

  writeJson(PATHS.state, state);
  writeJson(PATHS.summaryJson, summary);
  writeSummaryMarkdown(summary);
  process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
}

function createSummary() {
  return {
    last_run_at: "",
    captures_created: 0,
    captures_skipped: 0,
    errors: 0,
    sources: [],
    intake: null,
  };
}

async function syncSource(source, defaults, state) {
  if (source.provider === "gmail") {
    return syncGmailSource(source, defaults, state);
  }
  if (source.provider === "microsoft_graph_mail") {
    return syncGraphMailSource(source, defaults, state);
  }
  if (source.provider === "microsoft_graph_calendar") {
    return syncGraphCalendarSource(source, defaults, state);
  }
  if (source.provider === "ics_calendar") {
    return syncIcsCalendarSource(source, defaults, state);
  }
  return {
    source_id: source.source_id,
    provider: source.provider,
    captures_created: 0,
    captures_skipped: 0,
    errors: 1,
    status: "unsupported-provider",
    notes: `Unsupported provider: ${source.provider}`,
  };
}

function runEngagementIntake() {
  const result = spawnSync(process.execPath, [PATHS.intakeScript], {
    cwd: REPO_ROOT,
    encoding: "utf8",
  });

  if (result.status !== 0) {
    return {
      ok: false,
      error: (result.stderr || result.stdout || "Engagement intake failed.").trim(),
    };
  }

  const latestSummary = readJson(PATHS.intakeSummary, null);
  return {
    ok: true,
    summary: latestSummary,
  };
}

function loadEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return;
  const raw = fs.readFileSync(filePath, "utf8");
  raw.split(/\r?\n/).forEach((line) => {
    const trimmed = String(line || "").trim();
    if (!trimmed || trimmed.startsWith("#")) return;
    const index = trimmed.indexOf("=");
    if (index <= 0) return;
    const key = trimmed.slice(0, index).trim();
    let value = trimmed.slice(index + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (process.env[key] === undefined) process.env[key] = value;
  });
}

function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) fs.mkdirSync(dirPath, { recursive: true });
}

function readJson(filePath, fallback) {
  if (!fs.existsSync(filePath)) return fallback;
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (_error) {
    return fallback;
  }
}

function writeJson(filePath, value) {
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function nowIso() {
  return new Date().toISOString().slice(0, 19);
}

function dateIso(value = new Date()) {
  return new Date(value).toISOString().slice(0, 10);
}

function resolveRepoPath(value) {
  if (!value) return "";
  if (path.isAbsolute(value)) return value;
  return path.join(REPO_ROOT, value);
}

function truncate(value, maxLength) {
  const text = String(value || "").trim();
  if (text.length <= maxLength) return text;
  return `${text.slice(0, Math.max(0, maxLength - 3)).trim()}...`;
}

function slugify(value) {
  const cleaned = String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return cleaned || "item";
}

function htmlToText(value) {
  return String(value || "")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/p>/gi, "\n")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/\s+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .replace(/[ \t]{2,}/g, " ")
    .trim();
}

function stripAngleAddress(value) {
  const match = String(value || "").match(/<([^>]+)>/);
  return (match ? match[1] : value || "").trim().toLowerCase();
}

function getDomain(address) {
  const at = String(address || "").split("@");
  return at.length > 1 ? at[1].toLowerCase() : "";
}

function decodeBase64Url(value) {
  const normalized = String(value || "").replace(/-/g, "+").replace(/_/g, "/");
  const padding = normalized.length % 4 === 0 ? "" : "=".repeat(4 - (normalized.length % 4));
  return Buffer.from(`${normalized}${padding}`, "base64").toString("utf8");
}

async function syncGmailSource(source, defaults, state) {
  const tokenPath = resolveRepoPath(source.token_path || process.env.GOOGLE_GMAIL_OAUTH_TOKEN_JSON || "");
  const outputDir = resolveRepoPath(source.output_dir || path.join("marketing-agents", "data", "engagement-inbox", "live-sync", "gmail"));
  ensureDir(outputDir);

  if (!tokenPath || !fs.existsSync(tokenPath)) {
    return buildSourceResult(source, "missing-token", "Gmail token file not found.");
  }

  try {
    const accessToken = await refreshGoogleAccessToken(tokenPath);
    const messageIds = await listGmailMessages(accessToken, source);
    let capturesCreated = 0;
    let capturesSkipped = 0;

    for (const messageId of messageIds) {
      const processedKey = `${source.source_id}|${messageId}`;
      if (state.processed[processedKey]) {
        capturesSkipped += 1;
        continue;
      }

      const message = await getGmailMessage(accessToken, messageId);
      const normalized = normalizeGmailMessage(message, source, defaults);
      if (!normalized || shouldSkipEmailCapture(normalized, source, defaults)) {
        state.processed[processedKey] = { skipped: true, processed_at: nowIso() };
        capturesSkipped += 1;
        continue;
      }

      writeCaptureFile(outputDir, normalized.fileName, normalized.content);
      state.processed[processedKey] = {
        skipped: false,
        provider: source.provider,
        message_id: messageId,
        capture_file: path.relative(REPO_ROOT, path.join(outputDir, normalized.fileName)).replace(/\\/g, "/"),
        processed_at: nowIso(),
      };
      capturesCreated += 1;
    }

    return {
      source_id: source.source_id,
      provider: source.provider,
      captures_created: capturesCreated,
      captures_skipped: capturesSkipped,
      errors: 0,
      status: "ok",
      notes: `Fetched ${messageIds.length} Gmail message ids.`,
    };
  } catch (error) {
    return buildSourceResult(source, "error", error.message, 1);
  }
}

async function refreshGoogleAccessToken(tokenPath) {
  const tokenData = readJson(tokenPath, null);
  if (!tokenData || !tokenData.refresh_token || !tokenData.client_id || !tokenData.client_secret || !tokenData.token_uri) {
    throw new Error("Gmail token file is missing refresh credentials.");
  }

  const body = new URLSearchParams({
    client_id: tokenData.client_id,
    client_secret: tokenData.client_secret,
    refresh_token: tokenData.refresh_token,
    grant_type: "refresh_token",
  });

  const response = await fetch(tokenData.token_uri, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  const payload = await response.json();
  if (!response.ok || !payload.access_token) {
    throw new Error(payload.error_description || payload.error || "Failed to refresh Gmail access token.");
  }

  const nextTokenData = {
    ...tokenData,
    token: payload.access_token,
    expiry: payload.expires_in ? new Date(Date.now() + (Number(payload.expires_in) * 1000)).toISOString() : tokenData.expiry,
  };
  writeJson(tokenPath, nextTokenData);
  return payload.access_token;
}

async function listGmailMessages(accessToken, source) {
  const params = new URLSearchParams();
  params.set("maxResults", String(source.max_results || 15));
  if (source.query) params.set("q", source.query);
  (source.label_ids || []).forEach((labelId) => params.append("labelIds", labelId));

  const response = await fetch(`https://gmail.googleapis.com/gmail/v1/users/me/messages?${params.toString()}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error?.message || "Failed to list Gmail messages.");
  }
  return (payload.messages || []).map((message) => message.id).filter(Boolean);
}

async function getGmailMessage(accessToken, messageId) {
  const response = await fetch(`https://gmail.googleapis.com/gmail/v1/users/me/messages/${messageId}?format=full`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error?.message || `Failed to fetch Gmail message ${messageId}.`);
  }
  return payload;
}

function normalizeGmailMessage(message, source, defaults) {
  const headers = getGmailHeaderMap(message.payload?.headers || []);
  const subject = headers.subject || "(No Subject)";
  const from = headers.from || "";
  const to = headers.to || "";
  const cc = headers.cc || "";
  const dateHeader = headers.date || "";
  const internalDate = message.internalDate ? new Date(Number(message.internalDate)).toISOString() : "";
  const bodyText = extractGmailBody(message.payload);
  const direction = inferDirection(from, to, defaults);
  const attachmentNames = collectGmailAttachmentNames(message.payload);
  const counterparty = direction === "outbound" ? to : from;
  const captureDate = internalDate ? dateIso(internalDate) : dateIso();
  const safeSubject = truncate(subject.replace(/[\\/:*?"<>|]+/g, " "), 72);
  const fileName = `${captureDate}__gmail__${slugify(safeSubject)}__${message.id}.md`;

  return {
    direction,
    subject,
    from,
    to,
    cc,
    counterparty,
    labelIds: message.labelIds || [],
    attachmentNames,
    date: captureDate,
    text: bodyText,
    snippet: message.snippet || "",
    fileName,
    content: [
      `Subject: ${subject}`,
      `Direction: ${direction}`,
      `Date: ${dateHeader || internalDate || captureDate}`,
      `From: ${from}`,
      `To: ${to}`,
      `CC: ${cc}`,
      `Thread ID: ${message.threadId || ""}`,
      `Labels: ${(message.labelIds || []).join(", ")}`,
      `Attachments: ${attachmentNames.join(", ")}`,
      `Source: Gmail live sync (${source.source_id})`,
      "",
      "Body:",
      "",
      bodyText || message.snippet || "",
    ].join("\n"),
  };
}

function getGmailHeaderMap(headers) {
  const map = {};
  headers.forEach((header) => {
    const key = String(header.name || "").toLowerCase();
    if (!key) return;
    map[key] = String(header.value || "").trim();
  });
  return map;
}

function extractGmailBody(payload) {
  if (!payload) return "";
  if (payload.mimeType === "text/plain" && payload.body?.data) {
    return decodeBase64Url(payload.body.data);
  }
  if (payload.mimeType === "text/html" && payload.body?.data) {
    return htmlToText(decodeBase64Url(payload.body.data));
  }
  const parts = payload.parts || [];
  for (const part of parts) {
    const extracted = extractGmailBody(part);
    if (extracted) return extracted;
  }
  if (payload.body?.data) return decodeBase64Url(payload.body.data);
  return "";
}

function collectGmailAttachmentNames(payload, bucket = []) {
  if (!payload) return bucket;
  if (payload.filename) bucket.push(payload.filename);
  (payload.parts || []).forEach((part) => collectGmailAttachmentNames(part, bucket));
  return bucket.filter(Boolean);
}

function shouldSkipEmailCapture(email, source, defaults) {
  const skipPatterns = [...(defaults.skip_sender_patterns || []), ...(source.skip_sender_patterns || [])].map((value) => String(value).toLowerCase());
  const fromLower = String(email.from || "").toLowerCase();
  if (skipPatterns.some((pattern) => pattern && fromLower.includes(pattern))) return true;
  if ((email.labelIds || []).some((label) => ["CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL", "SPAM", "TRASH"].includes(label))) return true;
  if (!source.require_business_signal) return false;
  return !hasBusinessSignal(email, source, defaults);
}

function hasBusinessSignal(email, source, defaults) {
  const combined = [email.subject, email.text, email.snippet].join(" ").toLowerCase();
  const keywords = [...(defaults.business_keywords || []), ...(source.business_keywords || [])].map((value) => String(value).toLowerCase());
  if (keywords.some((keyword) => keyword && combined.includes(keyword))) return true;
  if ((email.attachmentNames || []).length > 0) return true;
  if (/meet\.google\.com|zoom\.us|teams\.microsoft\.com|calendar|invite/i.test(combined)) return true;

  const addresses = [email.from, email.to, email.cc]
    .join(",")
    .split(/[;,]/)
    .map((value) => stripAngleAddress(value))
    .filter(Boolean);

  return addresses.some((address) => {
    const domain = getDomain(address);
    return domain && !FREE_EMAIL_DOMAINS.has(domain);
  });
}

function inferDirection(from, to, defaults) {
  const selfAddresses = new Set((defaults.self_addresses || []).map((value) => String(value).trim().toLowerCase()).filter(Boolean));
  const fromAddress = stripAngleAddress(from);
  const toAddresses = String(to || "").split(/[;,]/).map((value) => stripAngleAddress(value)).filter(Boolean);
  if (selfAddresses.has(fromAddress)) return "outbound";
  if (toAddresses.some((address) => selfAddresses.has(address))) return "inbound";
  return "unknown";
}

function writeCaptureFile(outputDir, fileName, content) {
  ensureDir(outputDir);
  fs.writeFileSync(path.join(outputDir, fileName), `${String(content || "").trim()}\n`, "utf8");
}

function buildSourceResult(source, status, notes, errors = 0) {
  return {
    source_id: source.source_id,
    provider: source.provider,
    captures_created: 0,
    captures_skipped: 0,
    errors,
    status,
    notes,
  };
}
