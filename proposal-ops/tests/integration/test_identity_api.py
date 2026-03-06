from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "Identity Scoped Pursuit",
            "client": "Identity Client",
            "estimated_contract_value": 700000,
            "lead_time_days": 34,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 61,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_user_create_and_role_assignment_api(client: TestClient) -> None:
    user = client.post(
        "/api/users",
        json={"display_name": "Paula Manager", "email": "paula.manager@example.test"},
    )
    assert user.status_code == 200
    user_id = user.json()["id"]

    role = client.post(
        f"/api/users/{user_id}/roles",
        json={"role": "proposal_manager", "scope_type": "GLOBAL", "scope_id": None},
    )
    assert role.status_code == 200
    listed = client.get(f"/api/users/{user_id}/roles")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_role_assignment_scope_validation_and_effective_roles(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    user = client.post(
        "/api/users",
        json={"display_name": "Scoped Analyst", "email": "scoped.analyst@example.test"},
    ).json()

    invalid = client.post(
        f"/api/users/{user['id']}/roles",
        json={"role": "proposal_manager", "scope_type": "OPPORTUNITY", "scope_id": None},
    )
    assert invalid.status_code == 400

    assigned = client.post(
        f"/api/users/{user['id']}/roles",
        json={"role": "proposal_manager", "scope_type": "OPPORTUNITY", "scope_id": opportunity_id},
    )
    assert assigned.status_code == 200

    effective = client.get(
        f"/api/users/{user['id']}/effective-roles",
        params={"opportunity_id": opportunity_id},
    )
    assert effective.status_code == 200
    assert "proposal_manager" in effective.json()["roles"]


def test_gate_decision_with_decider_user_id_generates_signature(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    user = client.post(
        "/api/users",
        json={"display_name": "Avery PM", "email": "avery.pm@example.test"},
    ).json()
    client.post(
        f"/api/users/{user['id']}/roles",
        json={"role": "proposal_manager", "scope_type": "OPPORTUNITY", "scope_id": opportunity_id},
    )

    decision = client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_A",
            "decision": "APPROVED",
            "decider": "ignored-name",
            "decider_user_id": user["id"],
            "decider_role": "proposal_manager",
            "rationale": "User-scoped approval.",
        },
    )
    assert decision.status_code == 200
    payload = decision.json()
    assert payload["decider_user_id"] == user["id"]
    assert payload["approval_signature"] is not None
    assert len(payload["approval_signature"]) == 64


def test_gate_decision_denied_for_user_without_scoped_role(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    user = client.post(
        "/api/users",
        json={"display_name": "No Scope", "email": "noscope@example.test"},
    ).json()
    denied = client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_A",
            "decision": "APPROVED",
            "decider": "No Scope",
            "decider_user_id": user["id"],
            "decider_role": "proposal_manager",
            "rationale": "Should fail scoped auth.",
        },
    )
    assert denied.status_code == 409
    detail = client.get(f"/api/opportunities/{opportunity_id}").json()
    actions = [e["action"] for e in detail["audit_events"]]
    assert "gate_policy_violation" in actions
