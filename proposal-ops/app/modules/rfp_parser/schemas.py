from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RfpParseRequest(BaseModel):
    raw_text: str = Field(min_length=20)
    source_filename: str = Field(default="manual-input.txt")
    actor: str = Field(default="operator")


class RequirementRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    requirement_code: str
    requirement_text: str
    category: str
    requirement_type: str
    mandatory: bool
    created_at: datetime


class RfpParseResponse(BaseModel):
    solicitation_id: str
    opportunity_id: str
    requirement_count: int
    extracted_deadline: str | None
    extracted_evaluation_criteria: str | None
    extracted_submission_instructions: str | None
    requirements: list[RequirementRecord]
