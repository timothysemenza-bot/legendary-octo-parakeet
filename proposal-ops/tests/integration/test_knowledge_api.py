from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "Lessons Pipeline Pursuit",
            "client": "State DOT",
            "estimated_contract_value": 1200000,
            "lead_time_days": 45,
            "incumbent_status": False,
            "strategic_alignment": 5,
            "estimated_probability_win": 63,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_lessons_record_and_promotion_decision_flow(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    created = client.post(
        f"/api/opportunities/{opportunity_id}/lessons",
        json={
            "outcome": "LOSS",
            "root_causes": ["Weak discriminator evidence", "Late review start"],
            "actions": ["Add discriminator evidence rubric", "Start red review earlier"],
            "promotions": [
                {
                    "asset_title": "Discriminator Evidence Checklist",
                    "asset_type": "PLAYBOOK",
                    "rationale": "Reusable for future pursuits",
                }
            ],
            "created_by": "operator",
        },
    )
    assert created.status_code == 200
    record = created.json()
    assert record["status"] == "DRAFT"
    assert len(record["promotions"]) == 1
    promo_id = record["promotions"][0]["id"]

    ready_before = client.get(f"/api/opportunities/{opportunity_id}/knowledge/readiness")
    assert ready_before.status_code == 200
    assert ready_before.json()["gate_g_ready"] is False

    approved_record = client.post(
        f"/api/opportunities/{opportunity_id}/lessons/{record['id']}/approve",
        json={"actor": "knowledge_manager"},
    )
    assert approved_record.status_code == 200
    assert approved_record.json()["status"] == "APPROVED"

    pending_after_approve = client.get(f"/api/opportunities/{opportunity_id}/knowledge/readiness").json()
    assert pending_after_approve["gate_g_ready"] is False

    promo_decision = client.post(
        f"/api/opportunities/knowledge/promotions/{promo_id}/decision",
        json={"decision": "APPROVED", "actor": "knowledge_manager"},
    )
    assert promo_decision.status_code == 200
    assert promo_decision.json()["promotion_status"] == "APPROVED"

    ready_after = client.get(f"/api/opportunities/{opportunity_id}/knowledge/readiness").json()
    assert ready_after["gate_g_ready"] is True


def test_gate_g_approval_blocked_until_knowledge_ready(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    blocked = client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_G",
            "decision": "APPROVED",
            "decider": "km-1",
            "decider_role": "knowledge_manager",
            "rationale": "Attempting closeout before lessons.",
        },
    )
    assert blocked.status_code == 409

