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


def test_capture_plan_readiness_reports_bootstrap_blockers_until_strategy_is_enriched(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)

    initial = client.get(f"/api/opportunities/{opportunity_id}/capture-plan/readiness")
    assert initial.status_code == 200
    initial_payload = initial.json()
    assert initial_payload["ready_for_gate_b"] is False
    assert initial_payload["uses_bootstrap_template"] is True
    assert "Capture plan is still the intake bootstrap template." in initial_payload["blockers"]
    assert "No solicitation has been parsed for this opportunity." in initial_payload["blockers"]

    _parse_strategy_rfp(client, opportunity_id)
    generated = client.post(
        f"/api/opportunities/{opportunity_id}/capture-plan/generate",
        json={"actor": "capture_lead"},
    )
    assert generated.status_code == 200

    enriched = client.get(f"/api/opportunities/{opportunity_id}/capture-plan/readiness")
    assert enriched.status_code == 200
    enriched_payload = enriched.json()
    assert enriched_payload["ready_for_gate_b"] is True
    assert enriched_payload["uses_bootstrap_template"] is False
    assert enriched_payload["matrix_row_count"] >= 1
    assert enriched_payload["win_theme_count"] >= 2
    assert enriched_payload["blockers"] == []


def test_capture_plan_generate_creates_enriched_version_from_latest_rfp(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    _parse_strategy_rfp(client, opportunity_id)

    generated = client.post(
        f"/api/opportunities/{opportunity_id}/capture-plan/generate",
        json={"actor": "capture_lead"},
    )
    assert generated.status_code == 200
    payload = generated.json()
    assert payload["version"] == 2
    assert "Capture Plan API Pursuit" in payload["summary"]
    assert "State Procurement" in payload["summary"]
    assert "2026-05-30" in payload["summary"]
    assert "Evaluation focus:" in payload["client_priorities"]
    assert "Submission discipline:" in payload["client_priorities"]
    assert "Incumbent advantage is in play" in payload["competitive_landscape"]
    assert "Win Theme:" in payload["win_themes_draft"]
    assert "technical response" in payload["solution_positioning"].lower()
    assert "Submission on 2026-05-30." in payload["timeline"]

    versions = client.get(f"/api/opportunities/{opportunity_id}/capture-plan/versions")
    assert versions.status_code == 200
    items = versions.json()
    assert items[0]["version"] == 2
    assert items[1]["version"] == 1

    detail = client.get(f"/api/opportunities/{opportunity_id}").json()
    actions = [event["action"] for event in detail["audit_events"]]
    assert "capture_plan_enriched_generated" in actions


def test_capture_plan_generate_requires_existing_opportunity_and_solicitation(client: TestClient) -> None:
    missing_opp = client.post(
        "/api/opportunities/unknown-id/capture-plan/generate",
        json={"actor": "capture_lead"},
    )
    assert missing_opp.status_code == 404

    missing_readiness = client.get("/api/opportunities/unknown-id/capture-plan/readiness")
    assert missing_readiness.status_code == 404

    opportunity_id = _create_opportunity(client)
    missing_rfp = client.post(
        f"/api/opportunities/{opportunity_id}/capture-plan/generate",
        json={"actor": "capture_lead"},
    )
    assert missing_rfp.status_code == 409
