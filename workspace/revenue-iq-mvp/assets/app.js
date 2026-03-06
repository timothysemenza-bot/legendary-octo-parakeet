
const STORAGE_KEY = "revenue-iq-proposal-agent-mvp-v1";

const GATE_CHECKS = [
  { id: "sow_match", label: "Scope aligns to FM proposal delivery strengths" },
  { id: "past_performance", label: "Relevant past performance evidence is available" },
  { id: "capacity", label: "Delivery and proposal capacity exists for timeline" },
  { id: "compliance_window", label: "Compliance package can be completed on time" }
];

const SCORE_CRITERIA = [
  { id: "capability_fit", label: "Capability fit", weight: 6 },
  { id: "past_performance_relevance", label: "Past performance relevance", weight: 5 },
  { id: "timeline_feasibility", label: "Timeline feasibility", weight: 4 },
  { id: "win_path_clarity", label: "Win path clarity", weight: 4 },
  { id: "risk_profile", label: "Contract risk profile", weight: 3 },
  { id: "margin_attractiveness", label: "Revenue/margin attractiveness", weight: 3 },
  { id: "strategic_value", label: "Strategic value", weight: 2 }
];

const CLIENTS = [
  {
    client_id: "demo-facilities-group",
    name: "Demo Facilities Group",
    industry: "Facilities Management",
    sharepoint_asset_index: {
      brand_files: ["brand/brand-guide.pdf", "brand/logo-primary.svg", "brand/proposal-cover-template.pptx"],
      past_performance_snippets: [
        "Delivered 98.7% SLA adherence for multi-site janitorial operations.",
        "Reduced mobilization timeline by 22% across regional FM transitions."
      ],
      approved_claims: [
        "12 years proposal management experience",
        "5 years facilities management proposal experience",
        "30+ years FM strategy and operational advisory partner experience"
      ],
      proposal_templates: ["templates/red-team-outline-v1.md", "templates/compliance-matrix-v1.csv"],
      restrictions: ["Do not claim certifications unless client validates in writing"]
    }
  },
  {
    client_id: "pilot-campus-services",
    name: "Pilot Campus Services",
    industry: "Facilities Management",
    sharepoint_asset_index: {
      brand_files: ["brand/pilot-campus-style-guide.pdf", "brand/pilot-campus-logo.png"],
      past_performance_snippets: ["Managed custodial and event support programs for 3 campus portfolios."],
      approved_claims: ["APMP lifecycle-driven proposal governance", "Human-supervised AI delivery model"],
      proposal_templates: ["templates/fm-rfp-response-v2.docx"],
      restrictions: ["No wage-rate commitments in draft without finance review"]
    }
  }
];

const DEMO_RFP = {
  opportunity_title: "Regional Facilities Operations and Janitorial Services",
  due_date: nextDate(14),
  priority_flags: ["incumbent", "tight timeline"],
  rfp_text: "This solicitation seeks facilities operations and janitorial services across 12 sites. Evaluation criteria include technical approach, relevant past performance, staffing plan, and price. Proposal due date is 2026-03-28. Submit mandatory compliance forms and references."
};

let state = loadState();
let selectedSubmissionId = state.submissions[0]?.id || null;

const $ = (id) => document.getElementById(id);

const refs = {
  kpiGrid: $("kpiGrid"),
  intakeForm: $("intakeForm"),
  clientId: $("clientId"),
  intakeStatus: $("intakeStatus"),
  assetIndex: $("assetIndex"),
  qualificationResult: $("qualificationResult"),
  submissionSelect: $("submissionSelect"),
  selectedSubmissionLabel: $("selectedSubmissionLabel"),
  gatePanel: $("gatePanel"),
  scorecard: $("scorecard"),
  criteriaRows: $("criteriaRows"),
  decisionSummary: $("decisionSummary"),
  saveDecisionBtn: $("saveDecisionBtn"),
  generateDraftBtn: $("generateDraftBtn"),
  saveDraftEditsBtn: $("saveDraftEditsBtn"),
  draftStatus: $("draftStatus"),
  draftWorkspace: $("draftWorkspace"),
  reviewNoteForm: $("reviewNoteForm"),
  reviewNotesList: $("reviewNotesList"),
  versionHistory: $("versionHistory"),
  auditTrail: $("auditTrail")
};

init();

function init() {
  configureDocumentParsers();
  hydrateClientSelect();
  refs.intakeForm.addEventListener("submit", onRunIntake);
  refs.saveDecisionBtn.addEventListener("click", onSaveDecision);
  refs.generateDraftBtn.addEventListener("click", onGenerateDraft);
  refs.saveDraftEditsBtn.addEventListener("click", onSaveDraftEdits);
  refs.reviewNoteForm.addEventListener("submit", onAddReviewerNote);
  refs.submissionSelect.addEventListener("change", onSelectSubmission);

  $("seedDataBtn").addEventListener("click", onSeedData);
  $("exportStateBtn").addEventListener("click", onExportState);
  $("openReportBtn").addEventListener("click", () => window.open("./report.html", "_blank"));

  render();
}

function configureDocumentParsers() {
  if (window.pdfjsLib) {
    try {
      window.pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.7.76/pdf.worker.min.js";
    } catch (_) {
      // Keep default worker settings.
    }
  }
}

function hydrateClientSelect() {
  refs.clientId.innerHTML = "";
  CLIENTS.forEach((client) => {
    const option = document.createElement("option");
    option.value = client.client_id;
    option.textContent = `${client.name} (${client.industry})`;
    refs.clientId.appendChild(option);
  });
}

async function onRunIntake(e) {
  e.preventDefault();

  const files = $("sourceDocs").files ? Array.from($("sourceDocs").files) : [];
  const pasted = $("rfpText").value.trim();

  if (!files.length && !pasted) {
    refs.intakeStatus.textContent = "Intake failed: add RFP files or paste solicitation text.";
    refs.intakeStatus.style.color = "#8f2020";
    return;
  }

  const snippets = [];
  const parseErrors = [];
  for (const file of files) {
    try {
      const parsed = await extractTextFromFile(file);
      if (parsed.trim()) snippets.push(parsed);
    } catch (error) {
      parseErrors.push(`${file.name}: ${error.message}`);
    }
  }
  if (pasted) snippets.push(pasted);

  const text = snippets.join("\n\n").slice(0, 120000);
  if (!text.trim()) {
    refs.intakeStatus.textContent = "Intake failed: no parseable text was extracted.";
    refs.intakeStatus.style.color = "#8f2020";
    return;
  }

  const submission = {
    id: crypto.randomUUID(),
    created_at: new Date().toISOString(),
    client_id: refs.clientId.value,
    opportunity_title: $("opportunityTitle").value.trim(),
    source_docs: files.map((f) => f.name),
    due_date: $("dueDate").value || nextDate(14),
    industry: $("industry").value.trim() || "Facilities Management",
    priority_flags: parseCsvField($("priorityFlags").value),
    raw_text: text,
    gate_checks: defaultGateChecks(),
    scores: Object.fromEntries(SCORE_CRITERIA.map((criterion) => [criterion.id, 0])),
    qualification_result: null,
    reviewer_notes: [],
    drafts: [],
    active_draft_version_id: null
  };

  submission.qualification_result = analyzeRfpText(submission.raw_text, submission);
  submission.gate_checks = submission.qualification_result.gate_checks;
  submission.scores = scoreSeedFromQualification(submission.qualification_result);

  state.submissions.unshift(submission);
  selectedSubmissionId = submission.id;

  logAudit("intake_created", `Created intake for ${submission.opportunity_title}`);
  logAudit("qualification_completed", `Qualification generated with ${submission.qualification_result.recommendation} recommendation`);

  persist();
  render();

  refs.intakeForm.reset();
  refs.clientId.value = submission.client_id;

  refs.intakeStatus.textContent = parseErrors.length
    ? `Intake complete with ${parseErrors.length} parser warning(s).`
    : "Intake and qualification complete.";
  refs.intakeStatus.style.color = parseErrors.length ? "#8f2020" : "#136446";
}

function onSaveDecision() {
  const submission = getSelectedSubmission();
  if (!submission) return;

  submission.qualification_result = buildQualificationResultFromCurrentState(submission);
  logAudit("decision_saved", `Decision saved as ${submission.qualification_result.recommendation} for ${submission.opportunity_title}`);
  persist();
  renderQualification(submission);
  renderKpis();
  renderSubmissionSelect();
}

function onGenerateDraft() {
  const submission = getSelectedSubmission();
  if (!submission) return;

  const recommendation = submission.qualification_result?.recommendation || "No-Go";
  if (recommendation === "No-Go") {
    refs.draftStatus.textContent = "Draft generation blocked: submission is No-Go.";
    refs.draftStatus.style.color = "#8f2020";
    logAudit("draft_blocked", `Draft blocked for ${submission.opportunity_title} due to No-Go decision`);
    return;
  }

  const client = getClient(submission.client_id);
  const previous = getActiveDraft(submission);
  const generated = generateDraft(submission, client, previous);

  submission.drafts.push(generated);
  submission.active_draft_version_id = generated.version_id;

  logAudit("draft_generated", `Generated draft version ${generated.version_label} for ${submission.opportunity_title}`);
  persist();
  render();

  refs.draftStatus.textContent = `Draft ${generated.version_label} generated.`;
  refs.draftStatus.style.color = "#136446";
}

function onSaveDraftEdits() {
  const submission = getSelectedSubmission();
  const draft = submission ? getActiveDraft(submission) : null;
  if (!submission || !draft) return;

  const sectionEls = document.querySelectorAll("[data-draft-section]");
  sectionEls.forEach((el) => {
    const key = el.dataset.draftSection;
    draft.sections[key].content = el.value;
  });

  const lockEls = document.querySelectorAll("[data-lock-section]");
  lockEls.forEach((el) => {
    const key = el.dataset.lockSection;
    draft.sections[key].locked = Boolean(el.checked);
  });

  logAudit("draft_edits_saved", `Saved manual edits for ${draft.version_label}`);
  persist();
  renderDraftWorkspace(submission);
}
function onAddReviewerNote(e) {
  e.preventDefault();
  const submission = getSelectedSubmission();
  if (!submission) return;

  const reviewer = $("reviewerName").value.trim() || "Reviewer";
  const note = $("reviewerNote").value.trim();
  if (!note) return;

  const item = {
    id: crypto.randomUUID(),
    created_at: new Date().toISOString(),
    reviewer,
    note
  };

  submission.reviewer_notes.unshift(item);
  logAudit("review_note_added", `${reviewer} added note on ${submission.opportunity_title}`);
  persist();
  renderReviewerNotes(submission);
  refs.reviewNoteForm.reset();
  $("reviewerName").value = reviewer;
}

function onSeedData() {
  const existing = state.submissions.find((submission) => submission.opportunity_title === DEMO_RFP.opportunity_title);
  if (existing) {
    selectedSubmissionId = existing.id;
    render();
    return;
  }

  const demoSubmission = {
    id: crypto.randomUUID(),
    created_at: new Date().toISOString(),
    client_id: CLIENTS[0].client_id,
    opportunity_title: DEMO_RFP.opportunity_title,
    source_docs: ["demo-rfp.txt"],
    due_date: DEMO_RFP.due_date,
    industry: "Facilities Management",
    priority_flags: DEMO_RFP.priority_flags,
    raw_text: DEMO_RFP.rfp_text,
    gate_checks: defaultGateChecks(),
    scores: Object.fromEntries(SCORE_CRITERIA.map((criterion) => [criterion.id, 0])),
    qualification_result: null,
    reviewer_notes: [],
    drafts: [],
    active_draft_version_id: null
  };

  demoSubmission.qualification_result = analyzeRfpText(demoSubmission.raw_text, demoSubmission);
  demoSubmission.gate_checks = demoSubmission.qualification_result.gate_checks;
  demoSubmission.scores = scoreSeedFromQualification(demoSubmission.qualification_result);

  state.submissions.unshift(demoSubmission);
  selectedSubmissionId = demoSubmission.id;

  logAudit("seed_demo", "Seeded demo RFP data");
  persist();
  render();
}

function onExportState() {
  const exportObj = {
    exported_at: new Date().toISOString(),
    contracts: {
      rfp_submission: {
        client_id: "string",
        opportunity_title: "string",
        source_docs: ["string"],
        due_date: "YYYY-MM-DD",
        industry: "string",
        priority_flags: ["string"]
      },
      qualification_result: {
        gate_checks: [{ id: "string", status: "pass|pending|fail", rationale: "string" }],
        weighted_score: "number",
        recommendation: "Go|Conditional|No-Go",
        rationale: ["string"],
        missing_data: ["string"]
      },
      proposal_draft_v1: {
        executive_summary: "string",
        compliance_matrix: "string",
        solution_outline: "string",
        assumptions: "string",
        risk_callouts: "string",
        brand_elements_applied: ["string"]
      },
      sharepoint_asset_index: {
        brand_files: ["string"],
        past_performance_snippets: ["string"],
        approved_claims: ["string"],
        proposal_templates: ["string"],
        restrictions: ["string"]
      }
    },
    state
  };

  const blob = new Blob([JSON.stringify(exportObj, null, 2)], { type: "application/json;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `revenue-iq-mvp-export-${new Date().toISOString().slice(0, 10)}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

function render() {
  renderKpis();

  const submission = getSelectedSubmission();
  renderAssetIndex(submission);
  renderQualification(submission);
  renderDecision(submission);
  renderDraftWorkspace(submission);
  renderReviewerNotes(submission);
  renderVersionHistory(submission);
  renderAuditTrail();
}

function renderKpis() {
  const total = state.submissions.length;
  const goCount = state.submissions.filter((item) => item.qualification_result?.recommendation === "Go").length;
  const conditionalCount = state.submissions.filter((item) => item.qualification_result?.recommendation === "Conditional").length;
  const noGoCount = state.submissions.filter((item) => item.qualification_result?.recommendation === "No-Go").length;
  const avgScore = total
    ? (state.submissions.reduce((sum, item) => sum + Number(item.qualification_result?.weighted_score || 0), 0) / total).toFixed(1)
    : "0.0";

  refs.kpiGrid.innerHTML = "";
  [
    { label: "RFP Intakes", value: total },
    { label: "Go", value: goCount },
    { label: "Conditional", value: conditionalCount },
    { label: "No-Go", value: noGoCount },
    { label: "Average Score", value: avgScore }
  ].forEach((metric) => {
    const item = document.createElement("div");
    item.className = "kpi";
    item.innerHTML = `<p>${metric.label}</p><h3>${metric.value}</h3>`;
    refs.kpiGrid.appendChild(item);
  });
}

function renderSubmissionSelect() {
  refs.submissionSelect.innerHTML = "";
  if (!state.submissions.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No submissions yet";
    refs.submissionSelect.appendChild(option);
    refs.submissionSelect.disabled = true;
    return;
  }

  refs.submissionSelect.disabled = false;
  state.submissions.forEach((submission) => {
    const option = document.createElement("option");
    option.value = submission.id;
    option.textContent = `${submission.opportunity_title} | ${submission.due_date}`;
    if (submission.id === selectedSubmissionId) option.selected = true;
    refs.submissionSelect.appendChild(option);
  });
}

function onSelectSubmission() {
  const value = refs.submissionSelect.value;
  if (!value) return;
  selectedSubmissionId = value;
  render();
}

function renderAssetIndex(submission) {
  if (!submission) {
    refs.assetIndex.className = "empty";
    refs.assetIndex.textContent = "Select or create a submission to view client assets.";
    return;
  }

  const client = getClient(submission.client_id);
  const assets = client?.sharepoint_asset_index;
  if (!assets) {
    refs.assetIndex.className = "empty";
    refs.assetIndex.textContent = "No client asset profile found.";
    return;
  }

  refs.assetIndex.className = "review-box";
  refs.assetIndex.innerHTML = `
    <p><strong>Client:</strong> ${escapeHtml(client.name)}</p>
    <ul class="review-list">
      <li><strong>brand_files[]:</strong> ${assets.brand_files.map(escapeHtml).join(", ")}</li>
      <li><strong>past_performance_snippets[]:</strong> ${assets.past_performance_snippets.map(escapeHtml).join(" | ")}</li>
      <li><strong>approved_claims[]:</strong> ${assets.approved_claims.map(escapeHtml).join(" | ")}</li>
      <li><strong>proposal_templates[]:</strong> ${assets.proposal_templates.map(escapeHtml).join(", ")}</li>
      <li><strong>restrictions[]:</strong> ${assets.restrictions.map(escapeHtml).join(" | ")}</li>
    </ul>
  `;
}

function renderQualification(submission) {
  if (!submission || !submission.qualification_result) {
    refs.selectedSubmissionLabel.textContent = "No submission selected.";
    refs.qualificationResult.className = "empty";
    refs.qualificationResult.textContent = "Run intake to generate qualification output.";
    return;
  }

  const result = submission.qualification_result;
  refs.selectedSubmissionLabel.textContent = `${submission.opportunity_title} (${submission.due_date})`;
  refs.qualificationResult.className = "review-box";
  refs.qualificationResult.innerHTML = `
    <h4>qualification_result</h4>
    <ul class="review-list">
      <li><strong>weighted_score:</strong> ${Number(result.weighted_score).toFixed(1)}</li>
      <li><strong>recommendation:</strong> ${escapeHtml(result.recommendation)}</li>
      <li><strong>rationale[]:</strong> ${result.rationale.map(escapeHtml).join(" | ") || "n/a"}</li>
      <li><strong>missing_data[]:</strong> ${result.missing_data.map(escapeHtml).join(" | ") || "none"}</li>
    </ul>
  `;
}
function renderDecision(submission) {
  if (!submission || !submission.qualification_result) {
    refs.gatePanel.classList.add("hidden");
    refs.scorecard.classList.add("hidden");
    refs.saveDecisionBtn.classList.add("hidden");
    refs.decisionSummary.className = "empty";
    refs.decisionSummary.textContent = "Complete qualification to score and decide.";
    return;
  }

  refs.gatePanel.classList.remove("hidden");
  refs.scorecard.classList.remove("hidden");
  refs.saveDecisionBtn.classList.remove("hidden");

  refs.gatePanel.innerHTML = "<h3>gate_checks[]</h3>";
  GATE_CHECKS.forEach((gate) => {
    const row = document.createElement("div");
    row.className = "gate-row";
    const current = submission.gate_checks[gate.id] || { status: "pending", rationale: "Not reviewed" };
    row.innerHTML = `
      <p>${escapeHtml(gate.label)}</p>
      <select data-gate-id="${gate.id}">
        <option value="pending" ${current.status === "pending" ? "selected" : ""}>Pending</option>
        <option value="pass" ${current.status === "pass" ? "selected" : ""}>Pass</option>
        <option value="fail" ${current.status === "fail" ? "selected" : ""}>Fail</option>
      </select>
      <span class="gate-chip ${current.status}">${current.status.toUpperCase()}</span>
    `;

    row.querySelector("select").addEventListener("change", (event) => {
      const status = event.target.value;
      submission.gate_checks[gate.id].status = status;
      submission.gate_checks[gate.id].rationale = `Set manually during review (${status})`;
      renderDecision(submission);
    });

    refs.gatePanel.appendChild(row);
  });

  refs.criteriaRows.innerHTML = "";
  SCORE_CRITERIA.forEach((criterion) => {
    const row = document.createElement("div");
    row.className = "criteria-row";
    const value = Number(submission.scores[criterion.id] || 0);
    row.innerHTML = `
      <label>${escapeHtml(criterion.label)}</label>
      <span>wt ${criterion.weight}</span>
      <input type="range" min="0" max="5" step="1" value="${value}" data-score-id="${criterion.id}">
      <strong>${value}</strong>
    `;

    const input = row.querySelector("input");
    const valueLabel = row.querySelector("strong");
    input.addEventListener("input", () => {
      submission.scores[criterion.id] = Number(input.value);
      valueLabel.textContent = input.value;
      const updated = buildQualificationResultFromCurrentState(submission);
      refs.decisionSummary.className = "review-box";
      refs.decisionSummary.innerHTML = `<p><strong>Preview recommendation:</strong> ${escapeHtml(updated.recommendation)} (${updated.weighted_score.toFixed(1)})</p>`;
    });

    refs.criteriaRows.appendChild(row);
  });

  const current = buildQualificationResultFromCurrentState(submission);
  refs.decisionSummary.className = "review-box";
  refs.decisionSummary.innerHTML = `
    <p><strong>Current recommendation:</strong> ${escapeHtml(current.recommendation)}</p>
    <p><strong>Weighted score:</strong> ${current.weighted_score.toFixed(1)}</p>
  `;
}

function renderDraftWorkspace(submission) {
  const draft = submission ? getActiveDraft(submission) : null;
  if (!submission || !draft) {
    refs.draftWorkspace.className = "empty";
    refs.draftWorkspace.textContent = "No draft generated yet.";
    return;
  }

  const sectionsHtml = Object.entries(draft.sections).map(([key, section]) => `
    <div class="panel" style="margin-bottom:8px;">
      <div class="panel-head">
        <h2>${escapeHtml(key)}</h2>
        <label class="hint">
          <input type="checkbox" data-lock-section="${escapeHtml(key)}" ${section.locked ? "checked" : ""}>
          Lock section on regenerate
        </label>
      </div>
      <textarea data-draft-section="${escapeHtml(key)}" style="min-height:110px;">${escapeHtml(section.content)}</textarea>
      <p class="hint"><strong>Citations:</strong> ${section.citations.map(escapeHtml).join(" | ") || "None"}</p>
    </div>
  `).join("");

  refs.draftWorkspace.className = "";
  refs.draftWorkspace.innerHTML = `
    <p><strong>Active Version:</strong> ${escapeHtml(draft.version_label)} (${new Date(draft.created_at).toLocaleString()})</p>
    ${sectionsHtml}
  `;
}

function renderReviewerNotes(submission) {
  if (!submission || !submission.reviewer_notes.length) {
    refs.reviewNotesList.className = "empty";
    refs.reviewNotesList.textContent = "No notes yet.";
    return;
  }

  refs.reviewNotesList.className = "";
  refs.reviewNotesList.innerHTML = submission.reviewer_notes
    .map((note) => `<div class="profile"><div><h4>${escapeHtml(note.reviewer)}</h4><p>${escapeHtml(note.note)}</p></div><p class="hint">${new Date(note.created_at).toLocaleString()}</p></div>`)
    .join("");
}

function renderVersionHistory(submission) {
  if (!submission || !submission.drafts.length) {
    refs.versionHistory.className = "empty";
    refs.versionHistory.textContent = "No versions yet.";
    return;
  }

  refs.versionHistory.className = "";
  refs.versionHistory.innerHTML = submission.drafts
    .slice()
    .reverse()
    .map((draft) => {
      const active = draft.version_id === submission.active_draft_version_id;
      return `
        <div class="profile">
          <div>
            <h4>${escapeHtml(draft.version_label)} ${active ? "(Active)" : ""}</h4>
            <p>${new Date(draft.created_at).toLocaleString()}</p>
          </div>
          <button class="btn secondary" data-version-id="${draft.version_id}">Load</button>
        </div>
      `;
    })
    .join("");

  document.querySelectorAll("[data-version-id]").forEach((button) => {
    button.addEventListener("click", () => {
      submission.active_draft_version_id = button.dataset.versionId;
      logAudit("draft_version_loaded", `Loaded ${button.dataset.versionId}`);
      persist();
      renderDraftWorkspace(submission);
      renderVersionHistory(submission);
    });
  });
}

function renderAuditTrail() {
  if (!state.audit_trail.length) {
    refs.auditTrail.className = "empty";
    refs.auditTrail.textContent = "No audit entries yet.";
    return;
  }

  refs.auditTrail.className = "";
  refs.auditTrail.innerHTML = state.audit_trail
    .slice(0, 50)
    .map((entry) => `
      <div class="profile">
        <div>
          <h4>${escapeHtml(entry.type)}</h4>
          <p>${escapeHtml(entry.message)}</p>
        </div>
        <p class="hint">${new Date(entry.created_at).toLocaleString()}</p>
      </div>
    `)
    .join("");
}

function analyzeRfpText(text, submission) {
  const lower = text.toLowerCase();
  const rationale = [];
  const missingData = [];
  let score = 50;

  const has = (pattern) => pattern.test(lower);

  if (has(/\b(facilities|janitorial|operations support|maintenance)\b/)) {
    rationale.push("Scope language aligns with facilities management service profile.");
    score += 15;
  } else {
    rationale.push("Scope language has weak facilities management alignment.");
    score -= 12;
  }

  if (has(/\b(past performance|references|experience)\b/)) {
    rationale.push("RFP asks for past performance evidence, matching available assets.");
    score += 8;
  } else {
    missingData.push("Past performance requirements were not clearly detected.");
  }

  if (has(/\b(proposal due|response due|question due|closing date|due date)\b/)) {
    rationale.push("Submission timing language detected.");
    score += 6;
  } else {
    missingData.push("No explicit due-date language found in provided text.");
    score -= 5;
  }

  if (has(/\b(secret|top secret|facility clearance)\b/)) {
    rationale.push("Security clearance requirement detected; potential blocker.");
    score -= 20;
  }

  if (has(/\bincumbent\b/)) {
    rationale.push("Incumbent advantage signal detected.");
    score -= 8;
  }

  if (has(/\blpta|lowest price technically acceptable\b/)) {
    rationale.push("LPTA signal detected; margin pressure expected.");
    score -= 7;
  }

  if (!has(/\b(evaluation criteria|technical approach|price|staffing plan|compliance)\b/)) {
    missingData.push("Evaluation criteria not clearly identified from provided text.");
  }

  if (!submission.priority_flags.length) {
    missingData.push("priority_flags[] is empty; leadership priorities may be under-specified.");
  }

  score = Math.max(0, Math.min(100, score));

  const gateChecks = defaultGateChecks();
  gateChecks.sow_match = {
    status: has(/\b(facilities|janitorial|operations support|maintenance)\b/) ? "pass" : "fail",
    rationale: "Automated scope fit assessment"
  };
  gateChecks.past_performance = {
    status: has(/\b(past performance|references|experience)\b/) ? "pass" : "pending",
    rationale: "Automated evidence signal detection"
  };
  gateChecks.capacity = {
    status: has(/\b(24\/7|24x7|multiple shifts)\b/) ? "pending" : "pass",
    rationale: "Capacity complexity signal check"
  };
  gateChecks.compliance_window = {
    status: has(/\b(proposal due|response due|question due|closing date|due date)\b/) ? "pass" : "pending",
    rationale: "Timeline completeness check"
  };

  const weightedScore = score;
  const recommendation = decideRecommendation(weightedScore, gateChecks);

  return {
    gate_checks: gateChecks,
    weighted_score: weightedScore,
    recommendation,
    rationale,
    missing_data: missingData
  };
}
function scoreSeedFromQualification(result) {
  const baseline = result.weighted_score;
  const normalized = Math.round((baseline / 100) * 5);
  return Object.fromEntries(SCORE_CRITERIA.map((criterion) => [criterion.id, Math.max(0, Math.min(5, normalized))]));
}

function buildQualificationResultFromCurrentState(submission) {
  const totalWeight = SCORE_CRITERIA.reduce((sum, criterion) => sum + criterion.weight, 0);
  const weighted = SCORE_CRITERIA.reduce((sum, criterion) => {
    const value = Number(submission.scores[criterion.id] || 0);
    return sum + (value * criterion.weight);
  }, 0);

  const weightedScore = (weighted / (totalWeight * 5)) * 100;
  const recommendation = decideRecommendation(weightedScore, submission.gate_checks);

  const rationale = [
    `Weighted score calculated from ${SCORE_CRITERIA.length} criteria.`,
    `Gate status is ${gateStatusSummary(submission.gate_checks)}.`
  ];

  const missingData = [];
  if (!submission.source_docs.length) missingData.push("source_docs[] empty");
  if (!submission.priority_flags.length) missingData.push("priority_flags[] empty");
  if (!submission.due_date) missingData.push("due_date missing");

  return {
    gate_checks: submission.gate_checks,
    weighted_score: weightedScore,
    recommendation,
    rationale,
    missing_data: missingData
  };
}

function decideRecommendation(weightedScore, gateChecks) {
  const statuses = Object.values(gateChecks).map((item) => item.status);
  if (statuses.includes("fail")) return "No-Go";
  if (statuses.includes("pending")) return weightedScore >= 70 ? "Conditional" : "No-Go";
  if (weightedScore >= 80) return "Go";
  if (weightedScore >= 65) return "Conditional";
  return "No-Go";
}

function generateDraft(submission, client, previousDraft) {
  const lockedSections = previousDraft
    ? Object.fromEntries(Object.entries(previousDraft.sections).filter(([, section]) => section.locked))
    : {};

  const versionNumber = submission.drafts.length + 1;
  const versionLabel = `v${versionNumber}`;

  const sectionMap = {
    executive_summary: {
      content: `We recommend pursuing ${submission.opportunity_title} with a disciplined response strategy based on leadership go/no-go criteria, documented compliance controls, and FM-specific delivery credibility.`,
      citations: [
        client.sharepoint_asset_index.approved_claims[0],
        client.sharepoint_asset_index.brand_files[0]
      ]
    },
    compliance_matrix: {
      content: "Requirement coverage matrix initialized. Reviewer should map each requirement to owner, source evidence, and draft section before client review.",
      citations: [client.sharepoint_asset_index.proposal_templates[0]]
    },
    solution_outline: {
      content: "Proposed approach: mobilization governance, staffing transition, SLA controls, QA cadence, and client communication rhythm tied to evaluation criteria.",
      citations: [client.sharepoint_asset_index.past_performance_snippets[0]]
    },
    assumptions: {
      content: "Assumptions: client provides complete forms package; incumbent transition data is available; pricing table finalized after leadership review.",
      citations: [client.sharepoint_asset_index.restrictions[0]]
    },
    risk_callouts: {
      content: "Primary risks include timeline compression, incomplete requirements, and unsupported claims. Mitigations include red-team review, compliance checklist, and explicit assumption labels.",
      citations: ["Internal QA protocol"]
    },
    brand_elements_applied: {
      content: client.sharepoint_asset_index.brand_files.join("\n"),
      citations: client.sharepoint_asset_index.brand_files
    }
  };

  Object.entries(lockedSections).forEach(([key, section]) => {
    if (section?.content) {
      sectionMap[key] = {
        ...sectionMap[key],
        content: section.content,
        locked: true
      };
    }
  });

  const sections = Object.fromEntries(Object.entries(sectionMap).map(([key, section]) => [key, {
    content: section.content,
    citations: section.citations || [],
    locked: Boolean(section.locked)
  }]));

  return {
    version_id: crypto.randomUUID(),
    version_label: versionLabel,
    created_at: new Date().toISOString(),
    sections
  };
}

async function extractTextFromFile(file) {
  const lower = file.name.toLowerCase();

  if (/\.(txt|md|csv|json|html|xml|rtf)$/.test(lower)) {
    return file.text();
  }

  if (/\.pdf$/.test(lower)) {
    if (!window.pdfjsLib) throw new Error("PDF parser unavailable");
    const data = await file.arrayBuffer();
    const loadingTask = window.pdfjsLib.getDocument({ data });
    const pdf = await loadingTask.promise;
    const pages = [];
    const maxPages = Math.min(pdf.numPages, 30);
    for (let i = 1; i <= maxPages; i += 1) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      pages.push(content.items.map((item) => item.str).join(" "));
    }
    return pages.join("\n");
  }

  if (/\.docx$/.test(lower)) {
    if (!window.mammoth) throw new Error("DOCX parser unavailable");
    const buffer = await file.arrayBuffer();
    const result = await window.mammoth.extractRawText({ arrayBuffer: buffer });
    return result.value || "";
  }

  throw new Error("Unsupported file type");
}

function getSelectedSubmission() {
  if (!selectedSubmissionId) return null;
  return state.submissions.find((submission) => submission.id === selectedSubmissionId) || null;
}

function getClient(clientId) {
  return CLIENTS.find((client) => client.client_id === clientId) || CLIENTS[0];
}

function getActiveDraft(submission) {
  if (!submission.active_draft_version_id) return null;
  return submission.drafts.find((draft) => draft.version_id === submission.active_draft_version_id) || null;
}

function defaultGateChecks() {
  return Object.fromEntries(GATE_CHECKS.map((gate) => [gate.id, { status: "pending", rationale: "Not reviewed" }]));
}

function gateStatusSummary(gateChecks) {
  const statuses = Object.values(gateChecks).map((item) => item.status);
  if (statuses.includes("fail")) return "FAIL";
  if (statuses.includes("pending")) return "PENDING";
  return "PASS";
}

function logAudit(type, message) {
  state.audit_trail.unshift({
    id: crypto.randomUUID(),
    type,
    message,
    created_at: new Date().toISOString()
  });
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return {
        submissions: parsed.submissions || [],
        audit_trail: parsed.audit_trail || []
      };
    }
  } catch (_) {
    // ignore and fall back
  }

  return {
    submissions: [],
    audit_trail: []
  };
}

function parseCsvField(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

function nextDate(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}
