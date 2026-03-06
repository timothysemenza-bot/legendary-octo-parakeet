from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "Capture Plan UI Pursuit",
            "client": "County Transit",
            "estimated_contract_value": 730000,
            "lead_time_days": 37,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 62,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_capture_plan_page_renders_and_create_version_web_flow(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)

    page = client.get(f"/opportunities/{opportunity_id}/capture-plan")
    assert page.status_code == 200
    assert "Capture Plan" in page.text
    assert "Current Version" in page.text

    update = client.post(
        f"/opportunities/{opportunity_id}/capture-plan",
        data={
            "summary": "UI update summary for new version.",
            "client_priorities": "Compliance confidence and schedule certainty.",
            "competitive_landscape": "Incumbent is strong but delivery metrics are inconsistent.",
            "win_themes_draft": "Lower execution risk with transparent governance.",
            "solution_positioning": "Operational model with clear ownership by phase.",
            "timeline": "Week 1 discovery, week 3 pilot, week 10 stabilization.",
            "actor": "operator-ui",
        },
        follow_redirects=False,
    )
    assert update.status_code == 303

    refreshed = client.get(f"/opportunities/{opportunity_id}/capture-plan")
    assert refreshed.status_code == 200
    assert "UI update summary for new version." in refreshed.text
    assert ">2<" in refreshed.text
