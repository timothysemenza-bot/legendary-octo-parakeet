from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProposalOutlineSection(BaseModel):
    sequence: int = Field(ge=1)
    proposal_section: str
    owner: str
    requirement_ids: list[str]
    requirement_count: int = Field(ge=0)


class ProposalOutlineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    opportunity_id: str
    version: int
    source: str
    sections: list[ProposalOutlineSection]
    created_at: datetime


class ProposalOutlineGenerateRequest(BaseModel):
    actor: str = Field(default="operator", min_length=2, max_length=100)
    include_unmapped: bool = False


class ProposalOutlineManualSectionInput(BaseModel):
    sequence: int = Field(ge=1)
    proposal_section: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    requirement_ids: list[str]


class ProposalOutlineManualCreateRequest(BaseModel):
    actor: str = Field(default="operator", min_length=2, max_length=100)
    sections: list[ProposalOutlineManualSectionInput] = Field(min_length=1)
