from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "Submission Control Pursuit",
            "client": "Regional Health",
            "estimated_contract_value": 990000,
            "lead_time_days": 36,
            "incumbent_status": False,
            "strategic_alignment": 5,
            "estimated_probability_win": 67,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def _advance_to_submission_stage(client: TestClient, opportunity_id: str) -> None:
    client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": "The Contractor shall provide staffing plan. The Bidder must submit pricing sheet.",
            "source_filename": "rfp.txt",
            "actor": "operator",
        },
    )
    rows = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix").json()
    for row in rows:
        client.patch(
            f"/api/compliance-matrix/{row['id']}",
            json={
                "proposal_section": row["proposal_section"],
                "owner": "Compliance Lead",
                "status": "COMPLETE",
                "actor": "operator",
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
    client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_B",
            "decision": "APPROVED",
            "decider": "strategy-1",
            "decider_role": "capture_strategy_lead",
            "rationale": "Strategy approved.",
        },
    )
    client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_C",
            "decision": "APPROVED",
            "decider": "compliance-1",
            "decider_role": "compliance_lead",
            "rationale": "Compliance architecture approved.",
        },
    )
    client.post(
        f"/api/opportunities/{opportunity_id}/stage-transition",
        json={
            "next_stage": "DRAFTING",
            "actor": "pm-1",
            "actor_role": "proposal_manager",
            "reason": "Start drafting after planning.",
        },
    )
    pink = client.post(
        f"/api/opportunities/{opportunity_id}/reviews",
        json={"review_type": "PINK", "round_number": 1, "actor": "review-lead"},
    ).json()
    client.post(
        f"/api/opportunities/{opportunity_id}/reviews/{pink['id']}/close",
        json={"actor": "review-lead"},
    )
    client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_D",
            "decision": "APPROVED",
            "decider": "review-lead-1",
            "decider_role": "review_lead",
            "rationale": "Pink review complete.",
        },
    )
    red = client.post(
        f"/api/opportunities/{opportunity_id}/reviews",
        json={"review_type": "RED", "round_number": 1, "actor": "review-lead"},
    ).json()
    client.post(
        f"/api/opportunities/{opportunity_id}/reviews/{red['id']}/close",
        json={"actor": "review-lead"},
    )
    client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_E",
            "decision": "APPROVED",
            "decider": "pm-1",
            "decider_role": "proposal_manager",
            "rationale": "Narrative review complete.",
        },
    )


def test_submission_checklist_bootstraps_and_updates_items(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    checklist = client.get(f"/api/opportunities/{opportunity_id}/submission/checklist")
    assert checklist.status_code == 200
    payload = checklist.json()
    assert len(payload["items"]) >= 6

    first_item = payload["items"][0]
    updated = client.patch(
        f"/api/opportunities/{opportunity_id}/submission/checklist/items/{first_item['id']}",
        json={"status": "COMPLETE", "details": "Validated by operator", "actor": "operator"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "COMPLETE"


def test_submission_filename_validation_marks_checklist_item(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    invalid = client.post(
        f"/api/opportunities/{opportunity_id}/submission/validate-filenames",
        json={"file_names": ["Proposal Main.docx", "Pricing#.xlsx"], "actor": "operator"},
    )
    assert invalid.status_code == 200
    assert invalid.json()["valid"] is False
    assert len(invalid.json()["invalid_names"]) == 2

    valid = client.post(
        f"/api/opportunities/{opportunity_id}/submission/validate-filenames",
        json={"file_names": ["Proposal_Main.docx", "Pricing_Sheet.xlsx"], "actor": "operator"},
    )
    assert valid.status_code == 200
    assert valid.json()["valid"] is True


def test_gate_f_approval_blocked_by_submission_readiness(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    _advance_to_submission_stage(client, opportunity_id)
    gate_f = client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_F",
            "decision": "APPROVED",
            "decider": "exec-1",
            "decider_role": "executive_approver",
            "rationale": "Attempting final authorization early.",
        },
    )
    assert gate_f.status_code == 409
    assert "Gate F cannot be approved" in str(gate_f.json())
