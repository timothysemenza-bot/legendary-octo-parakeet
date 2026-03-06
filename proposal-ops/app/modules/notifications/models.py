import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class NotificationEvent(Base):
    __tablename__ = "notification_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=True, index=True
    )
    gate_code: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    notification_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN", index=True)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    escalation_tier: Mapped[int | None] = mapped_column(nullable=True)
    recipients_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    acknowledged_by: Mapped[str | None] = mapped_column(String(100), nullable=True)


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notification_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notification_events.id"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    target: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    attempt_count: Mapped[int] = mapped_column(nullable=False, default=0)
    last_error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class NotificationPolicyConfig(Base):
    __tablename__ = "notification_policy_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_key: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True, default="default")
    policy_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class NotificationPolicyClientMapping(Base):
    __tablename__ = "notification_policy_client_mappings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    policy_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True, default="default")
    updated_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class EmailSignalUpdate(Base):
    __tablename__ = "email_signal_updates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    opportunity_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=True, index=True
    )
    from_address: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    proposed_bid_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    confidence: Mapped[float] = mapped_column(nullable=False, default=0.0)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING", index=True)
    auto_applied: Mapped[bool] = mapped_column(nullable=False, default=False)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    applied_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class EmailConnection(Base):
    __tablename__ = "email_connections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    inbox_address: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)
    config_json: Mapped[str] = mapped_column(Text, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
