from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationScanRequest(BaseModel):
    actor: str = Field(default="system")


class NotificationAckRequest(BaseModel):
    actor: str = Field(default="operator")


class NotificationDispatchRequest(BaseModel):
    actor: str = Field(default="system")
    channels: list[str] | None = None


class NotificationPolicyUpdateRequest(BaseModel):
    actor: str = Field(default="operator")
    policy: dict


class NotificationPolicyClientMappingUpsertRequest(BaseModel):
    actor: str = Field(default="operator")
    client_name: str = Field(min_length=1, max_length=255)
    policy_key: str = Field(min_length=1, max_length=80)


class NotificationPolicyCreateRequest(BaseModel):
    actor: str = Field(default="operator")
    policy_key: str = Field(min_length=1, max_length=80)
    policy: dict


class NotificationPolicyCloneRequest(BaseModel):
    actor: str = Field(default="operator")
    target_policy_key: str = Field(min_length=1, max_length=80)


class EmailSignalIngestRequest(BaseModel):
    actor: str = Field(default="email-agent")
    external_message_id: str | None = Field(default=None, max_length=255)
    opportunity_id: str | None = Field(default=None, max_length=36)
    from_address: str = Field(min_length=3, max_length=255)
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1)
    auto_apply: bool = False


class EmailSignalDecisionRequest(BaseModel):
    actor: str = Field(default="operator")


class EmailConnectionCreateRequest(BaseModel):
    actor: str = Field(default="operator")
    provider: str = Field(min_length=3, max_length=30)
    inbox_address: str = Field(min_length=3, max_length=255)
    config: dict = Field(default_factory=dict)


class EmailConnectionSyncRequest(BaseModel):
    actor: str = Field(default="email-agent")


class EmailConnectionUpdateRequest(BaseModel):
    actor: str = Field(default="operator")
    status: str | None = None
    config: dict | None = None


class OutlookTokenSetRequest(BaseModel):
    actor: str = Field(default="operator")
    access_token: str = Field(min_length=1)
    refresh_token: str | None = None
    expires_at: str | None = None


class OutlookTokenRefreshRequest(BaseModel):
    actor: str = Field(default="operator")
    force: bool = False


class NotificationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str | None
    gate_code: str | None
    notification_type: str
    severity: str
    status: str
    message: str
    escalation_tier: int | None
    recipients_json: str | None
    details_json: str | None
    created_at: datetime
    acknowledged_at: datetime | None
    acknowledged_by: str | None


class NotificationDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    notification_id: str
    channel: str
    target: str
    status: str
    attempt_count: int
    last_error_code: str | None
    last_error: str | None
    last_response: str | None
    last_attempt_at: datetime | None
    next_attempt_at: datetime | None
    created_at: datetime
    updated_at: datetime


class NotificationPolicyConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    policy_key: str
    policy_json: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class NotificationPolicyClientMappingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    client_name: str
    policy_key: str
    updated_by: str
    created_at: datetime
    updated_at: datetime


class EmailSignalUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    external_message_id: str | None
    opportunity_id: str | None
    from_address: str
    subject: str
    body_excerpt: str
    received_at: datetime
    signal_type: str
    proposed_bid_status: str | None
    confidence: float
    rationale: str
    status: str
    auto_applied: bool
    applied_at: datetime | None
    applied_by: str | None
    created_at: datetime
    updated_at: datetime


class EmailConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider: str
    inbox_address: str
    status: str
    config_json: str
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime


class EmailConnectionSyncResult(BaseModel):
    connection_id: str
    provider: str
    inbox_address: str
    synced_count: int
    skipped_count: int
    applied_count: int
