from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    body = {
        "name": "Regional Facilities Proposal",
        "client": "Metro County",
        "estimated_contract_value": 950000,
        "lead_time_days": 40,
        "incumbent_status": False,
        "strategic_alignment": 4,
        "estimated_probability_win": 68,
        "actor": "operator",
    }
    response = client.post("/api/opportunities/intake", json=body)
    assert response.status_code == 200
    return response.json()["id"]


def test_rfp_parse_generates_requirements_and_matrix(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    raw_text = """
    Proposal due date is 2026-07-15.
    Evaluation criteria include technical approach and pricing.
    The offeror shall provide a technical transition plan.
    The offeror must submit past performance references.
    """
    parsed = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": raw_text,
            "source_filename": "sample-rfp.txt",
            "actor": "operator",
        },
    )
    assert parsed.status_code == 200
    payload = parsed.json()
    assert payload["requirement_count"] >= 2
    assert payload["solicitation_id"]

    matrix = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix")
    assert matrix.status_code == 200
    rows = matrix.json()
    assert len(rows) == payload["requirement_count"]
    assert "proposal_section" in rows[0]
    assert "requirement_type" in rows[0]


def test_compliance_row_update(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": "The contractor shall provide a staffing plan and must submit pricing narrative by 05/20/2026.",
            "source_filename": "rfp.txt",
            "actor": "operator",
        },
    )
    rows = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix").json()
    row_id = rows[0]["id"]
    updated = client.patch(
        f"/api/compliance-matrix/{row_id}",
        json={
            "proposal_section": "Management Plan",
            "owner": "Jane Reviewer",
            "status": "IN_PROGRESS",
            "actor": "operator",
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["owner"] == "Jane Reviewer"
    assert body["status"] == "IN_PROGRESS"


def test_compliance_matrix_hides_context_only_by_default(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": (
                "Dealer/Distributor – means a relationship definition.\n"
                "The Bidder must submit its pricing using the State-Supplied Price Sheet."
            ),
            "source_filename": "rfp.txt",
            "actor": "operator",
        },
    )

    default_rows = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix").json()
    assert len(default_rows) >= 1
    assert all(row["requirement_type"] != "CONTEXT_ONLY" for row in default_rows)

    with_context = client.get(
        f"/api/opportunities/{opportunity_id}/compliance-matrix?include_context=true"
    ).json()
    # No context matrix rows are generated; context stays in parsed requirements only.
    assert len(with_context) == len(default_rows)


def test_compliance_matrix_quality_endpoint_reports_gate_c_readiness(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": (
                "The Bidder must submit pricing sheet.\n"
                "The Contractor shall provide staffing plan.\n"
            ),
            "source_filename": "rfp.txt",
            "actor": "operator",
        },
    )

    quality = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix/quality")
    assert quality.status_code == 200
    payload = quality.json()
    assert payload["gate_c_ready"] is False
    assert payload["unmapped_rows"] >= 1
    assert payload["missing_owner_rows"] >= 1

    rows = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix").json()
    for row in rows:
        update = client.patch(
            f"/api/compliance-matrix/{row['id']}",
            json={
                "proposal_section": row["proposal_section"],
                "owner": "Compliance Lead",
                "status": "COMPLETE",
                "actor": "operator",
            },
        )
        assert update.status_code == 200

    quality_after = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix/quality")
    assert quality_after.status_code == 200
    payload_after = quality_after.json()
    assert payload_after["gate_c_ready"] is True
    assert payload_after["unmapped_rows"] == 0
    assert payload_after["missing_owner_rows"] == 0
