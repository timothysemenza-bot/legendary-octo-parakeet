from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgePromotionDraft(BaseModel):
    asset_title: str = Field(min_length=2, max_length=255)
    asset_type: str = Field(min_length=2, max_length=50)
    rationale: str = Field(min_length=3)


class LessonsRecordCreateRequest(BaseModel):
    outcome: str = Field(pattern="^(WIN|LOSS|NO_AWARD|WITHDRAWN)$")
    root_causes: list[str] = Field(default_factory=list, min_length=1)
    actions: list[str] = Field(default_factory=list, min_length=1)
    promotions: list[KnowledgePromotionDraft] = Field(default_factory=list)
    created_by: str = Field(default="operator")


class LessonsRecordApproveRequest(BaseModel):
    actor: str = Field(default="knowledge_manager")


class KnowledgePromotionDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(APPROVED|REJECTED)$")
    actor: str = Field(default="knowledge_manager")


class KnowledgePromotionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    lessons_record_id: str
    asset_title: str
    asset_type: str
    rationale: str
    promotion_status: str
    created_by: str
    decided_by: str | None
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LessonsRecordResponse(BaseModel):
    id: str
    opportunity_id: str
    outcome: str
    root_causes: list[str]
    actions: list[str]
    status: str
    created_by: str
    approved_by: str | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    promotions: list[KnowledgePromotionResponse]


class KnowledgeReadinessResponse(BaseModel):
    opportunity_id: str
    gate_g_ready: bool
    blockers: list[str]

