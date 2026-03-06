from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "UI Lessons Pursuit",
            "client": "State Labor",
            "estimated_contract_value": 430000,
            "lead_time_days": 33,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 59,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_lessons_dashboard_renders_and_create_flow(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    page = client.get(f"/opportunities/{opportunity_id}/lessons")
    assert page.status_code == 200
    assert "Lessons Learned" in page.text

    created = client.post(
        f"/opportunities/{opportunity_id}/lessons",
        data={
            "outcome": "WIN",
            "root_causes": "Early engagement\nStrong teaming",
            "actions": "Codify engagement playbook\nPromote teaming template",
            "created_by": "operator",
            "promotion_title": "Teaming Template",
            "promotion_type": "TEMPLATE",
            "promotion_rationale": "Reusable in future bids",
        },
        follow_redirects=False,
    )
    assert created.status_code == 303

    refreshed = client.get(f"/opportunities/{opportunity_id}/lessons")
    assert refreshed.status_code == 200
    assert "Teaming Template" in refreshed.text

