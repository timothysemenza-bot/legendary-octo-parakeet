from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReviewCycleCreateRequest(BaseModel):
    review_type: str = Field(pattern="^(PINK|RED|GOLD)$")
    round_number: int = Field(default=1, ge=1, le=20)
    actor: str = Field(default="operator")


class ReviewCycleCloseRequest(BaseModel):
    actor: str = Field(default="operator")


class ReviewCycleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    review_type: str
    round_number: int
    status: str
    started_at: datetime
    closed_at: datetime | None


class ReviewCommentCreateRequest(BaseModel):
    requirement_id: str | None = None
    section_code: str = Field(min_length=2, max_length=100)
    severity: str = Field(pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    comment_text: str = Field(min_length=3)
    owner: str = Field(default="UNASSIGNED", min_length=2, max_length=100)
    created_by: str = Field(default="reviewer")


class ReviewCommentResolveRequest(BaseModel):
    actor: str = Field(default="reviewer")


class ReviewCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    review_cycle_id: str
    requirement_id: str | None
    section_code: str
    severity: str
    comment_text: str
    resolution_status: str
    owner: str
    created_by: str
    created_at: datetime
    resolved_at: datetime | None


class ReviewReadinessResponse(BaseModel):
    opportunity_id: str
    gate_d_ready: bool
    gate_d_blockers: list[str]
    gate_e_ready: bool
    gate_e_blockers: list[str]

