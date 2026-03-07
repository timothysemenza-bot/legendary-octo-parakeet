from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RfpSourceDocumentInput(BaseModel):
    source_filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(min_length=1, max_length=100)
    parse_status: str = Field(pattern="^(PARSED|SKIPPED)$")
    skip_reason: str | None = None
    document_family_id: str | None = Field(default=None, min_length=36, max_length=36)
    upload_order: int = Field(ge=1)
    source_size_bytes: int = Field(ge=0)
    extracted_text_length: int = Field(ge=0)
    content_text: str | None = None
    source_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    storage_path: str | None = Field(default=None, max_length=255)
    source_payload: bytes | None = None


class RfpParseRequest(BaseModel):
    raw_text: str = Field(min_length=20)
    source_filename: str = Field(default="manual-input.txt")
    actor: str = Field(default="operator")
    source_documents: list[RfpSourceDocumentInput] = Field(default_factory=list)


class RfpReparseRequest(BaseModel):
    actor: str = Field(default="operator")
    source_solicitation_id: str | None = None
    source_documents: list[RfpSourceDocumentInput] = Field(default_factory=list)


class RfpSourceDocumentRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_filename: str
    content_type: str
    parse_status: str
    skip_reason: str | None
    document_family_id: str
    upload_order: int
    source_size_bytes: int
    extracted_text_length: int
    source_sha256: str | None
    has_stored_binary: bool
    created_at: datetime


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
    solicitation_version: int
    requirement_count: int
    extracted_deadline: str | None
    extracted_evaluation_criteria: str | None
    extracted_submission_instructions: str | None
    requirements: list[RequirementRecord]
    source_documents: list[RfpSourceDocumentRecord] = Field(default_factory=list)


class SolicitationVersionRecord(BaseModel):
    solicitation_id: str
    opportunity_id: str
    version: int
    source_filename: str
    requirement_count: int
    source_documents: list[RfpSourceDocumentRecord] = Field(default_factory=list)
    created_at: datetime


class RequirementTextChangeRecord(BaseModel):
    base_requirement_code: str
    compare_requirement_code: str
    base_requirement_text: str
    compare_requirement_text: str


class SourceDocumentDiffRecord(BaseModel):
    document_family_id: str
    label: str
    base_source_document_id: str | None = None
    compare_source_document_id: str | None = None
    base_source_filename: str | None = None
    compare_source_filename: str | None = None
    base_has_stored_binary: bool = False
    compare_has_stored_binary: bool = False


class SolicitationComparisonResponse(BaseModel):
    base_solicitation_id: str
    compare_solicitation_id: str
    base_version: int
    compare_version: int
    added_requirement_codes: list[str] = Field(default_factory=list)
    removed_requirement_codes: list[str] = Field(default_factory=list)
    added_documents: list[str] = Field(default_factory=list)
    removed_documents: list[str] = Field(default_factory=list)
    changed_documents: list[str] = Field(default_factory=list)
    added_document_records: list[SourceDocumentDiffRecord] = Field(default_factory=list)
    removed_document_records: list[SourceDocumentDiffRecord] = Field(default_factory=list)
    changed_document_records: list[SourceDocumentDiffRecord] = Field(default_factory=list)
    changed_requirements: list[RequirementTextChangeRecord] = Field(default_factory=list)
