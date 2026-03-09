const fs = require("fs");
const fsp = require("fs/promises");
const path = require("path");
const { expect, test } = require("@playwright/test");

const REPO_ROOT = path.resolve(__dirname, "..", "..", "..");
const DEMO_CONTRACTOR_NAME = "Chris Demo Facility Services";
const DEMO_PURSUIT_TITLE = "Chris Demo Airport Pursuit";
const CURSOR_START = { x: 180, y: 180 };
const CURSOR_SIZE = 28;

function isoDate(daysFromToday) {
  const value = new Date();
  value.setDate(value.getDate() + daysFromToday);
  return value.toISOString().slice(0, 10);
}

function isoDateTime(hoursFromNow = 0) {
  const value = new Date();
  value.setHours(value.getHours() + hoursFromNow);
  return value.toISOString();
}

function isoDateTimeLocal(hoursFromNow = 0) {
  return isoDateTime(hoursFromNow).slice(0, 16);
}

function loadNarrationScript(fileName) {
  const filePath = path.join(__dirname, fileName);
  return {
    filePath,
    content: JSON.parse(fs.readFileSync(filePath, "utf8")),
  };
}

function getNarrationStep(narrationScript, key) {
  const step = narrationScript.steps[key];
  if (!step) {
    throw new Error(`Missing narration step '${key}'.`);
  }
  return step;
}

async function expectOk(response, context) {
  const body = await response.text();
  expect(response.ok(), `${context}\n${body}`).toBeTruthy();
  return body;
}

function createNarrationRecorder(testInfo, { demoId, title, narrationScriptPath }) {
  const startedAtMs = Date.now();
  const steps = [];
  const relativeNarrationPath = path.relative(REPO_ROOT, narrationScriptPath).split(path.sep).join("/");

  return {
    async step(key, stepTitle, runStep) {
      const stepStartedAtMs = Date.now() - startedAtMs;
      await test.step(stepTitle, async () => {
        await runStep();
      });
      const stepFinishedAtMs = Date.now() - startedAtMs;
      steps.push({
        key,
        title: stepTitle,
        start_ms: stepStartedAtMs,
        end_ms: stepFinishedAtMs,
        duration_ms: stepFinishedAtMs - stepStartedAtMs,
      });
    },
    async writeManifest() {
      const manifestPath = testInfo.outputPath("narration-manifest.json");
      const manifest = {
        demo: demoId,
        title,
        generated_at: new Date().toISOString(),
        narration_script: relativeNarrationPath,
        video_file: "video.webm",
        total_duration_ms: Date.now() - startedAtMs,
        steps,
      };

      await fsp.writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
      return manifestPath;
    },
  };
}

async function ensureDemoCursor(page) {
  await page.evaluate(({ cursorSize }) => {
    const styleId = "bosskey-demo-cursor-style";
    const cursorId = "bosskey-demo-cursor";

    if (!document.getElementById(styleId)) {
      const style = document.createElement("style");
      style.id = styleId;
      style.textContent = `
        #${cursorId} {
          position: fixed;
          top: 0;
          left: 0;
          width: ${cursorSize}px;
          height: ${cursorSize}px;
          border-radius: 999px;
          pointer-events: none;
          z-index: 2147483647;
          transform: translate(-200px, -200px);
          background: rgba(255, 255, 255, 0.18);
          border: 1.5px solid rgba(255, 255, 255, 0.94);
          box-shadow: 0 10px 30px rgba(5, 14, 38, 0.28);
          backdrop-filter: blur(6px);
        }

        #${cursorId}::after {
          content: "";
          position: absolute;
          inset: 8px;
          border-radius: 999px;
          background: linear-gradient(135deg, #0f58f7, #37c4ff);
        }

        #${cursorId} .bosskey-demo-cursor-ring {
          position: absolute;
          inset: -8px;
          border: 2px solid rgba(55, 196, 255, 0.55);
          border-radius: 999px;
          opacity: 0;
          transform: scale(0.72);
        }

        #${cursorId}.is-clicking .bosskey-demo-cursor-ring {
          animation: bosskey-demo-cursor-pulse 360ms ease-out;
        }

        @keyframes bosskey-demo-cursor-pulse {
          0% { opacity: 0.82; transform: scale(0.72); }
          100% { opacity: 0; transform: scale(1.55); }
        }
      `;
      document.head.append(style);
    }

    if (!document.getElementById(cursorId)) {
      const cursor = document.createElement("div");
      cursor.id = cursorId;
      const ring = document.createElement("div");
      ring.className = "bosskey-demo-cursor-ring";
      cursor.append(ring);
      document.body.append(cursor);
    }
  }, { cursorSize: CURSOR_SIZE });
}

async function syncDemoCursor(page, point, click = false) {
  await page.evaluate(
    ({ nextPoint, cursorSize, clickPulse }) => {
      const cursor = document.getElementById("bosskey-demo-cursor");
      if (!cursor) {
        return;
      }

      const left = Math.round(nextPoint.x - cursorSize / 2);
      const top = Math.round(nextPoint.y - cursorSize / 2);
      cursor.style.transform = `translate(${left}px, ${top}px)`;

      if (clickPulse) {
        cursor.classList.remove("is-clicking");
        void cursor.offsetWidth;
        cursor.classList.add("is-clicking");
        window.clearTimeout(window.__bosskeyDemoCursorTimer);
        window.__bosskeyDemoCursorTimer = window.setTimeout(() => {
          cursor.classList.remove("is-clicking");
        }, 380);
      }
    },
    { nextPoint: point, cursorSize: CURSOR_SIZE, clickPulse: click },
  );
}

async function locatorCenter(locator) {
  await locator.scrollIntoViewIfNeeded();
  const box = await locator.boundingBox();
  expect(box, "Locator did not resolve to a visible bounding box.").toBeTruthy();
  return {
    x: box.x + box.width / 2,
    y: box.y + box.height / 2,
  };
}

function createDemoDriver(page) {
  let currentPoint = { ...CURSOR_START };

  return {
    async install() {
      await ensureDemoCursor(page);
      await syncDemoCursor(page, currentPoint);
    },
    async pause(ms) {
      await page.waitForTimeout(ms);
    },
    async setContent(html) {
      await page.setContent(html, { waitUntil: "load" });
      await this.install();
    },
    async goto(url) {
      await page.goto(url, { waitUntil: "networkidle" });
      await this.install();
    },
    async reload() {
      await page.reload({ waitUntil: "networkidle" });
      await this.install();
    },
    async moveToPoint(targetPoint, options = {}) {
      const steps = options.steps ?? 24;
      const durationMs = options.durationMs ?? 360;
      const frameDelay = Math.max(10, Math.round(durationMs / steps));

      for (let index = 1; index <= steps; index += 1) {
        const progress = index / steps;
        const point = {
          x: currentPoint.x + (targetPoint.x - currentPoint.x) * progress,
          y: currentPoint.y + (targetPoint.y - currentPoint.y) * progress,
        };
        await page.mouse.move(point.x, point.y);
        await syncDemoCursor(page, point);
        await page.waitForTimeout(frameDelay);
      }

      currentPoint = targetPoint;
    },
    async moveToLocator(locator, options = {}) {
      const point = await locatorCenter(locator);
      await this.moveToPoint(point, options);
      return point;
    },
    async hover(locator, options = {}) {
      await this.moveToLocator(locator, options);
      await page.waitForTimeout(options.afterMs ?? 120);
    },
    async click(locator, options = {}) {
      const point = await this.moveToLocator(locator, options);
      await page.waitForTimeout(options.beforeMs ?? 80);
      await syncDemoCursor(page, point, true);
      await locator.click();
      await page.waitForTimeout(options.afterMs ?? 140);
    },
    async typeInto(locator, text, options = {}) {
      await this.click(locator, options);
      if (options.selectAll !== false) {
        await page.keyboard.press("Control+A");
        await page.waitForTimeout(50);
      }
      await page.keyboard.type(text, { delay: options.delay ?? 35 });
      await page.waitForTimeout(options.afterMs ?? 120);
    },
    async select(locator, value, options = {}) {
      await this.click(locator, options);
      await locator.selectOption(value);
      await page.waitForTimeout(options.afterMs ?? 140);
    },
  };
}

function buildPursuitPayload(contract, overrides = {}) {
  return {
    title: overrides.title ?? DEMO_PURSUIT_TITLE,
    primary_facility_id: overrides.primary_facility_id ?? contract.facility_ids?.[0] ?? null,
    pursuit_stage: overrides.pursuit_stage ?? "PRE_RFP_CAPTURE",
    confidence_level: overrides.confidence_level ?? "HIGH",
    expected_rfp_date: overrides.expected_rfp_date ?? isoDate(45),
    provenance_summary: overrides.provenance_summary ?? "Created from the Boss Key filmed demo workflow.",
    strategic_fit: overrides.strategic_fit ?? 4,
    incumbent_vulnerability: overrides.incumbent_vulnerability ?? 3,
    rebid_probability: overrides.rebid_probability ?? 4,
    relationship_access: overrides.relationship_access ?? 4,
    contractor_fit: overrides.contractor_fit ?? 5,
    operational_complexity: overrides.operational_complexity ?? 3,
    margin_potential: overrides.margin_potential ?? 4,
    pre_rfp_influence: overrides.pre_rfp_influence ?? 4,
    timeline_urgency: overrides.timeline_urgency ?? 3,
    actor: overrides.actor ?? "operator",
  };
}

async function createContractPursuit(request, contract, overrides = {}) {
  const response = await request.post(`/api/contracts/${contract.id}/pursuits`, {
    data: buildPursuitPayload(contract, overrides),
  });
  await expectOk(response, "Creating contract pursuit failed.");
  return response.json();
}

async function createContractorPursuit(request, contractorId, contract, overrides = {}) {
  const response = await request.post(`/api/contractors/${contractorId}/pursuits`, {
    data: {
      contract_id: contract.id,
      ...buildPursuitPayload(contract, overrides),
    },
  });
  await expectOk(response, "Creating contractor pursuit handoff failed.");
  return response.json();
}

async function saveCommercial(request, opportunityId, overrides = {}) {
  const response = await request.post(`/api/opportunities/${opportunityId}/commercials`, {
    data: {
      retainer_amount: overrides.retainer_amount ?? 6000,
      contractor_id: overrides.contractor_id,
      success_fee_type: overrides.success_fee_type ?? "FIXED",
      success_fee_value: overrides.success_fee_value ?? 12000,
      projected_payout_date: overrides.projected_payout_date ?? isoDate(120),
      projected_payout_amount: overrides.projected_payout_amount,
      realized_revenue: overrides.realized_revenue,
      notes: overrides.notes ?? "Demo commercial model for a managed live-pursuit engagement.",
    },
  });
  await expectOk(response, "Saving commercial data failed.");
  return response.json();
}

async function applyPursuitDefaults(page, data) {
  await page.evaluate((payload) => {
    const dispatch = (element) => {
      element.dispatchEvent(new Event("input", { bubbles: true }));
      element.dispatchEvent(new Event("change", { bubbles: true }));
    };
    const setValue = (name, value) => {
      const element = document.querySelector(`[name="${name}"]`);
      if (!element) {
        throw new Error(`Missing pursuit form field '${name}'.`);
      }
      element.value = String(value);
      dispatch(element);
    };

    setValue("primary_facility_id", payload.facilityId);
    setValue("pursuit_stage", payload.pursuitStage ?? "PRE_RFP_CAPTURE");
    setValue("confidence_level", payload.confidenceLevel ?? "HIGH");
    setValue("expected_rfp_date", payload.expectedRfpDate);
    setValue("strategic_fit", payload.strategicFit ?? "4");
    setValue("incumbent_vulnerability", payload.incumbentVulnerability ?? "3");
    setValue("rebid_probability", payload.rebidProbability ?? "4");
    setValue("relationship_access", payload.relationshipAccess ?? "4");
    setValue("contractor_fit", payload.contractorFit ?? "5");
    setValue("operational_complexity", payload.operationalComplexity ?? "3");
    setValue("margin_potential", payload.marginPotential ?? "4");
    setValue("pre_rfp_influence", payload.preRfpInfluence ?? "4");
    setValue("timeline_urgency", payload.timelineUrgency ?? "3");
    setValue("provenance_summary", payload.provenanceSummary);
  }, data);
}

async function seedChrisDemo(request, overrides = {}) {
  const seed = await request.post("/api/dashboard/seed-demo");
  await expectOk(seed, "Seeding demo data failed.");

  const contractsResponse = await request.get("/api/contracts");
  await expectOk(contractsResponse, "Fetching contracts failed.");
  const contracts = await contractsResponse.json();
  const contract = contracts.find((item) => Array.isArray(item.facility_ids) && item.facility_ids.length > 0);
  expect(contract, "No contract with a facility was available for the demo.").toBeTruthy();

  const contractorResponse = await request.post("/api/contractors", {
    data: {
      name: overrides.contractorName ?? DEMO_CONTRACTOR_NAME,
      service_geographies: "NJ PA DE",
      headquarters_city: "Cherry Hill",
      headquarters_state: "NJ",
      vertical_experience: "airport municipal operations",
      labor_profile: "W2 self-perform",
      union_profile: "mixed",
      diversity_certs: "MWBE",
      airport_experience: true,
      healthcare_experience: false,
      education_experience: false,
      municipal_experience: true,
      scale_band: "REGIONAL",
      relationship_strength: 4,
      prospect_stage: "ENGAGED",
      next_follow_up_date: isoDate(overrides.followUpDays ?? 5),
      relationship_notes: "Strong regional relationship and qualified interest in a pilot pursuit.",
      strategic_fit_notes: "Best fit for airport day porter and terminal presentation work.",
      ...(overrides.contractorData ?? {}),
    },
  });
  await expectOk(contractorResponse, "Creating demo contractor failed.");
  const contractor = await contractorResponse.json();

  if (overrides.seedTouchpoint === false) {
    return { contract, contractor };
  }

  const touchpointResponse = await request.post(`/api/contractors/${contractor.id}/touchpoints`, {
    data: {
      contact_name: "Chris Demo Sponsor",
      touchpoint_type: "MEETING",
      touchpoint_at: isoDateTime(-2),
      summary: "Reviewed the pilot workflow and agreed to evaluate one live pursuit.",
      next_step: "Create pursuit handoff and confirm advised-contractor positioning.",
      next_follow_up_date: isoDate(3),
      ...(overrides.touchpointData ?? {}),
    },
  });
  await expectOk(touchpointResponse, "Creating demo touchpoint failed.");

  return { contract, contractor };
}

async function seedWorkbenchSupportRecords(request, opportunityId, contract, contractor) {
  const contractorContact = await request.post(`/api/opportunities/${opportunityId}/contacts`, {
    data: {
      contractor_id: contractor.id,
      full_name: "Riley Partner",
      role_title: "Regional Growth Lead",
      email: "riley.partner@example.com",
      contact_side: "CONTRACTOR",
      source_type: "DIRECT_CONVERSATION",
      confidence_level: "HIGH",
      notes: "Confirmed pursuit support and pilot availability.",
    },
  });
  await expectOk(contractorContact, "Creating the seeded contractor contact failed.");

  const noteResponse = await request.post(`/api/opportunities/${opportunityId}/intelligence`, {
    data: {
      title: "Evaluator emphasis",
      note_type: "POSITIONING",
      note_text: "The buyer is likely to prioritize visible daytime cleanliness and transition confidence.",
      source_class: "INFERRED",
      provenance: "Derived from public board commentary, current contract performance noise, and facility conditions.",
      confidence_level: "MEDIUM",
    },
  });
  await expectOk(noteResponse, "Creating the seeded intelligence note failed.");
  const note = await noteResponse.json();

  const evidenceResponse = await request.post(`/api/opportunities/${opportunityId}/evidence`, {
    data: {
      intelligence_note_id: note.id,
      contract_id: contract.id,
      source_class: "PUBLIC",
      provenance: "Public board packet and contract radar review completed for the demo.",
      source_url: "https://example.org/airport-board-packet",
      summary: "Board packet confirms transition timing sensitivity and terminal presentation concerns.",
      confidence_level: "HIGH",
    },
  });
  await expectOk(evidenceResponse, "Creating the seeded evidence record failed.");

  const actionResponse = await request.post(`/api/opportunities/${opportunityId}/capture-actions`, {
    data: {
      title: "Confirm next live-pursuit working session",
      action_type: "FOLLOW_UP",
      status: "OPEN",
      owner: "Tim",
      due_date: isoDate(7),
      notes: "Carry the pilot pursuit into the next capture review with Chris.",
    },
  });
  await expectOk(actionResponse, "Creating the seeded capture action failed.");
}

async function prefillBuyerContact(page, overrides = {}) {
  await page.evaluate((payload) => {
    const setValue = (selector, value) => {
      const element = document.querySelector(selector);
      if (!element) {
        throw new Error(`Missing workbench field '${selector}'.`);
      }
      element.value = value;
      element.dispatchEvent(new Event("input", { bubbles: true }));
      element.dispatchEvent(new Event("change", { bubbles: true }));
    };

    setValue('form[action$="/contacts"] input[name="role_title"]', payload.roleTitle);
    setValue('form[action$="/contacts"] input[name="email"]', payload.email);
    setValue('form[action$="/contacts"] select[name="contact_side"]', payload.contactSide);
    setValue('form[action$="/contacts"] select[name="source_type"]', payload.sourceType);
    setValue('form[action$="/contacts"] select[name="confidence_level"]', payload.confidenceLevel);
    setValue('form[action$="/contacts"] textarea[name="notes"]', payload.notes);
  }, {
    roleTitle: overrides.roleTitle ?? "Procurement Director",
    email: overrides.email ?? "dana.procurement@example.com",
    contactSide: overrides.contactSide ?? "BUYER",
    sourceType: overrides.sourceType ?? "PUBLIC",
    confidenceLevel: overrides.confidenceLevel ?? "HIGH",
    notes: overrides.notes ?? "Primary buyer-side contact for the live pilot pursuit.",
  });
}

async function prefillCommercials(page, projectedPayoutDate, overrides = {}) {
  await page.evaluate((payload) => {
    const setValue = (selector, value) => {
      const element = document.querySelector(selector);
      if (!element) {
        throw new Error(`Missing commercial field '${selector}'.`);
      }
      element.value = value;
      element.dispatchEvent(new Event("input", { bubbles: true }));
      element.dispatchEvent(new Event("change", { bubbles: true }));
    };

    if (payload.contractorId) {
      setValue('form[action$="/commercials"] select[name="contractor_id"]', payload.contractorId);
    }
    setValue('form[action$="/commercials"] select[name="success_fee_type"]', payload.successFeeType);
    setValue('form[action$="/commercials"] input[name="success_fee_value"]', payload.successFeeValue);
    setValue('form[action$="/commercials"] input[name="projected_payout_date"]', payload.projectedPayoutDate);
    setValue('form[action$="/commercials"] textarea[name="notes"]', payload.notes);
  }, {
    contractorId: overrides.contractorId,
    successFeeType: overrides.successFeeType ?? "FIXED",
    successFeeValue: String(overrides.successFeeValue ?? 12000),
    projectedPayoutDate,
    notes: overrides.notes ?? "Demo commercial model for a managed live-pursuit engagement.",
  });
}

async function showIntroCard(demo, options) {
  const eyebrow = options.eyebrow ?? "Boss Key Pursuit OS";
  const title = Array.isArray(options.title) ? options.title.join("<br>") : options.title;
  const body = options.body ?? "";

  await demo.setContent(`
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <title>${eyebrow}</title>
        <style>
          :root {
            color-scheme: light;
            font-family: "Segoe UI", "Helvetica Neue", sans-serif;
          }
          body {
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            background:
              radial-gradient(circle at top left, rgba(55, 196, 255, 0.18), transparent 34%),
              linear-gradient(145deg, #071224 0%, #0c1d39 52%, #0f274d 100%);
            color: #f6f8fc;
            overflow: hidden;
          }
          .frame {
            width: min(1180px, calc(100vw - 160px));
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 28px;
            padding: 48px 56px;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.03));
            box-shadow: 0 24px 80px rgba(0, 0, 0, 0.28);
          }
          .eyebrow {
            letter-spacing: 0.22em;
            text-transform: uppercase;
            font-size: 14px;
            color: rgba(255, 255, 255, 0.72);
            margin-bottom: 20px;
          }
          h1 {
            margin: 0 0 18px;
            font-size: clamp(48px, 6vw, 80px);
            line-height: 0.95;
            letter-spacing: -0.04em;
          }
          p {
            margin: 0;
            max-width: 760px;
            font-size: 22px;
            line-height: 1.45;
            color: rgba(255, 255, 255, 0.82);
          }
          .accent {
            margin-top: 28px;
            width: 132px;
            height: 5px;
            border-radius: 999px;
            background: linear-gradient(90deg, #37c4ff, #0f58f7);
          }
        </style>
      </head>
      <body>
        <section class="frame">
          <div class="eyebrow">${eyebrow}</div>
          <h1>${title}</h1>
          <p>${body}</p>
          <div class="accent"></div>
        </section>
      </body>
    </html>
  `);
  await demo.pause(options.pauseMs ?? 1000);
}

module.exports = {
  DEMO_CONTRACTOR_NAME,
  DEMO_PURSUIT_TITLE,
  applyPursuitDefaults,
  buildPursuitPayload,
  createContractPursuit,
  createContractorPursuit,
  createDemoDriver,
  createNarrationRecorder,
  getNarrationStep,
  isoDate,
  isoDateTime,
  isoDateTimeLocal,
  loadNarrationScript,
  prefillBuyerContact,
  prefillCommercials,
  saveCommercial,
  seedChrisDemo,
  seedWorkbenchSupportRecords,
  showIntroCard,
};
