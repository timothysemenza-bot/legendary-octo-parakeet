from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ComplianceMatrixRowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    requirement_id: str
    requirement_code: str
    requirement_text: str
    requirement_type: str
    proposal_section: str
    owner: str
    status: str
    updated_at: datetime


class ComplianceMatrixUpdateRequest(BaseModel):
    proposal_section: str = Field(min_length=2, max_length=100)
    owner: str = Field(min_length=2, max_length=100)
    status: str = Field(pattern="^(UNMAPPED|IN_PROGRESS|COMPLETE|BLOCKED)$")
    actor: str = Field(default="operator")


class ComplianceMatrixQualityResponse(BaseModel):
    opportunity_id: str
    total_rows: int
    compliance_required_rows: int
    evaluation_signal_rows: int
    complete_rows: int
    in_progress_rows: int
    unmapped_rows: int
    blocked_rows: int
    missing_owner_rows: int
    gate_c_ready: bool
    gate_c_blockers: list[str]
