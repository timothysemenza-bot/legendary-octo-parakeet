from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CapturePlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    version: int
    summary: str
    client_priorities: str
    competitive_landscape: str
    win_themes_draft: str
    solution_positioning: str
    timeline: str
    created_at: datetime


class CapturePlanUpdateRequest(BaseModel):
    summary: str = Field(min_length=3)
    client_priorities: str = Field(min_length=3)
    competitive_landscape: str = Field(min_length=3)
    win_themes_draft: str = Field(min_length=3)
    solution_positioning: str = Field(min_length=3)
    timeline: str = Field(min_length=3)
    actor: str = Field(default="operator", min_length=2, max_length=100)


class CapturePlanGenerateRequest(BaseModel):
    actor: str = Field(default="operator", min_length=2, max_length=100)


class CapturePlanReadinessResponse(BaseModel):
    opportunity_id: str
    capture_plan_id: str | None
    capture_plan_version: int | None
    solicitation_id: str | None
    matrix_row_count: int
    win_theme_count: int
    uses_bootstrap_template: bool
    ready_for_gate_b: bool
    blockers: list[str]
