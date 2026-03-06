import test from "node:test";
import assert from "node:assert/strict";
import workflow from "../../packages/workflow-definitions/state-machine.js";

const { evaluateGateTransition, canEnterDrafting, canAuthorizeSubmission } = workflow;

test("Gate approval advances stage", () => {
  const result = evaluateGateTransition("COMPLIANCE", "APPROVED");
  assert.equal(result.next_stage, "CONTENT_PLANNING");
  assert.equal(result.status, "IN_PROGRESS");
});

test("Gate rework stays in stage", () => {
  const result = evaluateGateTransition("REVIEW", "REWORK_REQUIRED");
  assert.equal(result.next_stage, "REVIEW");
  assert.equal(result.status, "IN_PROGRESS");
});

test("Gate rejection returns previous stage and blocks", () => {
  const result = evaluateGateTransition("COMPLIANCE", "REJECTED");
  assert.equal(result.next_stage, "STRATEGY");
  assert.equal(result.status, "BLOCKED");
});

test("Drafting blocked until Gate C approved", () => {
  assert.equal(canEnterDrafting(null), false);
  assert.equal(canEnterDrafting("REJECTED"), false);
  assert.equal(canEnterDrafting("APPROVED"), true);
});

test("Submission authorization blocked until Gate F approved", () => {
  assert.equal(canAuthorizeSubmission(null), false);
  assert.equal(canAuthorizeSubmission("REWORK_REQUIRED"), false);
  assert.equal(canAuthorizeSubmission("APPROVED"), true);
});
