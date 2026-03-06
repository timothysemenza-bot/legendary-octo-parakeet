import json
from sqlalchemy import text
from fastapi.testclient import TestClient

from app.core.db import engine


def _create_opportunity(client: TestClient, *, name: str = "Notification Pursuit") -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": name,
            "client": "Alert Client",
            "estimated_contract_value": 600000,
            "lead_time_days": 28,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 62,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def _age_opportunity_days(opportunity_id: str, days: int) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE opportunities SET updated_at = datetime('now', :offset) WHERE id = :opportunity_id"
            ),
            {"offset": f"-{days} day", "opportunity_id": opportunity_id},
        )


def test_notification_scan_emits_sla_breach_and_deduplicates(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    _age_opportunity_days(opportunity_id, 5)

    first = client.post("/api/notifications/scan", json={"actor": "ops-bot"})
    assert first.status_code == 200
    payload = first.json()
    assert any(item["notification_type"] == "SLA_BREACH" for item in payload)
    assert any(item["notification_type"] == "SLA_ESCALATION" for item in payload)
    escalation = next(item for item in payload if item["notification_type"] == "SLA_ESCALATION")
    assert escalation["escalation_tier"] is not None

    second = client.post("/api/notifications/scan", json={"actor": "ops-bot"})
    assert second.status_code == 200
    assert second.json() == []

    open_events = client.get("/api/notifications").json()
    assert any(item["opportunity_id"] == opportunity_id for item in open_events)


def test_notification_scan_emits_blocker_escalation_for_gate_c(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client, name="Blocker Pursuit")
    client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_A",
            "decision": "APPROVED",
            "decider": "pm-1",
            "decider_role": "proposal_manager",
            "rationale": "Proceed.",
        },
    )
    client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_B",
            "decision": "APPROVED",
            "decider": "strategy-1",
            "decider_role": "capture_strategy_lead",
            "rationale": "Proceed.",
        },
    )

    scan = client.post("/api/notifications/scan", json={"actor": "ops-bot"})
    assert scan.status_code == 200
    emitted = scan.json()
    assert any(item["notification_type"] == "BLOCKER_ESCALATION" for item in emitted)


def test_notification_routing_targets_users_by_role(client: TestClient) -> None:
    user = client.post(
        "/api/users",
        json={"display_name": "Exec Approver", "email": "exec.approver@example.test"},
    ).json()
    assign = client.post(
        f"/api/users/{user['id']}/roles",
        json={"role": "executive_approver", "scope_type": "GLOBAL", "scope_id": None},
    )
    assert assign.status_code == 200

    opportunity_id = _create_opportunity(client, name="Routing Pursuit")
    _age_opportunity_days(opportunity_id, 5)

    scan = client.post("/api/notifications/scan", json={"actor": "ops-bot"})
    assert scan.status_code == 200
    events = scan.json()
    breach = next(item for item in events if item["notification_type"] == "SLA_BREACH")
    assert breach["recipients_json"] is not None
    assert "exec.approver@example.test" in breach["recipients_json"]


def test_notification_acknowledge_changes_status(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client, name="Ack Pursuit")
    _age_opportunity_days(opportunity_id, 5)
    client.post("/api/notifications/scan", json={"actor": "ops-bot"})
    open_events = client.get("/api/notifications").json()
    assert open_events
    target = open_events[0]

    ack = client.post(f"/api/notifications/{target['id']}/ack", json={"actor": "ops-user"})
    assert ack.status_code == 200
    assert ack.json()["status"] == "ACKNOWLEDGED"

    remaining_open = client.get("/api/notifications").json()
    assert all(item["id"] != target["id"] for item in remaining_open)


def test_notification_dispatch_creates_delivery_logs(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client, name="Dispatch Pursuit")
    _age_opportunity_days(opportunity_id, 5)
    client.post("/api/notifications/scan", json={"actor": "ops-bot"})

    dispatch = client.post("/api/notifications/dispatch", json={"actor": "dispatcher", "channels": ["console"]})
    assert dispatch.status_code == 200
    deliveries = dispatch.json()
    assert deliveries
    assert all(item["status"] == "SENT" for item in deliveries)
    assert all(item["channel"] == "console" for item in deliveries)

    listed = client.get("/api/notifications/deliveries")
    assert listed.status_code == 200
    assert listed.json()


def test_notification_delivery_retry_flow_for_failed_email(client: TestClient) -> None:
    # Force a routed recipient that will fail email adapter.
    user = client.post(
        "/api/users",
        json={"display_name": "Fail PM", "email": "fail.delivery@example.test"},
    ).json()
    client.post(
        f"/api/users/{user['id']}/roles",
        json={"role": "proposal_manager", "scope_type": "GLOBAL", "scope_id": None},
    )
    opportunity_id = _create_opportunity(client, name="Retry Pursuit")
    _age_opportunity_days(opportunity_id, 5)
    client.post("/api/notifications/scan", json={"actor": "ops-bot"})

    dispatch = client.post("/api/notifications/dispatch", json={"actor": "dispatcher", "channels": ["email"]})
    assert dispatch.status_code == 200
    rows = dispatch.json()
    assert any(item["status"] in {"RETRY_PENDING", "FAILED"} for item in rows)
    failed = next(item for item in rows if item["status"] in {"RETRY_PENDING", "FAILED"})
    assert failed["last_error_code"] in {"VALIDATION", "TRANSIENT_NETWORK", "UNKNOWN"}

    retry = client.post(f"/api/notifications/deliveries/{failed['id']}/retry", json={"actor": "dispatcher"})
    assert retry.status_code == 200
    assert retry.json()["attempt_count"] >= 2


def test_notification_policy_api_get_schema_get_and_update(client: TestClient) -> None:
    schema = client.get("/api/notifications/policy/schema")
    assert schema.status_code == 200
    assert "required" in schema.json()

    current = client.get("/api/notifications/policy")
    assert current.status_code == 200
    current_payload = current.json()
    assert current_payload["policy_key"] == "default"

    invalid = client.put(
        "/api/notifications/policy",
        json={
            "actor": "policy-admin",
            "policy": {"routing": {}},
        },
    )
    assert invalid.status_code == 422

    valid_policy = {
        "global_thresholds": {
            "reminder_days_before_sla": 2,
            "escalation_tiers": [1, 2, 5],
        },
        "client_threshold_overrides": {
            "Alert Client": {"reminder_days_before_sla": 1, "escalation_tiers": [1, 3]}
        },
        "routing": {
            "REMINDER": {"roles": ["proposal_manager"]},
            "SLA_BREACH": {"roles": ["proposal_manager", "executive_approver"]},
            "BLOCKER_ESCALATION": {"roles": ["compliance_lead", "review_lead"]},
            "SLA_ESCALATION": {"roles": ["executive_approver"]},
        },
    }
    updated = client.put(
        "/api/notifications/policy",
        json={"actor": "policy-admin", "policy": valid_policy},
    )
    assert updated.status_code == 200
    assert "\"reminder_days_before_sla\": 2" in updated.json()["policy_json"]


def test_client_policy_mapping_changes_scan_thresholds(client: TestClient) -> None:
    # Create a second policy with tighter reminder threshold.
    custom_policy = {
        "global_thresholds": {"reminder_days_before_sla": 5, "escalation_tiers": [1]},
        "client_threshold_overrides": {},
        "routing": {
            "REMINDER": {"roles": ["proposal_manager"]},
            "SLA_BREACH": {"roles": ["proposal_manager"]},
            "BLOCKER_ESCALATION": {"roles": ["compliance_lead"]},
            "SLA_ESCALATION": {"roles": ["executive_approver"]},
        },
    }
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO notification_policy_configs (id, policy_key, policy_json, updated_by, created_at, updated_at) "
                "VALUES ('pol_custom_1', 'custom_high_alert', :policy_json, 'test', datetime('now'), datetime('now'))"
            ),
            {"policy_json": json.dumps(custom_policy)},
        )
        conn.execute(
            text(
                "INSERT INTO notification_policy_client_mappings (id, client_name, policy_key, updated_by, created_at, updated_at) "
                "VALUES ('map_1', 'Mapped Alert Client', 'custom_high_alert', 'test', datetime('now'), datetime('now'))"
            )
        )

    opportunity_id = _create_opportunity(client, name="Mapped Policy Pursuit")
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE opportunities SET client='Mapped Alert Client', updated_at=datetime('now', '-2 day') WHERE id=:id"),
            {"id": opportunity_id},
        )
    scan = client.post("/api/notifications/scan", json={"actor": "ops-bot"})
    assert scan.status_code == 200
    emitted = scan.json()
    # With reminder_days_before_sla=5 and SLA=2 for Gate A, 2 days in stage should emit a REMINDER.
    assert any(item["notification_type"] == "REMINDER" for item in emitted)


def test_policy_mapping_api_upsert_list_delete(client: TestClient) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO notification_policy_configs (id, policy_key, policy_json, updated_by, created_at, updated_at) "
                "VALUES ('pol_custom_2', 'custom_map_policy', :policy_json, 'test', datetime('now'), datetime('now'))"
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

    bad = client.put(
        "/api/notifications/policy/mappings",
        json={"actor": "policy-admin", "client_name": "Acme", "policy_key": "does_not_exist"},
    )
    assert bad.status_code == 422

    upsert = client.put(
        "/api/notifications/policy/mappings",
        json={"actor": "policy-admin", "client_name": "Acme", "policy_key": "custom_map_policy"},
    )
    assert upsert.status_code == 200
    assert upsert.json()["client_name"] == "Acme"

    listed = client.get("/api/notifications/policy/mappings")
    assert listed.status_code == 200
    assert any(item["client_name"] == "Acme" for item in listed.json())

    deleted = client.delete("/api/notifications/policy/mappings/Acme")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True


def test_policy_config_lifecycle_api_create_clone_delete_with_guards(client: TestClient) -> None:
    base_policy = {
        "global_thresholds": {"reminder_days_before_sla": 1, "escalation_tiers": [1, 2]},
        "client_threshold_overrides": {},
        "routing": {
            "REMINDER": {"roles": ["proposal_manager"]},
            "SLA_BREACH": {"roles": ["proposal_manager"]},
            "BLOCKER_ESCALATION": {"roles": ["compliance_lead"]},
            "SLA_ESCALATION": {"roles": ["executive_approver"]},
        },
    }
    created = client.post(
        "/api/notifications/policy/configs",
        json={"actor": "policy-admin", "policy_key": "lifecycle_policy", "policy": base_policy},
    )
    assert created.status_code == 200

    listed = client.get("/api/notifications/policy/configs")
    assert listed.status_code == 200
    assert any(item["policy_key"] == "lifecycle_policy" for item in listed.json())

    cloned = client.post(
        "/api/notifications/policy/configs/lifecycle_policy/clone",
        json={"actor": "policy-admin", "target_policy_key": "lifecycle_policy_clone"},
    )
    assert cloned.status_code == 200
    assert cloned.json()["policy_key"] == "lifecycle_policy_clone"

    # Cannot delete default.
    default_delete = client.delete("/api/notifications/policy/configs/default")
    assert default_delete.status_code == 422

    # Cannot delete mapped policy.
    map_created = client.put(
        "/api/notifications/policy/mappings",
        json={"actor": "policy-admin", "client_name": "MappedClient", "policy_key": "lifecycle_policy_clone"},
    )
    assert map_created.status_code == 200
    mapped_delete = client.delete("/api/notifications/policy/configs/lifecycle_policy_clone")
    assert mapped_delete.status_code == 422

    # After unmapping, delete succeeds.
    client.delete("/api/notifications/policy/mappings/MappedClient")
    deleted = client.delete("/api/notifications/policy/configs/lifecycle_policy_clone")
    assert deleted.status_code == 200


def test_email_signal_ingest_list_apply_and_dismiss(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client, name="Email Signal Pursuit")

    ingested = client.post(
        "/api/notifications/email/ingest",
        json={
            "actor": "mailbot",
            "external_message_id": "msg-123",
            "opportunity_id": opportunity_id,
            "from_address": "capture.lead@example.test",
            "subject": "Bid approved - proceed",
            "body": "Team confirmed we are bidding. Please proceed.",
            "auto_apply": False,
        },
    )
    assert ingested.status_code == 200
    row = ingested.json()
    assert row["status"] == "PENDING"
    assert row["signal_type"] == "BID_STATUS"
    assert row["proposed_bid_status"] == "BID"

    listed = client.get("/api/notifications/email/updates", params={"status": "PENDING"})
    assert listed.status_code == 200
    assert any(item["id"] == row["id"] for item in listed.json())

    applied = client.post(f"/api/notifications/email/updates/{row['id']}/apply", json={"actor": "pm-user"})
    assert applied.status_code == 200
    assert applied.json()["status"] == "APPLIED"

    updated_opp = client.get(f"/api/opportunities/{opportunity_id}")
    assert updated_opp.status_code == 200
    assert updated_opp.json()["pursuit_recommendation"] == "BID"

    second = client.post(
        "/api/notifications/email/ingest",
        json={
            "actor": "mailbot",
            "external_message_id": "msg-124",
            "opportunity_id": opportunity_id,
            "from_address": "exec@example.test",
            "subject": "FYI only",
            "body": "General update with no explicit bid decision.",
            "auto_apply": False,
        },
    )
    assert second.status_code == 200
    second_row = second.json()
    dismissed = client.post(
        f"/api/notifications/email/updates/{second_row['id']}/dismiss",
        json={"actor": "pm-user"},
    )
    assert dismissed.status_code == 200
    assert dismissed.json()["status"] == "DISMISSED"


def test_email_connection_create_list_and_sync_manual_feed(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client, name="Connection Sync Pursuit")
    created = client.post(
        "/api/notifications/email/connections",
        json={
            "actor": "ops-admin",
            "provider": "MANUAL_FEED",
            "inbox_address": "ops.inbox@example.test",
            "config": {
                "seed_messages": [
                    {
                        "id": "conn-msg-001",
                        "opportunity_id": opportunity_id,
                        "from_address": "exec@example.test",
                        "subject": "Bid approved - proceed",
                        "body": "We are bidding this. Proceed.",
                        "auto_apply": True,
                    },
                    {
                        "id": "conn-msg-002",
                        "opportunity_id": opportunity_id,
                        "from_address": "exec@example.test",
                        "subject": "FYI",
                        "body": "No decision text here.",
                        "auto_apply": False,
                    },
                ]
            },
        },
    )
    assert created.status_code == 200
    connection = created.json()

    listed = client.get("/api/notifications/email/connections")
    assert listed.status_code == 200
    assert any(item["id"] == connection["id"] for item in listed.json())

    sync = client.post(
        f"/api/notifications/email/connections/{connection['id']}/sync",
        json={"actor": "mailbot"},
    )
    assert sync.status_code == 200
    sync_payload = sync.json()
    assert sync_payload["synced_count"] == 2
    assert sync_payload["applied_count"] >= 1

    # Second sync should skip duplicates by external message id.
    sync_again = client.post(
        f"/api/notifications/email/connections/{connection['id']}/sync",
        json={"actor": "mailbot"},
    )
    assert sync_again.status_code == 200
    assert sync_again.json()["skipped_count"] >= 2

    opp = client.get(f"/api/opportunities/{opportunity_id}")
    assert opp.status_code == 200
    assert opp.json()["pursuit_recommendation"] == "BID"


def test_email_connection_outlook_graph_sync_and_incremental_cursor(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client, name="Outlook Sync Pursuit")
    bad_create = client.post(
        "/api/notifications/email/connections",
        json={
            "actor": "ops-admin",
            "provider": "OUTLOOK_GRAPH",
            "inbox_address": "graph.inbox@example.test",
            "config": {"mailbox": "graph.inbox@example.test"},
        },
    )
    assert bad_create.status_code == 422

    created = client.post(
        "/api/notifications/email/connections",
        json={
            "actor": "ops-admin",
            "provider": "OUTLOOK_GRAPH",
            "inbox_address": "graph.valid@example.test",
            "config": {
                "tenant_id": "tenant-1",
                "client_id": "client-1",
                "mailbox": "graph.valid@example.test",
                "graph_mock_pages": [
                    {
                        "cursor": "START",
                        "messages": [
                            {
                                "id": "graph-msg-001",
                                "opportunity_id": opportunity_id,
                                "from_address": "capture.lead@example.test",
                                "subject": "Bid approved - proceed",
                                "body": "We are bidding this one.",
                                "auto_apply": True,
                            },
                            {
                                "id": "graph-msg-002",
                                "opportunity_id": opportunity_id,
                                "from_address": "capture.lead@example.test",
                                "subject": "No bid update",
                                "body": "No bid for this one.",
                                "auto_apply": False,
                            },
                        ],
                        "next_cursor": "page-2",
                    },
                    {"cursor": "page-2", "messages": [], "next_cursor": None},
                ],
            },
        },
    )
    assert created.status_code == 200
    connection_id = created.json()["id"]

    token_set = client.post(
        f"/api/notifications/email/connections/{connection_id}/outlook/token",
        json={
            "actor": "ops-admin",
            "access_token": "access-token-1",
            "refresh_token": "refresh-token-1",
            "expires_at": "2030-01-01T00:00:00Z",
        },
    )
    assert token_set.status_code == 200
    assert "***REDACTED_REF***" in token_set.json()["config_json"]
    with engine.begin() as conn:
        stored = conn.execute(
            text("SELECT config_json FROM email_connections WHERE id = :id"),
            {"id": connection_id},
        ).scalar_one()
    assert "access-token-1" not in stored
    assert "refresh-token-1" not in stored
    assert "access_token_ref" in stored
    assert "refresh_token_ref" in stored

    first_sync = client.post(
        f"/api/notifications/email/connections/{connection_id}/sync",
        json={"actor": "mailbot"},
    )
    assert first_sync.status_code == 200
    assert first_sync.json()["synced_count"] == 2
    assert first_sync.json()["skipped_count"] == 0

    second_sync = client.post(
        f"/api/notifications/email/connections/{connection_id}/sync",
        json={"actor": "mailbot"},
    )
    assert second_sync.status_code == 200
    assert second_sync.json()["synced_count"] == 0
    assert second_sync.json()["skipped_count"] == 0


def test_email_connection_update_pause_and_delete_lifecycle(client: TestClient) -> None:
    created = client.post(
        "/api/notifications/email/connections",
        json={
            "actor": "ops-admin",
            "provider": "MANUAL_FEED",
            "inbox_address": "lifecycle.inbox@example.test",
            "config": {"seed_messages": []},
        },
    )
    assert created.status_code == 200
    connection_id = created.json()["id"]

    # Active connections cannot be deleted directly.
    active_delete = client.delete(f"/api/notifications/email/connections/{connection_id}")
    assert active_delete.status_code == 422

    paused = client.put(
        f"/api/notifications/email/connections/{connection_id}",
        json={"actor": "ops-admin", "status": "PAUSED"},
    )
    assert paused.status_code == 200
    assert paused.json()["status"] == "PAUSED"

    # Sync blocked while paused.
    paused_sync = client.post(
        f"/api/notifications/email/connections/{connection_id}/sync",
        json={"actor": "mailbot"},
    )
    assert paused_sync.status_code == 422

    deleted = client.delete(f"/api/notifications/email/connections/{connection_id}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True


def test_outlook_token_refresh_endpoint_and_sync_auto_refresh(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client, name="Outlook Refresh Pursuit")
    created = client.post(
        "/api/notifications/email/connections",
        json={
            "actor": "ops-admin",
            "provider": "OUTLOOK_GRAPH",
            "inbox_address": "refresh.outlook@example.test",
            "config": {
                "tenant_id": "tenant-r",
                "client_id": "client-r",
                "mailbox": "refresh.outlook@example.test",
                "access_token": "stale-token",
                "refresh_token": "refresh-token-r",
                "token_expires_at": "2000-01-01T00:00:00Z",
                "graph_mock_refresh": {"access_token": "fresh-token", "expires_in": 3600},
                "graph_mock_pages": [
                    {
                        "cursor": "START",
                        "messages": [
                            {
                                "id": "refresh-msg-001",
                                "opportunity_id": opportunity_id,
                                "from_address": "capture@example.test",
                                "subject": "Bid approved - proceed",
                                "body": "We are bidding this one.",
                                "auto_apply": True,
                            }
                        ],
                        "next_cursor": None,
                    }
                ],
            },
        },
    )
    assert created.status_code == 200
    connection_id = created.json()["id"]

    refreshed = client.post(
        f"/api/notifications/email/connections/{connection_id}/outlook/refresh",
        json={"actor": "ops-admin", "force": True},
    )
    assert refreshed.status_code == 200
    assert "***REDACTED_REF***" in refreshed.json()["config_json"]
    with engine.begin() as conn:
        stored_after = conn.execute(
            text("SELECT config_json FROM email_connections WHERE id = :id"),
            {"id": connection_id},
        ).scalar_one()
    parsed = json.loads(stored_after)
    assert "access_token" not in parsed
    assert "refresh_token" not in parsed
    assert parsed.get("access_token_ref", "")
    assert parsed.get("refresh_token_ref", "")

    sync = client.post(
        f"/api/notifications/email/connections/{connection_id}/sync",
        json={"actor": "mailbot"},
    )
    assert sync.status_code == 200
    assert sync.json()["synced_count"] == 1
