const STORAGE_KEY = "federal-bid-cockpit-v1";
const STAGES = ["Review", "Qualify", "Pursue", "Submitted", "Won", "Lost"];
const GATE_PROFILES = {
  SAM: [
    { id: "sowMatch", label: "Scope aligns directly to your offered services" },
    { id: "pastPerfEvidence", label: "You can cite relevant past performance" },
    { id: "capacity", label: "You have delivery capacity for the period" },
    { id: "complianceWindow", label: "You can submit a compliant response on time" }
  ],
  NJSTART: [
    { id: "sowMatch", label: "Scope aligns to services you actively deliver now" },
    { id: "njCompliance", label: "NJ compliance forms/certifications can be met on time" },
    { id: "nigpMatch", label: "NIGP/commodity classification matches your profile" },
    { id: "capacity", label: "You can deliver with current capacity and timeline" }
  ]
};

const CRITERIA = [
  { id: "capabilityFit", label: "Capability fit", weight: 6 },
  { id: "pastPerformance", label: "Past performance relevance", weight: 5 },
  { id: "naicsAlignment", label: "NAICS/service alignment", weight: 4 },
  { id: "timeline", label: "Proposal effort vs timeline", weight: 4 },
  { id: "winPath", label: "Win path clarity", weight: 4 },
  { id: "risk", label: "Contract risk", weight: 3 },
  { id: "margin", label: "Revenue/margin attractiveness", weight: 2 },
  { id: "strategic", label: "Strategic value", weight: 2 }
];

const EXPERIENCE_PROFILE = {
  strengths: [
    /\bproposal (management|support|development|operations|writing|coordination)\b/,
    /\brfp (response|support|development|management|writer)\b/,
    /\bcapture\b/,
    /\bcompliance matrix\b/,
    /\bcontent library\b/,
    /\bqvidian\b/,
    /\bworkflow (improvement|optimization|automation)\b/,
    /\boperations? (consulting|support|improvement|management)\b/,
    /\bstrategic planning\b/,
    /\bpmo\b/,
    /\badministrative management\b/
  ],
  moderate: [
    /\btraining\b/,
    /\bchange management\b/,
    /\bbusiness process\b/,
    /\bprogram support\b/
  ],
  avoid: [
    /\bconstruction\b/,
    /\barchitectural\b/,
    /\bengineering\b/,
    /\bmechanical\b/,
    /\belectrical\b/,
    /\bhvac\b/,
    /\bplumbing\b/,
    /\broadway|asphalt|concrete\b/,
    /\bmedical supplies?|pharmaceuticals?\b/,
    /\bequipment purchase|heavy equipment\b/
  ]
};

const DEFAULT_SEARCHES = [
  {
    id: crypto.randomUUID(),
    name: "Core Consulting (NJ + Remote)",
    naics: "541611",
    include: "management consulting, strategic planning, operations support, process improvement",
    exclude: "construction, asphalt, hvac, plumbing, janitorial supplies"
  },
  {
    id: crypto.randomUUID(),
    name: "Process/IT Support",
    naics: "541611,541512",
    include: "workflow, business process, PMO support, digital transformation",
    exclude: "medical supplies, vehicle purchase, uniforms"
  }
];

const seedOpportunities = [
  {
    id: crypto.randomUUID(),
    source: "SAM",
    title: "Program Operations Advisory Support",
    agency: "GSA",
    naics: "541611",
    dueDate: nextDate(12),
    noticeType: "Solicitation",
    setAside: "Total Small Business",
    fitLane: "Management Consulting",
    url: "",
    notes: "Remote-heavy support, clear SOW.",
    stage: "Qualify",
    createdAt: new Date().toISOString(),
    gate: { sowMatch: "pass", pastPerfEvidence: "pass", capacity: "pass", complianceWindow: "pass" },
    scores: {
      capabilityFit: 4,
      pastPerformance: 3,
      naicsAlignment: 5,
      timeline: 4,
      winPath: 3,
      risk: 3,
      margin: 3,
      strategic: 4
    }
  },
  {
    id: crypto.randomUUID(),
    source: "SAM",
    title: "Acquisition Planning Process Modernization",
    agency: "Department of Labor",
    naics: "541611",
    dueDate: nextDate(7),
    noticeType: "Sources Sought",
    setAside: "Open Competition",
    fitLane: "Program Support",
    url: "",
    notes: "Good influence opportunity; not immediate bid.",
    stage: "Review",
    createdAt: new Date().toISOString(),
    gate: { sowMatch: "pending", pastPerfEvidence: "pending", capacity: "pending", complianceWindow: "pending" },
    scores: {
      capabilityFit: 0,
      pastPerformance: 0,
      naicsAlignment: 0,
      timeline: 0,
      winPath: 0,
      risk: 0,
      margin: 0,
      strategic: 0
    }
  }
];

let state = loadState();
let selectedOpportunityId = state.opportunities[0]?.id || null;

const $ = (id) => document.getElementById(id);

const refs = {
  form: $("opportunityForm"),
  tableBody: $("opportunityTableBody"),
  kpi: $("kpiGrid"),
  scorecard: $("scorecard"),
  scorecardEmpty: $("scorecardEmpty"),
  gatePanel: $("gatePanel"),
  gateLocked: $("gateLocked"),
  selectedLabel: $("selectedOpportunityLabel"),
  criteriaRows: $("criteriaRows"),
  weightedScore: $("weightedScore"),
  recommendationText: $("recommendationText"),
  recommendationReason: $("recommendationReason"),
  pipeline: $("pipelineBoard"),
  searchForm: $("searchForm"),
  searchProfiles: $("searchProfiles"),
  weeklyReview: $("weeklyReview"),
  importCsvForm: $("importCsvForm"),
  importApiForm: $("importApiForm"),
  importStatus: $("importStatus"),
  docReviewForm: $("docReviewForm"),
  docReviewResult: $("docReviewResult")
};

init();

function init() {
  configureDocumentParsers();
  refs.form.addEventListener("submit", onAddOpportunity);
  refs.searchForm.addEventListener("submit", onAddSearch);
  refs.importCsvForm.addEventListener("submit", onImportCsv);
  refs.importApiForm.addEventListener("submit", onImportApi);
  refs.docReviewForm.addEventListener("submit", onReviewDocuments);
  $("seedDataBtn").addEventListener("click", onSeedData);
  $("exportCsvBtn").addEventListener("click", onExportCsv);
  $("openReportBtn").addEventListener("click", () => window.open("./report.html", "_blank"));
  render();
}

function configureDocumentParsers() {
  if (window.pdfjsLib) {
    try {
      window.pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.7.76/pdf.worker.min.js";
    } catch (_) {
      // keep default worker if CDN worker cannot be set
    }
  }
}

function onAddOpportunity(e) {
  e.preventDefault();
  const opportunity = buildOpportunity({
    source: $("source").value,
    title: $("title").value.trim(),
    agency: $("agency").value.trim(),
    naics: $("naics").value.trim(),
    dueDate: $("dueDate").value,
    noticeType: $("noticeType").value,
    setAside: $("setAside").value,
    fitLane: $("fitLane").value,
    url: $("url").value.trim(),
    notes: $("notes").value.trim()
  });

  state.opportunities.unshift(opportunity);
  selectedOpportunityId = opportunity.id;
  persist();
  refs.form.reset();
  $("source").value = "SAM";
  $("naics").value = "541611";
  render();
}

function onAddSearch(e) {
  e.preventDefault();
  state.searches.unshift({
    id: crypto.randomUUID(),
    name: $("searchName").value.trim(),
    naics: $("searchNaics").value.trim(),
    include: $("searchInclude").value.trim(),
    exclude: $("searchExclude").value.trim()
  });

  persist();
  refs.searchForm.reset();
  renderSearches();
}

function onSeedData() {
  state.opportunities = [...seedOpportunities, ...state.opportunities];
  selectedOpportunityId = state.opportunities[0].id;
  persist();
  render();
}

async function onImportCsv(e) {
  e.preventDefault();
  const file = $("samCsvFile").files?.[0];
  const source = $("importSource").value || "SAM";
  if (!file) {
    setImportStatus("CSV import failed: choose a file.", true);
    return;
  }

  try {
    const text = await file.text();
    const rows = parseCsv(text);
    if (!rows.length) {
      setImportStatus("CSV import failed: no rows found.", true);
      return;
    }

    const headers = rows[0].map((h) => normalizeKey(h));
    const imported = [];

    for (let i = 1; i < rows.length; i += 1) {
      const row = rows[i];
      if (!row.length || row.every((v) => !String(v).trim())) continue;
      const obj = {};
      headers.forEach((h, idx) => { obj[h] = row[idx] || ""; });

      const title = source === "NJSTART"
        ? pick(obj, ["title", "bid title", "bidtitle", "solicitation", "description"])
        : pick(obj, ["title", "solicitationtitle", "notice_title", "opportunitytitle", "opportunity_title"]);
      const agency = source === "NJSTART"
        ? pick(obj, ["agency", "buyer", "department", "contracting unit", "issuing agency"])
        : pick(obj, ["agency", "departmentindoffice", "office", "organization", "fullparentpathname"]);
      const naics = source === "NJSTART"
        ? (pick(obj, ["naics", "naicscode", "naics code"]) || "541611")
        : (pick(obj, ["naics", "naicscode", "naics_code"]) || "541611");
      const dueDate = source === "NJSTART"
        ? (normalizeDate(pick(obj, ["due date", "closing date", "bid due", "response due"])) || nextDate(14))
        : (normalizeDate(pick(obj, ["responsedeadlinedate", "response_deadline", "due_date", "closedate", "archive_date"])) || nextDate(14));
      const noticeType = source === "NJSTART"
        ? (pick(obj, ["notice type", "event type", "status"]) || "Solicitation")
        : (pick(obj, ["noticetype", "notice_type"]) || "Solicitation");
      const url = pick(obj, ["ui_link", "link", "url", "resource_url", "event url", "bid url"]);
      const notes = source === "NJSTART"
        ? pick(obj, ["notes", "description", "commodity", "nigp", "category"]).slice(0, 220)
        : pick(obj, ["description", "summary", "additionalinfo"]).slice(0, 220);

      if (!title || !agency) continue;
      imported.push(buildOpportunity({ source, title, agency, naics, dueDate, noticeType, setAside: "Open Competition", fitLane: inferLane(naics), url, notes }));
    }

    if (!imported.length) {
      setImportStatus("CSV import completed but no usable opportunities were parsed.", true);
      return;
    }

    state.opportunities = [...imported, ...state.opportunities];
    selectedOpportunityId = state.opportunities[0].id;
    persist();
    render();
    refs.importCsvForm.reset();
    setImportStatus(`${source} CSV import complete: ${imported.length} opportunities added.`);
  } catch (error) {
    setImportStatus(`CSV import failed: ${error.message}`, true);
  }
}

async function onImportApi(e) {
  e.preventDefault();
  const apiKey = $("samApiKey").value.trim();
  const naics = $("samApiNaics").value.trim() || "541611";
  const keyword = $("samApiKeyword").value.trim() || "management consulting";

  if (!apiKey) {
    setImportStatus("API import failed: add your SAM API key.", true);
    return;
  }

  try {
    const endpoint = new URL("https://api.sam.gov/prod/opportunities/v2/search");
    endpoint.searchParams.set("api_key", apiKey);
    endpoint.searchParams.set("ncode", naics);
    endpoint.searchParams.set("q", keyword);
    endpoint.searchParams.set("limit", "20");
    endpoint.searchParams.set("postedFrom", new Date(Date.now() - 1000 * 60 * 60 * 24 * 21).toISOString().slice(0, 10));

    const response = await fetch(endpoint.toString());
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();
    const list = payload?.opportunitiesData || payload?.opportunities || payload?.data || [];
    const imported = list
      .map((item) => {
        const title = item.title || item.solicitationTitle || item.noticeTitle || "";
        const agency = item.fullParentPathName || item.departmentIndAgency || item.organizationName || "";
        if (!title || !agency) return null;
        return buildOpportunity({
          source: "SAM",
          title,
          agency,
          naics: item.naicsCode || naics,
          dueDate: normalizeDate(item.responseDeadLine || item.responseDeadline || item.closeDate) || nextDate(14),
          noticeType: item.noticeType || "Solicitation",
          setAside: item.typeOfSetAsideDescription || "Open Competition",
          fitLane: inferLane(item.naicsCode || naics),
          url: item.uiLink || "",
          notes: (item.description || "Imported from SAM API").slice(0, 220)
        });
      })
      .filter(Boolean);

    if (!imported.length) {
      setImportStatus("API import completed but returned no usable opportunities.", true);
      return;
    }

    state.opportunities = [...imported, ...state.opportunities];
    selectedOpportunityId = state.opportunities[0].id;
    persist();
    render();
    setImportStatus(`API import complete: ${imported.length} opportunities added.`);
  } catch (error) {
    setImportStatus(`API import failed: ${error.message}`, true);
  }
}

async function onReviewDocuments(e) {
  e.preventDefault();
  const files = $("bidFiles").files ? Array.from($("bidFiles").files) : [];
  const pasted = $("bidText").value.trim();

  if (!files.length && !pasted) {
    refs.docReviewResult.className = "empty";
    refs.docReviewResult.textContent = "Add files or paste bid text to run review.";
    return;
  }

  const snippets = [];
  const parseErrors = [];
  for (const file of files) {
    try {
      const parsed = await extractTextFromFile(file);
      if (parsed.trim()) snippets.push(parsed);
    } catch (err) {
      parseErrors.push(`${file.name}: ${err.message}`);
    }
  }
  if (pasted) snippets.push(pasted);

  const joined = snippets.join("\n\n").slice(0, 120000);
  if (!joined.trim()) {
    refs.docReviewResult.className = "empty";
    refs.docReviewResult.textContent = "No parseable text found. Try different files or paste text excerpts.";
    return;
  }

  const selected = state.opportunities.find((o) => o.id === selectedOpportunityId) || null;
  const result = analyzeBidText(joined, selected?.source || "SAM", selected);
  renderDocReview(result, selected);
  if (parseErrors.length) {
    const msg = `Reviewed with warnings: ${parseErrors.length} file(s) could not be parsed.`;
    setImportStatus(msg, true);
  }
}

async function extractTextFromFile(file) {
  const lower = file.name.toLowerCase();

  if (/\.(txt|md|csv|json|html|xml|rtf)$/.test(lower)) {
    return file.text();
  }

  if (/\.pdf$/.test(lower)) {
    if (!window.pdfjsLib) throw new Error("PDF parser not loaded");
    const data = await file.arrayBuffer();
    const loadingTask = window.pdfjsLib.getDocument({ data });
    const pdf = await loadingTask.promise;
    const pages = [];
    const maxPages = Math.min(pdf.numPages, 30);
    for (let i = 1; i <= maxPages; i += 1) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      const line = content.items.map((item) => item.str).join(" ");
      pages.push(line);
    }
    return pages.join("\n");
  }

  if (/\.docx$/.test(lower)) {
    if (!window.mammoth) throw new Error("DOCX parser not loaded");
    const arrayBuffer = await file.arrayBuffer();
    const result = await window.mammoth.extractRawText({ arrayBuffer });
    return result.value || "";
  }

  throw new Error("Unsupported file type");
}

function onExportCsv() {
  const header = [
    "title", "source", "agency", "naics", "dueDate", "noticeType", "setAside", "fitLane", "stage", "gateStatus", "score", "recommendation", "notes"
  ];

  const rows = state.opportunities.map((o) => {
    const score = getWeightedScore(o).toFixed(1);
    const rec = getRecommendation(o).label;
    const gate = getGateStatus(o);
    return [
      o.title, (o.source || "SAM"), o.agency, o.naics, o.dueDate, o.noticeType, o.setAside, o.fitLane, o.stage, gate.label, score, rec, o.notes
    ].map(csvEscape).join(",");
  });

  const csv = [header.join(","), ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `bid-cockpit-export-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function render() {
  renderKpis();
  renderOpportunities();
  renderScorecard();
  renderPipeline();
  renderSearches();
  renderWeeklyReview();
}

function renderKpis() {
  const total = state.opportunities.length;
  const pursue = state.opportunities.filter((o) => ["Pursue", "Submitted"].includes(o.stage)).length;
  const won = state.opportunities.filter((o) => o.stage === "Won").length;
  const avgScore = total ? (state.opportunities.reduce((sum, o) => sum + getWeightedScore(o), 0) / total).toFixed(1) : "0.0";

  refs.kpi.innerHTML = "";
  [
    { label: "Total Opportunities", value: total },
    { label: "Active Pursuits", value: pursue },
    { label: "Wins", value: won },
    { label: "Average Score", value: avgScore }
  ].forEach((k) => {
    const div = document.createElement("div");
    div.className = "kpi";
    div.innerHTML = `<p>${k.label}</p><h3>${k.value}</h3>`;
    refs.kpi.appendChild(div);
  });
}

function renderOpportunities() {
  refs.tableBody.innerHTML = "";
  state.opportunities.forEach((o) => {
    const tr = document.createElement("tr");
    if (o.id === selectedOpportunityId) tr.classList.add("active");
    const score = getWeightedScore(o);
    const rec = getRecommendation(o);
    tr.innerHTML = `
      <td>${escapeHtml(o.title)}</td>
      <td>${escapeHtml(o.source || "SAM")}</td>
      <td>${escapeHtml(o.agency)}</td>
      <td>${escapeHtml(o.naics)}</td>
      <td>${escapeHtml(o.dueDate)}</td>
      <td>${escapeHtml(o.stage)}</td>
      <td>${score.toFixed(1)}</td>
      <td><span class="badge ${rec.className}">${rec.label}</span></td>
      <td><button class="icon-btn" data-delete-id="${o.id}">Delete</button></td>
    `;

    tr.addEventListener("click", (e) => {
      if (e.target.dataset.deleteId) return;
      selectedOpportunityId = o.id;
      renderOpportunities();
      renderScorecard();
    });

    const delBtn = tr.querySelector("[data-delete-id]");
    delBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      state.opportunities = state.opportunities.filter((x) => x.id !== o.id);
      if (selectedOpportunityId === o.id) selectedOpportunityId = state.opportunities[0]?.id || null;
      persist();
      render();
    });

    refs.tableBody.appendChild(tr);
  });
}

function renderScorecard() {
  const opportunity = state.opportunities.find((o) => o.id === selectedOpportunityId);
  if (!opportunity) {
    refs.scorecard.classList.add("hidden");
    refs.scorecardEmpty.classList.remove("hidden");
    refs.gatePanel.classList.add("hidden");
    refs.gateLocked.classList.add("hidden");
    refs.selectedLabel.textContent = "Select an opportunity";
    return;
  }

  if (!opportunity.gate) opportunity.gate = defaultGate(opportunity.source);

  refs.scorecardEmpty.classList.add("hidden");
  refs.selectedLabel.textContent = opportunity.title;

  renderGatePanel(opportunity);
  const gate = getGateStatus(opportunity);
  const locked = !gate.passed;

  refs.scorecard.classList.toggle("hidden", locked);
  refs.gateLocked.classList.toggle("hidden", !locked);

  if (locked) {
    updateScoreSummary(opportunity);
    return;
  }

  refs.criteriaRows.innerHTML = "";
  CRITERIA.forEach((criterion) => {
    const row = document.createElement("div");
    row.className = "criteria-row";
    const value = Number(opportunity.scores[criterion.id] || 0);
    row.innerHTML = `
      <label>${criterion.label}</label>
      <span>wt ${criterion.weight}</span>
      <input type="range" min="0" max="5" step="1" value="${value}" data-score-id="${criterion.id}">
      <strong>${value}</strong>
    `;

    const input = row.querySelector("input");
    const display = row.querySelector("strong");
    input.addEventListener("input", () => {
      display.textContent = input.value;
      opportunity.scores[criterion.id] = Number(input.value);
      persist();
      updateScoreSummary(opportunity);
      renderOpportunities();
      renderPipeline();
      renderWeeklyReview();
      renderKpis();
    });

    refs.criteriaRows.appendChild(row);
  });

  updateScoreSummary(opportunity);
}

function renderGatePanel(opportunity) {
  const requiredGates = getRequiredGates(opportunity.source);
  refs.gatePanel.classList.remove("hidden");
  refs.gatePanel.innerHTML = `<h3>Required Gate Checks (${escapeHtml(opportunity.source || "SAM")})</h3>`;

  requiredGates.forEach((gate) => {
    const value = opportunity.gate[gate.id] || "pending";
    const row = document.createElement("div");
    row.className = "gate-row";
    row.innerHTML = `
      <p>${gate.label}</p>
      <select data-gate-id="${gate.id}">
        <option value="pending" ${value === "pending" ? "selected" : ""}>Pending</option>
        <option value="pass" ${value === "pass" ? "selected" : ""}>Pass</option>
        <option value="fail" ${value === "fail" ? "selected" : ""}>Fail</option>
      </select>
      <span class="gate-chip ${value}">${value.toUpperCase()}</span>
    `;

    const select = row.querySelector("select");
    const chip = row.querySelector(".gate-chip");
    select.addEventListener("change", () => {
      opportunity.gate[gate.id] = select.value;
      chip.className = `gate-chip ${select.value}`;
      chip.textContent = select.value.toUpperCase();
      persist();
      renderScorecard();
      renderOpportunities();
      renderPipeline();
      renderWeeklyReview();
      renderKpis();
    });

    refs.gatePanel.appendChild(row);
  });
}

function updateScoreSummary(opportunity) {
  const score = getWeightedScore(opportunity);
  const rec = getRecommendation(opportunity);
  refs.weightedScore.textContent = score.toFixed(1);
  refs.recommendationText.textContent = rec.label;
  refs.recommendationReason.textContent = rec.reason;
}

function renderPipeline() {
  refs.pipeline.innerHTML = "";
  STAGES.forEach((stage) => {
    const col = document.createElement("div");
    col.className = "column";
    const count = state.opportunities.filter((o) => o.stage === stage).length;
    col.innerHTML = `<h4>${stage} (${count})</h4>`;

    state.opportunities
      .filter((o) => o.stage === stage)
      .forEach((o) => {
        const rec = getRecommendation(o);
        const gate = getGateStatus(o);
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `
          <h5>${escapeHtml(o.title)}</h5>
          <p>${escapeHtml(o.source || "SAM")} | ${escapeHtml(o.agency)} | ${escapeHtml(o.naics)}</p>
          <p>Due ${escapeHtml(o.dueDate)} | Gate ${gate.label} | Score ${getWeightedScore(o).toFixed(1)} | ${rec.label}</p>
          <select data-stage-id="${o.id}">
            ${STAGES.map((s) => `<option ${s === o.stage ? "selected" : ""}>${s}</option>`).join("")}
          </select>
        `;

        const select = card.querySelector("select");
        select.addEventListener("change", () => {
          o.stage = select.value;
          persist();
          renderPipeline();
          renderKpis();
          renderWeeklyReview();
          renderOpportunities();
        });

        col.appendChild(card);
      });

    refs.pipeline.appendChild(col);
  });
}

function renderSearches() {
  refs.searchProfiles.innerHTML = "";
  state.searches.forEach((s) => {
    const row = document.createElement("div");
    row.className = "profile";
    row.innerHTML = `
      <div>
        <h4>${escapeHtml(s.name)}</h4>
        <p><strong>NAICS:</strong> ${escapeHtml(s.naics)}</p>
        <p><strong>Include:</strong> ${escapeHtml(s.include)}</p>
        <p><strong>Exclude:</strong> ${escapeHtml(s.exclude)}</p>
      </div>
      <div>
        <button class="icon-btn" data-search-delete="${s.id}">Delete</button>
      </div>
    `;

    row.querySelector("button").addEventListener("click", () => {
      state.searches = state.searches.filter((x) => x.id !== s.id);
      persist();
      renderSearches();
    });

    refs.searchProfiles.appendChild(row);
  });
}

function renderWeeklyReview() {
  const recent = state.opportunities.filter((o) => {
    const createdAt = new Date(o.createdAt);
    const daysOld = (Date.now() - createdAt.getTime()) / (1000 * 60 * 60 * 24);
    return daysOld <= 7;
  });

  const reviewed = recent.length;
  const bids = recent.filter((o) => ["Pursue", "Submitted", "Won", "Lost"].includes(o.stage)).length;
  const noBids = recent.filter((o) => getRecommendation(o).label === "No-bid").length;
  const winRate = (() => {
    const completed = state.opportunities.filter((o) => ["Won", "Lost"].includes(o.stage));
    if (!completed.length) return "0%";
    const won = completed.filter((o) => o.stage === "Won").length;
    return `${Math.round((won / completed.length) * 100)}%`;
  })();

  refs.weeklyReview.innerHTML = "";
  [
    { label: "Reviewed (7d)", value: reviewed },
    { label: "Bid decisions (7d)", value: bids },
    { label: "No-bid decisions (7d)", value: noBids },
    { label: "Win rate (closed)", value: winRate }
  ].forEach((m) => {
    const item = document.createElement("div");
    item.className = "review-item";
    item.innerHTML = `<p>${m.label}</p><h4>${m.value}</h4>`;
    refs.weeklyReview.appendChild(item);
  });
}

function getWeightedScore(opportunity) {
  const totalWeight = CRITERIA.reduce((sum, c) => sum + c.weight, 0);
  const weighted = CRITERIA.reduce((sum, c) => {
    const score = Number(opportunity.scores[c.id] || 0);
    return sum + score * c.weight;
  }, 0);
  return (weighted / (totalWeight * 5)) * 100;
}

function getGateStatus(opportunity) {
  const requiredGates = getRequiredGates(opportunity.source);
  const gate = opportunity.gate || defaultGate(opportunity.source);
  const values = requiredGates.map((g) => gate[g.id] || "pending");
  if (values.includes("fail")) return { passed: false, label: "FAIL" };
  if (values.includes("pending")) return { passed: false, label: "PENDING" };
  return { passed: true, label: "PASS" };
}

function getRecommendation(opportunity) {
  const gate = getGateStatus(opportunity);
  if (!gate.passed) {
    return {
      label: "No-bid",
      className: "no-bid",
      reason: gate.label === "FAIL" ? "Gate check failed. Resolve scope/capacity/compliance blockers." : "Gate checks are incomplete. Complete all required checks."
    };
  }

  const score = getWeightedScore(opportunity);
  const autoNoBid =
    Number(opportunity.scores.capabilityFit || 0) <= 1 ||
    Number(opportunity.scores.pastPerformance || 0) <= 1 ||
    Number(opportunity.scores.timeline || 0) <= 1;

  if (autoNoBid) {
    return {
      label: "No-bid",
      className: "no-bid",
      reason: "Automatic no-bid triggered: capability, past performance, or timeline is critically low."
    };
  }

  if (score >= 80) return { label: "Bid", className: "bid", reason: "Strong fit and execution confidence." };
  if (score >= 65) return { label: "Conditional", className: "conditional", reason: "Pursue only if capacity and differentiation are clear." };
  return { label: "No-bid", className: "no-bid", reason: "Score is below threshold for disciplined pursuit." };
}

function getRequiredGates(source) {
  return GATE_PROFILES[source] || GATE_PROFILES.SAM;
}

function defaultGate(source) {
  return Object.fromEntries(getRequiredGates(source).map((g) => [g.id, "pending"]));
}

function buildOpportunity(input) {
  const source = input.source || "SAM";
  return {
    id: crypto.randomUUID(),
    source,
    title: input.title,
    agency: input.agency,
    naics: input.naics || "541611",
    dueDate: input.dueDate || nextDate(14),
    noticeType: input.noticeType || "Solicitation",
    setAside: input.setAside || "Open Competition",
    fitLane: input.fitLane || inferLane(input.naics),
    url: input.url || "",
    notes: input.notes || "",
    stage: "Review",
    createdAt: new Date().toISOString(),
    gate: defaultGate(source),
    scores: Object.fromEntries(CRITERIA.map((c) => [c.id, 0]))
  };
}

function setImportStatus(message, isError = false) {
  refs.importStatus.textContent = message;
  refs.importStatus.style.color = isError ? "#8f2020" : "#136446";
}

function inferLane(naics) {
  if (String(naics).startsWith("541512")) return "Process/IT Support";
  if (String(naics).startsWith("541611") || String(naics).startsWith("541618")) return "Management Consulting";
  return "Program Support";
}

function analyzeBidText(text, source, opportunity) {
  const t = text.toLowerCase();
  const includes = [];
  const risks = [];
  let score = 50;

  const has = (pattern) => pattern.test(t);

  if (has(/\b(541611|management consulting|operations support|strategic planning)\b/)) {
    includes.push("Service language aligns to management consulting lane.");
    score += 15;
  } else {
    risks.push("No clear management consulting language detected.");
    score -= 10;
  }

  if (has(/\b(remote|virtual|telework|hybrid)\b/)) {
    includes.push("Remote/hybrid execution appears possible.");
    score += 8;
  }

  if (has(/\b(secret|top secret|clearance|facility clearance)\b/)) {
    risks.push("Security clearance requirement detected.");
    score -= 20;
  }

  if (has(/\bonsite\b/) && !has(/\bremote\b/)) {
    risks.push("Onsite-heavy delivery appears required.");
    score -= 10;
  }

  if (has(/\bincumbent\b/)) {
    risks.push("Incumbent advantage language detected.");
    score -= 8;
  }

  if (has(/\bsmall business set-?aside|total small business\b/)) {
    includes.push("Small business set-aside signal detected.");
    score += 10;
  }

  if (has(/\b(lpta|lowest price technically acceptable)\b/)) {
    risks.push("LPTA pricing pressure detected.");
    score -= 8;
  }

  if (has(/\b(question due|response due|proposal due|closing date)\b/)) {
    includes.push("Submission deadline language detected.");
    score += 4;
  } else {
    risks.push("No explicit deadline terms found in provided text.");
    score -= 6;
  }

  const dueMatch = text.match(/\b(20\d{2}[-\/.]\d{1,2}[-\/.]\d{1,2}|\d{1,2}[-\/.]\d{1,2}[-\/.](20\d{2}|\d{2}))\b/);
  const extractedDue = dueMatch ? normalizeDate(dueMatch[0]) : "";

  const strongHits = EXPERIENCE_PROFILE.strengths.filter((rx) => has(rx)).length;
  const moderateHits = EXPERIENCE_PROFILE.moderate.filter((rx) => has(rx)).length;
  const avoidHits = EXPERIENCE_PROFILE.avoid.filter((rx) => has(rx)).length;

  if (strongHits > 0) {
    includes.push(`Experience-aligned scope signals detected (${strongHits} strong match${strongHits === 1 ? "" : "es"}).`);
    score += Math.min(22, strongHits * 5);
  } else {
    risks.push("No strong proposal/operations scope match found against your documented experience.");
    score -= 12;
  }

  if (moderateHits > 0) {
    includes.push(`Secondary experience signals detected (${moderateHits}).`);
    score += Math.min(8, moderateHits * 2);
  }

  if (avoidHits > 0) {
    risks.push(`Scope includes likely low-fit delivery domains (${avoidHits} mismatch signal${avoidHits === 1 ? "" : "s"}).`);
    score -= Math.min(24, avoidHits * 8);
  }

  const amountMatches = [...text.matchAll(/\$ ?([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{1,3}(?:\.[0-9]+)?)(?:\s*(million|billion|m|b))?/gi)];
  const maxAmount = amountMatches.reduce((max, m) => {
    const base = Number(String(m[1]).replaceAll(",", ""));
    if (Number.isNaN(base)) return max;
    const unit = (m[2] || "").toLowerCase();
    const val = unit === "million" || unit === "m" ? base * 1_000_000
      : unit === "billion" || unit === "b" ? base * 1_000_000_000
      : base;
    return Math.max(max, val);
  }, 0);

  if (maxAmount >= 25_000_000) {
    risks.push("Opportunity value appears very large for a new prime; consider subcontract or team strategy.");
    score -= 10;
  } else if (maxAmount > 0 && maxAmount <= 5_000_000) {
    includes.push("Opportunity value appears in a more realistic near-term prime range.");
    score += 4;
  }

  let gateSuggestion;
  if (source === "NJSTART") {
    if (has(/\b(nigp|commodity code)\b/)) includes.push("NIGP/commodity references detected.");
    else risks.push("No NIGP/commodity language detected in text.");

    if (has(/\b(chapter 51|eo 333|ownership disclosure|aa\/eeoc|insurance)\b/)) {
      includes.push("NJ compliance terms detected.");
    } else {
      risks.push("NJ-specific compliance terms were not detected.");
    }

    gateSuggestion = {
      sowMatch: includes.some((x) => x.includes("aligns")) ? "pass" : "pending",
      njCompliance: has(/\b(chapter 51|eo 333|ownership disclosure|aa\/eeoc|insurance)\b/) ? "pass" : "pending",
      nigpMatch: has(/\b(nigp|commodity code)\b/) ? "pass" : "pending",
      capacity: has(/\b(24\/7|24x7)\b/) ? "pending" : "pass"
    };
  } else {
    gateSuggestion = {
      sowMatch: includes.some((x) => x.includes("aligns")) ? "pass" : "pending",
      pastPerfEvidence: has(/\b(past performance|experience|references)\b/) ? "pass" : "pending",
      capacity: has(/\b(24\/7|24x7)\b/) ? "pending" : "pass",
      complianceWindow: extractedDue ? "pass" : "pending"
    };
  }
  if (risks.some((r) => r.includes("clearance"))) gateSuggestion.capacity = "fail";
  if (strongHits === 0 || avoidHits >= 2) gateSuggestion.sowMatch = "fail";

  score = Math.max(0, Math.min(100, score));
  let recommendation = "Conditional";
  if (score >= 75 && !Object.values(gateSuggestion).includes("fail")) recommendation = "Go";
  if (score < 60 || Object.values(gateSuggestion).includes("fail")) recommendation = "No-Go";

  return {
    recommendation,
    confidenceScore: score,
    includes,
    risks,
    extractedDue,
    gateSuggestion
  };
}

function renderDocReview(result, selectedOpportunity) {
  const gateRows = Object.entries(result.gateSuggestion)
    .map(([k, v]) => `<li><strong>${escapeHtml(k)}</strong>: ${escapeHtml(v.toUpperCase())}</li>`)
    .join("");
  const includeRows = (result.includes.length ? result.includes : ["No strong positive signals found."])
    .map((x) => `<li>${escapeHtml(x)}</li>`)
    .join("");
  const riskRows = (result.risks.length ? result.risks : ["No major risk terms detected in provided text."])
    .map((x) => `<li>${escapeHtml(x)}</li>`)
    .join("");

  refs.docReviewResult.className = "review-box";
  refs.docReviewResult.innerHTML = `
    <h4>Recommendation: <span class="badge ${result.recommendation === "Go" ? "bid" : result.recommendation === "No-Go" ? "no-bid" : "conditional"}">${escapeHtml(result.recommendation)}</span> | Confidence ${result.confidenceScore.toFixed(0)}/100</h4>
    <div class="review-grid">
      <div>
        <p><strong>Positive signals</strong></p>
        <ul class="review-list">${includeRows}</ul>
      </div>
      <div>
        <p><strong>Risk signals</strong></p>
        <ul class="review-list">${riskRows}</ul>
      </div>
    </div>
    <p class="hint">Extracted due date: ${escapeHtml(result.extractedDue || "Not detected")}</p>
    <p><strong>Suggested gate prefills</strong></p>
    <ul class="review-list">${gateRows}</ul>
    ${selectedOpportunity ? '<button id="applyGateSuggestionsBtn" class="btn">Apply Gate Suggestions To Selected Opportunity</button>' : '<p class="hint">No opportunity selected; suggestions not applied.</p>'}
  `;

  if (selectedOpportunity) {
    const btn = $("applyGateSuggestionsBtn");
    if (btn) {
      btn.addEventListener("click", () => {
        selectedOpportunity.gate = { ...selectedOpportunity.gate, ...result.gateSuggestion };
        if (result.extractedDue) selectedOpportunity.dueDate = result.extractedDue;
        persist();
        render();
      });
    }
  }
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      parsed.opportunities = (parsed.opportunities || []).map((o) => {
        const source = o.source || "SAM";
        return { ...o, source, gate: { ...defaultGate(source), ...(o.gate || {}) } };
      });
      parsed.searches = parsed.searches || DEFAULT_SEARCHES;
      return parsed;
    }
  } catch (_) {
    // fall through to defaults
  }

  return {
    opportunities: [],
    searches: DEFAULT_SEARCHES
  };
}

function csvEscape(value) {
  const str = String(value ?? "");
  if (str.includes(",") || str.includes("\"") || str.includes("\n")) {
    return `"${str.replaceAll("\"", "\"\"")}"`;
  }
  return str;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeKey(value) {
  return String(value || "").toLowerCase().trim().replaceAll(/[^a-z0-9]/g, "");
}

function pick(obj, keys) {
  for (const key of keys) {
    const value = obj[normalizeKey(key)] || obj[key];
    if (value && String(value).trim()) return String(value).trim();
  }
  return "";
}

function normalizeDate(value) {
  if (!value) return "";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return "";
  return dt.toISOString().slice(0, 10);
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"' && inQuotes && next === '"') {
      cell += '"';
      i += 1;
      continue;
    }

    if (char === '"') {
      inQuotes = !inQuotes;
      continue;
    }

    if (char === "," && !inQuotes) {
      row.push(cell);
      cell = "";
      continue;
    }

    if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && next === "\n") i += 1;
      row.push(cell);
      rows.push(row);
      row = [];
      cell = "";
      continue;
    }

    cell += char;
  }

  if (cell.length || row.length) {
    row.push(cell);
    rows.push(row);
  }

  return rows;
}

function nextDate(days) {
  const dt = new Date();
  dt.setDate(dt.getDate() + days);
  return dt.toISOString().slice(0, 10);
}
