from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "Proposal Outline API Pursuit",
            "client": "State Commerce",
            "estimated_contract_value": 880000,
            "lead_time_days": 39,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 64,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def _parse_rfp(client: TestClient, opportunity_id: str) -> None:
    parsed = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": (
                "The offeror shall provide a technical transition plan.\n"
                "The offeror must submit past performance references.\n"
                "Pricing must include all travel costs.\n"
            ),
            "source_filename": "rfp.txt",
            "actor": "operator",
        },
    )
    assert parsed.status_code == 200


def test_proposal_outline_generation_and_versioning(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    _parse_rfp(client, opportunity_id)

    blocked = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-outline/generate",
        json={"actor": "outline_bot"},
    )
    assert blocked.status_code == 409

    rows = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix").json()
    assert rows
    for row in rows:
        patched = client.patch(
            f"/api/compliance-matrix/{row['id']}",
            json={
                "proposal_section": row["proposal_section"],
                "owner": "Section Owner",
                "status": "COMPLETE",
                "actor": "operator",
            },
        )
        assert patched.status_code == 200

    generated = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-outline/generate",
        json={"actor": "outline_bot"},
    )
    assert generated.status_code == 200
    body = generated.json()
    assert body["version"] == 1
    assert body["sections"]
    assert body["sections"][0]["sequence"] == 1

    latest = client.get(f"/api/opportunities/{opportunity_id}/proposal-outline")
    assert latest.status_code == 200
    assert latest.json()["version"] == 1

    generated_again = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-outline/generate",
        json={"actor": "outline_bot"},
    )
    assert generated_again.status_code == 200
    assert generated_again.json()["version"] == 2

    versions = client.get(f"/api/opportunities/{opportunity_id}/proposal-outline/versions")
    assert versions.status_code == 200
    history = versions.json()
    assert len(history) == 2
    assert history[0]["version"] == 2
    assert history[1]["version"] == 1

    detail = client.get(f"/api/opportunities/{opportunity_id}").json()
    actions = [event["action"] for event in detail["audit_events"]]
    assert "proposal_outline_generated" in actions
