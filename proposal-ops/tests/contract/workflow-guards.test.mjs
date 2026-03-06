import test from "node:test";
import assert from "node:assert/strict";
import guards from "../../services/workflow-orchestrator/src/workflow-guards.js";

const { requiredGatesForStage, canProgressToStage } = guards;

test("Review stage requires D and E gates", () => {
  const gates = requiredGatesForStage("REVIEW");
  assert.deepEqual(gates, ["GATE_D", "GATE_E"]);
});

test("Cannot enter drafting without Gate C approval", () => {
  assert.equal(canProgressToStage("DRAFTING", { GATE_C: "REJECTED" }), false);
  assert.equal(canProgressToStage("DRAFTING", { GATE_C: "APPROVED" }), true);
});

test("Cannot enter submission without D and E approvals", () => {
  assert.equal(canProgressToStage("SUBMISSION", { GATE_D: "APPROVED", GATE_E: "REJECTED" }), false);
  assert.equal(canProgressToStage("SUBMISSION", { GATE_D: "APPROVED", GATE_E: "APPROVED" }), true);
});

test("Cannot close archive path before Gate F approval", () => {
  assert.equal(canProgressToStage("ARCHIVE", { GATE_F: "REWORK_REQUIRED" }), false);
  assert.equal(canProgressToStage("ARCHIVE", { GATE_F: "APPROVED" }), true);
});
