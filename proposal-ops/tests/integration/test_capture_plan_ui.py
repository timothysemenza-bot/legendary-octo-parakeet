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


def _parse_strategy_rfp(client: TestClient, opportunity_id: str) -> None:
    response = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": (
                "Proposal due date is 2026-05-30 and submissions must be uploaded electronically.\n"
                "Evaluation criteria include technical approach, management, and pricing.\n"
                "The contractor shall provide a staffing plan and must submit past performance references.\n"
                "Offeror must submit a technical approach narrative.\n"
                "Offeror must provide a detailed pricing narrative."
            ),
            "source_filename": "capture-plan-rfp.txt",
            "actor": "operator",
        },
    )
    assert response.status_code == 200


def test_capture_plan_page_renders_and_create_version_web_flow(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)

    page = client.get(f"/opportunities/{opportunity_id}/capture-plan")
    assert page.status_code == 200
    assert "Capture Plan" in page.text
    assert "Current Version" in page.text
    assert "Strategy Readiness" in page.text
    assert "Gate B Ready:" in page.text
    assert "Capture plan is still the intake bootstrap template." in page.text
    assert "Generate Enriched Version" in page.text

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


def test_capture_plan_generate_web_flow(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    _parse_strategy_rfp(client, opportunity_id)

    generated = client.post(
        f"/opportunities/{opportunity_id}/capture-plan/generate",
        data={"actor": "capture_lead"},
        follow_redirects=False,
    )
    assert generated.status_code == 303

    refreshed = client.get(f"/opportunities/{opportunity_id}/capture-plan")
    assert refreshed.status_code == 200
    assert ">2<" in refreshed.text
    assert "2026-05-30" in refreshed.text
    assert "Gate B Ready:</strong> YES" in refreshed.text
    assert "Strategy artifacts are ready for Gate B approval." in refreshed.text
    assert "Generate Enriched Version" in refreshed.text
