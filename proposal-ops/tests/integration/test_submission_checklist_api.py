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


def _prepare_outline(client: TestClient, opportunity_id: str) -> list[str]:
    parsed = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": (
                "Proposal due date is 2026-05-30 and submissions must be uploaded electronically.\n"
                "Evaluation criteria include technical approach, management, and pricing.\n"
                "The contractor shall provide a staffing plan and must submit past performance references.\n"
                "Offeror must provide a detailed pricing narrative."
            ),
            "source_filename": "rfp.txt",
            "actor": "operator",
        },
    )
    assert parsed.status_code == 200
    rows = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix").json()
    assert len(rows) >= 2
    outline = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-outline/manual",
        json={
            "actor": "operator",
            "sections": [
                {
                    "sequence": 2,
                    "proposal_section": "Technical Approach",
                    "owner": "Section Owner",
                    "requirement_ids": [rows[0]["requirement_id"]],
                },
                {
                    "sequence": 1,
                    "proposal_section": "Executive Summary",
                    "owner": "Proposal Manager",
                    "requirement_ids": [rows[1]["requirement_id"]],
                },
            ],
        },
    )
    assert outline.status_code == 200
    return [section["proposal_section"] for section in outline.json()["sections"]]


def _advance_to_submission_stage(client: TestClient, opportunity_id: str) -> None:
    parsed = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": (
                "Proposal due date is 2026-05-30 and submissions must be uploaded electronically.\n"
                "Evaluation criteria include technical approach, management, and pricing.\n"
                "The Contractor shall provide staffing plan.\n"
                "The Bidder must submit pricing sheet.\n"
                "Offeror must provide past performance references."
            ),
            "source_filename": "rfp.txt",
            "actor": "operator",
        },
    )
    assert parsed.status_code == 200
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
    generated = client.post(
        f"/api/opportunities/{opportunity_id}/capture-plan/generate",
        json={"actor": "capture-lead"},
    )
    assert generated.status_code == 200
    gate_a = client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_A",
            "decision": "APPROVED",
            "decider": "pm-1",
            "decider_role": "proposal_manager",
            "rationale": "Proceed to strategy.",
        },
    )
    assert gate_a.status_code == 200
    gate_b = client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_B",
            "decision": "APPROVED",
            "decider": "strategy-1",
            "decider_role": "capture_strategy_lead",
            "rationale": "Strategy approved.",
        },
    )
    assert gate_b.status_code == 200
    gate_c = client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_C",
            "decision": "APPROVED",
            "decider": "compliance-1",
            "decider_role": "compliance_lead",
            "rationale": "Compliance architecture approved.",
        },
    )
    assert gate_c.status_code == 200
    drafting = client.post(
        f"/api/opportunities/{opportunity_id}/stage-transition",
        json={
            "next_stage": "DRAFTING",
            "actor": "pm-1",
            "actor_role": "proposal_manager",
            "reason": "Start drafting after planning.",
        },
    )
    assert drafting.status_code == 200
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


def test_submission_package_structure_validation_uses_latest_outline(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    missing_outline = client.post(
        f"/api/opportunities/{opportunity_id}/submission/validate-package",
        json={"section_names": ["Executive Summary"], "actor": "operator"},
    )
    assert missing_outline.status_code == 200
    assert missing_outline.json()["valid"] is False
    assert missing_outline.json()["outline_version"] is None

    expected_sections = _prepare_outline(client, opportunity_id)
    invalid = client.post(
        f"/api/opportunities/{opportunity_id}/submission/validate-package",
        json={"section_names": list(reversed(expected_sections)), "actor": "operator"},
    )
    assert invalid.status_code == 200
    invalid_payload = invalid.json()
    assert invalid_payload["valid"] is False
    assert invalid_payload["out_of_order"] is True

    valid = client.post(
        f"/api/opportunities/{opportunity_id}/submission/validate-package",
        json={"section_names": expected_sections, "actor": "operator"},
    )
    assert valid.status_code == 200
    payload = valid.json()
    assert payload["valid"] is True
    assert payload["outline_version"] == 1

    checklist = client.get(f"/api/opportunities/{opportunity_id}/submission/checklist")
    assert checklist.status_code == 200
    structure_item = next(
        item for item in checklist.json()["items"] if item["item_code"] == "DOCUMENT_STRUCTURE_VALIDATED"
    )
    assert structure_item["status"] == "COMPLETE"

    detail = client.get(f"/api/opportunities/{opportunity_id}").json()
    actions = [event["action"] for event in detail["audit_events"]]
    assert "submission_package_structure_validation_ran" in actions


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
