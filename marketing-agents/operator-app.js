const fs = require("fs");
const http = require("http");
const path = require("path");
const { spawn } = require("child_process");
const crypto = require("crypto");
const { URL } = require("url");

const PORT = Number(process.env.OPS_APP_PORT || 3201);
const ROOT = __dirname;
const APP_DIR = path.join(ROOT, "app");
const DATA_DIR = path.join(ROOT, "data");
const BRIEFS_DIR = path.join(ROOT, "briefs");
const SCRIPTS_DIR = path.join(ROOT, "scripts");

const FILES = {
  callPlan: path.join(DATA_DIR, "daily_call_plan.csv"),
  pipeline: path.join(DATA_DIR, "prospect_pipeline.csv"),
  interactions: path.join(DATA_DIR, "interaction_log.csv"),
  state: path.join(DATA_DIR, "call_session_state.json"),
  followUps: path.join(DATA_DIR, "follow_up_events.csv"),
  followUpsIcs: path.join(BRIEFS_DIR, "follow-up-events.ics"),
};

function loadEnvFile(filePath) {
  try {
    const raw = fs.readFileSync(filePath, "utf8");
    raw.split(/\r?\n/).forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) return;
      const idx = trimmed.indexOf("=");
      if (idx <= 0) return;
      const key = trimmed.slice(0, idx).trim();
      if (!key) return;
      let value = trimmed.slice(idx + 1).trim();
      if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      if (process.env[key] === undefined) process.env[key] = value;
    });
  } catch (_e) {}
}

loadEnvFile(path.join(ROOT, ".env"));
loadEnvFile(path.join(ROOT, ".env.local"));

const AIRCALL_WEBHOOK_SECRET = String(process.env.AIRCALL_WEBHOOK_SECRET || "").trim();
const AIRCALL_WEBHOOK_TOKEN = String(process.env.AIRCALL_WEBHOOK_TOKEN || "").trim();

function ensureDirs() {
  [APP_DIR, DATA_DIR, BRIEFS_DIR].forEach((dir) => {
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  });
}

function readCsv(filePath) {
  if (!fs.existsSync(filePath)) return [];
  const raw = fs.readFileSync(filePath, "utf8").trim();
  if (!raw) return [];
  const lines = raw.split(/\r?\n/);
  if (!lines.length) return [];
  const headers = parseCsvLine(lines[0]);
  return lines.slice(1).filter(Boolean).map((line) => {
    const values = parseCsvLine(line);
    const row = {};
    headers.forEach((h, i) => {
      row[h] = values[i] ?? "";
    });
    return row;
  });
}

function parseCsvLine(line) {
  const out = [];
  let cur = "";
  let inQ = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (inQ) {
      if (ch === '"') {
        if (line[i + 1] === '"') {
          cur += '"';
          i += 1;
        } else {
          inQ = false;
        }
      } else {
        cur += ch;
      }
    } else if (ch === ",") {
      out.push(cur);
      cur = "";
    } else if (ch === '"') {
      inQ = true;
    } else {
      cur += ch;
    }
  }
  out.push(cur);
  return out;
}

function writeCsv(filePath, rows) {
  const headers = rows.length ? Object.keys(rows[0]) : [];
  const body = [headers.join(",")]
    .concat(rows.map((row) => headers.map((h) => csvEscape(row[h] ?? "")).join(",")))
    .join("\n");
  fs.writeFileSync(filePath, body === "" ? "" : `${body}\n`, "utf8");
}

function csvEscape(value) {
  const str = String(value ?? "");
  if (str.includes(",") || str.includes('"') || str.includes("\n")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function readState(callDate) {
  if (!fs.existsSync(FILES.state)) {
    return { call_date: callDate, next_index: 0, pending_call: null, updated_at: nowIso() };
  }
  try {
    const obj = JSON.parse(fs.readFileSync(FILES.state, "utf8"));
    if (!obj.call_date) obj.call_date = callDate;
    if (typeof obj.next_index !== "number") obj.next_index = Number(obj.next_index || 0);
    if (!Object.prototype.hasOwnProperty.call(obj, "pending_call")) obj.pending_call = null;
    return obj;
  } catch (_e) {
    return { call_date: callDate, next_index: 0, pending_call: null, updated_at: nowIso() };
  }
}

function writeState(state) {
  state.updated_at = nowIso();
  fs.writeFileSync(FILES.state, `${JSON.stringify(state, null, 2)}\n`, "utf8");
}

function nowIso() {
  return new Date().toISOString().slice(0, 19);
}

function getActiveCallDate(callPlan) {
  if (!callPlan.length) return new Date().toISOString().slice(0, 10);
  const dates = [...new Set(callPlan.map((r) => r.call_date).filter(Boolean))].sort();
  const today = new Date().toISOString().slice(0, 10);
  if (dates.includes(today)) return today;
  return dates[dates.length - 1];
}

function cleanPhone(value) {
  const digits = String(value || "").replace(/\D/g, "");
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length === 11 && digits.startsWith("1")) return `+${digits}`;
  if (digits.length > 11) return `+${digits}`;
  return "";
}

function isCallable(row) {
  return Boolean(cleanPhone(row?.contact_phone || ""));
}

function outcomeToStage(outcome, currentStage) {
  if (outcome === "meeting-booked") return "meeting-scheduled";
  if (outcome === "connected") return "connected";
  if (outcome === "not-fit" || outcome === "do-not-contact") return "closed-lost";
  return currentStage || "outreach-sent";
}

function outcomeToStatus(outcome, currentStatus) {
  if (outcome === "not-fit") return "closed-lost";
  if (outcome === "do-not-contact") return "do-not-contact";
  return currentStatus || "active";
}

function defaultNextTouch(outcome, today) {
  const d = new Date(`${today}T09:00:00`);
  const add = (days) => {
    const n = new Date(d);
    n.setDate(n.getDate() + days);
    return n.toISOString().slice(0, 10);
  };
  if (outcome === "meeting-booked") return add(1);
  if (outcome === "connected") return add(2);
  if (outcome === "voicemail") return add(3);
  if (outcome === "no-answer") return add(2);
  if (outcome === "not-now") return add(7);
  return "";
}

function followUpOffsets(outcome) {
  if (["connected", "voicemail", "no-answer"].includes(outcome)) return [2, 7];
  if (outcome === "meeting-booked") return [1, 7];
  if (outcome === "not-now") return [7, 14];
  return [];
}

function writeFollowUpIcs(rows) {
  const active = rows.filter((r) => r.status !== "cancelled" && r.due_date);
  const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Boss Key//Follow Ups//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH"];
  active.forEach((r) => {
    const start = `${r.due_date.replace(/-/g, "")}T${(r.start_time || "0900").replace(":", "")}00`;
    const end = `${r.due_date.replace(/-/g, "")}T${(r.end_time || "0915").replace(":", "")}00`;
    lines.push("BEGIN:VEVENT");
    lines.push(`UID:${r.event_id}@bosskeyops.com`);
    lines.push(`DTSTAMP:${new Date().toISOString().replace(/[-:]/g, "").slice(0, 15)}Z`);
    lines.push(`DTSTART:${start}`);
    lines.push(`DTEND:${end}`);
    lines.push(`SUMMARY:${(r.title || "").replace(/\n/g, " ")}`);
    lines.push(`DESCRIPTION:${(r.notes || "").replace(/\n/g, " ")}`);
    lines.push("END:VEVENT");
  });
  lines.push("END:VCALENDAR");
  fs.writeFileSync(FILES.followUpsIcs, `${lines.join("\n")}\n`, "utf8");
}

function runPsScript(scriptName, args = []) {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(SCRIPTS_DIR, scriptName);
    const proc = spawn("powershell.exe", ["-ExecutionPolicy", "Bypass", "-File", scriptPath, ...args], {
      cwd: path.join(ROOT, ".."),
      windowsHide: true,
    });
    let stdout = "";
    let stderr = "";
    proc.stdout.on("data", (d) => {
      stdout += d.toString();
    });
    proc.stderr.on("data", (d) => {
      stderr += d.toString();
    });
    proc.on("close", (code) => {
      if (code === 0) return resolve({ stdout: stdout.trim(), stderr: stderr.trim() });
      return reject(new Error(stderr || stdout || `Exit ${code}`));
    });
  });
}

function json(res, code, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(code, { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(body) });
  res.end(body);
}

function buildOpeningScript(callRow, pipelineRow) {
  const contact = String(callRow?.target_contact || "there").trim();
  const company = String(callRow?.company_name || "your company").trim();
  const hook1 = String(pipelineRow?.personalization_hook_1 || "").trim();
  const hook2 = String(pipelineRow?.personalization_hook_2 || "").trim();
  const bottleneck = String(pipelineRow?.likely_bottleneck || "admin burden between bid and delivery").trim();
  const angle = String(pipelineRow?.primary_angle || "reduce admin drag and protect margin").trim();

  const contextLine = [hook1, hook2].filter(Boolean).join(" and ");
  const tailored = contextLine
    ? `I noticed ${contextLine}, and thought this might be useful for ${company}.`
    : `I wanted to share a practical idea that may help ${company}.`;

  return [
    `Hi ${contact}, this is Timmy Semenza with Boss Key in South Jersey.`,
    "I help local cleaning operators cut office workload so bids move faster and margins stay protected.",
    tailored,
    `Quick question: is ${bottleneck} still a pressure point for your team?`,
    `If helpful, I can meet you at your next site visit and show a simple first step to ${angle}.`,
  ].join(" ");
}

function safeUrl(value) {
  const v = String(value || "").trim();
  if (!v) return "";
  if (v.startsWith("http://") || v.startsWith("https://")) return v;
  return `https://${v}`;
}

function domainFromUrl(value) {
  try {
    const u = new URL(safeUrl(value));
    return u.hostname.replace(/^www\./i, "");
  } catch (_e) {
    return "";
  }
}

function googleSearchUrl(query) {
  return `https://www.google.com/search?q=${encodeURIComponent(query)}`;
}

function buildProspectSnapshot(callRow, pipelineRow) {
  const company = String(callRow?.company_name || pipelineRow?.company_name || "").trim();
  const contact = String(callRow?.target_contact || pipelineRow?.target_contact || "").trim();
  const role = String(callRow?.role || pipelineRow?.role || "").trim();
  const location = String(pipelineRow?.location || "").trim();
  const website = safeUrl(pipelineRow?.website || "");
  const phone = String(callRow?.contact_phone || pipelineRow?.contact_phone || "").trim();
  const email = String(callRow?.contact_email || pipelineRow?.contact_email || "").trim();
  const notes = String(pipelineRow?.notes || "").trim();
  const domain = domainFromUrl(website);
  const photoUrl = String(pipelineRow?.contact_photo_url || pipelineRow?.photo_url || "").trim();
  const companyLogo = domain ? `https://logo.clearbit.com/${domain}` : "";
  const avatar = `https://ui-avatars.com/api/?name=${encodeURIComponent(contact || company || "Prospect")}&background=0b0f17&color=f5f7fb&size=128`;

  return {
    name: contact || "Unknown contact",
    role: role || "Unknown role",
    company: company || "Unknown company",
    location: location || "South Jersey",
    website,
    phone,
    email,
    notes: notes ? notes.slice(0, 260) : "",
    image_url: photoUrl || companyLogo || avatar,
    image_fallback_url: avatar,
    links: {
      website,
      linkedin_search: googleSearchUrl(`${contact} ${company} LinkedIn`),
      local_news: googleSearchUrl(`${company} ${location || "South Jersey"} news`),
      bbb: googleSearchUrl(`${company} BBB`),
      maps: googleSearchUrl(`${company} ${location || ""}`),
    },
  };
}

function getDashboard() {
  const callPlan = readCsv(FILES.callPlan);
  const pipeline = readCsv(FILES.pipeline);
  const callDate = getActiveCallDate(callPlan);
  const calls = callPlan.filter((c) => c.call_date === callDate).sort((a, b) => Number(a.plan_order) - Number(b.plan_order));
  const callableCalls = calls.filter((c) => isCallable(c));
  const state = readState(callDate);
  if (state.call_date !== callDate) {
    state.call_date = callDate;
    state.next_index = 0;
    state.pending_call = null;
    writeState(state);
  }
  const pending = state.pending_call && state.pending_call.awaiting_log ? state.pending_call : null;
  const next = callableCalls[state.next_index] || null;
  const getPipe = (company) => pipeline.find((p) => p.company_name === company) || null;
  return {
    call_date: callDate,
    total_calls: callableCalls.length,
    next_index: state.next_index,
    remaining: Math.max(0, callableCalls.length - state.next_index),
    pending_call: pending,
    next_call: next
      ? {
          ...next,
          clean_phone: cleanPhone(next.contact_phone),
          pipeline: getPipe(next.company_name),
          opening_script: buildOpeningScript(next, getPipe(next.company_name)),
          prospect_snapshot: buildProspectSnapshot(next, getPipe(next.company_name)),
        }
      : null,
    follow_up_ics: "marketing-agents/briefs/follow-up-events.ics",
  };
}

function startNextCall() {
  const callPlan = readCsv(FILES.callPlan);
  const callDate = getActiveCallDate(callPlan);
  const calls = callPlan
    .filter((c) => c.call_date === callDate)
    .sort((a, b) => Number(a.plan_order) - Number(b.plan_order))
    .filter((c) => isCallable(c));
  const state = readState(callDate);
  if (state.call_date !== callDate) {
    state.call_date = callDate;
    state.next_index = 0;
    state.pending_call = null;
  }
  if (state.pending_call && state.pending_call.awaiting_log) {
    return { blocked: true, message: "Log previous call outcome first.", pending_call: state.pending_call };
  }
  const c = calls[state.next_index];
  if (!c) return { done: true, message: "Queue complete for current call date." };
  const interactionId = `call-${callDate.replace(/-/g, "")}-${String(c.plan_order).padStart(3, "0")}`;
  state.pending_call = {
    interaction_id: interactionId,
    plan_order: Number(c.plan_order),
    company_name: c.company_name,
    contact_name: c.target_contact,
    role: c.role,
    call_date: callDate,
    awaiting_log: true,
    created_at: nowIso(),
  };
  state.next_index += 1;
  writeState(state);
  return { started: true, pending_call: state.pending_call, phone: cleanPhone(c.contact_phone), call: c };
}

function logOutcome(payload) {
  const requiredOutcome = ["connected", "voicemail", "no-answer", "bad-number", "meeting-booked", "not-now", "not-fit", "do-not-contact"];
  const outcome = String(payload.outcome || "").trim();
  if (!requiredOutcome.includes(outcome)) {
    throw new Error("Invalid outcome.");
  }
  const callPlan = readCsv(FILES.callPlan);
  const callDate = getActiveCallDate(callPlan);
  const state = readState(callDate);
  const pending = state.pending_call;
  if (!pending || !pending.awaiting_log) {
    throw new Error("No pending call awaiting log.");
  }
  const today = new Date().toISOString().slice(0, 10);
  const nextTouch = String(payload.next_touch_date || "").trim() || defaultNextTouch(outcome, today);
  const nextAction = String(payload.next_action || "").trim() || "Follow-up";
  const summary = String(payload.summary || "").trim() || "Outcome logged from operator app.";

  applyLoggedOutcome({
    interactionId: pending.interaction_id,
    companyName: pending.company_name,
    contactName: pending.contact_name || "",
    outcome,
    nextTouch,
    nextAction,
    summary,
    dateStr: today,
  });

  state.pending_call.awaiting_log = false;
  writeState(state);
  return { ok: true, outcome, company_name: pending.company_name };
}

function applyLoggedOutcome({
  interactionId,
  companyName,
  contactName,
  outcome,
  nextTouch,
  nextAction,
  summary,
  dateStr,
}) {
  let interactionRows = readCsv(FILES.interactions);
  if (!interactionRows.length) interactionRows = [];
  const existingIx = interactionRows.find((r) => r.interaction_id === interactionId);
  const row = {
    interaction_id: interactionId,
    date: dateStr,
    company_name: companyName,
    contact_name: contactName,
    channel: "call",
    direction: "outbound",
    summary,
    outcome,
    next_action: nextAction,
    next_touch_date: nextTouch,
    owner: "Timmy Semenza",
    created_at: nowIso(),
  };
  if (existingIx) Object.assign(existingIx, row);
  else interactionRows.push(row);
  writeCsv(FILES.interactions, interactionRows);

  const pipeline = readCsv(FILES.pipeline);
  pipeline.forEach((p) => {
    if (p.company_name !== companyName) return;
    p.last_touch_date = dateStr;
    if (nextTouch) p.next_touch_date = nextTouch;
    p.stage = outcomeToStage(outcome, p.stage);
    p.status = outcomeToStatus(outcome, p.status);
    p.notes = p.notes ? `${p.notes} | ${dateStr}: ${summary}` : summary;
  });
  writeCsv(FILES.pipeline, pipeline);

  const offsets = followUpOffsets(outcome);
  if (offsets.length) {
    let followRows = readCsv(FILES.followUps);
    offsets.forEach((d) => {
      const due = new Date(`${dateStr}T09:00:00`);
      due.setDate(due.getDate() + d);
      const dueDate = due.toISOString().slice(0, 10);
      const eventId = `${interactionId}-d${d}`;
      const ex = followRows.find((r) => r.event_id === eventId);
      const next = {
        event_id: eventId,
        source_interaction_id: interactionId,
        company_name: companyName,
        contact_name: contactName,
        outcome,
        due_date: dueDate,
        start_time: "09:00",
        end_time: "09:15",
        title: `Follow-up call - ${companyName}`,
        notes: `Outcome: ${outcome} | Next action: ${nextAction} | Notes: ${summary}`,
        status: "planned",
        created_at: nowIso(),
      };
      if (ex) Object.assign(ex, next);
      else followRows.push(next);
    });
    writeCsv(FILES.followUps, followRows);
    writeFollowUpIcs(followRows);
  }
}

function inferOutcomeFromText(text) {
  const t = String(text || "").toLowerCase();
  if (t.includes("meeting booked") || t.includes("booked a meeting") || t.includes("calendar invite")) return "meeting-booked";
  if (t.includes("do not contact") || t.includes("remove me")) return "do-not-contact";
  if (t.includes("bad number") || t.includes("wrong number")) return "bad-number";
  if (t.includes("not a fit") || t.includes("no fit")) return "not-fit";
  if (t.includes("call back later") || t.includes("not now")) return "not-now";
  if (t.includes("voicemail") || t.includes("left a message")) return "voicemail";
  if (t.includes("no answer") || t.includes("didn't answer")) return "no-answer";
  return "connected";
}

function normalizeOutcome(outcomeRaw, notesText) {
  const o = String(outcomeRaw || "").toLowerCase().trim();
  if (!o) return inferOutcomeFromText(notesText || "");
  if (o.includes("meeting")) return "meeting-booked";
  if (o.includes("do_not_contact") || o.includes("do-not-contact") || o.includes("unsubscribe")) return "do-not-contact";
  if (o.includes("bad") || o.includes("wrong number")) return "bad-number";
  if (o.includes("not fit")) return "not-fit";
  if (o.includes("not now") || o.includes("call back")) return "not-now";
  if (o.includes("voicemail") || o.includes("message")) return "voicemail";
  if (o.includes("no answer") || o.includes("no-answer") || o.includes("missed") || o.includes("unanswered")) return "no-answer";
  if (o.includes("connected") || o.includes("answered") || o.includes("completed")) return "connected";
  return inferOutcomeFromText(`${o} ${notesText || ""}`);
}

function verifyWebhookAuth(headers, rawBody) {
  if (!AIRCALL_WEBHOOK_SECRET && !AIRCALL_WEBHOOK_TOKEN) return true;

  const authHeader = String(headers.authorization || "");
  const tokenHeader =
    String(headers["x-webhook-token"] || "") ||
    String(headers["x-api-key"] || "") ||
    (authHeader.toLowerCase().startsWith("bearer ") ? authHeader.slice(7).trim() : "");

  if (AIRCALL_WEBHOOK_TOKEN && tokenHeader === AIRCALL_WEBHOOK_TOKEN) return true;

  if (AIRCALL_WEBHOOK_SECRET) {
    const sigHeader = String(headers["x-aircall-signature"] || headers["x-signature"] || "").trim();
    if (sigHeader) {
      const computedHex = crypto.createHmac("sha256", AIRCALL_WEBHOOK_SECRET).update(rawBody, "utf8").digest("hex");
      const provided = sigHeader.startsWith("sha256=") ? sigHeader.slice(7) : sigHeader;
      try {
        const a = Buffer.from(computedHex, "hex");
        const b = Buffer.from(provided, "hex");
        if (a.length === b.length && crypto.timingSafeEqual(a, b)) return true;
      } catch (_e) {}
    }
  }

  return false;
}

function getByPath(obj, pathExpr) {
  const parts = pathExpr.split(".");
  let cur = obj;
  for (const p of parts) {
    if (!cur || typeof cur !== "object" || !(p in cur)) return "";
    cur = cur[p];
  }
  return cur ?? "";
}

function firstNonEmpty(obj, paths) {
  for (const p of paths) {
    const v = getByPath(obj, p);
    if (v !== undefined && v !== null && String(v).trim() !== "") return v;
  }
  return "";
}

function normalizeAircallPayload(payload) {
  const callId = String(
    firstNonEmpty(payload, [
      "id",
      "event_id",
      "call.id",
      "call_id",
      "data.id",
      "data.call.id",
      "data.call_id",
      "data.callid",
      "data.sid",
      "sid",
    ])
  ).trim();

  const companyName = String(
    firstNonEmpty(payload, [
      "company_name",
      "contact.company_name",
      "contact.company",
      "data.company_name",
      "data.contact.company_name",
      "call.company_name",
    ])
  ).trim();

  const contactName = String(
    firstNonEmpty(payload, [
      "contact_name",
      "contact.name",
      "data.contact_name",
      "data.contact.name",
      "call.contact_name",
      "call.contact.name",
    ])
  ).trim();

  const phone = String(
    firstNonEmpty(payload, [
      "phone",
      "number",
      "to",
      "from",
      "contact.phone_number",
      "contact.phone",
      "data.phone",
      "data.number",
      "data.to",
      "data.from",
      "data.contact.phone_number",
      "call.raw_digits",
      "call.number",
      "call.to",
      "call.from",
    ])
  ).trim();

  const notes = String(
    firstNonEmpty(payload, [
      "notes",
      "summary",
      "comment",
      "comments",
      "data.notes",
      "data.summary",
      "data.comment",
      "data.comments",
      "call.notes",
      "call.summary",
    ])
  ).trim();

  const transcript = String(
    firstNonEmpty(payload, [
      "transcript",
      "transcript.text",
      "data.transcript",
      "data.transcript.text",
      "call.transcript",
      "call.transcript.text",
      "ai_summary",
      "data.ai_summary",
    ])
  ).trim();

  const outcomeRaw = String(
    firstNonEmpty(payload, [
      "outcome",
      "disposition",
      "status",
      "data.outcome",
      "data.disposition",
      "data.status",
      "call.outcome",
      "call.status",
      "event",
      "event_type",
      "type",
    ])
  ).trim();

  const dateRaw = String(
    firstNonEmpty(payload, [
      "date",
      "created_at",
      "ended_at",
      "timestamp",
      "occurred_at",
      "data.date",
      "data.created_at",
      "data.ended_at",
      "data.timestamp",
      "call.created_at",
      "call.ended_at",
    ])
  ).trim();

  let date = new Date().toISOString().slice(0, 10);
  if (dateRaw) {
    const dt = new Date(dateRaw);
    if (!Number.isNaN(dt.getTime())) date = dt.toISOString().slice(0, 10);
  }

  const combinedText = `${notes} ${transcript}`.trim();
  const outcome = normalizeOutcome(outcomeRaw, combinedText);
  const interactionId = callId ? `aircall-${callId}` : `aircall-${Date.now()}`;
  const summary = notes || transcript.slice(0, 240) || "Imported from Aircall webhook.";

  return {
    interactionId,
    companyName,
    contactName,
    phone,
    summary,
    transcript,
    outcome,
    date,
  };
}

function findProspectByCompanyOrPhone(companyName, phoneRaw) {
  const pipeline = readCsv(FILES.pipeline);
  const company = String(companyName || "").trim().toLowerCase();
  const phone = cleanPhone(phoneRaw);
  let match = null;
  if (company) {
    match = pipeline.find((p) => String(p.company_name || "").trim().toLowerCase() === company) || null;
  }
  if (!match && phone) {
    match =
      pipeline.find((p) => cleanPhone(p.contact_phone || "") === phone) ||
      null;
  }
  return match;
}

function launchDial(phone) {
  const clean = cleanPhone(phone);
  if (!clean) throw new Error("Invalid phone number.");
  spawn("powershell.exe", ["-NoProfile", "-Command", `Start-Process "tel:${clean}"`], {
    cwd: path.join(ROOT, ".."),
    windowsHide: true,
    detached: true,
    stdio: "ignore",
  }).unref();
  return clean;
}

async function handleApi(req, res, url) {
  if (req.method === "GET" && url.pathname === "/api/follow-up-ics") {
    if (!fs.existsSync(FILES.followUpsIcs)) return json(res, 404, { error: "Follow-up ICS not found yet." });
    const data = fs.readFileSync(FILES.followUpsIcs, "utf8");
    res.writeHead(200, { "Content-Type": "text/calendar; charset=utf-8", "Content-Length": Buffer.byteLength(data) });
    res.end(data);
    return;
  }
  if (req.method === "GET" && url.pathname === "/api/dashboard") {
    return json(res, 200, getDashboard());
  }
  if (req.method === "POST" && url.pathname === "/api/run-morning-refresh") {
    try {
      const out = await runPsScript("run-daily-brief-job.ps1");
      return json(res, 200, { ok: true, output: out.stdout });
    } catch (e) {
      return json(res, 500, { ok: false, error: e.message });
    }
  }
  if (req.method === "POST" && url.pathname === "/api/reset-queue") {
    const dash = getDashboard();
    const state = { call_date: dash.call_date, next_index: 0, pending_call: null, updated_at: nowIso() };
    writeState(state);
    return json(res, 200, { ok: true });
  }
  if (req.method === "POST" && url.pathname === "/api/start-next-call") {
    try {
      return json(res, 200, startNextCall());
    } catch (e) {
      return json(res, 400, { error: e.message });
    }
  }
  if (req.method === "POST" && url.pathname === "/api/log-outcome") {
    let body = "";
    req.on("data", (d) => {
      body += d.toString();
    });
    req.on("end", () => {
      try {
        const payload = body ? JSON.parse(body) : {};
        const result = logOutcome(payload);
        json(res, 200, result);
      } catch (e) {
        json(res, 400, { error: e.message });
      }
    });
    return;
  }
  if (req.method === "POST" && url.pathname === "/api/launch-dial") {
    let body = "";
    req.on("data", (d) => {
      body += d.toString();
    });
    req.on("end", () => {
      try {
        const payload = body ? JSON.parse(body) : {};
        const clean = launchDial(payload.phone || "");
        json(res, 200, { ok: true, phone: clean });
      } catch (e) {
        json(res, 400, { error: e.message });
      }
    });
    return;
  }
  if (req.method === "POST" && url.pathname === "/api/aircall-ingest") {
    let body = "";
    req.on("data", (d) => {
      body += d.toString();
    });
    req.on("end", () => {
      try {
        const payload = body ? JSON.parse(body) : {};
        const transcript = String(payload.transcript || "").trim();
        const notes = String(payload.notes || "").trim();
        const companyInput = String(payload.company_name || "").trim();
        const contactInput = String(payload.contact_name || "").trim();
        const phoneInput = String(payload.phone || "").trim();
        const interactionId = String(payload.interaction_id || "").trim() || `aircall-${Date.now()}`;
        const dateStr = String(payload.date || "").trim() || new Date().toISOString().slice(0, 10);
        const summary = notes || transcript.slice(0, 240) || "Imported from Aircall.";
        const combined = `${notes} ${transcript}`.trim();
        const outcome = String(payload.outcome || "").trim() || inferOutcomeFromText(combined);
        const nextAction = String(payload.next_action || "").trim() || "Follow-up based on call notes";
        const defaultTouch = defaultNextTouch(outcome, dateStr);
        const nextTouch = String(payload.next_touch_date || "").trim() || defaultTouch;

        const matched = findProspectByCompanyOrPhone(companyInput, phoneInput);
        const companyName = matched ? matched.company_name : companyInput || "Unknown Prospect";
        const contactName = contactInput || (matched ? matched.target_contact : "");

        applyLoggedOutcome({
          interactionId,
          companyName,
          contactName,
          outcome,
          nextTouch,
          nextAction,
          summary,
          dateStr,
        });

        json(res, 200, {
          ok: true,
          company_name: companyName,
          contact_name: contactName,
          outcome,
          next_touch_date: nextTouch,
          interaction_id: interactionId,
          matched: !!matched,
        });
      } catch (e) {
        json(res, 400, { error: e.message });
      }
    });
    return;
  }
  if (req.method === "POST" && url.pathname === "/api/aircall-webhook") {
    let rawBody = "";
    req.on("data", (d) => {
      rawBody += d.toString();
    });
    req.on("end", () => {
      try {
        if (!verifyWebhookAuth(req.headers || {}, rawBody)) {
          json(res, 401, { error: "Webhook authentication failed." });
          return;
        }
        const payload = rawBody ? JSON.parse(rawBody) : {};
        const parsed = normalizeAircallPayload(payload);
        const matched = findProspectByCompanyOrPhone(parsed.companyName, parsed.phone);
        const companyName = matched ? matched.company_name : parsed.companyName || "Unknown Prospect";
        const contactName = parsed.contactName || (matched ? matched.target_contact : "");
        const nextAction = "Follow-up based on webhook call outcome";
        const nextTouch = defaultNextTouch(parsed.outcome, parsed.date);

        applyLoggedOutcome({
          interactionId: parsed.interactionId,
          companyName,
          contactName,
          outcome: parsed.outcome,
          nextTouch,
          nextAction,
          summary: parsed.summary,
          dateStr: parsed.date,
        });

        json(res, 200, {
          ok: true,
          interaction_id: parsed.interactionId,
          company_name: companyName,
          contact_name: contactName,
          outcome: parsed.outcome,
          matched: !!matched,
        });
      } catch (e) {
        json(res, 400, { error: e.message });
      }
    });
    return;
  }
  json(res, 404, { error: "Not found" });
}

function serveStatic(req, res, url) {
  const rel = url.pathname === "/" ? "index.html" : url.pathname.slice(1);
  const filePath = path.join(APP_DIR, rel);
  if (!filePath.startsWith(`${APP_DIR}${path.sep}`) && filePath !== path.join(APP_DIR, "index.html")) {
    res.writeHead(403);
    res.end("forbidden");
    return;
  }
  if (!fs.existsSync(filePath)) {
    res.writeHead(404);
    res.end("not found");
    return;
  }
  const ext = path.extname(filePath).toLowerCase();
  const types = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
  };
  res.writeHead(200, { "Content-Type": types[ext] || "application/octet-stream" });
  fs.createReadStream(filePath).pipe(res);
}

function requestHandler(req, res) {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  if (url.pathname.startsWith("/api/")) return handleApi(req, res, url);
  return serveStatic(req, res, url);
}

ensureDirs();
const server = http.createServer(requestHandler);
server.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Boss Key Operator Console running at http://localhost:${PORT}`);
});
