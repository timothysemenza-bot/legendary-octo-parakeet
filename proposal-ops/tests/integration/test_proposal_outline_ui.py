from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "Proposal Outline UI Pursuit",
            "client": "County Health",
            "estimated_contract_value": 540000,
            "lead_time_days": 26,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 60,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def _prepare_mapped_rows(client: TestClient, opportunity_id: str) -> None:
    parsed = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": (
                "The contractor shall provide onboarding and training.\n"
                "The contractor must submit a management plan.\n"
            ),
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
                "owner": "UI Owner",
                "status": "COMPLETE",
                "actor": "operator",
            },
        )
        assert patched.status_code == 200


def test_proposal_outline_dashboard_generate_flow(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    _prepare_mapped_rows(client, opportunity_id)

    page = client.get(f"/opportunities/{opportunity_id}/proposal-outline")
    assert page.status_code == 200
    assert "Proposal Outline" in page.text
    assert "No outline generated yet." in page.text

    generated = client.post(
        f"/opportunities/{opportunity_id}/proposal-outline/generate",
        data={"actor": "ui-operator"},
        follow_redirects=False,
    )
    assert generated.status_code == 303

    refreshed = client.get(f"/opportunities/{opportunity_id}/proposal-outline")
    assert refreshed.status_code == 200
    assert "Current Version:" in refreshed.text
    assert "Current Sections" in refreshed.text
