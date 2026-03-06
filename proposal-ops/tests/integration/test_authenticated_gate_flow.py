from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "Session Signed Approval Pursuit",
            "client": "Session Client",
            "estimated_contract_value": 540000,
            "lead_time_days": 30,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 60,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_web_gate_decision_uses_session_identity_for_signature(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)

    user = client.post(
        "/api/users",
        json={"display_name": "Session PM", "email": "session.pm@example.test"},
    ).json()
    role = client.post(
        f"/api/users/{user['id']}/roles",
        json={"role": "proposal_manager", "scope_type": "GLOBAL", "scope_id": None},
    )
    assert role.status_code == 200

    login = client.post(
        "/auth/login",
        data={"email": "session.pm@example.test"},
        follow_redirects=False,
    )
    assert login.status_code == 303

    gate = client.post(
        f"/opportunities/{opportunity_id}/gate-decisions",
        data={
            "decision": "APPROVED",
            "decider_role": "proposal_manager",
            "rationale": "Session-backed approval",
            "gate_code": "GATE_A",
        },
        follow_redirects=False,
    )
    assert gate.status_code == 303

    detail = client.get(f"/api/opportunities/{opportunity_id}").json()
    recorded = detail["gate_decisions"][0]
    assert recorded["decider"] == "Session PM"
    assert recorded["decider_user_id"] == user["id"]
    assert recorded["approval_signature"] is not None


def test_opportunity_detail_shows_only_authorized_gate_options_for_session_user(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    user = client.post(
        "/api/users",
        json={"display_name": "Scoped PM", "email": "scoped.pm@example.test"},
    ).json()
    client.post(
        f"/api/users/{user['id']}/roles",
        json={"role": "proposal_manager", "scope_type": "GLOBAL", "scope_id": None},
    )
    client.post(
        "/auth/login",
        data={"email": "scoped.pm@example.test"},
        follow_redirects=False,
    )

    page = client.get(f"/opportunities/{opportunity_id}")
    assert page.status_code == 200
    assert "value=\"GATE_A\"" in page.text
    assert "value=\"GATE_F\"" not in page.text
    assert "My Gate Permissions" in page.text
    assert "Authorized by matched role assignment." in page.text


def test_stage_transition_web_denies_session_user_without_transition_authority(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    user = client.post(
        "/api/users",
        json={"display_name": "Scoped Section Owner", "email": "scoped.section@example.test"},
    ).json()
    client.post(
        f"/api/users/{user['id']}/roles",
        json={"role": "section_owner", "scope_type": "GLOBAL", "scope_id": None},
    )
    client.post(
        "/auth/login",
        data={"email": "scoped.section@example.test"},
        follow_redirects=False,
    )

    transition = client.post(
        f"/opportunities/{opportunity_id}/stage-transition",
        data={"next_stage": "QUALIFICATION", "reason": "Try unauthorized transition"},
        follow_redirects=False,
    )
    assert transition.status_code == 403
