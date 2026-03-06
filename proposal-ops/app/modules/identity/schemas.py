from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreateRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)


class RoleAssignmentRequest(BaseModel):
    role: str = Field(min_length=2, max_length=100)
    scope_type: str = Field(pattern="^(GLOBAL|OPPORTUNITY)$")
    scope_id: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str
    email: str
    status: str
    created_at: datetime
    updated_at: datetime


class UserRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    role: str
    scope_type: str
    scope_id: str | None
    created_at: datetime


class EffectiveRolesResponse(BaseModel):
    user_id: str
    opportunity_id: str
    roles: list[str]


class GatePermissionReport(BaseModel):
    gate_code: str
    allowed: bool
    required_roles: list[str]
    user_roles: list[str]
    matched_roles: list[str]
    reason: str


class AuthPermissionResponse(BaseModel):
    user_id: str
    opportunity_id: str
    reports: list[GatePermissionReport]
