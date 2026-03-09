const { test, expect } = require("@playwright/test");
const {
  createContractorPursuit,
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

const { content: narrationScript, filePath: narrationScriptPath } = loadNarrationScript("capture-workbench.narration.json");

const CONTRACTOR_NAME = "Workbench Knowledge Base Contractor";
const PURSUIT_TITLE = "Workbench Knowledge Base Pursuit";

test("records the capture workbench knowledge-base video", async ({ page, request }, testInfo) => {
  test.setTimeout(300_000);

  const demo = createDemoDriver(page);
  const { contract, contractor } = await seedChrisDemo(request, { contractorName: CONTRACTOR_NAME });
  const opportunity = await createContractorPursuit(request, contractor.id, contract, {
    title: PURSUIT_TITLE,
    provenance_summary: "Created for the capture workbench knowledge-base walkthrough.",
  });
  await seedWorkbenchSupportRecords(request, opportunity.id, contract, contractor);
  const narration = createNarrationRecorder(testInfo, {
    demoId: narrationScript.output_basename ?? narrationScript.demo,
    title: narrationScript.title ?? "Boss Key Capture Workbench",
    narrationScriptPath,
  });

  await showIntroCard(demo, {
    title: ["Capture Workbench", "Knowledge Base"],
    body: "How to use the workbench as the live operating file for one pursuit.",
  });

  try {
    await narration.step("workbench_arrival", "open the seeded workbench", async () => {
      await demo.goto(`/opportunities/${opportunity.id}/capture-workbench`);
      await expect(page.getByRole("heading", { name: `Capture Workbench: ${PURSUIT_TITLE}` })).toBeVisible();

      await demo.hover(page.getByText(contract.title).first(), { durationMs: 320 });
      await demo.hover(page.getByText("Provenance").first(), { durationMs: 280 });
      await demo.hover(page.getByText("Confidence").first(), { durationMs: 280 });

      await page.screenshot({ path: testInfo.outputPath("01-workbench-arrival.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "workbench_arrival").hold_ms);
    });

    await narration.step("contractor_context", "show contractor context inside the workbench", async () => {
      await expect(page.getByText("Advised Contractor Context")).toBeVisible();
      await expect(page.getByRole("link", { name: CONTRACTOR_NAME })).toBeVisible();

      await demo.hover(page.getByRole("link", { name: CONTRACTOR_NAME }), { durationMs: 340 });
      await demo.hover(page.getByText("Relationship Notes:").first(), { durationMs: 300 });
      await demo.hover(page.getByText("Reviewed the pilot workflow and agreed to evaluate one live pursuit."), {
        durationMs: 320,
      });

      await page.screenshot({ path: testInfo.outputPath("02-contractor-context.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "contractor_context").hold_ms);
    });

    await narration.step("contacts", "show visible contact capture", async () => {
      const contactsForm = page.locator(`form[action="/opportunities/${opportunity.id}/capture-workbench/contacts"]`);
      await demo.typeInto(contactsForm.locator('input[name="full_name"]'), "Dana Procurement", {
        delay: 34,
        durationMs: 260,
      });
      await prefillBuyerContact(page, {
        notes: "Primary buyer contact for the capture workbench knowledge-base walkthrough.",
      });
      await demo.click(contactsForm.getByRole("button", { name: "Add Contact" }), { durationMs: 240 });

      await expect(page.getByText("Dana Procurement")).toBeVisible();
      await demo.hover(page.getByText("Dana Procurement"), { durationMs: 320 });
      await demo.hover(page.getByText("Riley Partner"), { durationMs: 300 });

      await page.screenshot({ path: testInfo.outputPath("03-contacts.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "contacts").hold_ms);
    });

    await narration.step("intelligence_evidence", "focus on intelligence and evidence sections", async () => {
      await demo.hover(page.getByText("Evaluator emphasis"), { durationMs: 320 });
      await demo.hover(
        page.getByText("The buyer is likely to prioritize visible daytime cleanliness and transition confidence."),
        { durationMs: 320 },
      );
      await demo.hover(
        page.getByText("Board packet confirms transition timing sensitivity and terminal presentation concerns."),
        { durationMs: 320 },
      );

      await page.screenshot({ path: testInfo.outputPath("04-intelligence-evidence.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "intelligence_evidence").hold_ms);
    });

    await narration.step("actions_and_commercials", "capture actions and save commercials", async () => {
      const actionsForm = page.locator(`form[action="/opportunities/${opportunity.id}/capture-workbench/actions"]`);
      await demo.typeInto(actionsForm.locator('input[name="title"]'), "Review internal readiness with Chris", {
        delay: 30,
        durationMs: 240,
      });
      await demo.select(actionsForm.locator('select[name="action_type"]'), "FOLLOW_UP", { durationMs: 230 });
      await demo.select(actionsForm.locator('select[name="status"]'), "OPEN", { durationMs: 230 });
      const dueDateInput = actionsForm.locator('input[name="due_date"]');
      await demo.click(dueDateInput, { durationMs: 220 });
      await dueDateInput.evaluate((element, value) => {
        element.value = value;
        element.dispatchEvent(new Event("input", { bubbles: true }));
        element.dispatchEvent(new Event("change", { bubbles: true }));
      }, isoDate(9));
      await demo.click(actionsForm.getByRole("button", { name: "Add Capture Action" }), { durationMs: 240 });

      const commercialsForm = page.locator(`form[action="/opportunities/${opportunity.id}/capture-workbench/commercials"]`);
      await demo.typeInto(commercialsForm.locator('input[name="retainer_amount"]'), "6500", {
        delay: 34,
        durationMs: 240,
      });
      await prefillCommercials(page, isoDate(120), { contractorId: contractor.id, successFeeValue: 15000 });
      await demo.click(commercialsForm.getByRole("button", { name: "Save Commercials" }), { durationMs: 240 });

      await expect(page.getByText("Weighted Expected Value")).toBeVisible();
      await demo.hover(page.getByText("Review internal readiness with Chris").first(), { durationMs: 320 });
      await demo.hover(page.getByText("Weighted Expected Value"), { durationMs: 320 });

      await page.screenshot({ path: testInfo.outputPath("05-actions-commercials.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "actions_and_commercials").hold_ms);
    });

    await narration.step("filters", "show the review filters", async () => {
      const filterForm = page.locator(`form[action="/opportunities/${opportunity.id}/capture-workbench"][method="get"]`);
      await demo.select(filterForm.locator('select[name="contact_side"]'), "BUYER", { durationMs: 240 });
      await demo.select(filterForm.locator('select[name="note_type"]'), "POSITIONING", { durationMs: 240 });
      await demo.select(filterForm.locator('select[name="action_status"]'), "OPEN", { durationMs: 240 });
      await demo.click(filterForm.getByRole("button", { name: "Apply Filters" }), { durationMs: 260 });

      await expect(page.getByText("Dana Procurement")).toBeVisible();
      await demo.hover(page.getByText("Dana Procurement"), { durationMs: 300 });
      await demo.hover(page.getByText("Evaluator emphasis"), { durationMs: 300 });
      await demo.hover(page.getByText("Review internal readiness with Chris").first(), { durationMs: 300 });

      await page.screenshot({ path: testInfo.outputPath("06-filters.png"), fullPage: false });
      await demo.pause(getNarrationStep(narrationScript, "filters").hold_ms);
    });
  } finally {
    await narration.writeManifest();
  }
});
