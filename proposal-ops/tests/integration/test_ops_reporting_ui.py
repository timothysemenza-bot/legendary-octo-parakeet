from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "Ops UI Pursuit",
            "client": "Ops UI Client",
            "estimated_contract_value": 650000,
            "lead_time_days": 28,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 57,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_ops_dashboard_renders(client: TestClient) -> None:
    _create_opportunity(client)
    page = client.get("/ops/dashboard")
    assert page.status_code == 200
    assert "Ops Dashboard" in page.text
    assert "Gate Latency" in page.text
    assert "Export CSV" in page.text

