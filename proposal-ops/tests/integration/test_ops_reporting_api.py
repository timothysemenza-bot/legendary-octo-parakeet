from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient, name: str) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": name,
            "client": "Ops Metrics Client",
            "estimated_contract_value": 500000,
            "lead_time_days": 30,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 60,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_ops_metrics_endpoint_returns_expected_shape(client: TestClient) -> None:
    _create_opportunity(client, "Metrics Pursuit A")
    _create_opportunity(client, "Metrics Pursuit B")

    response = client.get("/api/ops/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert "generated_at" in payload
    assert "gate_latency" in payload
    assert "rework_velocity" in payload
    assert "defect_rates" in payload
    assert "blocker_aging" in payload
    assert payload["opportunities_total"] >= 2
    assert len(payload["gate_latency"]) >= 7


def test_ops_metrics_csv_export(client: TestClient) -> None:
    _create_opportunity(client, "CSV Export Pursuit")
    response = client.get("/api/ops/metrics/export.csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "metric,value" in response.text
    assert "opportunities_total" in response.text

