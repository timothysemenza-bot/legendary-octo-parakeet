from fastapi.testclient import TestClient


def test_users_admin_page_and_create_flow(client: TestClient) -> None:
    admin = client.post(
        "/api/users",
        json={"display_name": "Admin User", "email": "admin.user@example.test"},
    ).json()
    client.post(
        f"/api/users/{admin['id']}/roles",
        json={"role": "admin", "scope_type": "GLOBAL", "scope_id": None},
    )
    client.post(
        "/auth/login",
        data={"email": "admin.user@example.test"},
        follow_redirects=False,
    )

    page = client.get("/admin/users")
    assert page.status_code == 200
    assert "User Admin" in page.text

    created = client.post(
        "/admin/users",
        data={"display_name": "UI User", "email": "ui.user@example.test"},
        follow_redirects=False,
    )
    assert created.status_code == 303
    refreshed = client.get("/admin/users")
    assert refreshed.status_code == 200
    assert "UI User" in refreshed.text
    assert "Opportunity Scope" in refreshed.text


def test_users_admin_requires_admin_session(client: TestClient) -> None:
    denied = client.get("/admin/users")
    assert denied.status_code == 403
