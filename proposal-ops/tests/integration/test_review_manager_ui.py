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


def _prepare_outline(client: TestClient, opportunity_id: str) -> None:
    parsed = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": "The Contractor shall provide staffing plan. The Bidder must submit pricing sheet.",
            "source_filename": "rfp.txt",
            "actor": "operator",
        },
    )
    assert parsed.status_code == 200
    rows = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix").json()
    for row in rows:
        patched = client.patch(
            f"/api/compliance-matrix/{row['id']}",
            json={
                "proposal_section": row["proposal_section"],
                "owner": "Outline Owner",
                "status": "COMPLETE",
                "actor": "operator",
            },
        )
        assert patched.status_code == 200
    generated = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-outline/generate",
        json={"actor": "operator"},
    )
    assert generated.status_code == 200


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


def test_review_dashboard_seed_from_outline_web_flow(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    _prepare_outline(client, opportunity_id)
    cycle = client.post(
        f"/api/opportunities/{opportunity_id}/reviews",
        json={"review_type": "PINK", "round_number": 1, "actor": "operator"},
    )
    assert cycle.status_code == 200
    cycle_id = cycle.json()["id"]

    seeded = client.post(
        f"/opportunities/{opportunity_id}/reviews/{cycle_id}/seed-from-outline",
        data={"actor": "operator"},
        follow_redirects=False,
    )
    assert seeded.status_code == 303

    refreshed = client.get(f"/opportunities/{opportunity_id}/reviews")
    assert refreshed.status_code == 200
    assert "Seeded from proposal outline section." in refreshed.text
