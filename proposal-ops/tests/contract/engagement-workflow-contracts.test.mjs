import test from "node:test";
import assert from "node:assert/strict";
import guards from "../../services/workflow-orchestrator/src/engagement-workflow-guards.js";

const {
  STAGE_SEQUENCE,
  canProgressToStage,
  evaluateEngagementTransition,
  isDuplicateSignal,
  requiredGatesForStage
} = guards;

test("engagement workflow has the requested stage order", () => {
  const expectedStages = [
    "SIGNAL_CAPTURE",
    "ENGAGEMENT_TRIAGE",
    "TIMELINE_SEED",
    "ACTION_SEED",
    "APPROVAL_WAIT",
    "FOUNDER_BRIEF",
    "FOLLOW_THROUGH",
    "KNOWLEDGE_PROMOTION",
    "CLOSED"
  ];

  assert.deepEqual(STAGE_SEQUENCE, expectedStages);
});

test("stage progression uses linear advancement on gate approval", () => {
  const signalGates = requiredGatesForStage("APPROVAL_WAIT");
  assert.equal(signalGates.length, 1);
  assert.equal(signalGates[0], "GATE_APPROVAL_DECISION");

  const transition = evaluateEngagementTransition("APPROVAL_WAIT", "APPROVED");
  assert.equal(transition.next_stage, "FOUNDER_BRIEF");
  assert.equal(transition.status, "IN_PROGRESS");
});

test("approval wait accepts only approved gate decisions", () => {
  assert.equal(canProgressToStage("APPROVAL_WAIT", { GATE_APPROVAL_DECISION: "APPROVED" }), true);
  assert.equal(canProgressToStage("APPROVAL_WAIT", { GATE_APPROVAL_DECISION: "REWORK_REQUIRED" }), false);
  assert.equal(canProgressToStage("APPROVAL_WAIT", {}), false);
});

test("rework and rejection in approval wait return controlled reopen behavior", () => {
  const rework = evaluateEngagementTransition("APPROVAL_WAIT", "REWORK_REQUIRED");
  assert.equal(rework.next_stage, "APPROVAL_WAIT");
  assert.equal(rework.status, "WAITING_APPROVAL");

  const rejected = evaluateEngagementTransition("APPROVAL_WAIT", "REJECTED");
  assert.equal(rejected.next_stage, "ENGAGEMENT_TRIAGE");
  assert.equal(rejected.status, "IN_PROGRESS");
});

test("duplicate gate signals can be ignored for idempotency", () => {
  const processedSignalIds = ["signal-123", "signal-456"];
  const latestSignal = {
    signal_id: "signal-123"
  };
  const freshSignal = {
    signal_id: "signal-789"
  };

  assert.equal(isDuplicateSignal(processedSignalIds, latestSignal), true);
  assert.equal(isDuplicateSignal(processedSignalIds, freshSignal), false);
});
