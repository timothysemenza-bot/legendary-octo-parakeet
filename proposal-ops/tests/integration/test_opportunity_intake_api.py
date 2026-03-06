from fastapi.testclient import TestClient


def _payload() -> dict:
    return {
        "name": "Regional Operations Support",
        "client": "City of Springfield",
        "estimated_contract_value": 1200000,
        "lead_time_days": 50,
        "incumbent_status": False,
        "strategic_alignment": 5,
        "estimated_probability_win": 80,
        "actor": "tim"
    }


def test_intake_persists_records_and_audit(client: TestClient) -> None:
    response = client.post("/api/opportunities/intake", json=_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["id"]
    assert body["capture_plan_id"]
    assert body["qualification_score"] > 0

    detail = client.get(f"/api/opportunities/{body['id']}")
    assert detail.status_code == 200
    data = detail.json()
    assert data["capture_plan"] is not None
    assert "win_themes_draft" in data["capture_plan"]
    assert len(data["audit_events"]) >= 3


def test_invalid_payload_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/opportunities/intake",
        json={"name": "x", "client": "y", "estimated_contract_value": -1},
    )
    assert response.status_code == 422


def test_gate_decision_creates_audit_event(client: TestClient) -> None:
    intake = client.post("/api/opportunities/intake", json=_payload()).json()
    decision = client.post(
        f"/api/opportunities/{intake['id']}/gate-decisions",
        json={
            "gate_code": "BID_NO_BID",
            "decision": "APPROVED",
            "decider": "principal",
            "rationale": "Strategic fit and timing are strong."
        },
    )
    assert decision.status_code == 200
    detail = client.get(f"/api/opportunities/{intake['id']}").json()
    assert len(detail["gate_decisions"]) == 1
    actions = [e["action"] for e in detail["audit_events"]]
    assert "bid_decision_recorded" in actions


def test_list_and_detail_consistency(client: TestClient) -> None:
    first = client.post("/api/opportunities/intake", json=_payload()).json()
    second_payload = _payload() | {"name": "Cybersecurity Uplift RFP", "estimated_probability_win": 40}
    second = client.post("/api/opportunities/intake", json=second_payload).json()
    listing = client.get("/api/opportunities")
    assert listing.status_code == 200
    items = listing.json()
    ids = {item["id"] for item in items}
    assert first["id"] in ids
    assert second["id"] in ids


def test_stage_transition_blocks_drafting_before_gate_c_approval(client: TestClient) -> None:
    intake = client.post("/api/opportunities/intake", json=_payload()).json()
    response = client.post(
        f"/api/opportunities/{intake['id']}/stage-transition",
        json={"next_stage": "DRAFTING", "actor": "operator", "reason": "Trying to start drafting"},
    )
    assert response.status_code == 409
    assert "GATE_C must be APPROVED" in str(response.json())


def test_stage_transition_blocks_unauthorized_actor_role(client: TestClient) -> None:
    intake = client.post("/api/opportunities/intake", json=_payload()).json()
    response = client.post(
        f"/api/opportunities/{intake['id']}/stage-transition",
        json={
            "next_stage": "QUALIFICATION",
            "actor": "analyst-1",
            "actor_role": "section_owner",
            "reason": "Manual move",
        },
    )
    assert response.status_code == 409
    assert "not authorized" in str(response.json()).lower()


def test_gate_c_approval_blocked_when_matrix_not_ready(client: TestClient) -> None:
    intake = client.post("/api/opportunities/intake", json=_payload()).json()
    gate_c = client.post(
        f"/api/opportunities/{intake['id']}/gate-decisions",
        json={
            "gate_code": "GATE_C",
            "decision": "APPROVED",
            "decider": "compliance-lead",
            "rationale": "Looks good.",
        },
    )
    assert gate_c.status_code == 409


def test_non_active_gate_decision_is_blocked_and_audited(client: TestClient) -> None:
    intake = client.post("/api/opportunities/intake", json=_payload()).json()
    blocked = client.post(
        f"/api/opportunities/{intake['id']}/gate-decisions",
        json={
            "gate_code": "GATE_C",
            "decision": "APPROVED",
            "decider": "compliance-lead",
            "rationale": "Attempt out-of-sequence gate decision.",
        },
    )
    assert blocked.status_code == 409
    assert "Active gate is GATE_A" in str(blocked.json())
    detail = client.get(f"/api/opportunities/{intake['id']}").json()
    actions = [e["action"] for e in detail["audit_events"]]
    assert "gate_policy_violation" in actions


def test_gate_rework_records_rework_packet_and_changes_stage(client: TestClient) -> None:
    intake = client.post("/api/opportunities/intake", json=_payload()).json()
    rework = client.post(
        f"/api/opportunities/{intake['id']}/gate-decisions",
        json={
            "gate_code": "GATE_A",
            "decision": "REWORK_REQUIRED",
            "decider": "review-lead",
            "rationale": "Claims lack evidence.",
            "rework_instructions": "Add citations for every performance claim.",
            "rework_owner": "section-owner-1",
            "rework_due_date": "2026-03-20",
        },
    )
    assert rework.status_code == 200
    detail = client.get(f"/api/opportunities/{intake['id']}").json()
    assert detail["stage"] == "QUALIFICATION"
    assert detail["gate_decisions"][0]["rework_instructions"] == "Add citations for every performance claim."


def test_pending_gates_api_shows_active_gate_and_updates_after_approval(client: TestClient) -> None:
    intake = client.post("/api/opportunities/intake", json=_payload()).json()
    pending = client.get("/api/opportunities/gates/pending")
    assert pending.status_code == 200
    items = pending.json()
    row = next(i for i in items if i["opportunity_id"] == intake["id"])
    assert row["gate_code"] == "GATE_A"
    assert row["gate_status"] == "PENDING"

    decision = client.post(
        f"/api/opportunities/{intake['id']}/gate-decisions",
        json={
            "gate_code": "GATE_A",
            "decision": "APPROVED",
            "decider": "principal",
            "rationale": "Proceeding to strategy.",
        },
    )
    assert decision.status_code == 200

    pending_after = client.get("/api/opportunities/gates/pending")
    assert pending_after.status_code == 200
    items_after = pending_after.json()
    row_after = next(i for i in items_after if i["opportunity_id"] == intake["id"])
    assert row_after["gate_code"] == "GATE_B"


def test_gate_policy_blocks_unauthorized_role_and_logs_violation(client: TestClient) -> None:
    intake = client.post("/api/opportunities/intake", json=_payload()).json()
    blocked = client.post(
        f"/api/opportunities/{intake['id']}/gate-decisions",
        json={
            "gate_code": "GATE_F",
            "decision": "APPROVED",
            "decider": "content-writer-1",
            "decider_role": "section_owner",
            "rationale": "Attempting unauthorized final approval.",
        },
    )
    assert blocked.status_code == 409
    detail = client.get(f"/api/opportunities/{intake['id']}").json()
    actions = [e["action"] for e in detail["audit_events"]]
    assert "gate_policy_violation" in actions


def test_stage_transition_preview_returns_blockers_and_does_not_mutate_stage(client: TestClient) -> None:
    intake = client.post("/api/opportunities/intake", json=_payload()).json()
    preview = client.get(
        f"/api/opportunities/{intake['id']}/stage-transition-preview",
        params={"next_stage": "DRAFTING", "actor": "operator", "actor_role": "proposal_manager"},
    )
    assert preview.status_code == 200
    payload = preview.json()
    assert payload["from_stage"] == "INTAKE"
    assert payload["to_stage"] == "DRAFTING"
    assert payload["blockers"]
    assert any("not allowed by state machine" in item for item in payload["blockers"])
    detail = client.get(f"/api/opportunities/{intake['id']}").json()
    assert detail["stage"] == "INTAKE"


def test_workflow_timeline_api_returns_events_and_category_filter(client: TestClient) -> None:
    intake = client.post("/api/opportunities/intake", json=_payload()).json()
    opportunity_id = intake["id"]
    client.post(
        f"/api/opportunities/{opportunity_id}/stage-transition",
        json={
            "next_stage": "QUALIFICATION",
            "actor": "pm-1",
            "actor_role": "proposal_manager",
            "reason": "Manual progression.",
        },
    )
    client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_A",
            "decision": "APPROVED",
            "decider": "pm-1",
            "decider_role": "proposal_manager",
            "rationale": "Proceed to strategy.",
        },
    )

    timeline = client.get(f"/api/opportunities/{opportunity_id}/timeline")
    assert timeline.status_code == 200
    rows = timeline.json()
    assert len(rows) >= 3
    assert any(item["action"] == "stage_transition_recorded" for item in rows)
    assert any(item["action"] == "gate_decision_recorded" for item in rows)

    gate_only = client.get(
        f"/api/opportunities/{opportunity_id}/timeline",
        params={"category": "GATE"},
    )
    assert gate_only.status_code == 200
    gate_rows = gate_only.json()
    assert gate_rows
    assert all(item["category"] == "GATE" for item in gate_rows)
