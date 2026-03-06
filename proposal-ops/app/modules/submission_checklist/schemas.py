from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class SubmissionChecklistItemUpdateRequest(BaseModel):
    status: str = Field(pattern="^(PENDING|COMPLETE|BLOCKED)$")
    details: str | None = None
    actor: str = Field(default="operator")


class FileNameValidationRequest(BaseModel):
    file_names: list[str] = Field(default_factory=list)
    actor: str = Field(default="operator")


class FileNameValidationResponse(BaseModel):
    valid: bool
    invalid_names: list[str]
    message: str


class SubmissionChecklistItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    checklist_id: str
    item_code: str
    item_label: str
    category: str
    required: bool
    status: str
    details: str | None
    updated_by: str
    created_at: datetime
    updated_at: datetime


class SubmissionChecklistResponse(BaseModel):
    checklist_id: str
    opportunity_id: str
    status: str
    items: list[SubmissionChecklistItemResponse]


class SubmissionReadinessResponse(BaseModel):
    opportunity_id: str
    deadline: date | None
    days_to_deadline: int | None
    required_total: int
    required_complete: int
    blocked_items: int
    ready_for_gate_f: bool
    blockers: list[str]

