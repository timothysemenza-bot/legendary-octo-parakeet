const { test, expect } = require("@playwright/test");
const {
  createDemoDriver,
  createNarrationRecorder,
  getNarrationStep,
  isoDate,
  isoDateTimeLocal,
  loadNarrationScript,
  seedChrisDemo,
  showIntroCard,
} = require("./bosskey-demo-film-kit");

const { content: narrationScript, filePath: narrationScriptPath } = loadNarrationScript("contractor-workflow.narration.json");

const CONTRACTOR_NAME = "Knowledge Base Contractor";
const PURSUIT_TITLE = "Knowledge Base Contractor Handoff";

test("records the contractor workflow knowledge-base video", async ({ page, request }, testInfo) => {
  test.setTimeout(300_000);

  const demo = createDemoDriver(page);
  const { contract, contractor } = await seedChrisDemo(request, {
    contractorName: CONTRACTOR_NAME,
    touchpointData: {
      summary: "Reviewed onboarding expectations and agreed to stage a first live pursuit.",
      next_step: "Log the next relationship step and push the contractor into a live pursuit.",
      next_follow_up_date: isoDate(2),
    },
  });
  const contractorDetailPath = `/contractors/${contractor.id}`;
  const narration = createNarrationRecorder(testInfo, {
    demoId: narrationScript.output_basename ?? narrationScript.demo,
    title: narrationScript.title ?? "Boss Key Contractor Workflow",
    narrationScriptPath,
  });

  await showIntroCard(demo, {
    title: ["Contractor Workflow", "Knowledge Base"],
    body: "How Boss Key tracks contractor relationships, touchpoints, and pursuit handoff from one operating record.",
  });

  try {
    await narration.step("dashboard_followups", "show the contractor follow-up queue", async () => {
      await demo.goto("/dashboard");
      await expect(page.getByRole("heading", { name: "Overdue Contractor Follow-Ups" })).toBeVisible();
      await expect(page.getByRole("heading", { name: "Upcoming Contractor Follow-Ups" })).toBeVisible();

      await demo.hover(page.getByRole("heading", { name: "Overdue Contractor Follow-Ups" }), { durationMs: 340 });
      await demo.hover(page.getByRole("heading", { name: "Upcoming Contractor Follow-Ups" }), { durationMs: 320 });
      await demo.hover(page.getByRole("link", { name: CONTRACTOR_NAME, exact: true }), { durationMs: 360 });

      await page.screenshot({ path: testInfo.outputPath("01-dashboard-followups.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "dashboard_followups").hold_ms);
    });

    await narration.step("contractor_list", "filter the contractor list", async () => {
      await demo.goto("/contractors");
      const filterForm = page.locator('form[action="/contractors"][method="get"]');
      await demo.select(filterForm.locator('select[name="prospect_stage"]'), "ENGAGED", { durationMs: 320 });
      await demo.click(filterForm.getByRole("button", { name: "Apply Filters" }), { durationMs: 260 });

      const contractorLink = page.getByRole("link", { name: CONTRACTOR_NAME, exact: true });
      await expect(contractorLink).toBeVisible();
      await demo.hover(contractorLink, { durationMs: 360 });
      const contractorRow = page.locator("tr", { has: contractorLink });
      await demo.hover(contractorRow.getByText("ENGAGED"), { durationMs: 280 });
      await demo.hover(contractorRow.getByText("NJ PA DE"), { durationMs: 280 });
      await demo.hover(contractorRow.getByText("4/5"), { durationMs: 280 });

      await page.screenshot({ path: testInfo.outputPath("02-contractor-list.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "contractor_list").hold_ms);
    });

    await narration.step("touchpoint_logging", "log a contractor touchpoint", async () => {
      await demo.click(page.getByRole("link", { name: CONTRACTOR_NAME, exact: true }), { durationMs: 360 });

      await expect(page).toHaveURL(new RegExp(`${contractorDetailPath}$`));
      await expect(page.getByRole("heading", { name: CONTRACTOR_NAME })).toBeVisible();

      const touchpointForm = page.locator(`form[action="/contractors/${contractor.id}/touchpoints"]`);
      await demo.typeInto(touchpointForm.locator('input[name="contact_name"]'), "Chris Partner", {
        delay: 34,
        durationMs: 260,
      });
      await demo.select(touchpointForm.locator('select[name="touchpoint_type"]'), "FOLLOW_UP", { durationMs: 260 });
      const touchpointAtInput = touchpointForm.locator('input[name="touchpoint_at"]');
      await demo.click(touchpointAtInput, { durationMs: 240 });
      await touchpointAtInput.evaluate((element, value) => {
        element.value = value;
        element.dispatchEvent(new Event("input", { bubbles: true }));
        element.dispatchEvent(new Event("change", { bubbles: true }));
      }, isoDateTimeLocal(-1));
      await demo.typeInto(
        touchpointForm.locator('textarea[name="summary"]'),
        "Confirmed the contractor is ready to support one live pilot pursuit and one follow-on opportunity review.",
        { delay: 18, durationMs: 260 },
      );
      await demo.typeInto(
        touchpointForm.locator('textarea[name="next_step"]'),
        "Create the pursuit handoff and send a same-week working-session hold.",
        { delay: 18, durationMs: 250 },
      );
      const nextFollowUpInput = touchpointForm.locator('input[name="next_follow_up_date"]');
      await demo.click(nextFollowUpInput, { durationMs: 220 });
      await nextFollowUpInput.evaluate((element, value) => {
        element.value = value;
        element.dispatchEvent(new Event("input", { bubbles: true }));
        element.dispatchEvent(new Event("change", { bubbles: true }));
      }, isoDate(4));
      await demo.click(touchpointForm.getByRole("button", { name: "Log Touchpoint" }), { durationMs: 250 });

      await expect(page.getByText("Confirmed the contractor is ready to support one live pilot pursuit")).toBeVisible();
      await demo.hover(page.getByText("Confirmed the contractor is ready to support one live pilot pursuit").first(), {
        durationMs: 320,
      });

      await page.screenshot({ path: testInfo.outputPath("03-touchpoint-log.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "touchpoint_logging").hold_ms);
    });

    await narration.step("pursuit_handoff", "create the pursuit handoff from contractor detail", async () => {
      const handoffForm = page.locator(`form[action="${contractorDetailPath}/pursuits"]`);
      await demo.select(handoffForm.locator('select[name="contract_id"]'), contract.id, { durationMs: 320 });
      await demo.typeInto(handoffForm.locator('input[name="title"]'), PURSUIT_TITLE, {
        delay: 38,
        durationMs: 300,
      });
      await demo.select(handoffForm.locator('select[name="primary_facility_id"]'), contract.facility_ids[0], {
        durationMs: 280,
      });
      await demo.select(handoffForm.locator('select[name="pursuit_stage"]'), "PRE_RFP_CAPTURE", { durationMs: 240 });
      await demo.select(handoffForm.locator('select[name="confidence_level"]'), "HIGH", { durationMs: 240 });
      await demo.typeInto(
        handoffForm.locator('textarea[name="provenance_summary"]'),
        "Promoted from the contractor workflow knowledge-base demo into active capture.",
        { delay: 18, durationMs: 260 },
      );
      await demo.click(handoffForm.getByRole("button", { name: "Create Pursuit Handoff" }), {
        durationMs: 260,
        afterMs: 180,
      });

      await expect(page).toHaveURL(/\/opportunities\/[^/]+\/capture-workbench$/);
      await expect(page.getByRole("heading", { name: `Capture Workbench: ${PURSUIT_TITLE}` })).toBeVisible();

      await demo.hover(page.getByText(CONTRACTOR_NAME).first(), { durationMs: 320 });
      await demo.hover(page.getByText("Advised Contractor Context"), { durationMs: 260 });

      await page.screenshot({ path: testInfo.outputPath("04-pursuit-handoff.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "pursuit_handoff").hold_ms);
    });

    await narration.step("linked_opportunities", "return to the contractor record and show linked opportunities", async () => {
      await demo.goto(contractorDetailPath);
      await expect(page.getByRole("heading", { name: CONTRACTOR_NAME })).toBeVisible();
      await expect(page.getByRole("link", { name: PURSUIT_TITLE, exact: true })).toBeVisible();

      await demo.hover(page.getByText("Linked Opportunities"), { durationMs: 300 });
      await demo.hover(page.getByRole("link", { name: PURSUIT_TITLE, exact: true }), { durationMs: 320 });
      await demo.hover(page.getByRole("link", { name: "Capture Workbench" }).first(), {
        durationMs: 300,
        afterMs: 140,
      });

      await page.screenshot({ path: testInfo.outputPath("05-linked-opportunities.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "linked_opportunities").hold_ms);
    });
  } finally {
    await narration.writeManifest();
  }
});
