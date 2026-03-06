from sqlalchemy import text
from fastapi.testclient import TestClient

from app.core.db import engine


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "UI Notification Pursuit",
            "client": "UI Alert Client",
            "estimated_contract_value": 450000,
            "lead_time_days": 20,
            "incumbent_status": False,
            "strategic_alignment": 3,
            "estimated_probability_win": 55,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_notifications_digest_page_renders_and_acknowledges(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE opportunities SET updated_at = datetime('now', '-5 day') WHERE id = :opportunity_id"),
            {"opportunity_id": opportunity_id},
        )

    scan = client.post("/notifications/scan", follow_redirects=False)
    assert scan.status_code == 303

    page = client.get("/notifications/digest")
    assert page.status_code == 200
    assert "Notification Digest" in page.text
    assert "SLA_BREACH" in page.text or "REMINDER" in page.text
    assert "Dispatch Open Notifications" in page.text

    events = client.get("/api/notifications").json()
    assert events
    ack = client.post(
        f"/notifications/{events[0]['id']}/ack",
        data={"status": "OPEN"},
        follow_redirects=False,
    )
    assert ack.status_code == 303

    dispatch = client.post("/notifications/dispatch", follow_redirects=False)
    assert dispatch.status_code == 303
    refreshed = client.get("/notifications/digest")
    assert refreshed.status_code == 200
    assert "Delivery Log" in refreshed.text


def test_notifications_policy_editor_renders_and_saves(client: TestClient) -> None:
    page = client.get("/notifications/policy")
    assert page.status_code == 200
    assert "Notification Policy Editor" in page.text
    assert "Client Policy Mappings" in page.text
    assert "Policy Keys" in page.text

    invalid = client.post(
        "/notifications/policy",
        data={"policy_json": "{\"routing\":{}}"},
    )
    assert invalid.status_code == 422
    assert "Missing top-level keys" in invalid.text

    valid_policy = {
        "global_thresholds": {"reminder_days_before_sla": 1, "escalation_tiers": [1, 3, 7]},
        "client_threshold_overrides": {},
        "routing": {
            "REMINDER": {"roles": ["proposal_manager"]},
            "SLA_BREACH": {"roles": ["proposal_manager"]},
            "BLOCKER_ESCALATION": {"roles": ["compliance_lead"]},
            "SLA_ESCALATION": {"roles": ["executive_approver"]},
        },
    }
    import json
    saved = client.post("/notifications/policy", data={"policy_json": json.dumps(valid_policy)})
    assert saved.status_code == 200
    assert "Policy saved successfully." in saved.text


def test_notifications_policy_editor_mapping_save_and_delete(client: TestClient) -> None:
    import json
    from app.core.db import engine
    from sqlalchemy import text

    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO notification_policy_configs (id, policy_key, policy_json, updated_by, created_at, updated_at) "
                "VALUES ('pol_ui_1', 'ui_policy', :policy_json, 'test', datetime('now'), datetime('now'))"
            ),
            {
                "policy_json": json.dumps(
                    {
                        "global_thresholds": {"reminder_days_before_sla": 1, "escalation_tiers": [1]},
                        "client_threshold_overrides": {},
                        "routing": {"REMINDER": {"roles": ["proposal_manager"]}},
                    }
                )
            },
        )

    bad = client.post(
        "/notifications/policy/mappings",
        data={"client_name": "UI Client", "policy_key": "missing_policy"},
    )
    assert bad.status_code == 422
    assert "does not exist" in bad.text

    saved = client.post(
        "/notifications/policy/mappings",
        data={"client_name": "UI Client", "policy_key": "ui_policy"},
    )
    assert saved.status_code == 200
    assert "UI Client" in saved.text

    deleted = client.post("/notifications/policy/mappings/UI Client/delete", follow_redirects=False)
    assert deleted.status_code == 303


def test_notifications_policy_editor_policy_key_lifecycle(client: TestClient) -> None:
    import json

    valid_policy = {
        "global_thresholds": {"reminder_days_before_sla": 1, "escalation_tiers": [1, 3, 7]},
        "client_threshold_overrides": {},
        "routing": {
            "REMINDER": {"roles": ["proposal_manager"]},
            "SLA_BREACH": {"roles": ["proposal_manager"]},
            "BLOCKER_ESCALATION": {"roles": ["compliance_lead"]},
            "SLA_ESCALATION": {"roles": ["executive_approver"]},
        },
    }
    created = client.post(
        "/notifications/policy/configs",
        data={"policy_key": "ui_lifecycle_policy", "policy_json": json.dumps(valid_policy)},
        follow_redirects=False,
    )
    assert created.status_code == 303

    clone = client.post(
        "/notifications/policy/configs/ui_lifecycle_policy/clone",
        data={"target_policy_key": "ui_lifecycle_policy_clone"},
        follow_redirects=False,
    )
    assert clone.status_code == 303

    # map then verify delete blocked
    client.post(
        "/notifications/policy/mappings",
        data={"client_name": "UI Map Client", "policy_key": "ui_lifecycle_policy_clone"},
    )
    blocked_delete = client.post("/notifications/policy/configs/ui_lifecycle_policy_clone/delete")
    assert blocked_delete.status_code == 422
    assert "mapped to one or more clients" in blocked_delete.text


def test_notifications_email_updates_page_ingest_and_apply(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)

    page = client.get("/notifications/email")
    assert page.status_code == 200
    assert "Email-Derived Bid Updates" in page.text

    ingested = client.post(
        "/notifications/email/ingest",
        data={
            "from_address": "capture@example.test",
            "opportunity_id": opportunity_id,
            "external_message_id": "ui-msg-001",
            "subject": "No Bid for this one",
            "body": "Leadership decided no bid for this pursuit.",
        },
        follow_redirects=False,
    )
    assert ingested.status_code == 303

    pending = client.get("/notifications/email?status=PENDING")
    assert pending.status_code == 200
    assert "ui-msg-001" not in pending.text  # message id is stored but not displayed in table
    assert "No Bid for this one" in pending.text
    assert "NO_BID" in pending.text

    updates = client.get("/api/notifications/email/updates", params={"status": "PENDING"}).json()
    assert updates
    target = updates[0]

    applied = client.post(
        f"/notifications/email/updates/{target['id']}/apply",
        follow_redirects=False,
    )
    assert applied.status_code == 303

    opp = client.get(f"/api/opportunities/{opportunity_id}")
    assert opp.status_code == 200
    assert opp.json()["pursuit_recommendation"] == "NO_BID"


def test_notifications_email_connections_page_create_and_sync(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)

    page = client.get("/notifications/email/connections")
    assert page.status_code == 200
    assert "Email Connections" in page.text

    import json
    seed = json.dumps(
        [
            {
                "id": "ui-conn-msg-001",
                "opportunity_id": opportunity_id,
                "from_address": "capture@example.test",
                "subject": "Bid approved - proceed",
                "body": "We are bidding this one.",
                "auto_apply": True,
            }
        ]
    )
    created = client.post(
        "/notifications/email/connections",
        data={
            "provider": "MANUAL_FEED",
            "inbox_address": "ui.inbox@example.test",
            "config_json": "{\"seed_messages\": " + seed + "}",
        },
        follow_redirects=False,
    )
    assert created.status_code == 303

    connections = client.get("/api/notifications/email/connections")
    assert connections.status_code == 200
    rows = connections.json()
    assert rows
    connection_id = rows[0]["id"]

    synced = client.post(
        f"/notifications/email/connections/{connection_id}/sync",
        follow_redirects=False,
    )
    assert synced.status_code == 303

    opp = client.get(f"/api/opportunities/{opportunity_id}")
    assert opp.status_code == 200
    assert opp.json()["pursuit_recommendation"] == "BID"


def test_notifications_email_connections_status_and_delete(client: TestClient) -> None:
    created = client.post(
        "/api/notifications/email/connections",
        json={
            "actor": "ops-admin",
            "provider": "MANUAL_FEED",
            "inbox_address": "ui.lifecycle@example.test",
            "config": {"seed_messages": []},
        },
    )
    assert created.status_code == 200
    connection_id = created.json()["id"]

    paused = client.post(
        f"/notifications/email/connections/{connection_id}/status",
        data={"status": "PAUSED"},
        follow_redirects=False,
    )
    assert paused.status_code == 303

    rows = client.get("/api/notifications/email/connections").json()
    row = next(item for item in rows if item["id"] == connection_id)
    assert row["status"] == "PAUSED"

    deleted = client.post(
        f"/notifications/email/connections/{connection_id}/delete",
        follow_redirects=False,
    )
    assert deleted.status_code == 303

    rows_after = client.get("/api/notifications/email/connections").json()
    assert all(item["id"] != connection_id for item in rows_after)


def test_notifications_email_connections_outlook_token_web(client: TestClient) -> None:
    created = client.post(
        "/api/notifications/email/connections",
        json={
            "actor": "ops-admin",
            "provider": "OUTLOOK_GRAPH",
            "inbox_address": "ui.outlook@example.test",
            "config": {
                "tenant_id": "tenant-ui",
                "client_id": "client-ui",
                "mailbox": "ui.outlook@example.test",
                "graph_mock_pages": [{"cursor": "START", "messages": [], "next_cursor": None}],
            },
        },
    )
    assert created.status_code == 200
    connection_id = created.json()["id"]

    set_token = client.post(
        f"/notifications/email/connections/{connection_id}/outlook/token",
        data={"access_token": "ui-token", "refresh_token": "ui-refresh", "expires_at": "2030-01-01T00:00:00Z"},
        follow_redirects=False,
    )
    assert set_token.status_code == 303

    rows = client.get("/api/notifications/email/connections").json()
    row = next(item for item in rows if item["id"] == connection_id)
    assert "***REDACTED_REF***" in row["config_json"]


def test_notifications_email_connections_outlook_refresh_web(client: TestClient) -> None:
    created = client.post(
        "/api/notifications/email/connections",
        json={
            "actor": "ops-admin",
            "provider": "OUTLOOK_GRAPH",
            "inbox_address": "ui.outlook.refresh@example.test",
            "config": {
                "tenant_id": "tenant-ui-r",
                "client_id": "client-ui-r",
                "mailbox": "ui.outlook.refresh@example.test",
                "access_token": "stale-ui-token",
                "refresh_token": "stale-ui-refresh",
                "token_expires_at": "2000-01-01T00:00:00Z",
                "graph_mock_refresh": {"access_token": "ui-fresh-token", "expires_in": 3600},
                "graph_mock_pages": [{"cursor": "START", "messages": [], "next_cursor": None}],
            },
        },
    )
    assert created.status_code == 200
    connection_id = created.json()["id"]

    refreshed = client.post(
        f"/notifications/email/connections/{connection_id}/outlook/refresh",
        data={"force": "true"},
        follow_redirects=False,
    )
    assert refreshed.status_code == 303

    rows = client.get("/api/notifications/email/connections").json()
    row = next(item for item in rows if item["id"] == connection_id)
    assert "***REDACTED_REF***" in row["config_json"]
