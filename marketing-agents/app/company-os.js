const companyName = document.getElementById("companyName");
const companyTagline = document.getElementById("companyTagline");
const northStar = document.getElementById("northStar");
const principlesList = document.getElementById("principlesList");
const metricStrip = document.getElementById("metricStrip");
const cadenceGrid = document.getElementById("cadenceGrid");
const departmentDeck = document.getElementById("departmentDeck");
const fileGrid = document.getElementById("fileGrid");
const approvalGrid = document.getElementById("approvalGrid");
const app = document.getElementById("app");
const errorBox = document.getElementById("errorBox");

function createEl(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
}

function buildChipRow(values, className = "tag-chip") {
  const row = createEl("div", "chip-row");
  values.forEach((value) => {
    row.appendChild(createEl("span", className, value));
  });
  return row;
}

function renderMetrics(model) {
  const metricItems = [
    {
      label: "Agents",
      value: String(model.agents.length).padStart(2, "0"),
      note: "Specialized roles across revenue, delivery, finance, and founder ops."
    },
    {
      label: "Departments",
      value: String(model.departments.length),
      note: "Six operating lanes so the system mirrors the company, not just marketing."
    },
    {
      label: "Approval Gates",
      value: String(model.approval_gates.length),
      note: "Moments where a human still approves trust, money, or external obligations."
    },
    {
      label: "Control Files",
      value: String(model.operating_files.length),
      note: "Lightweight files that make the new agents auditable and runnable."
    }
  ];

  metricItems.forEach((item) => {
    const card = createEl("article", "metric-card");
    card.appendChild(createEl("p", "stat-label", item.label));
    card.appendChild(createEl("div", "stat-value", item.value));
    card.appendChild(createEl("p", "stat-note", item.note));
    metricStrip.appendChild(card);
  });
}

function renderCadence(model, agentMap) {
  Object.entries(model.cadence).forEach(([cadenceKey, items]) => {
    const lane = createEl("section", "cadence-lane");
    const header = createEl("div", "lane-header");
    const titleWrap = createEl("div");
    titleWrap.appendChild(createEl("p", "lane-label", cadenceKey));
    titleWrap.appendChild(createEl("h3", "", cadenceKey.charAt(0).toUpperCase() + cadenceKey.slice(1)));
    header.appendChild(titleWrap);
    header.appendChild(createEl("span", "slot-badge", `${items.length} loops`));
    lane.appendChild(header);

    const list = createEl("div", "lane-list");
    items.forEach((item) => {
      const card = createEl("article", "lane-item");
      const meta = createEl("div", "lane-meta");
      meta.appendChild(createEl("span", "slot-badge", item.slot));
      meta.appendChild(createEl("strong", "", item.title));
      card.appendChild(meta);
      card.appendChild(createEl("p", "", item.summary));
      card.appendChild(
        buildChipRow(
          item.agent_ids.map((id) => `A${id} ${agentMap.get(id)?.name || "Unknown Agent"}`),
          "mini-chip"
        )
      );
      list.appendChild(card);
    });

    lane.appendChild(list);
    cadenceGrid.appendChild(lane);
  });
}

function renderDepartments(model, agentMap) {
  model.departments.forEach((department) => {
    const card = createEl("section", "department-card");
    const header = createEl("div", "department-header");
    const copy = createEl("div");
    copy.appendChild(createEl("p", "lane-label", department.name));
    copy.appendChild(createEl("h3", "", department.name));
    copy.appendChild(createEl("p", "section-copy", department.theme));
    header.appendChild(copy);
    header.appendChild(createEl("span", "slot-badge", `${department.agent_ids.length} agents`));
    card.appendChild(header);

    const grid = createEl("div", "agent-grid");
    department.agent_ids.forEach((agentId, index) => {
      const agent = agentMap.get(agentId);
      if (!agent) return;

      const details = createEl("details", "agent-item");
      if (index === 0) details.open = true;

      const summary = createEl("summary");
      const top = createEl("div", "agent-top");
      const titleBlock = createEl("div");
      titleBlock.appendChild(createEl("div", "agent-id", `Agent ${agent.id}`));
      titleBlock.appendChild(createEl("h4", "", agent.name));
      top.appendChild(titleBlock);
      if (agent.approval_gate) {
        top.appendChild(createEl("span", "tag-chip alert", "Human gate"));
      }
      summary.appendChild(top);
      summary.appendChild(createEl("p", "agent-summary", agent.objective));
      summary.appendChild(
        createEl("div", "meta-row", `${agent.owner} | ${agent.frequency}`)
      );

      const body = createEl("div", "agent-body");

      const inputs = createEl("div", "detail-block");
      inputs.appendChild(createEl("div", "detail-title", "Inputs"));
      inputs.appendChild(buildChipRow(agent.inputs));
      body.appendChild(inputs);

      const outputs = createEl("div", "detail-block");
      outputs.appendChild(createEl("div", "detail-title", "Outputs"));
      outputs.appendChild(buildChipRow(agent.outputs, "mini-chip"));
      body.appendChild(outputs);

      const guardrails = createEl("div", "detail-block");
      guardrails.appendChild(createEl("div", "detail-title", "Guardrails"));
      guardrails.appendChild(createEl("p", "detail-copy", agent.guardrails.join(" ")));
      body.appendChild(guardrails);

      const handoff = createEl("div", "detail-block");
      handoff.appendChild(createEl("div", "detail-title", "Handoff"));
      handoff.appendChild(
        buildChipRow(
          agent.handoff_to.map((id) => `A${id} ${agentMap.get(id)?.name || "Unknown Agent"}`),
          "tag-chip"
        )
      );
      body.appendChild(handoff);

      if (agent.approval_gate) {
        const approval = createEl("div", "detail-block");
        approval.appendChild(createEl("div", "detail-title", "Approval Gate"));
        approval.appendChild(createEl("p", "detail-copy", agent.approval_gate));
        body.appendChild(approval);
      }

      details.appendChild(summary);
      details.appendChild(body);
      grid.appendChild(details);
    });

    card.appendChild(grid);
    departmentDeck.appendChild(card);
  });
}

function renderFiles(model, agentMap) {
  model.operating_files.forEach((file) => {
    const card = createEl("article", "file-card");
    card.appendChild(createEl("p", "file-label", "Operating File"));
    card.appendChild(createEl("div", "file-path", file.path));
    card.appendChild(createEl("p", "", file.purpose));
    card.appendChild(
      buildChipRow(
        file.agent_ids.map((id) => `A${id} ${agentMap.get(id)?.name || "Unknown Agent"}`),
        "mini-chip"
      )
    );
    fileGrid.appendChild(card);
  });
}

function renderApprovals(model, agentMap) {
  model.approval_gates.forEach((item) => {
    const card = createEl("article", "approval-card");
    card.appendChild(createEl("p", "approval-label", "Human Approval"));
    card.appendChild(createEl("div", "approval-title", item.title));
    card.appendChild(createEl("p", "", item.trigger));
    card.appendChild(
      buildChipRow(
        item.agent_ids.map((id) => `A${id} ${agentMap.get(id)?.name || "Unknown Agent"}`),
        "tag-chip alert"
      )
    );
    approvalGrid.appendChild(card);
  });
}

function renderHero(model) {
  companyName.textContent = model.company.name;
  companyTagline.textContent = model.company.tagline;
  northStar.textContent = model.company.north_star;

  model.company.principles.forEach((principle) => {
    principlesList.appendChild(createEl("li", "", principle));
  });
}

function render(model) {
  const agentMap = new Map(model.agents.map((agent) => [agent.id, agent]));
  renderHero(model);
  renderMetrics(model);
  renderCadence(model, agentMap);
  renderDepartments(model, agentMap);
  renderFiles(model, agentMap);
  renderApprovals(model, agentMap);
  app.hidden = false;
}

async function loadCompanyOs() {
  try {
    const response = await fetch("/api/company-os");
    if (!response.ok) {
      throw new Error(`Failed to load company OS data (${response.status}).`);
    }
    const model = await response.json();
    render(model);
  } catch (error) {
    errorBox.hidden = false;
    errorBox.textContent = error.message;
    companyName.textContent = "Boss Key Company OS";
    companyTagline.textContent = "The dashboard could not load the company operating model.";
  }
}

loadCompanyOs();
