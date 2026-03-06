from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "UI Review Board Pursuit",
            "client": "County Utilities",
            "estimated_contract_value": 620000,
            "lead_time_days": 32,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 58,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_review_dashboard_renders_and_creates_cycle(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    page = client.get(f"/opportunities/{opportunity_id}/reviews")
    assert page.status_code == 200
    assert "Review Dashboard" in page.text

    create = client.post(
        f"/opportunities/{opportunity_id}/reviews",
        data={"review_type": "PINK", "round_number": 1, "actor": "operator"},
        follow_redirects=False,
    )
    assert create.status_code == 303

    refreshed = client.get(f"/opportunities/{opportunity_id}/reviews")
    assert refreshed.status_code == 200
    assert "PINK" in refreshed.text

