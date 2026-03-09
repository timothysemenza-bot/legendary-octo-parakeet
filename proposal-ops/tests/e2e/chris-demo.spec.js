const { test, expect } = require("@playwright/test");
const {
  DEMO_CONTRACTOR_NAME,
  DEMO_PURSUIT_TITLE,
  applyPursuitDefaults,
  createDemoDriver,
  createNarrationRecorder,
  getNarrationStep,
  isoDate,
  loadNarrationScript,
  prefillBuyerContact,
  prefillCommercials,
  seedChrisDemo,
  seedWorkbenchSupportRecords,
  showIntroCard,
} = require("./bosskey-demo-film-kit");

const { content: narrationScript, filePath: narrationScriptPath } = loadNarrationScript("chris-demo.narration.json");

test("records the Chris demo walkthrough", async ({ page, request }, testInfo) => {
  test.setTimeout(300_000);

  const demo = createDemoDriver(page);
  let opportunityId = "";

  const { contract, contractor } = await seedChrisDemo(request);
  const contractorDetailPath = `/contractors/${contractor.id}`;
  const narration = createNarrationRecorder(testInfo, {
    demoId: narrationScript.output_basename ?? narrationScript.demo,
    title: narrationScript.title ?? "Boss Key Overview",
    narrationScriptPath,
  });

  await showIntroCard(demo, {
    title: ["From Relationship", "to Live Pursuit"],
    body: "A filmed walkthrough of the contractor handoff, capture workbench, and readiness flow.",
  });

  try {
    await narration.step("dashboard_start", "show the dashboard starting point", async () => {
      await demo.goto("/dashboard");
      await expect(page.getByRole("heading", { name: "Janitorial Capture Dashboard" })).toBeVisible();
      await expect(page.getByText("Live Pursuit Readiness")).toBeVisible();

      await demo.hover(page.getByText("Live Pursuit Readiness"), { durationMs: 420 });
      await demo.hover(page.getByRole("heading", { name: "Upcoming Contractor Follow-Ups" }), { durationMs: 340 });
      await demo.hover(page.getByRole("heading", { name: "Overdue Contractor Follow-Ups" }), {
        durationMs: 320,
        afterMs: 160,
      });

      await page.screenshot({ path: testInfo.outputPath("01-dashboard-start.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "dashboard_start").hold_ms);
    });

    await narration.step("contractor_detail", "open the contractor relationship detail view", async () => {
      await demo.goto("/contractors");
      const filterForm = page.locator('form[action="/contractors"][method="get"]');
      const stageSelect = filterForm.locator('select[name="prospect_stage"]');
      await demo.select(stageSelect, "ENGAGED", { durationMs: 320 });
      await demo.click(filterForm.getByRole("button", { name: "Apply Filters" }), { durationMs: 280 });

      const contractorLink = page.getByRole("link", { name: DEMO_CONTRACTOR_NAME });
      await expect(contractorLink).toBeVisible();
      await demo.click(contractorLink, { durationMs: 360 });

      await expect(page).toHaveURL(new RegExp(`${contractorDetailPath}$`));
      await expect(page.getByRole("heading", { name: DEMO_CONTRACTOR_NAME })).toBeVisible();
      await demo.hover(page.getByText("Reviewed the pilot workflow and agreed to evaluate one live pursuit."), {
        durationMs: 360,
      });

      await page.screenshot({ path: testInfo.outputPath("02-contractor-detail.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "contractor_detail").hold_ms);
    });

    await narration.step("pursuit_handoff", "handoff the contractor into a new pursuit", async () => {
      const handoffForm = page.locator(`form[action="${contractorDetailPath}/pursuits"]`);
      const contractSelect = handoffForm.locator('select[name="contract_id"]');
      const titleInput = handoffForm.locator('input[name="title"]');
      const createButton = handoffForm.getByRole("button", { name: "Create Pursuit Handoff" });

      await demo.select(contractSelect, contract.id, { durationMs: 340 });
      await demo.typeInto(titleInput, DEMO_PURSUIT_TITLE, { delay: 40, durationMs: 320 });
      await applyPursuitDefaults(page, {
        facilityId: contract.facility_ids[0],
        expectedRfpDate: isoDate(45),
        provenanceSummary: "Created from the contractor handoff workflow for the Chris demo walkthrough.",
      });
      await demo.hover(createButton, { durationMs: 300, afterMs: 100 });
      await demo.click(createButton, { durationMs: 240, afterMs: 180 });

      await expect(page).toHaveURL(/\/opportunities\/[^/]+\/capture-workbench$/);
      await expect(page.getByRole("heading", { name: `Capture Workbench: ${DEMO_PURSUIT_TITLE}` })).toBeVisible();

      const match = page.url().match(/\/opportunities\/([^/]+)\/capture-workbench$/);
      expect(match, "Could not parse the opportunity id from the capture-workbench URL.").toBeTruthy();
      opportunityId = match[1];

      await seedWorkbenchSupportRecords(request, opportunityId, contract, contractor);
      await demo.reload();
      await expect(page.getByText("Evaluator emphasis")).toBeVisible();

      await page.screenshot({ path: testInfo.outputPath("03-capture-workbench-arrival.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "pursuit_handoff").hold_ms);
    });

    await narration.step("capture_context", "show the advised contractor context inside the workbench", async () => {
      await expect(page.getByRole("link", { name: DEMO_CONTRACTOR_NAME })).toBeVisible();
      await demo.hover(page.getByRole("link", { name: DEMO_CONTRACTOR_NAME }), { durationMs: 360 });
      await demo.hover(page.getByText("Evaluator emphasis"), { durationMs: 320 });
      await demo.hover(
        page.getByText("Board packet confirms transition timing sensitivity and terminal presentation concerns."),
        { durationMs: 320 },
      );

      await page.screenshot({ path: testInfo.outputPath("04-capture-workbench-context.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "capture_context").hold_ms);
    });

    await narration.step("capture_completion", "complete the visible capture work on camera", async () => {
      const contactsForm = page.locator(`form[action="/opportunities/${opportunityId}/capture-workbench/contacts"]`);
      await demo.typeInto(contactsForm.locator('input[name="full_name"]'), "Dana Procurement", {
        delay: 34,
        durationMs: 260,
      });
      await prefillBuyerContact(page);
      await demo.click(contactsForm.getByRole("button", { name: "Add Contact" }), { durationMs: 260 });
      await expect(page.getByText("Dana Procurement")).toBeVisible();

      const commercialsForm = page.locator(`form[action="/opportunities/${opportunityId}/capture-workbench/commercials"]`);
      await demo.typeInto(commercialsForm.locator('input[name="retainer_amount"]'), "6000", {
        delay: 42,
        durationMs: 240,
      });
      await prefillCommercials(page, isoDate(120));
      await demo.click(commercialsForm.getByRole("button", { name: "Save Commercials" }), { durationMs: 260 });
      await expect(page.getByText("Weighted Expected Value")).toBeVisible();

      await demo.hover(page.getByText("Weighted Expected Value"), { durationMs: 320, afterMs: 140 });
      await page.screenshot({ path: testInfo.outputPath("05-capture-workbench-complete.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "capture_completion").hold_ms);
    });

    await narration.step("dashboard_ready", "return to the dashboard and verify readiness", async () => {
      await demo.goto("/dashboard");
      await expect(page.getByText("Live Pursuit Readiness")).toBeVisible();
      const readinessRow = page.locator("tr", {
        has: page.getByRole("link", { name: DEMO_PURSUIT_TITLE, exact: true }),
      }).filter({ hasText: "Ready (6/6)" });
      await expect(readinessRow.getByRole("link", { name: DEMO_PURSUIT_TITLE, exact: true })).toBeVisible();
      await expect(readinessRow.getByText("Ready (6/6)")).toBeVisible();

      await demo.hover(readinessRow.getByRole("link", { name: DEMO_PURSUIT_TITLE, exact: true }), { durationMs: 360 });
      await demo.hover(readinessRow.getByText("Ready (6/6)"), { durationMs: 300 });
      await demo.hover(page.getByText(DEMO_CONTRACTOR_NAME).first(), { durationMs: 320, afterMs: 160 });

      await page.screenshot({ path: testInfo.outputPath("06-dashboard-ready.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "dashboard_ready").hold_ms);
    });
  } finally {
    await narration.writeManifest();
  }
});
