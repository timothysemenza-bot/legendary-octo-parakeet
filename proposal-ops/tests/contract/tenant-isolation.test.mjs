import test from "node:test";
import assert from "node:assert/strict";
import policy from "../../packages/authz-policy/tenant-scope.js";

const { enforceTenantScope } = policy;

test("Tenant access allowed when client and workspace match", () => {
  const result = enforceTenantScope(
    { client_id: "cli_demo", workspace_id: "ws_a" },
    { client_id: "cli_demo", workspace_id: "ws_a", id: "opp_1" }
  );
  assert.equal(result.allowed, true);
});

test("Tenant access denied on client mismatch", () => {
  const result = enforceTenantScope(
    { client_id: "cli_demo", workspace_id: "ws_a" },
    { client_id: "cli_other", workspace_id: "ws_a", id: "opp_2" }
  );
  assert.equal(result.allowed, false);
  assert.match(result.reason, /Client scope mismatch/);
});

test("Tenant access denied on workspace mismatch", () => {
  const result = enforceTenantScope(
    { client_id: "cli_demo", workspace_id: "ws_a" },
    { client_id: "cli_demo", workspace_id: "ws_b", id: "opp_3" }
  );
  assert.equal(result.allowed, false);
  assert.match(result.reason, /Workspace scope mismatch/);
});
