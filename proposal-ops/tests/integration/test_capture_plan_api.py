from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "Capture Plan API Pursuit",
            "client": "State Procurement",
            "estimated_contract_value": 910000,
            "lead_time_days": 41,
            "incumbent_status": True,
            "strategic_alignment": 5,
            "estimated_probability_win": 67,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_capture_plan_get_and_version_create_flow(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)

    initial = client.get(f"/api/opportunities/{opportunity_id}/capture-plan")
    assert initial.status_code == 200
    initial_payload = initial.json()
    assert initial_payload["version"] == 1

    create = client.post(
        f"/api/opportunities/{opportunity_id}/capture-plan",
        json={
            "summary": "Updated summary for capture strategy.",
            "client_priorities": "Modernization, faster onboarding, clearer reporting.",
            "competitive_landscape": "Two incumbents with weak delivery quality.",
            "win_themes_draft": "Lower transition risk and stronger compliance discipline.",
            "solution_positioning": "Phased rollout with measurable performance gates.",
            "timeline": "Kickoff in 2 weeks, pilot in 45 days, full launch in 90 days.",
            "actor": "capture_lead",
        },
    )
    assert create.status_code == 200
    created_payload = create.json()
    assert created_payload["version"] == 2
    assert created_payload["summary"] == "Updated summary for capture strategy."

    versions = client.get(f"/api/opportunities/{opportunity_id}/capture-plan/versions")
    assert versions.status_code == 200
    items = versions.json()
    assert len(items) == 2
    assert items[0]["version"] == 2
    assert items[1]["version"] == 1

    detail = client.get(f"/api/opportunities/{opportunity_id}").json()
    actions = [e["action"] for e in detail["audit_events"]]
    assert "capture_plan_version_created" in actions


def test_capture_plan_404_for_unknown_opportunity(client: TestClient) -> None:
    response = client.get("/api/opportunities/unknown-id/capture-plan")
    assert response.status_code == 404
