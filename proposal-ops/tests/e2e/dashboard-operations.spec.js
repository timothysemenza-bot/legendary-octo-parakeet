const { test, expect } = require("@playwright/test");
const {
  createContractPursuit,
  createContractorPursuit,
  createDemoDriver,
  createNarrationRecorder,
  getNarrationStep,
  isoDate,
  loadNarrationScript,
  saveCommercial,
  seedChrisDemo,
  seedWorkbenchSupportRecords,
  showIntroCard,
} = require("./bosskey-demo-film-kit");

const { content: narrationScript, filePath: narrationScriptPath } = loadNarrationScript("dashboard-operations.narration.json");

test("records the dashboard operations knowledge-base video", async ({ page, request }, testInfo) => {
  test.setTimeout(300_000);

  const demo = createDemoDriver(page);
  const { contract, contractor } = await seedChrisDemo(request, {
    contractorName: "Dashboard Operations Contractor",
  });

  const readyOpportunity = await createContractorPursuit(request, contractor.id, contract, {
    title: "Dashboard Ready Pursuit",
    provenance_summary: "Created to demonstrate a pilot-ready pursuit on the dashboard.",
  });
  await seedWorkbenchSupportRecords(request, readyOpportunity.id, contract, contractor);
  const buyerContactResponse = await request.post(`/api/opportunities/${readyOpportunity.id}/contacts`, {
    data: {
      organization_id: readyOpportunity.buying_organization_id,
      full_name: "Dana Procurement",
      role_title: "Procurement Director",
      email: "dana.procurement@example.com",
      contact_side: "BUYER",
      source_type: "PUBLIC",
      confidence_level: "HIGH",
      notes: "Buyer-side contact added to make the pursuit pilot-ready for dashboard review.",
    },
  });
  expect(buyerContactResponse.ok()).toBeTruthy();
  await saveCommercial(request, readyOpportunity.id, {
    contractor_id: contractor.id,
    retainer_amount: 6500,
    success_fee_value: 15000,
  });

  const gapOpportunity = await createContractPursuit(request, contract, {
    title: "Dashboard Gap Pursuit",
    confidence_level: "MEDIUM",
    provenance_summary: "Created to demonstrate a pursuit that still needs work.",
    contractor_fit: 3,
    relationship_access: 2,
    pre_rfp_influence: 2,
  });

  const overdueContractorResponse = await request.post("/api/contractors", {
    data: {
      name: "Overdue Follow-Up Contractor",
      service_geographies: "NJ",
      headquarters_city: "Newark",
      headquarters_state: "NJ",
      vertical_experience: "transportation terminals",
      labor_profile: "W2 self-perform",
      union_profile: "mixed",
      scale_band: "REGIONAL",
      relationship_strength: 3,
      prospect_stage: "OUTREACH",
      next_follow_up_date: isoDate(-3),
      relationship_notes: "Needs a same-week call back from the operator.",
      strategic_fit_notes: "Useful for airport overflow staffing.",
    },
  });
  expect(overdueContractorResponse.ok()).toBeTruthy();
  const overdueContractor = await overdueContractorResponse.json();
  const overdueTouchpointResponse = await request.post(`/api/contractors/${overdueContractor.id}/touchpoints`, {
    data: {
      contact_name: "Operations Sponsor",
      touchpoint_type: "FOLLOW_UP",
      touchpoint_at: new Date().toISOString(),
      summary: "Buyer requested a same-week callback to review next steps.",
      next_step: "Needs a same-week call back from the operator.",
      next_follow_up_date: isoDate(-2),
    },
  });
  expect(overdueTouchpointResponse.ok()).toBeTruthy();

  const narration = createNarrationRecorder(testInfo, {
    demoId: narrationScript.output_basename ?? narrationScript.demo,
    title: narrationScript.title ?? "Boss Key Dashboard Operations",
    narrationScriptPath,
  });

  await showIntroCard(demo, {
    title: ["Dashboard Operations", "Knowledge Base"],
    body: "How to use the dashboard as the weekly operating page for pipeline triage, contractor follow-up, and live-pursuit readiness.",
  });

  try {
    await narration.step("portfolio_overview", "show the operating overview", async () => {
      await demo.goto("/dashboard");
      await expect(page.getByRole("heading", { name: "Janitorial Capture Dashboard" })).toBeVisible();

      await demo.hover(page.getByText("Weighted Pipeline").first(), { durationMs: 320 });
      await demo.hover(page.getByRole("heading", { name: "Upcoming Rebids" }), { durationMs: 320 });
      await demo.hover(page.getByRole("heading", { name: "Hottest Pursuits" }), { durationMs: 320 });

      await page.screenshot({ path: testInfo.outputPath("01-portfolio-overview.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "portfolio_overview").hold_ms);
    });

    await narration.step("followup_triage", "review overdue and upcoming follow-ups", async () => {
      await expect(page.getByRole("heading", { name: "Overdue Contractor Follow-Ups" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Upcoming Contractor Follow-Ups" })).toBeVisible();

      await demo.hover(page.getByRole("link", { name: "Overdue Follow-Up Contractor" }), { durationMs: 340 });
      await demo.hover(page.getByRole("link", { name: "Dashboard Operations Contractor" }), { durationMs: 320 });
      await demo.hover(page.getByText("Needs a same-week call back from the operator.").first(), {
        durationMs: 320,
      });

      await page.screenshot({ path: testInfo.outputPath("02-followup-triage.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "followup_triage").hold_ms);
    });

    await narration.step("readiness_triage", "review ready versus gap pursuits", async () => {
      await expect(page.getByText("Live Pursuit Readiness")).toBeVisible();
      const readyRow = page.locator("tr").filter({ hasText: "Dashboard Ready Pursuit" }).filter({ hasText: "Ready (6/6)" });
      const gapRow = page.locator("tr").filter({ hasText: "Dashboard Gap Pursuit" }).filter({ hasText: "Needs Work" });
      await expect(readyRow.getByRole("link", { name: "Dashboard Ready Pursuit", exact: true })).toBeVisible();
      await expect(gapRow.getByRole("link", { name: "Dashboard Gap Pursuit", exact: true })).toBeVisible();

      await demo.hover(readyRow.getByRole("link", { name: "Dashboard Ready Pursuit", exact: true }), { durationMs: 340 });
      await demo.hover(readyRow.getByRole("cell", { name: "Ready (6/6)" }), { durationMs: 320 });
      await demo.hover(gapRow.getByRole("link", { name: "Dashboard Gap Pursuit", exact: true }), { durationMs: 340 });
      await demo.hover(gapRow.getByRole("cell", { name: /Needs Work/ }), { durationMs: 320 });

      await page.screenshot({ path: testInfo.outputPath("03-readiness-triage.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "readiness_triage").hold_ms);
    });

    await narration.step("gap_drilldown", "drill into a not-ready pursuit", async () => {
      await demo.click(page.getByRole("link", { name: "Dashboard Gap Pursuit", exact: true }).first(), { durationMs: 340 });
      await expect(page).toHaveURL(new RegExp(`/opportunities/${gapOpportunity.id}$`));
      await demo.goto(`/opportunities/${gapOpportunity.id}/capture-workbench`);
      await expect(page).toHaveURL(new RegExp(`/opportunities/${gapOpportunity.id}/capture-workbench$`));
      await expect(page.getByRole("heading", { name: "Capture Workbench: Dashboard Gap Pursuit" })).toBeVisible();

      await demo.hover(page.getByText("No advised contractor linked yet."), { durationMs: 320 });
      await demo.hover(page.getByText("No match snapshots yet."), { durationMs: 320 });

      await page.screenshot({ path: testInfo.outputPath("04-gap-drilldown.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "gap_drilldown").hold_ms);
    });

    await narration.step("operating_rhythm", "return to the dashboard and close on operating rhythm", async () => {
      await demo.goto("/dashboard");
      await expect(page.getByText("Active Pursuit Counts")).toBeVisible();

      await demo.hover(page.getByText("Active Pursuit Counts"), { durationMs: 300 });
      await demo.hover(page.getByRole("heading", { name: "Live Pursuit Readiness" }), { durationMs: 320 });
      await demo.hover(page.getByRole("heading", { name: "Upcoming Contractor Follow-Ups" }), {
        durationMs: 320,
        afterMs: 140,
      });

      await page.screenshot({ path: testInfo.outputPath("05-operating-rhythm.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "operating_rhythm").hold_ms);
    });
  } finally {
    await narration.writeManifest();
  }
});
