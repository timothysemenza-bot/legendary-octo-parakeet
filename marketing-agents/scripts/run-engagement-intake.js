const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const MARKETING_AGENTS_ROOT = path.join(__dirname, "..");
const REPO_ROOT = path.join(MARKETING_AGENTS_ROOT, "..");
const DATA_DIR = path.join(MARKETING_AGENTS_ROOT, "data");
const BRIEFS_DIR = path.join(MARKETING_AGENTS_ROOT, "briefs");

const PATHS = {
  sourceConfig: path.join(DATA_DIR, "approved_communication_sources.csv"),
  state: path.join(DATA_DIR, "engagement_intake_state.json"),
  summaryJson: path.join(DATA_DIR, "engagement_intake_summary.json"),
  summaryMd: path.join(BRIEFS_DIR, "engagement-intake-latest.md"),
  signalLog: path.join(DATA_DIR, "communication_signal_log.csv"),
  engagementRegister: path.join(DATA_DIR, "engagement_register.csv"),
  engagementTimeline: path.join(DATA_DIR, "engagement_timeline.csv"),
  stakeholderMap: path.join(DATA_DIR, "stakeholder_map.csv"),
  actionWorkbench: path.join(DATA_DIR, "action_workbench.csv"),
  approvalRouterQueue: path.join(DATA_DIR, "approval_router_queue.csv"),
  meetingFollowThrough: path.join(DATA_DIR, "meeting_follow_through.csv"),
};

const OWNER = "Timmy Semenza";
const SUPPORTED_FILE_EXTENSIONS = new Set([".txt", ".md", ".json", ".eml", ".srt"]);

const CSV_HEADERS = {
  signalLog: [
    "signal_id",
    "source_type",
    "source_system",
    "client_name",
    "engagement_id",
    "thread_or_meeting_id",
    "signal_date",
    "signal_kind",
    "summary",
    "owner",
    "status",
    "provenance_ref",
  ],
  engagementRegister: [
    "engagement_id",
    "client_name",
    "engagement_name",
    "engagement_type",
    "status",
    "intake_date",
    "owner",
    "complexity_level",
    "next_action",
    "deadline",
    "source_signal_id",
    "notes",
  ],
  engagementTimeline: [
    "engagement_id",
    "milestone_code",
    "milestone_label",
    "target_date",
    "owner",
    "status",
    "source",
    "notes",
  ],
  stakeholderMap: [
    "engagement_id",
    "stakeholder_name",
    "role_code",
    "role_label",
    "organization",
    "email",
    "status",
    "interview_required",
    "approval_scope",
    "notes",
  ],
  actionWorkbench: [
    "action_id",
    "engagement_id",
    "client_name",
    "source_signal_id",
    "action_type",
    "task_or_artifact",
    "owner",
    "due_date",
    "status",
    "review_required",
    "notes",
  ],
  approvalRouterQueue: [
    "routing_id",
    "engagement_id",
    "client_name",
    "approval_type",
    "requested_role",
    "requested_person",
    "status",
    "due_date",
    "channel",
    "policy_key",
    "notes",
  ],
  meetingFollowThrough: [
    "meeting_id",
    "meeting_date",
    "account_or_client",
    "meeting_title",
    "owner",
    "commitment",
    "commitment_owner",
    "due_date",
    "status",
    "system_to_update",
    "notes",
  ],
};

const ROUTE_CONFIG = {
  "proposal-capture": {
    label: "Proposal Capture",
    milestones: [
      { code: "signal-captured", label: "Signal Captured", offsetDays: 0 },
      { code: "qualification-review", label: "Qualification Review", offsetDays: 1, reverseOffsetDays: -14 },
      { code: "stakeholder-inputs", label: "Stakeholder Inputs", offsetDays: 3, reverseOffsetDays: -10 },
      { code: "draft-assembly", label: "Draft Assembly", offsetDays: 5, reverseOffsetDays: -7 },
      { code: "internal-review", label: "Internal Review", offsetDays: 7, reverseOffsetDays: -4 },
      { code: "final-package", label: "Final Package", offsetDays: 9, reverseOffsetDays: -2 },
      { code: "submission", label: "Submission", offsetDays: 11, reverseOffsetDays: 0 },
    ],
    stakeholders: [
      { name: OWNER, roleCode: "internal_owner", roleLabel: "Internal Owner", organization: "Boss Key", interviewRequired: "no", approvalScope: "workflow-owner" },
      { name: "Client Sponsor", roleCode: "client_sponsor", roleLabel: "Client Sponsor", organizationFromClient: true, interviewRequired: "yes", approvalScope: "requirements" },
      { name: "Sales Lead", roleCode: "sales_lead", roleLabel: "Sales Lead", organizationFromClient: true, interviewRequired: "yes", approvalScope: "commercial" },
      { name: "Operations Lead", roleCode: "operations_lead", roleLabel: "Operations Lead", organizationFromClient: true, interviewRequired: "yes", approvalScope: "delivery" },
      { name: "Executive Approver", roleCode: "executive_approver", roleLabel: "Executive Approver", organizationFromClient: true, interviewRequired: "no", approvalScope: "signoff" },
    ],
    defaultAction: "Review intake, confirm qualification, and build reverse timeline.",
  },
  "delivery-client-success": {
    label: "Delivery / Client Success",
    milestones: [
      { code: "intake", label: "Delivery Intake", offsetDays: 0 },
      { code: "scope-align", label: "Scope Alignment", offsetDays: 2 },
      { code: "work-plan", label: "Work Plan Published", offsetDays: 4 },
      { code: "client-checkpoint", label: "Client Checkpoint", offsetDays: 7 },
    ],
    stakeholders: [
      { name: OWNER, roleCode: "internal_owner", roleLabel: "Internal Owner", organization: "Boss Key", interviewRequired: "no", approvalScope: "workflow-owner" },
      { name: "Client Sponsor", roleCode: "client_sponsor", roleLabel: "Client Sponsor", organizationFromClient: true, interviewRequired: "yes", approvalScope: "service-direction" },
      { name: "Delivery Lead", roleCode: "delivery_lead", roleLabel: "Delivery Lead", organizationFromClient: true, interviewRequired: "yes", approvalScope: "execution" },
      { name: "Success Lead", roleCode: "success_lead", roleLabel: "Success Lead", organization: "Boss Key", interviewRequired: "no", approvalScope: "retention" },
    ],
    defaultAction: "Translate the client discussion into a scoped delivery work plan.",
  },
  "finance-commercial": {
    label: "Finance / Commercial",
    milestones: [
      { code: "intake", label: "Commercial Intake", offsetDays: 0 },
      { code: "estimate-review", label: "Estimate Review", offsetDays: 2 },
      { code: "terms-confirmed", label: "Terms Confirmed", offsetDays: 4 },
      { code: "billing-ready", label: "Billing Ready", offsetDays: 6 },
    ],
    stakeholders: [
      { name: OWNER, roleCode: "internal_owner", roleLabel: "Internal Owner", organization: "Boss Key", interviewRequired: "no", approvalScope: "workflow-owner" },
      { name: "Client Sponsor", roleCode: "client_sponsor", roleLabel: "Client Sponsor", organizationFromClient: true, interviewRequired: "yes", approvalScope: "commercial-input" },
      { name: "Commercial Owner", roleCode: "commercial_owner", roleLabel: "Commercial Owner", organization: "Boss Key", interviewRequired: "no", approvalScope: "pricing" },
      { name: "Billing Owner", roleCode: "billing_owner", roleLabel: "Billing Owner", organization: "Boss Key", interviewRequired: "no", approvalScope: "collections" },
    ],
    defaultAction: "Turn the commercial discussion into a budget, billing, or collections action.",
  },
  "revenue-follow-up": {
    label: "Revenue Follow-Up",
    milestones: [
      { code: "signal-captured", label: "Signal Captured", offsetDays: 0 },
      { code: "qualification", label: "Qualification", offsetDays: 1 },
      { code: "follow-up", label: "Follow-Up Sent", offsetDays: 2 },
      { code: "next-meeting", label: "Next Meeting Booked", offsetDays: 5 },
    ],
    stakeholders: [
      { name: OWNER, roleCode: "internal_owner", roleLabel: "Internal Owner", organization: "Boss Key", interviewRequired: "no", approvalScope: "workflow-owner" },
      { name: "Primary Contact", roleCode: "primary_contact", roleLabel: "Primary Contact", organizationFromClient: true, interviewRequired: "yes", approvalScope: "discovery" },
      { name: "Revenue Owner", roleCode: "revenue_owner", roleLabel: "Revenue Owner", organization: "Boss Key", interviewRequired: "no", approvalScope: "pipeline" },
    ],
    defaultAction: "Capture the next follow-up and move the engagement toward a scheduled decision step.",
  },
  "general-engagement": {
    label: "General Engagement",
    milestones: [
      { code: "intake", label: "Intake Logged", offsetDays: 0 },
      { code: "triage", label: "Triage Review", offsetDays: 1 },
      { code: "execution", label: "Execution Path Chosen", offsetDays: 3 },
    ],
    stakeholders: [
      { name: OWNER, roleCode: "internal_owner", roleLabel: "Internal Owner", organization: "Boss Key", interviewRequired: "no", approvalScope: "workflow-owner" },
      { name: "Primary Contact", roleCode: "primary_contact", roleLabel: "Primary Contact", organizationFromClient: true, interviewRequired: "yes", approvalScope: "context" },
    ],
    defaultAction: "Review the communication and route it into a concrete workstream.",
  },
};

try {
  main();
} catch (error) {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 1;
}

function main() {
  ensureDir(BRIEFS_DIR);
  ensureCsvFiles();

  const state = readJson(PATHS.state, { processed: {} });
  const previousSummary = readJson(PATHS.summaryJson, null);
  if (!state.processed || typeof state.processed !== "object") state.processed = {};

  const tables = loadTables();
  const sources = readCsv(PATHS.sourceConfig).filter((row) => String(row.enabled || "").trim().toLowerCase() === "yes");
  const summary = createSummary(sources, previousSummary);

  const items = collectSourceItems(sources, summary);
  for (const item of items) {
    if (state.processed[item.fingerprint]) continue;
    const normalized = normalizeItem(item, tables);
    if (!normalized) {
      state.processed[item.fingerprint] = { processed_at: nowIso(), skipped: true, provenance_ref: item.provenanceRef };
      summary.skipped_items += 1;
      continue;
    }
    applyNormalizedItem(normalized, tables, summary);
    state.processed[item.fingerprint] = {
      processed_at: nowIso(),
      skipped: false,
      signal_id: normalized.signalId,
      engagement_id: normalized.engagementId,
      provenance_ref: normalized.provenanceRef,
    };
  }

  writeTables(tables);
  summary.pending_approvals_open = tables.approvalRouterQueue.filter((row) => String(row.status || "").toLowerCase() === "pending").length;
  summary.last_run_at = nowIso();
  summary.last_changed_at = summary.signals_added > 0
    ? summary.last_run_at
    : String(previousSummary?.last_changed_at || previousSummary?.last_run_at || "");
  if (!summary.recent_engagements.length && Array.isArray(previousSummary?.recent_engagements)) {
    summary.recent_engagements = previousSummary.recent_engagements.slice(0, 8);
  }
  if (!summary.recent_engagements.length) {
    summary.recent_engagements = buildRecentEngagementsFromTables(tables);
  }
  writeJson(PATHS.state, state);
  writeSummaryFiles(summary);
  process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
}

function createSummary(sources, previousSummary) {
  return {
    last_run_at: "",
    last_changed_at: String(previousSummary?.last_changed_at || previousSummary?.last_run_at || ""),
    source_count: sources.length,
    sources_scanned: 0,
    items_discovered: 0,
    skipped_items: 0,
    signals_added: 0,
    engagements_created: 0,
    engagements_updated: 0,
    actions_added: 0,
    follow_through_added: 0,
    approvals_added: 0,
    pending_approvals_open: 0,
    recent_engagements: [],
  };
}

function ensureCsvFiles() {
  ensureDir(DATA_DIR);
  ensureDir(BRIEFS_DIR);
  Object.entries(CSV_HEADERS).forEach(([key, headers]) => {
    ensureCsvFile(PATHS[key], headers);
  });
}

function loadTables() {
  const tables = {
    signalLog: readCsv(PATHS.signalLog),
    engagementRegister: readCsv(PATHS.engagementRegister),
    engagementTimeline: readCsv(PATHS.engagementTimeline),
    stakeholderMap: readCsv(PATHS.stakeholderMap),
    actionWorkbench: readCsv(PATHS.actionWorkbench),
    approvalRouterQueue: readCsv(PATHS.approvalRouterQueue),
    meetingFollowThrough: readCsv(PATHS.meetingFollowThrough),
  };

  tables.engagementById = new Map(tables.engagementRegister.map((row) => [row.engagement_id, row]));
  tables.timelineKeys = new Set(tables.engagementTimeline.map((row) => `${row.engagement_id}|${row.milestone_code}`));
  tables.stakeholderKeys = new Set(tables.stakeholderMap.map((row) => `${row.engagement_id}|${row.role_code}|${row.stakeholder_name}`));
  tables.actionIds = new Set(tables.actionWorkbench.map((row) => row.action_id));
  tables.approvalIds = new Set(tables.approvalRouterQueue.map((row) => row.routing_id));
  tables.followIds = new Set(tables.meetingFollowThrough.map((row) => row.meeting_id));
  return tables;
}

function writeTables(tables) {
  writeCsv(PATHS.signalLog, CSV_HEADERS.signalLog, tables.signalLog);
  writeCsv(PATHS.engagementRegister, CSV_HEADERS.engagementRegister, tables.engagementRegister);
  writeCsv(PATHS.engagementTimeline, CSV_HEADERS.engagementTimeline, tables.engagementTimeline);
  writeCsv(PATHS.stakeholderMap, CSV_HEADERS.stakeholderMap, tables.stakeholderMap);
  writeCsv(PATHS.actionWorkbench, CSV_HEADERS.actionWorkbench, tables.actionWorkbench);
  writeCsv(PATHS.approvalRouterQueue, CSV_HEADERS.approvalRouterQueue, tables.approvalRouterQueue);
  writeCsv(PATHS.meetingFollowThrough, CSV_HEADERS.meetingFollowThrough, tables.meetingFollowThrough);
}

function ensureDir(dirPath) {
  if (!fs.existsSync(dirPath)) fs.mkdirSync(dirPath, { recursive: true });
}

function ensureCsvFile(filePath, headers) {
  if (!fs.existsSync(filePath)) {
    fs.writeFileSync(filePath, `${headers.join(",")}\n`, "utf8");
    return;
  }
  const content = fs.readFileSync(filePath, "utf8");
  if (!content.trim()) {
    fs.writeFileSync(filePath, `${headers.join(",")}\n`, "utf8");
  }
}

function nowIso() {
  return new Date().toISOString().slice(0, 19);
}

function dateIso(value = new Date()) {
  return new Date(value).toISOString().slice(0, 10);
}

function addDays(dateString, offsetDays) {
  const base = new Date(`${dateString}T12:00:00`);
  if (Number.isNaN(base.getTime())) return "";
  base.setDate(base.getDate() + offsetDays);
  return dateIso(base);
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

function readCsv(filePath) {
  if (!fs.existsSync(filePath)) return [];
  const raw = fs.readFileSync(filePath, "utf8").trim();
  if (!raw) return [];
  const lines = raw.split(/\r?\n/);
  const headers = parseCsvLine(lines[0]);
  return lines.slice(1).filter(Boolean).map((line) => {
    const values = parseCsvLine(line);
    const row = {};
    headers.forEach((header, index) => {
      row[header] = values[index] ?? "";
    });
    return row;
  });
}

function writeCsv(filePath, headers, rows) {
  const lines = [headers.join(",")];
  rows.forEach((row) => {
    lines.push(headers.map((header) => csvEscape(row[header] ?? "")).join(","));
  });
  fs.writeFileSync(filePath, `${lines.join("\n")}\n`, "utf8");
}

function parseCsvLine(line) {
  const out = [];
  let current = "";
  let inQuotes = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (inQuotes) {
      if (char === '"') {
        if (line[index + 1] === '"') {
          current += '"';
          index += 1;
        } else {
          inQuotes = false;
        }
      } else {
        current += char;
      }
    } else if (char === ",") {
      out.push(current);
      current = "";
    } else if (char === '"') {
      inQuotes = true;
    } else {
      current += char;
    }
  }
  out.push(current);
  return out;
}

function csvEscape(value) {
  const text = String(value ?? "");
  if (/[",\n]/.test(text)) return `"${text.replace(/"/g, '""')}"`;
  return text;
}

function collectSourceItems(sources, summary) {
  const items = [];
  sources.forEach((source) => {
    summary.sources_scanned += 1;
    const sourcePath = resolveRepoPath(source.source_path);
    const sourceType = String(source.source_type || "").trim();
    if (sourceType === "transcript_dir" || sourceType === "document_dir") {
      if (!fs.existsSync(sourcePath) || !fs.statSync(sourcePath).isDirectory()) return;
      const files = dedupeDirectoryFiles(listFilesRecursive(sourcePath), source.file_pattern || "*.*");
      files.forEach((filePath) => {
        const item = buildFileItem(source, filePath);
        if (item) items.push(item);
      });
      return;
    }
    if (sourceType === "csv_interactions") {
      readCsv(sourcePath).forEach((row, index) => {
        const item = buildInteractionItem(source, row, index);
        if (item) items.push(item);
      });
      return;
    }
    if (sourceType === "csv_events") {
      readCsv(sourcePath).forEach((row, index) => {
        const item = buildEventItem(source, row, index);
        if (item) items.push(item);
      });
    }
  });
  summary.items_discovered = items.length;
  return items;
}

function resolveRepoPath(value) {
  if (!value) return "";
  if (path.isAbsolute(value)) return value;
  return path.join(REPO_ROOT, value);
}

function listFilesRecursive(dirPath) {
  const out = [];
  fs.readdirSync(dirPath, { withFileTypes: true }).forEach((entry) => {
    const child = path.join(dirPath, entry.name);
    if (entry.isDirectory()) {
      out.push(...listFilesRecursive(child));
      return;
    }
    out.push(child);
  });
  return out;
}

function dedupeDirectoryFiles(files, pattern) {
  const matched = files.filter((filePath) => {
    const ext = path.extname(filePath).toLowerCase();
    if (!SUPPORTED_FILE_EXTENSIONS.has(ext)) return false;
    if (shouldIgnoreFile(filePath)) return false;
    return matchesPattern(path.basename(filePath), pattern || "*.*");
  });

  const preferredByStem = new Map();
  matched.forEach((filePath) => {
    const parsed = path.parse(filePath);
    const key = path.join(parsed.dir, parsed.name).toLowerCase();
    const existing = preferredByStem.get(key);
    if (!existing) {
      preferredByStem.set(key, filePath);
      return;
    }
    const winner = choosePreferredFile(existing, filePath);
    preferredByStem.set(key, winner);
  });
  return [...preferredByStem.values()].sort();
}

function shouldIgnoreFile(filePath) {
  const name = path.basename(filePath).toLowerCase();
  if (name === "readme.md") return true;
  if (name.startsWith(".")) return true;
  return false;
}

function matchesPattern(fileName, pattern) {
  if (!pattern || pattern === "*.*" || pattern === "*") return true;
  const escaped = pattern.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*").replace(/\?/g, ".");
  const regex = new RegExp(`^${escaped}$`, "i");
  return regex.test(fileName);
}

function choosePreferredFile(leftPath, rightPath) {
  const leftExt = path.extname(leftPath).toLowerCase();
  const rightExt = path.extname(rightPath).toLowerCase();
  if (leftExt === ".txt" && rightExt === ".srt") return leftPath;
  if (leftExt === ".srt" && rightExt === ".txt") return rightPath;
  const leftStat = fs.statSync(leftPath);
  const rightStat = fs.statSync(rightPath);
  return leftStat.mtimeMs >= rightStat.mtimeMs ? leftPath : rightPath;
}

function buildFileItem(source, filePath) {
  const stat = fs.statSync(filePath);
  if (stat.size <= 0) return null;
  const parsed = path.parse(filePath);
  const content = parseFileContent(filePath);
  if (!content.text || content.text.trim().length < 40) return null;

  const relative = path.relative(REPO_ROOT, filePath).replace(/\\/g, "/");
  const signalDate = extractDateFromString(relative) || dateIso(stat.mtime);
  const title = content.title || humanizeSlug(parsed.name);
  return {
    sourceId: source.source_id,
    sourceType: String(source.source_type || "").trim(),
    sourceSystem: source.source_id,
    itemId: relative,
    signalDate,
    title,
    rawClientName: inferClientFromFilename(parsed.name),
    text: content.text,
    provenanceRef: relative,
    threadOrMeetingId: slugify(parsed.name),
    fingerprint: sha1(`${source.source_id}|${relative}|${stat.mtimeMs}|${stat.size}`),
  };
}

function buildInteractionItem(source, row, index) {
  const interactionId = String(row.interaction_id || "").trim() || `${source.source_id}-${index + 1}`;
  const summary = [row.summary, row.next_action].filter(Boolean).join(". ").trim();
  if (!summary) return null;
  return {
    sourceId: source.source_id,
    sourceType: String(source.source_type || "").trim(),
    sourceSystem: source.source_id,
    itemId: interactionId,
    signalDate: String(row.date || "").trim() || dateIso(),
    title: `${row.company_name || "Unknown Client"} interaction`,
    rawClientName: String(row.company_name || row.contact_name || "").trim(),
    text: [
      `Company: ${row.company_name || ""}`,
      `Contact: ${row.contact_name || ""}`,
      `Channel: ${row.channel || ""}`,
      `Direction: ${row.direction || ""}`,
      `Summary: ${row.summary || ""}`,
      `Outcome: ${row.outcome || ""}`,
      `Next action: ${row.next_action || ""}`,
      `Next touch date: ${row.next_touch_date || ""}`,
    ].join("\n"),
    provenanceRef: path.relative(REPO_ROOT, resolveRepoPath(source.source_path)).replace(/\\/g, "/"),
    threadOrMeetingId: interactionId,
    fingerprint: sha1(`${source.source_id}|${interactionId}`),
  };
}

function buildEventItem(source, row, index) {
  const spamFlag = String(row.spam_flag || "").trim().toLowerCase();
  if (spamFlag === "yes" || spamFlag === "true" || spamFlag === "1") return null;
  const signalDate = String(row.event_date || row.event_at || "").trim();
  const context = String(row.context || "").trim();
  if (!context) return null;
  const itemId = `${source.source_id}-${signalDate || "unknown"}-${index + 1}`;
  return {
    sourceId: source.source_id,
    sourceType: String(source.source_type || "").trim(),
    sourceSystem: source.source_id,
    itemId,
    signalDate: signalDate ? signalDate.slice(0, 10) : dateIso(),
    title: `${row.source_page || "Website"} contact event`,
    rawClientName: deriveClientFromWebsiteContext(context),
    text: [
      `Source page: ${row.source_page || ""}`,
      `Context: ${context}`,
      `Channel: ${row.channel || ""}`,
      `Referrer: ${row.referrer || ""}`,
      `Spam score: ${row.spam_score || ""}`,
    ].join("\n"),
    provenanceRef: path.relative(REPO_ROOT, resolveRepoPath(source.source_path)).replace(/\\/g, "/"),
    threadOrMeetingId: itemId,
    fingerprint: sha1(`${source.source_id}|${itemId}|${context}`),
  };
}

function parseFileContent(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  if (ext === ".json") return parseJsonFile(filePath);
  const raw = fs.readFileSync(filePath, "utf8");
  if (ext === ".eml") return parseEml(raw);
  return { title: "", text: cleanTranscriptText(raw) };
}

function parseJsonFile(filePath) {
  try {
    const parsed = JSON.parse(fs.readFileSync(filePath, "utf8"));
    const title = firstNonEmpty([
      parsed.title,
      parsed.subject,
      parsed.name,
      parsed.summary,
    ]);
    const chunks = [];
    collectJsonText(parsed, chunks, 0);
    return { title, text: cleanTranscriptText(chunks.join("\n")) };
  } catch (_error) {
    return { title: "", text: "" };
  }
}

function collectJsonText(value, chunks, depth) {
  if (depth > 4 || chunks.length > 120) return;
  if (typeof value === "string") {
    const text = value.trim();
    if (text) chunks.push(text);
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((entry) => collectJsonText(entry, chunks, depth + 1));
    return;
  }
  if (!value || typeof value !== "object") return;
  ["summary", "notes", "transcript", "text", "body", "content", "message"].forEach((key) => {
    if (key in value) collectJsonText(value[key], chunks, depth + 1);
  });
  Object.keys(value).slice(0, 12).forEach((key) => {
    collectJsonText(value[key], chunks, depth + 1);
  });
}

function parseEml(raw) {
  const subjectMatch = raw.match(/^Subject:\s*(.+)$/im);
  const body = raw.split(/\r?\n\r?\n/).slice(1).join("\n\n");
  return {
    title: subjectMatch ? subjectMatch[1].trim() : "",
    text: cleanTranscriptText(body || raw),
  };
}

function cleanTranscriptText(value) {
  return String(value || "")
    .replace(/\r/g, "")
    .replace(/^\d+\s*$/gm, "")
    .replace(/^\d{2}:\d{2}:\d{2}[,.]\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}[,.]\d{3}\s*$/gm, "")
    .replace(/^\[\s*\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\]\s*/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function normalizeItem(item, tables) {
  const combinedText = [item.title, item.text].filter(Boolean).join("\n\n").trim();
  if (!combinedText || combinedText.length < 40) return null;
  if (/manual drop zone/i.test(combinedText) && /engagement-inbox\/readme\.md$/i.test(item.provenanceRef)) return null;

  const clientName = normalizeClientName(item.rawClientName || inferClientName(item.title, item.text));
  if (!clientName) return null;

  const route = classifyRoute(combinedText);
  const dueDate = extractDeadline(combinedText, item.signalDate);
  const engagementId = findEngagementId(clientName, route, tables.engagementRegister);
  const signalId = `signal-${slugify(clientName)}-${slugify(item.signalDate)}-${sha1(`${item.sourceId}|${item.itemId}`).slice(0, 8)}`;
  const actions = extractActionItems(combinedText, route, item.signalDate, dueDate);
  const engagementName = buildEngagementName(clientName, route, item.title);

  return {
    ...item,
    signalId,
    clientName,
    route,
    dueDate,
    engagementId,
    engagementName,
    signalKind: inferSignalKind(item, combinedText),
    summary: summarizeText(combinedText),
    complexityLevel: inferComplexityLevel(combinedText),
    actions,
  };
}

function applyNormalizedItem(item, tables, summary) {
  tables.signalLog.push({
    signal_id: item.signalId,
    source_type: item.sourceType,
    source_system: item.sourceSystem,
    client_name: item.clientName,
    engagement_id: item.engagementId,
    thread_or_meeting_id: item.threadOrMeetingId,
    signal_date: item.signalDate,
    signal_kind: item.signalKind,
    summary: item.summary,
    owner: OWNER,
    status: "captured",
    provenance_ref: item.provenanceRef,
  });
  summary.signals_added += 1;

  upsertEngagement(item, tables, summary);
  seedStakeholders(item, tables);
  seedTimeline(item, tables);
  seedApproval(item, tables, summary);
  seedActions(item, tables, summary);
  seedFollowThrough(item, tables, summary);
  trackRecentEngagement(item, summary);
}

function upsertEngagement(item, tables, summary) {
  const existing = tables.engagementById.get(item.engagementId);
  if (!existing) {
    const created = {
      engagement_id: item.engagementId,
      client_name: item.clientName,
      engagement_name: item.engagementName,
      engagement_type: item.route,
      status: "active",
      intake_date: item.signalDate,
      owner: OWNER,
      complexity_level: item.complexityLevel,
      next_action: item.actions[0] ? item.actions[0].task : ROUTE_CONFIG[item.route].defaultAction,
      deadline: item.dueDate,
      source_signal_id: item.signalId,
      notes: `Created from ${item.provenanceRef}. ${item.summary}`,
    };
    tables.engagementRegister.push(created);
    tables.engagementById.set(item.engagementId, created);
    summary.engagements_created += 1;
    return;
  }

  existing.client_name = item.clientName;
  existing.engagement_name = existing.engagement_name || item.engagementName;
  existing.engagement_type = existing.engagement_type || item.route;
  existing.status = existing.status || "active";
  existing.owner = existing.owner || OWNER;
  existing.complexity_level = highestComplexity(existing.complexity_level, item.complexityLevel);
  existing.next_action = item.actions[0] ? item.actions[0].task : existing.next_action;
  if (item.dueDate) existing.deadline = item.dueDate;
  existing.source_signal_id = item.signalId;
  existing.notes = appendNote(existing.notes, `${item.signalDate}: ${item.summary}`);
  summary.engagements_updated += 1;
}

function seedStakeholders(item, tables) {
  const route = ROUTE_CONFIG[item.route];
  route.stakeholders.forEach((stakeholder) => {
    const stakeholderName = stakeholder.name === "Primary Contact" && item.clientName ? item.clientName : stakeholder.name;
    const organization = stakeholder.organizationFromClient ? item.clientName : stakeholder.organization;
    const key = `${item.engagementId}|${stakeholder.roleCode}|${stakeholderName}`;
    if (tables.stakeholderKeys.has(key)) return;
    tables.stakeholderMap.push({
      engagement_id: item.engagementId,
      stakeholder_name: stakeholderName,
      role_code: stakeholder.roleCode,
      role_label: stakeholder.roleLabel,
      organization: organization || item.clientName,
      email: "",
      status: "active",
      interview_required: stakeholder.interviewRequired,
      approval_scope: stakeholder.approvalScope,
      notes: `Auto-seeded from ${item.route} intake.`,
    });
    tables.stakeholderKeys.add(key);
  });
}

function seedTimeline(item, tables) {
  const route = ROUTE_CONFIG[item.route];
  route.milestones.forEach((milestone) => {
    const key = `${item.engagementId}|${milestone.code}`;
    if (tables.timelineKeys.has(key)) return;
    const targetDate = item.dueDate && typeof milestone.reverseOffsetDays === "number"
      ? addDays(item.dueDate, milestone.reverseOffsetDays)
      : addDays(item.signalDate, milestone.offsetDays || 0);
    tables.engagementTimeline.push({
      engagement_id: item.engagementId,
      milestone_code: milestone.code,
      milestone_label: milestone.label,
      target_date: targetDate,
      owner: OWNER,
      status: milestone.code === "signal-captured" || milestone.code === "intake" ? "done" : "pending",
      source: item.signalId,
      notes: item.dueDate && typeof milestone.reverseOffsetDays === "number"
        ? "Reverse-timed from detected deadline."
        : "Auto-seeded from intake signal.",
    });
    tables.timelineKeys.add(key);
  });
}

function seedApproval(item, tables, summary) {
  const routingId = `approval-${item.engagementId}-intake-review`;
  if (tables.approvalIds.has(routingId)) return;
  tables.approvalRouterQueue.push({
    routing_id: routingId,
    engagement_id: item.engagementId,
    client_name: item.clientName,
    approval_type: "intake-review",
    requested_role: item.route === "proposal-capture" ? "Executive Approver" : "Internal Owner",
    requested_person: OWNER,
    status: "pending",
    due_date: addDays(item.signalDate, 1),
    channel: "operator-console",
    policy_key: `${item.route}-intake-review`,
    notes: `Review the newly captured signal from ${item.provenanceRef}.`,
  });
  tables.approvalIds.add(routingId);
  summary.approvals_added += 1;
}

function seedActions(item, tables, summary) {
  item.actions.forEach((action, index) => {
    const actionId = `action-${item.signalId}-${String(index + 1).padStart(2, "0")}`;
    if (tables.actionIds.has(actionId)) return;
    tables.actionWorkbench.push({
      action_id: actionId,
      engagement_id: item.engagementId,
      client_name: item.clientName,
      source_signal_id: item.signalId,
      action_type: action.type,
      task_or_artifact: action.task,
      owner: OWNER,
      due_date: action.dueDate,
      status: "open",
      review_required: action.reviewRequired ? "yes" : "no",
      notes: action.notes,
    });
    tables.actionIds.add(actionId);
    summary.actions_added += 1;
  });
}

function seedFollowThrough(item, tables, summary) {
  const followActions = item.actions.slice(0, 3);
  followActions.forEach((action, index) => {
    const meetingId = `follow-${item.signalId}-${String(index + 1).padStart(2, "0")}`;
    if (tables.followIds.has(meetingId)) return;
    tables.meetingFollowThrough.push({
      meeting_id: meetingId,
      meeting_date: item.signalDate,
      account_or_client: item.clientName,
      meeting_title: item.title || item.engagementName,
      owner: OWNER,
      commitment: action.task,
      commitment_owner: OWNER,
      due_date: action.dueDate,
      status: "open",
      system_to_update: "company-os",
      notes: `Captured from ${item.signalKind}.`,
    });
    tables.followIds.add(meetingId);
    summary.follow_through_added += 1;
  });
}

function trackRecentEngagement(item, summary) {
  const existing = summary.recent_engagements.find((entry) => entry.engagement_id === item.engagementId);
  if (existing) {
    existing.last_signal_date = item.signalDate;
    existing.client_name = item.clientName;
    existing.engagement_name = item.engagementName;
    existing.route = item.route;
    existing.summary = item.summary;
    return;
  }
  summary.recent_engagements.unshift({
    engagement_id: item.engagementId,
    client_name: item.clientName,
    engagement_name: item.engagementName,
    route: item.route,
    last_signal_date: item.signalDate,
    summary: item.summary,
  });
  summary.recent_engagements = summary.recent_engagements.slice(0, 8);
}

function buildRecentEngagementsFromTables(tables) {
  const sortedSignals = [...tables.signalLog].sort((left, right) => {
    if (left.signal_date === right.signal_date) return String(right.signal_id || "").localeCompare(String(left.signal_id || ""));
    return String(right.signal_date || "").localeCompare(String(left.signal_date || ""));
  });
  const seen = new Set();
  const recent = [];
  sortedSignals.forEach((signal) => {
    if (!signal.engagement_id || seen.has(signal.engagement_id) || recent.length >= 8) return;
    const engagement = tables.engagementById.get(signal.engagement_id);
    seen.add(signal.engagement_id);
    recent.push({
      engagement_id: signal.engagement_id,
      client_name: signal.client_name,
      engagement_name: engagement?.engagement_name || signal.client_name,
      route: engagement?.engagement_type || "general-engagement",
      last_signal_date: signal.signal_date,
      summary: signal.summary,
    });
  });
  return recent;
}

function highestComplexity(left, right) {
  const order = ["low", "medium", "high"];
  return order[Math.max(order.indexOf(left || "low"), order.indexOf(right || "low"))] || "medium";
}

function appendNote(existing, addition) {
  const value = String(existing || "").trim();
  if (!value) return addition;
  if (value.includes(addition)) return value;
  const lines = value.split(/\r?\n/).slice(-4);
  lines.push(addition);
  return lines.join("\n");
}

function classifyRoute(text) {
  const lower = text.toLowerCase();
  if (containsAny(lower, ["rfp", "proposal", "bid", "submission", "solicitation", "scope of work", "reverse timeline", "pricing sheet"])) {
    return "proposal-capture";
  }
  if (containsAny(lower, ["invoice", "billing", "collections", "payment", "retainer", "budget", "spend", "cost wise", "estimate", "pricing"])) {
    return "finance-commercial";
  }
  if (containsAny(lower, ["kickoff", "implementation", "deliverable", "client success", "onboarding", "support", "maintenance", "change order"])) {
    return "delivery-client-success";
  }
  if (containsAny(lower, ["follow up", "follow-up", "pipeline", "lead", "opportunity", "demo", "intro call", "discovery", "sales process", "meeting booked"])) {
    return "revenue-follow-up";
  }
  return "general-engagement";
}

function inferSignalKind(item, text) {
  const lower = text.toLowerCase();
  if (item.sourceType === "csv_interactions") return "interaction-log";
  if (item.sourceType === "csv_events") return "website-contact";
  if (item.provenanceRef.endsWith(".eml")) return "email-export";
  if (containsAny(lower, ["call", "intro call", "meeting"])) return "call-transcript";
  if (containsAny(lower, ["proposal", "rfp", "solicitation"])) return "opportunity-brief";
  return "communication-capture";
}

function summarizeText(text) {
  const cleaned = text.replace(/\s+/g, " ").trim();
  if (cleaned.length <= 220) return cleaned;
  const sentences = splitSentences(cleaned);
  const first = sentences.find((sentence) => sentence.length > 20) || cleaned.slice(0, 220);
  return truncate(first, 220);
}

function inferComplexityLevel(text) {
  const lower = text.toLowerCase();
  let score = 0;
  if (text.length > 1800) score += 2;
  if (containsAny(lower, ["stakeholder", "timeline", "deliverable", "interview", "approval", "pricing", "proposal", "compliance"])) score += 2;
  if (containsAny(lower, ["demo", "follow-up", "meeting", "budget", "workflow"])) score += 1;
  if (score >= 4) return "high";
  if (score >= 2) return "medium";
  return "low";
}

function extractActionItems(text, route, signalDate, dueDate) {
  const sentences = splitSentences(text);
  const tasks = [];
  sentences.forEach((sentence) => {
    const normalized = normalizeActionSentence(sentence);
    if (!normalized) return;
    if (tasks.some((task) => task.task.toLowerCase() === normalized.toLowerCase())) return;
    tasks.push({
      type: inferActionType(normalized),
      task: normalized,
      dueDate: extractDeadline(sentence, signalDate) || dueDate || addDays(signalDate, Math.min(tasks.length + 1, 5)),
      reviewRequired: /review|approve|signoff|proposal|strategy/i.test(normalized),
      notes: `Derived from intake signal sentence: ${truncate(sentence.trim(), 180)}`,
    });
  });

  if (!tasks.length) {
    tasks.push({
      type: "follow-up",
      task: ROUTE_CONFIG[route].defaultAction,
      dueDate: dueDate || addDays(signalDate, 1),
      reviewRequired: route === "proposal-capture",
      notes: "Fallback action seeded from route defaults.",
    });
  }

  return tasks.slice(0, 4);
}

function splitSentences(text) {
  return text
    .replace(/\s+/g, " ")
    .split(/(?<=[.!?])\s+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
}

function normalizeActionSentence(sentence) {
  const trimmed = sentence.replace(/^[-*]\s*/, "").trim();
  if (trimmed.length < 24 || trimmed.length > 220) return "";
  if (!containsAny(trimmed.toLowerCase(), [
    "need to",
    "will ",
    "follow up",
    "follow-up",
    "send",
    "review",
    "build",
    "prepare",
    "schedule",
    "draft",
    "deliver",
    "approve",
    "upload",
    "book",
    "set up",
    "incorporate",
    "organize",
    "compare",
    "extract",
    "rewrite",
    "formalizing",
  ])) {
    return "";
  }

  return trimmed
    .replace(/^so\s+/i, "")
    .replace(/^and\s+/i, "")
    .replace(/^but\s+/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

function inferActionType(text) {
  const lower = text.toLowerCase();
  if (containsAny(lower, ["schedule", "book", "meeting", "interview"])) return "meeting";
  if (containsAny(lower, ["review", "approve", "signoff"])) return "review";
  if (containsAny(lower, ["build", "draft", "rewrite", "prepare", "deliverable", "template", "content", "proposal"])) return "artifact-build";
  return "follow-up";
}

function findEngagementId(clientName, route, engagements) {
  const exact = engagements.find((row) => normalizeClientName(row.client_name) === clientName && row.engagement_type === route);
  if (exact) return exact.engagement_id;
  return `eng-${slugify(clientName)}-${slugify(route)}`;
}

function buildEngagementName(clientName, route, title) {
  const routeLabel = ROUTE_CONFIG[route].label;
  const titleText = truncate(title || routeLabel, 80);
  if (titleText.toLowerCase().includes(clientName.toLowerCase())) return titleText;
  return `${clientName} - ${routeLabel}`;
}

function inferClientName(title, text) {
  const byTitle = inferClientFromFilename(title || "");
  if (byTitle) return byTitle;
  const patterns = [
    /with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})/,
    /company:\s*([A-Z][^\n]+)/i,
    /account(?:\s+or\s+client)?:\s*([A-Z][^\n]+)/i,
  ];
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match && match[1]) return match[1].trim();
  }
  return "";
}

function inferClientFromFilename(value) {
  const cleaned = String(value || "")
    .replace(/\.[^.]+$/, "")
    .replace(/\b\d{4}-\d{2}-\d{2}\b/g, " ")
    .replace(/\b(?:intro|call|meeting|notes|transcript|email|thread|capture|processed|export|follow|followup|follow-up|proposal|rfp)\b/gi, " ")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  if (!cleaned || /^readme$/i.test(cleaned)) return "";
  return humanizeSlug(cleaned);
}

function deriveClientFromWebsiteContext(context) {
  const match = String(context || "").match(/(?:name|company)\s*[:=-]\s*([^,;\n]+)/i);
  return match ? match[1].trim() : "";
}

function normalizeClientName(value) {
  const text = humanizeSlug(String(value || "").replace(/\s+/g, " ").trim());
  if (!text) return "";
  if (/^(unknown|website|contact event|interaction)$/i.test(text)) return "";
  return text;
}

function extractDeadline(text, signalDate) {
  const exactPatterns = [
    /\b(\d{4}-\d{2}-\d{2})\b/,
    /\b(\d{1,2}\/\d{1,2}\/\d{2,4})\b/,
    /\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,\s*(\d{4}))?\b/i,
  ];
  for (const pattern of exactPatterns) {
    const match = text.match(pattern);
    if (!match) continue;
    const parsed = parseDateMatch(match, signalDate);
    if (parsed) return parsed;
  }

  const relativeMatch = text.match(/\b(?:due|deadline|finals by|proposal(?:\s+is)? due(?:\s+on)?)\s+the\s+(\d{1,2})(?:st|nd|rd|th)\b/i);
  if (relativeMatch) {
    const day = Number(relativeMatch[1]);
    const base = new Date(`${signalDate}T12:00:00`);
    if (!Number.isNaN(base.getTime())) {
      const guess = new Date(base);
      guess.setDate(day);
      if (guess < base) guess.setMonth(guess.getMonth() + 1);
      return dateIso(guess);
    }
  }
  return "";
}

function parseDateMatch(match, signalDate) {
  const token = match[1];
  if (/^\d{4}-\d{2}-\d{2}$/.test(token)) return token;
  if (/^\d{1,2}\/\d{1,2}\/\d{2,4}$/.test(token)) {
    const [month, day, yearRaw] = token.split("/");
    const year = yearRaw.length === 2 ? `20${yearRaw}` : yearRaw;
    return `${year.padStart(4, "0")}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
  }
  const monthName = match[1];
  const day = Number(match[2]);
  const year = Number(match[3] || new Date(`${signalDate}T12:00:00`).getFullYear());
  const monthIndex = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
  ].indexOf(monthName.toLowerCase());
  if (monthIndex < 0) return "";
  return `${String(year).padStart(4, "0")}-${String(monthIndex + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function extractDateFromString(value) {
  const match = String(value || "").match(/\b(\d{4}-\d{2}-\d{2})\b/);
  return match ? match[1] : "";
}

function containsAny(text, needles) {
  return needles.some((needle) => text.includes(needle));
}

function slugify(value) {
  const cleaned = String(value || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return cleaned || "item";
}

function humanizeSlug(value) {
  return String(value || "")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function truncate(value, maxLength) {
  const text = String(value || "").trim();
  if (text.length <= maxLength) return text;
  return `${text.slice(0, Math.max(0, maxLength - 3)).trim()}...`;
}

function sha1(value) {
  return crypto.createHash("sha1").update(String(value || "")).digest("hex");
}

function firstNonEmpty(values) {
  return values.map((value) => String(value || "").trim()).find(Boolean) || "";
}

function writeSummaryFiles(summary) {
  writeJson(PATHS.summaryJson, summary);
  const lines = [
    "# Engagement Intake Summary",
    "",
    `Last run: ${summary.last_run_at}`,
    "",
    "## Counts",
    "",
    `- Sources scanned: ${summary.sources_scanned}`,
    `- Items discovered: ${summary.items_discovered}`,
    `- Skipped items: ${summary.skipped_items}`,
    `- Signals added: ${summary.signals_added}`,
    `- Engagements created: ${summary.engagements_created}`,
    `- Engagements updated: ${summary.engagements_updated}`,
    `- Actions added: ${summary.actions_added}`,
    `- Follow-through items added: ${summary.follow_through_added}`,
    `- Approvals added: ${summary.approvals_added}`,
    `- Pending approvals open: ${summary.pending_approvals_open}`,
    "",
    "## Recent Engagements",
    "",
  ];

  if (!summary.recent_engagements.length) {
    lines.push("- No new engagements captured in this run.");
  } else {
    summary.recent_engagements.forEach((entry) => {
      lines.push(`- ${entry.client_name} | ${entry.route} | ${entry.last_signal_date} | ${entry.summary}`);
    });
  }

  fs.writeFileSync(PATHS.summaryMd, `${lines.join("\n")}\n`, "utf8");
}
