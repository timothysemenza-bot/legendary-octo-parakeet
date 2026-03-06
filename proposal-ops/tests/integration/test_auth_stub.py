from fastapi.testclient import TestClient


def test_auth_login_me_logout_flow(client: TestClient) -> None:
    login_page = client.get("/auth/login")
    assert login_page.status_code == 200
    assert "Sign In (OIDC Stub)" in login_page.text

    login = client.post(
        "/auth/login",
        data={"email": "stub.user@example.test", "display_name": "Stub User"},
        follow_redirects=False,
    )
    assert login.status_code == 303

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    payload = me.json()
    assert payload is not None
    assert payload["email"] == "stub.user@example.test"

    logout = client.post("/auth/logout", follow_redirects=False)
    assert logout.status_code == 303
    me_after = client.get("/api/auth/me")
    assert me_after.status_code == 200
    assert me_after.json() is None


def test_auth_permissions_requires_session_and_returns_gate_reports(client: TestClient) -> None:
    intake = client.post(
        "/api/opportunities/intake",
        json={
            "name": "Permissions Pursuit",
            "client": "Permissions Client",
            "estimated_contract_value": 500000,
            "lead_time_days": 35,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 62,
            "actor": "operator",
        },
    )
    assert intake.status_code == 200
    opportunity_id = intake.json()["id"]

    unauthorized = client.get("/api/auth/permissions", params={"opportunity_id": opportunity_id})
    assert unauthorized.status_code == 401

    user = client.post(
        "/api/users",
        json={"display_name": "Policy PM", "email": "policy.pm@example.test"},
    ).json()
    role = client.post(
        f"/api/users/{user['id']}/roles",
        json={"role": "proposal_manager", "scope_type": "GLOBAL", "scope_id": None},
    )
    assert role.status_code == 200

    login = client.post("/auth/login", data={"email": "policy.pm@example.test"}, follow_redirects=False)
    assert login.status_code == 303

    allowed = client.get("/api/auth/permissions", params={"opportunity_id": opportunity_id})
    assert allowed.status_code == 200
    payload = allowed.json()
    assert payload["opportunity_id"] == opportunity_id
    assert len(payload["reports"]) == 7
    gate_a = next(item for item in payload["reports"] if item["gate_code"] == "GATE_A")
    gate_f = next(item for item in payload["reports"] if item["gate_code"] == "GATE_F")
    assert gate_a["allowed"] is True
    assert gate_f["allowed"] is False
