import json
import re
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.config import NOTIFICATION_POLICY
from app.core.config import NOTIFICATION_CHANNELS, NOTIFICATION_MAX_RETRY_ATTEMPTS, NOTIFICATION_RETRY_DELAY_MINUTES
from app.core.config import SECRET_STORE_KEY, SECRET_STORE_PATH
from app.core.policy import gate_policy
from app.core.secret_store import LocalSecretStore
from app.modules.identity.models import User, UserRoleAssignment
from app.modules.notifications.adapters import dispatch_notification
from app.modules.notifications.models import (
    EmailConnection,
    EmailSignalUpdate,
    NotificationDelivery,
    NotificationEvent,
    NotificationPolicyClientMapping,
    NotificationPolicyConfig,
)
from app.modules.notifications.outlook_graph_adapter import fetch_outlook_messages, refresh_outlook_token
from app.modules.opportunity_intake.models import Opportunity
from app.modules.notifications.policy_schema import NOTIFICATION_POLICY_SCHEMA, default_policy, validate_policy
from app.modules.opportunity_intake.service import OpportunityIntakeService


class NotificationService:
    _SENSITIVE_CONNECTION_KEYS = {"access_token", "refresh_token", "client_secret"}

    def __init__(self, db: Session) -> None:
        self.db = db
        self._active_policy_cache: dict[str, dict] = {}
        self._secret_store = LocalSecretStore(key=SECRET_STORE_KEY, file_path=SECRET_STORE_PATH)

    def get_policy_schema(self) -> dict:
        return NOTIFICATION_POLICY_SCHEMA

    def list_policy_configs(self) -> list[NotificationPolicyConfig]:
        stmt = select(NotificationPolicyConfig).order_by(NotificationPolicyConfig.policy_key.asc())
        return list(self.db.scalars(stmt))

    def get_policy_config(self, policy_key: str = "default") -> NotificationPolicyConfig:
        stmt = select(NotificationPolicyConfig).where(NotificationPolicyConfig.policy_key == policy_key)
        row = self.db.scalars(stmt).first()
        if row:
            return row
        row = NotificationPolicyConfig(
            policy_key=policy_key,
            policy_json=json.dumps(default_policy()),
            updated_by="system",
        )
        self.db.add(row)
        self.db.flush()
        self.db.commit()
        return row

    def get_policy_key_for_client(self, client: str) -> str:
        stmt = select(NotificationPolicyClientMapping).where(NotificationPolicyClientMapping.client_name == client)
        mapping = self.db.scalars(stmt).first()
        return mapping.policy_key if mapping else "default"

    def list_client_mappings(self) -> list[NotificationPolicyClientMapping]:
        stmt = select(NotificationPolicyClientMapping).order_by(NotificationPolicyClientMapping.client_name.asc())
        return list(self.db.scalars(stmt))

    def upsert_client_mapping(
        self, *, client_name: str, policy_key: str, actor: str
    ) -> tuple[NotificationPolicyClientMapping | None, list[str]]:
        normalized_client = client_name.strip()
        normalized_policy_key = policy_key.strip()
        if not normalized_client:
            return (None, ["client_name is required."])
        if not normalized_policy_key:
            return (None, ["policy_key is required."])
        policy_row = self.db.scalars(
            select(NotificationPolicyConfig).where(NotificationPolicyConfig.policy_key == normalized_policy_key)
        ).first()
        if not policy_row:
            return (None, [f"policy_key '{normalized_policy_key}' does not exist."])

        mapping = self.db.scalars(
            select(NotificationPolicyClientMapping).where(NotificationPolicyClientMapping.client_name == normalized_client)
        ).first()
        if not mapping:
            mapping = NotificationPolicyClientMapping(
                client_name=normalized_client,
                policy_key=normalized_policy_key,
                updated_by=actor,
            )
            self.db.add(mapping)
        else:
            mapping.policy_key = normalized_policy_key
            mapping.updated_by = actor
        self.db.flush()
        self.db.commit()
        # Bust cache for the target policy and default lookup.
        self._active_policy_cache.pop("default", None)
        self._active_policy_cache.pop(normalized_policy_key, None)
        return (mapping, [])

    def delete_client_mapping(self, *, client_name: str) -> bool:
        mapping = self.db.scalars(
            select(NotificationPolicyClientMapping).where(NotificationPolicyClientMapping.client_name == client_name)
        ).first()
        if not mapping:
            return False
        self.db.delete(mapping)
        self.db.flush()
        self.db.commit()
        return True

    def get_active_policy(self, client: str = "") -> dict:
        policy_key = self.get_policy_key_for_client(client) if client else "default"
        if policy_key in self._active_policy_cache:
            return self._active_policy_cache[policy_key]
        row = self.get_policy_config(policy_key)
        try:
            parsed = json.loads(row.policy_json)
            if isinstance(parsed, dict):
                self._active_policy_cache[policy_key] = parsed
                return parsed
        except json.JSONDecodeError:
            pass
        self._active_policy_cache[policy_key] = NOTIFICATION_POLICY
        return NOTIFICATION_POLICY

    def update_policy_config(self, policy: dict, *, actor: str) -> tuple[NotificationPolicyConfig | None, list[str]]:
        errors = validate_policy(policy)
        if errors:
            return (None, errors)
        row = self.get_policy_config("default")
        row.policy_json = json.dumps(policy)
        row.updated_by = actor
        self.db.flush()
        self.db.commit()
        self._active_policy_cache["default"] = policy
        return (row, [])

    def create_policy_config(
        self, *, policy_key: str, policy: dict, actor: str
    ) -> tuple[NotificationPolicyConfig | None, list[str]]:
        normalized_key = policy_key.strip()
        if not normalized_key:
            return (None, ["policy_key is required."])
        existing = self.db.scalars(
            select(NotificationPolicyConfig).where(NotificationPolicyConfig.policy_key == normalized_key)
        ).first()
        if existing:
            return (None, [f"policy_key '{normalized_key}' already exists."])
        errors = validate_policy(policy)
        if errors:
            return (None, errors)
        row = NotificationPolicyConfig(
            policy_key=normalized_key,
            policy_json=json.dumps(policy),
            updated_by=actor,
        )
        self.db.add(row)
        self.db.flush()
        self.db.commit()
        self._active_policy_cache[normalized_key] = policy
        return (row, [])

    def clone_policy_config(
        self, *, source_policy_key: str, target_policy_key: str, actor: str
    ) -> tuple[NotificationPolicyConfig | None, list[str]]:
        source_key = source_policy_key.strip()
        target_key = target_policy_key.strip()
        if not source_key or not target_key:
            return (None, ["source and target policy keys are required."])
        source = self.db.scalars(
            select(NotificationPolicyConfig).where(NotificationPolicyConfig.policy_key == source_key)
        ).first()
        if not source:
            return (None, [f"source policy_key '{source_key}' does not exist."])
        exists = self.db.scalars(
            select(NotificationPolicyConfig).where(NotificationPolicyConfig.policy_key == target_key)
        ).first()
        if exists:
            return (None, [f"target policy_key '{target_key}' already exists."])
        row = NotificationPolicyConfig(
            policy_key=target_key,
            policy_json=source.policy_json,
            updated_by=actor,
        )
        self.db.add(row)
        self.db.flush()
        self.db.commit()
        try:
            self._active_policy_cache[target_key] = json.loads(source.policy_json)
        except json.JSONDecodeError:
            self._active_policy_cache.pop(target_key, None)
        return (row, [])

    def delete_policy_config(self, *, policy_key: str) -> tuple[bool, list[str]]:
        normalized_key = policy_key.strip()
        if normalized_key == "default":
            return (False, ["default policy cannot be deleted."])
        row = self.db.scalars(
            select(NotificationPolicyConfig).where(NotificationPolicyConfig.policy_key == normalized_key)
        ).first()
        if not row:
            return (False, ["policy not found."])
        in_use = self.db.scalars(
            select(NotificationPolicyClientMapping).where(NotificationPolicyClientMapping.policy_key == normalized_key)
        ).first()
        if in_use:
            return (False, [f"policy_key '{normalized_key}' is mapped to one or more clients."])
        self.db.delete(row)
        self.db.flush()
        self.db.commit()
        self._active_policy_cache.pop(normalized_key, None)
        return (True, [])

    def _policy_thresholds(self, client: str) -> dict:
        policy = self.get_active_policy(client)
        base = (policy.get("global_thresholds") or {}).copy()
        overrides = (policy.get("client_threshold_overrides") or {}).get(client, {})
        if isinstance(overrides, dict):
            base.update(overrides)
        return base

    def _routing_roles(self, notification_type: str, gate_code: str, client: str) -> list[str]:
        policy = self.get_active_policy(client)
        routing_roles = (
            ((policy.get("routing") or {}).get(notification_type, {})).get("roles", []) or []
        )
        gate_roles = gate_policy(gate_code)["approvers"] + gate_policy(gate_code)["delegates"]
        merged = []
        seen = set()
        for role in gate_roles + routing_roles:
            normalized = role.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            merged.append(role)
        return merged

    def _resolve_recipients(self, opportunity_id: str, roles: list[str]) -> list[dict]:
        if not roles:
            return []
        stmt = (
            select(UserRoleAssignment, User)
            .join(User, UserRoleAssignment.user_id == User.id)
            .where(User.status == "ACTIVE")
            .where(UserRoleAssignment.role.in_(roles))
        )
        rows = self.db.execute(stmt).all()
        recipients: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for assignment, user in rows:
            applies = assignment.scope_type == "GLOBAL" or (
                assignment.scope_type == "OPPORTUNITY" and assignment.scope_id == opportunity_id
            )
            if not applies:
                continue
            key = (user.id, assignment.role.lower())
            if key in seen:
                continue
            seen.add(key)
            recipients.append(
                {
                    "user_id": user.id,
                    "display_name": user.display_name,
                    "email": user.email,
                    "role": assignment.role,
                    "scope_type": assignment.scope_type,
                }
            )
        return recipients

    def list_email_signal_updates(
        self, *, status: str | None = None, opportunity_id: str | None = None, limit: int = 200
    ) -> list[EmailSignalUpdate]:
        stmt = select(EmailSignalUpdate)
        if status:
            stmt = stmt.where(EmailSignalUpdate.status == status.upper())
        if opportunity_id:
            stmt = stmt.where(EmailSignalUpdate.opportunity_id == opportunity_id)
        stmt = stmt.order_by(EmailSignalUpdate.received_at.desc()).limit(limit)
        return list(self.db.scalars(stmt))

    def list_email_connections(self, *, status: str | None = None) -> list[EmailConnection]:
        stmt = select(EmailConnection)
        if status:
            stmt = stmt.where(EmailConnection.status == status.upper())
        stmt = stmt.order_by(EmailConnection.created_at.desc())
        return list(self.db.scalars(stmt))

    @classmethod
    def _redact_connection_config(cls, config: dict) -> dict:
        redacted = dict(config)
        for key in cls._SENSITIVE_CONNECTION_KEYS:
            if key in redacted and str(redacted[key]).strip():
                redacted[key] = "***REDACTED***"
        for key in ("access_token_ref", "refresh_token_ref", "client_secret_ref"):
            if key in redacted and str(redacted[key]).strip():
                redacted[key] = "***REDACTED_REF***"
        return redacted

    def _persist_secret_field(
        self, *, config: dict, raw_key: str, ref_key: str
    ) -> None:
        raw_value = str(config.get(raw_key, "") or "").strip()
        existing_ref = str(config.get(ref_key, "") or "").strip() or None
        if raw_value:
            config[ref_key] = self._secret_store.put(raw_value, ref=existing_ref)
        elif existing_ref:
            config[ref_key] = existing_ref
        else:
            config[ref_key] = ""
        if raw_key in config:
            del config[raw_key]

    def _resolve_secret_value(self, *, config: dict, raw_key: str, ref_key: str) -> str:
        raw_value = str(config.get(raw_key, "") or "").strip()
        if raw_value:
            return raw_value
        ref = str(config.get(ref_key, "") or "").strip()
        if not ref:
            return ""
        value = self._secret_store.get(ref)
        return value or ""

    @classmethod
    def connection_response_payload(cls, row: EmailConnection, *, redact_secrets: bool = True) -> dict:
        try:
            parsed = json.loads(row.config_json or "{}")
            if not isinstance(parsed, dict):
                parsed = {}
        except json.JSONDecodeError:
            parsed = {}
        safe_config = cls._redact_connection_config(parsed) if redact_secrets else parsed
        return {
            "id": row.id,
            "provider": row.provider,
            "inbox_address": row.inbox_address,
            "status": row.status,
            "config_json": json.dumps(safe_config),
            "last_synced_at": row.last_synced_at,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    def get_email_connection(self, connection_id: str) -> EmailConnection | None:
        return self.db.get(EmailConnection, connection_id)

    def create_email_connection(
        self, *, provider: str, inbox_address: str, config: dict, actor: str
    ) -> tuple[EmailConnection | None, list[str]]:
        normalized_provider = provider.strip().upper()
        normalized_inbox = inbox_address.strip().lower()
        if normalized_provider not in {"MANUAL_FEED", "IMAP", "OUTLOOK_GRAPH", "GMAIL_API"}:
            return (None, ["provider must be one of MANUAL_FEED, IMAP, OUTLOOK_GRAPH, GMAIL_API"])
        existing = self.db.scalars(
            select(EmailConnection).where(EmailConnection.inbox_address == normalized_inbox)
        ).first()
        if existing:
            return (None, [f"connection for inbox '{normalized_inbox}' already exists."])
        normalized_config, config_errors = self._validate_and_normalize_connection_config(
            provider=normalized_provider, config=config
        )
        if config_errors:
            return (None, config_errors)
        row = EmailConnection(
            provider=normalized_provider,
            inbox_address=normalized_inbox,
            status="ACTIVE",
            config_json=json.dumps(normalized_config),
        )
        self.db.add(row)
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=None,
            actor=actor,
            action="email_connection_created",
            after_state_json=json.dumps(
                {"connection_id": row.id, "provider": row.provider, "inbox_address": row.inbox_address}
            ),
        )
        self.db.commit()
        return (row, [])

    def update_email_connection(
        self, *, connection_id: str, status: str | None, config: dict | None, actor: str
    ) -> tuple[EmailConnection | None, list[str]]:
        row = self.db.get(EmailConnection, connection_id)
        if not row:
            return (None, ["connection not found"])
        if status is None and config is None:
            return (None, ["no changes requested"])

        desired_status = row.status
        if status is not None:
            normalized_status = status.strip().upper()
            if normalized_status not in {"ACTIVE", "PAUSED", "DISABLED"}:
                return (None, ["status must be ACTIVE, PAUSED, or DISABLED"])
            desired_status = normalized_status

        current_config = json.loads(row.config_json or "{}")
        desired_config = current_config if config is None else config
        normalized_config, config_errors = self._validate_and_normalize_connection_config(
            provider=row.provider, config=desired_config
        )
        if config_errors:
            return (None, config_errors)

        before = {
            "status": row.status,
            "config_json": row.config_json,
        }
        row.status = desired_status
        row.config_json = json.dumps(normalized_config)
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=None,
            actor=actor,
            action="email_connection_updated",
            before_state_json=json.dumps(before),
            after_state_json=json.dumps(
                {"connection_id": row.id, "status": row.status, "provider": row.provider, "inbox_address": row.inbox_address}
            ),
        )
        self.db.commit()
        return (row, [])

    def delete_email_connection(self, *, connection_id: str, actor: str) -> tuple[bool, list[str]]:
        row = self.db.get(EmailConnection, connection_id)
        if not row:
            return (False, ["connection not found"])
        if row.status == "ACTIVE":
            return (False, ["ACTIVE connection must be paused or disabled before deletion"])
        self.db.delete(row)
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=None,
            actor=actor,
            action="email_connection_deleted",
            after_state_json=json.dumps(
                {"connection_id": connection_id, "provider": row.provider, "inbox_address": row.inbox_address}
            ),
        )
        self.db.commit()
        return (True, [])

    def _validate_and_normalize_connection_config(self, *, provider: str, config: dict) -> tuple[dict, list[str]]:
        if not isinstance(config, dict):
            return ({}, ["config must be an object"])
        normalized = dict(config)
        if provider == "MANUAL_FEED":
            seed = normalized.get("seed_messages", [])
            if seed is None:
                seed = []
            if not isinstance(seed, list):
                return ({}, ["MANUAL_FEED config.seed_messages must be an array"])
            normalized["seed_messages"] = seed
            return (normalized, [])
        if provider == "OUTLOOK_GRAPH":
            missing: list[str] = []
            for required_key in ["tenant_id", "client_id", "mailbox"]:
                value = str(normalized.get(required_key, "")).strip()
                if not value:
                    missing.append(required_key)
                else:
                    normalized[required_key] = value
            mock_messages = normalized.get("mock_messages", [])
            if mock_messages is None:
                mock_messages = []
            if not isinstance(mock_messages, list):
                return ({}, ["OUTLOOK_GRAPH config.mock_messages must be an array"])
            normalized["mock_messages"] = mock_messages
            processed = normalized.get("processed_message_ids", [])
            if processed is None:
                processed = []
            if not isinstance(processed, list):
                return ({}, ["OUTLOOK_GRAPH config.processed_message_ids must be an array"])
            normalized["processed_message_ids"] = [str(item) for item in processed]
            mock_pages = normalized.get("graph_mock_pages", [])
            if mock_pages is None:
                mock_pages = []
            if not isinstance(mock_pages, list):
                return ({}, ["OUTLOOK_GRAPH config.graph_mock_pages must be an array"])
            normalized["graph_mock_pages"] = mock_pages
            normalized["graph_cursor"] = str(normalized.get("graph_cursor", "START") or "START")
            normalized["graph_next_link"] = str(normalized.get("graph_next_link", "") or "")
            self._persist_secret_field(config=normalized, raw_key="access_token", ref_key="access_token_ref")
            self._persist_secret_field(config=normalized, raw_key="refresh_token", ref_key="refresh_token_ref")
            self._persist_secret_field(config=normalized, raw_key="client_secret", ref_key="client_secret_ref")
            token_expires_at = normalized.get("token_expires_at")
            normalized["token_expires_at"] = str(token_expires_at) if token_expires_at is not None else ""
            if missing:
                return ({}, [f"OUTLOOK_GRAPH missing required config fields: {', '.join(missing)}"])
            return (normalized, [])
        # Other providers are stubs for now; allow creation but no sync support.
        return (normalized, [])

    def _resolve_opportunity_from_text(
        self, *, explicit_opportunity_id: str | None, subject: str, body: str
    ) -> Opportunity | None:
        if explicit_opportunity_id:
            return self.db.get(Opportunity, explicit_opportunity_id)

        combined = f"{subject}\n{body}"
        token = re.search(r"\[OPP:([0-9a-fA-F-]{36})\]", combined)
        if token:
            return self.db.get(Opportunity, token.group(1))

        lowered = combined.lower()
        opportunities = self.db.scalars(select(Opportunity)).all()
        matches = [opp for opp in opportunities if opp.name.lower() in lowered]
        if len(matches) == 1:
            return matches[0]
        return None

    def _extract_bid_signal(self, subject: str, body: str) -> tuple[str, str | None, float, str]:
        text = f"{subject}\n{body}".lower()
        if any(phrase in text for phrase in ["no bid", "do not bid", "decline to bid", "not pursuing"]):
            return ("BID_STATUS", "NO_BID", 0.94, "Detected explicit no-bid language in email body/subject.")
        if any(phrase in text for phrase in ["bid approved", "go bid", "pursue this", "we are bidding"]):
            return ("BID_STATUS", "BID", 0.9, "Detected explicit bid approval language in email body/subject.")
        if any(phrase in text for phrase in ["hold bid", "pause bid", "conditional bid", "bid on hold"]):
            return ("BID_STATUS", "CONDITIONAL", 0.82, "Detected hold/conditional bid language in email body/subject.")
        if "submitted" in text and "proposal" in text:
            return ("SUBMISSION_STATUS", None, 0.75, "Detected proposal submitted language.")
        return ("UNCLASSIFIED", None, 0.2, "No deterministic status signal matched parsing rules.")

    def set_outlook_connection_token(
        self,
        *,
        connection_id: str,
        access_token: str,
        refresh_token: str | None,
        expires_at: str | None,
        actor: str,
    ) -> tuple[EmailConnection | None, list[str]]:
        connection = self.db.get(EmailConnection, connection_id)
        if not connection:
            return (None, ["connection not found"])
        if connection.provider != "OUTLOOK_GRAPH":
            return (None, ["token updates are only supported for OUTLOOK_GRAPH connections"])
        try:
            config = json.loads(connection.config_json or "{}")
        except json.JSONDecodeError:
            return (None, ["connection config_json is invalid"])

        access_ref = str(config.get("access_token_ref", "") or "").strip() or None
        refresh_ref = str(config.get("refresh_token_ref", "") or "").strip() or None
        config["access_token_ref"] = self._secret_store.put(access_token.strip(), ref=access_ref)
        if (refresh_token or "").strip():
            config["refresh_token_ref"] = self._secret_store.put((refresh_token or "").strip(), ref=refresh_ref)
        config["token_expires_at"] = (expires_at or "").strip()
        normalized, errors = self._validate_and_normalize_connection_config(provider=connection.provider, config=config)
        if errors:
            return (None, errors)
        connection.config_json = json.dumps(normalized)
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=None,
            actor=actor,
            action="email_connection_token_updated",
            after_state_json=json.dumps(
                {"connection_id": connection.id, "provider": connection.provider, "token_expires_at": normalized.get("token_expires_at", "")}
            ),
        )
        self.db.commit()
        return (connection, [])

    @staticmethod
    def _parse_iso_utc(value: str) -> datetime | None:
        text = (value or "").strip()
        if not text:
            return None
        try:
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is not None:
                return parsed.replace(tzinfo=None)
            return parsed
        except Exception:
            return None

    def refresh_outlook_connection_token(
        self, *, connection_id: str, actor: str, force: bool = False
    ) -> tuple[EmailConnection | None, list[str]]:
        connection = self.db.get(EmailConnection, connection_id)
        if not connection:
            return (None, ["connection not found"])
        if connection.provider != "OUTLOOK_GRAPH":
            return (None, ["refresh is only supported for OUTLOOK_GRAPH connections"])

        try:
            config = json.loads(connection.config_json or "{}")
        except json.JSONDecodeError:
            return (None, ["connection config_json is invalid"])

        expires_at = self._parse_iso_utc(str(config.get("token_expires_at", "")))
        needs_refresh = force or expires_at is None or (expires_at - datetime.utcnow()) <= timedelta(minutes=5)
        if not needs_refresh:
            return (connection, [])
        refresh_config = dict(config)
        refresh_config["refresh_token"] = self._resolve_secret_value(
            config=config, raw_key="refresh_token", ref_key="refresh_token_ref"
        )
        refresh_config["client_secret"] = self._resolve_secret_value(
            config=config, raw_key="client_secret", ref_key="client_secret_ref"
        )
        result = refresh_outlook_token(refresh_config)
        if result.errors:
            return (None, result.errors)

        assert result.access_token is not None
        access_ref = str(config.get("access_token_ref", "") or "").strip() or None
        config["access_token_ref"] = self._secret_store.put(result.access_token, ref=access_ref)
        if result.refresh_token:
            refresh_ref = str(config.get("refresh_token_ref", "") or "").strip() or None
            config["refresh_token_ref"] = self._secret_store.put(result.refresh_token, ref=refresh_ref)
        expiry = datetime.utcnow() + timedelta(seconds=result.expires_in or 3600)
        config["token_expires_at"] = expiry.isoformat(timespec="seconds") + "Z"
        normalized, errors = self._validate_and_normalize_connection_config(provider=connection.provider, config=config)
        if errors:
            return (None, errors)
        connection.config_json = json.dumps(normalized)
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=None,
            actor=actor,
            action="email_connection_token_refreshed",
            after_state_json=json.dumps(
                {
                    "connection_id": connection.id,
                    "provider": connection.provider,
                    "token_expires_at": normalized.get("token_expires_at", ""),
                }
            ),
        )
        self.db.commit()
        return (connection, [])

    def ingest_email_signal(
        self,
        *,
        actor: str,
        external_message_id: str | None,
        opportunity_id: str | None,
        from_address: str,
        subject: str,
        body: str,
        auto_apply: bool,
    ) -> EmailSignalUpdate:
        normalized_message_id = (external_message_id or "").strip() or None
        if normalized_message_id:
            existing = self.db.scalars(
                select(EmailSignalUpdate).where(EmailSignalUpdate.external_message_id == normalized_message_id)
            ).first()
            if existing:
                return existing

        opportunity = self._resolve_opportunity_from_text(
            explicit_opportunity_id=opportunity_id,
            subject=subject,
            body=body,
        )
        signal_type, proposed_bid_status, confidence, rationale = self._extract_bid_signal(subject, body)

        update = EmailSignalUpdate(
            external_message_id=normalized_message_id,
            opportunity_id=opportunity.id if opportunity else None,
            from_address=from_address.strip(),
            subject=subject.strip(),
            body_excerpt=body.strip()[:2000],
            received_at=datetime.now(),
            signal_type=signal_type,
            proposed_bid_status=proposed_bid_status,
            confidence=confidence,
            rationale=rationale,
            status="PENDING",
            auto_applied=False,
        )
        self.db.add(update)
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=update.opportunity_id,
            actor=actor,
            action="email_signal_ingested",
            after_state_json=json.dumps(
                {
                    "email_update_id": update.id,
                    "signal_type": update.signal_type,
                    "proposed_bid_status": update.proposed_bid_status,
                    "confidence": update.confidence,
                    "opportunity_id": update.opportunity_id,
                }
            ),
        )
        self.db.commit()

        if auto_apply and update.signal_type == "BID_STATUS" and update.proposed_bid_status and update.confidence >= 0.9:
            applied = self.apply_email_signal_update(update.id, actor=actor, auto_applied=True)
            if applied:
                return applied
        return update

    def sync_email_connection(self, connection_id: str, *, actor: str) -> tuple[dict | None, list[str]]:
        connection = self.db.get(EmailConnection, connection_id)
        if not connection:
            return (None, ["connection not found"])
        if connection.status != "ACTIVE":
            return (None, ["connection is not ACTIVE"])
        try:
            config = json.loads(connection.config_json or "{}")
        except json.JSONDecodeError:
            return (None, ["connection config_json is invalid"])
        normalized_config, config_errors = self._validate_and_normalize_connection_config(
            provider=connection.provider, config=config
        )
        if config_errors:
            return (None, config_errors)
        messages: list[dict] = []
        if connection.provider == "MANUAL_FEED":
            messages = normalized_config.get("seed_messages", [])
        elif connection.provider == "OUTLOOK_GRAPH":
            refreshed, refresh_errors = self.refresh_outlook_connection_token(
                connection_id=connection_id,
                actor=actor,
                force=False,
            )
            if refresh_errors:
                return (None, refresh_errors)
            assert refreshed is not None
            connection = refreshed
            normalized_config, config_errors = self._validate_and_normalize_connection_config(
                provider=connection.provider, config=json.loads(connection.config_json or "{}")
            )
            if config_errors:
                return (None, config_errors)
            fetch_config = dict(normalized_config)
            fetch_config["access_token"] = self._resolve_secret_value(
                config=normalized_config, raw_key="access_token", ref_key="access_token_ref"
            )
            fetch = fetch_outlook_messages(fetch_config)
            if fetch.errors:
                return (None, fetch.errors)
            messages = fetch.messages
            if fetch.next_cursor is not None:
                normalized_config["graph_cursor"] = fetch.next_cursor
            normalized_config["graph_next_link"] = fetch.next_cursor or ""
        else:
            return (None, [f"provider '{connection.provider}' sync is not yet implemented"])

        synced_count = 0
        skipped_count = 0
        applied_count = 0
        newly_processed_ids: list[str] = []
        for item in messages:
            if not isinstance(item, dict):
                skipped_count += 1
                continue
            message_id = str(item.get("id", "")).strip() or None
            if message_id:
                existing = self.db.scalars(
                    select(EmailSignalUpdate).where(EmailSignalUpdate.external_message_id == message_id)
                ).first()
                if existing:
                    skipped_count += 1
                    continue
            row = self.ingest_email_signal(
                actor=actor,
                external_message_id=message_id,
                opportunity_id=item.get("opportunity_id"),
                from_address=str(item.get("from_address", connection.inbox_address)),
                subject=str(item.get("subject", "")),
                body=str(item.get("body", "")),
                auto_apply=bool(item.get("auto_apply", False)),
            )
            synced_count += 1
            if message_id and connection.provider == "OUTLOOK_GRAPH":
                newly_processed_ids.append(message_id)
            if row.status == "APPLIED":
                applied_count += 1

        if connection.provider == "OUTLOOK_GRAPH":
            processed_ids = set(normalized_config.get("processed_message_ids", []))
            for message_id in newly_processed_ids:
                processed_ids.add(message_id)
            normalized_config["processed_message_ids"] = sorted(processed_ids)
            connection.config_json = json.dumps(normalized_config)
        connection.last_synced_at = datetime.now()
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=None,
            actor=actor,
            action="email_connection_synced",
            after_state_json=json.dumps(
                {
                    "connection_id": connection.id,
                    "provider": connection.provider,
                    "synced_count": synced_count,
                    "skipped_count": skipped_count,
                    "applied_count": applied_count,
                }
            ),
        )
        self.db.commit()
        return (
            {
                "connection_id": connection.id,
                "provider": connection.provider,
                "inbox_address": connection.inbox_address,
                "synced_count": synced_count,
                "skipped_count": skipped_count,
                "applied_count": applied_count,
            },
            [],
        )

    def apply_email_signal_update(
        self, update_id: str, *, actor: str, auto_applied: bool = False
    ) -> EmailSignalUpdate | None:
        update = self.db.get(EmailSignalUpdate, update_id)
        if not update:
            return None
        if update.status != "PENDING":
            return update
        if update.signal_type != "BID_STATUS" or not update.proposed_bid_status or not update.opportunity_id:
            return update
        opportunity = self.db.get(Opportunity, update.opportunity_id)
        if not opportunity:
            return update

        before = {"pursuit_recommendation": opportunity.pursuit_recommendation}
        opportunity.pursuit_recommendation = update.proposed_bid_status
        update.status = "APPLIED"
        update.auto_applied = auto_applied
        update.applied_at = datetime.now()
        update.applied_by = actor
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=opportunity.id,
            actor=actor,
            action="email_signal_applied",
            before_state_json=json.dumps(before),
            after_state_json=json.dumps(
                {
                    "pursuit_recommendation": opportunity.pursuit_recommendation,
                    "email_update_id": update.id,
                    "auto_applied": auto_applied,
                }
            ),
        )
        self.db.commit()
        return update

    def dismiss_email_signal_update(self, update_id: str, *, actor: str) -> EmailSignalUpdate | None:
        update = self.db.get(EmailSignalUpdate, update_id)
        if not update:
            return None
        if update.status != "PENDING":
            return update
        update.status = "DISMISSED"
        update.applied_at = datetime.now()
        update.applied_by = actor
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=update.opportunity_id,
            actor=actor,
            action="email_signal_dismissed",
            after_state_json=json.dumps({"email_update_id": update.id}),
        )
        self.db.commit()
        return update

    def list_events(
        self,
        *,
        status: str = "OPEN",
        severity: str | None = None,
        notification_type: str | None = None,
        limit: int = 200,
    ) -> list[NotificationEvent]:
        stmt = select(NotificationEvent)
        if status:
            stmt = stmt.where(NotificationEvent.status == status.upper())
        if severity:
            stmt = stmt.where(NotificationEvent.severity == severity.upper())
        if notification_type:
            stmt = stmt.where(NotificationEvent.notification_type == notification_type.upper())
        stmt = stmt.order_by(NotificationEvent.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt))

    def list_deliveries(self, *, status: str | None = None, limit: int = 500) -> list[NotificationDelivery]:
        stmt = select(NotificationDelivery)
        if status:
            stmt = stmt.where(NotificationDelivery.status == status.upper())
        stmt = stmt.order_by(NotificationDelivery.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt))

    def _has_open_duplicate(
        self, opportunity_id: str, gate_code: str, notification_type: str, escalation_tier: int | None = None
    ) -> bool:
        stmt = select(NotificationEvent).where(
            NotificationEvent.opportunity_id == opportunity_id,
            NotificationEvent.gate_code == gate_code,
            NotificationEvent.notification_type == notification_type,
            NotificationEvent.status == "OPEN",
        )
        if escalation_tier is None:
            stmt = stmt.where(NotificationEvent.escalation_tier.is_(None))
        else:
            stmt = stmt.where(NotificationEvent.escalation_tier == escalation_tier)
        return self.db.scalars(stmt).first() is not None

    def _emit(
        self,
        *,
        opportunity_id: str,
        gate_code: str,
        client: str,
        notification_type: str,
        severity: str,
        message: str,
        details: dict,
        escalation_tier: int | None,
        actor: str,
    ) -> NotificationEvent | None:
        if self._has_open_duplicate(opportunity_id, gate_code, notification_type, escalation_tier):
            return None
        target_roles = self._routing_roles(notification_type, gate_code, client)
        recipients = self._resolve_recipients(opportunity_id, target_roles)
        event = NotificationEvent(
            opportunity_id=opportunity_id,
            gate_code=gate_code,
            notification_type=notification_type,
            severity=severity,
            status="OPEN",
            message=message,
            escalation_tier=escalation_tier,
            recipients_json=json.dumps(recipients),
            details_json=json.dumps(details),
        )
        self.db.add(event)
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=actor,
            action="notification_emitted",
            after_state_json=json.dumps(
                {
                    "notification_id": event.id,
                    "notification_type": notification_type,
                    "severity": severity,
                    "gate_code": gate_code,
                    "message": message,
                    "escalation_tier": escalation_tier,
                    "recipient_count": len(recipients),
                }
            ),
        )
        return event

    def _recipient_targets(self, event: NotificationEvent, channel: str) -> list[str]:
        recipients = []
        try:
            parsed = json.loads(event.recipients_json or "[]")
            if isinstance(parsed, list):
                recipients = [item for item in parsed if isinstance(item, dict)]
        except json.JSONDecodeError:
            recipients = []
        if channel == "webhook":
            return ["default-webhook-target"]
        if channel == "email":
            emails = [r.get("email", "") for r in recipients if r.get("email")]
            return emails or ["ops-local@example.test"]
        targets = [r.get("display_name") or r.get("email") for r in recipients if (r.get("display_name") or r.get("email"))]
        return targets or ["ops-local"]

    def _attempt_delivery(
        self, *, delivery: NotificationDelivery, event: NotificationEvent, actor: str
    ) -> NotificationDelivery:
        result = dispatch_notification(
            delivery.channel,
            delivery.target,
            subject=f"[{event.severity}] {event.notification_type}",
            body=event.message,
            payload={
                "notification_id": event.id,
                "notification_type": event.notification_type,
                "severity": event.severity,
                "message": event.message,
                "gate_code": event.gate_code,
                "opportunity_id": event.opportunity_id,
            },
        )
        delivery.attempt_count += 1
        delivery.last_attempt_at = datetime.now()
        delivery.last_error_code = result.error_code
        delivery.last_error = result.error or None
        delivery.last_response = result.response or None
        if result.success:
            delivery.status = "SENT"
            delivery.next_attempt_at = None
            log_audit_event(
                self.db,
                opportunity_id=event.opportunity_id,
                actor=actor,
                action="notification_dispatched",
                after_state_json=json.dumps(
                    {
                        "notification_id": event.id,
                        "delivery_id": delivery.id,
                        "channel": delivery.channel,
                        "target": delivery.target,
                        "attempt_count": delivery.attempt_count,
                    }
                ),
            )
        else:
            if (not result.retryable) or delivery.attempt_count >= NOTIFICATION_MAX_RETRY_ATTEMPTS:
                delivery.status = "FAILED"
                delivery.next_attempt_at = None
            else:
                delivery.status = "RETRY_PENDING"
                delivery.next_attempt_at = datetime.now() + timedelta(minutes=NOTIFICATION_RETRY_DELAY_MINUTES)
            log_audit_event(
                self.db,
                opportunity_id=event.opportunity_id,
                actor=actor,
                action="notification_delivery_failed",
                after_state_json=json.dumps(
                    {
                        "notification_id": event.id,
                        "delivery_id": delivery.id,
                        "channel": delivery.channel,
                        "target": delivery.target,
                        "attempt_count": delivery.attempt_count,
                        "error": result.error,
                        "error_code": result.error_code,
                        "status": delivery.status,
                    }
                ),
            )
        self.db.flush()
        return delivery

    def _find_delivery(self, notification_id: str, channel: str, target: str) -> NotificationDelivery | None:
        stmt = (
            select(NotificationDelivery)
            .where(NotificationDelivery.notification_id == notification_id)
            .where(NotificationDelivery.channel == channel)
            .where(NotificationDelivery.target == target)
            .order_by(NotificationDelivery.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def scan_and_emit(self, *, actor: str = "system") -> list[NotificationEvent]:
        inbox = OpportunityIntakeService(self.db).list_gate_inbox()
        emitted: list[NotificationEvent] = []
        for item in inbox:
            thresholds = self._policy_thresholds(item.client)
            reminder_days_before = int(thresholds.get("reminder_days_before_sla", 1))
            escalation_tiers = thresholds.get("escalation_tiers", [1, 3, 7]) or [1, 3, 7]

            if item.days_in_stage >= max(1, item.sla_days - reminder_days_before):
                reminder = self._emit(
                    opportunity_id=item.opportunity_id,
                    gate_code=item.gate_code,
                    client=item.client,
                    notification_type="REMINDER",
                    severity="WARN",
                    message=f"{item.gate_code} approaching SLA window for {item.opportunity_name}.",
                    details={
                        "days_in_stage": item.days_in_stage,
                        "sla_days": item.sla_days,
                        "gate_status": item.gate_status,
                    },
                    escalation_tier=None,
                    actor=actor,
                )
                if reminder:
                    emitted.append(reminder)

            if item.sla_breached:
                breach = self._emit(
                    opportunity_id=item.opportunity_id,
                    gate_code=item.gate_code,
                    client=item.client,
                    notification_type="SLA_BREACH",
                    severity="CRITICAL",
                    message=f"{item.gate_code} SLA breached for {item.opportunity_name}.",
                    details={
                        "days_in_stage": item.days_in_stage,
                        "sla_days": item.sla_days,
                        "gate_status": item.gate_status,
                    },
                    escalation_tier=None,
                    actor=actor,
                )
                if breach:
                    emitted.append(breach)

                over_by = max(0, item.days_in_stage - item.sla_days)
                for tier, threshold in enumerate(escalation_tiers, start=1):
                    if over_by >= int(threshold):
                        tier_event = self._emit(
                            opportunity_id=item.opportunity_id,
                            gate_code=item.gate_code,
                            client=item.client,
                            notification_type="SLA_ESCALATION",
                            severity="CRITICAL",
                            message=(
                                f"{item.gate_code} escalation tier {tier} for {item.opportunity_name} "
                                f"(SLA +{over_by} days)."
                            ),
                            details={
                                "days_in_stage": item.days_in_stage,
                                "sla_days": item.sla_days,
                                "over_by_days": over_by,
                                "tier_threshold_days": int(threshold),
                            },
                            escalation_tier=tier,
                            actor=actor,
                        )
                        if tier_event:
                            emitted.append(tier_event)

            if item.blockers:
                escalation = self._emit(
                    opportunity_id=item.opportunity_id,
                    gate_code=item.gate_code,
                    client=item.client,
                    notification_type="BLOCKER_ESCALATION",
                    severity="CRITICAL",
                    message=f"{item.gate_code} has blockers for {item.opportunity_name}.",
                    details={"blockers": item.blockers},
                    escalation_tier=None,
                    actor=actor,
                )
                if escalation:
                    emitted.append(escalation)

        self.db.commit()
        return emitted

    def dispatch(
        self, *, actor: str = "system", channels: list[str] | None = None
    ) -> list[NotificationDelivery]:
        active_channels = [c.lower() for c in (channels or NOTIFICATION_CHANNELS)]
        open_events = self.list_events(status="OPEN", limit=1000)
        now = datetime.now()
        attempted: list[NotificationDelivery] = []
        for event in open_events:
            for channel in active_channels:
                for target in self._recipient_targets(event, channel):
                    existing = self._find_delivery(event.id, channel, target)
                    if existing:
                        if existing.status == "SENT":
                            continue
                        if existing.status == "RETRY_PENDING" and existing.next_attempt_at and existing.next_attempt_at > now:
                            continue
                        delivery = existing
                    else:
                        delivery = NotificationDelivery(
                            notification_id=event.id,
                            channel=channel,
                            target=target,
                            status="PENDING",
                            attempt_count=0,
                        )
                        self.db.add(delivery)
                        self.db.flush()
                    attempted.append(self._attempt_delivery(delivery=delivery, event=event, actor=actor))
        self.db.commit()
        return attempted

    def retry_delivery(self, delivery_id: str, *, actor: str = "system") -> NotificationDelivery | None:
        delivery = self.db.get(NotificationDelivery, delivery_id)
        if not delivery:
            return None
        event = self.db.get(NotificationEvent, delivery.notification_id)
        if not event:
            return None
        retried = self._attempt_delivery(delivery=delivery, event=event, actor=actor)
        self.db.commit()
        return retried

    def acknowledge(self, notification_id: str, *, actor: str) -> NotificationEvent | None:
        event = self.db.get(NotificationEvent, notification_id)
        if not event:
            return None
        event.status = "ACKNOWLEDGED"
        event.acknowledged_at = datetime.now()
        event.acknowledged_by = actor
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=event.opportunity_id,
            actor=actor,
            action="notification_acknowledged",
            after_state_json=json.dumps(
                {"notification_id": event.id, "notification_type": event.notification_type, "gate_code": event.gate_code}
            ),
        )
        self.db.commit()
        return event
