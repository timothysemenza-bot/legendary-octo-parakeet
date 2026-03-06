import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Solicitation(Base):
    __tablename__ = "solicitations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_deadline: Mapped[str | None] = mapped_column(String(40), nullable=True)
    extracted_evaluation_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_submission_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    requirements: Mapped[list["Requirement"]] = relationship(back_populates="solicitation")


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    solicitation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("solicitations.id"), nullable=False, index=True
    )
    requirement_code: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    requirement_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="GENERAL")
    requirement_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="COMPLIANCE_REQUIRED", index=True
    )
    mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    solicitation: Mapped[Solicitation] = relationship(back_populates="requirements")
    compliance_rows: Mapped[list["ComplianceMatrixRow"]] = relationship(back_populates="requirement")


class ComplianceMatrixRow(Base):
    __tablename__ = "compliance_matrix_rows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    requirement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("requirements.id"), nullable=False, index=True
    )
    proposal_section: Mapped[str] = mapped_column(String(100), nullable=False, default="Unassigned")
    owner: Mapped[str] = mapped_column(String(100), nullable=False, default="UNASSIGNED")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNMAPPED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    requirement: Mapped[Requirement] = relationship(back_populates="compliance_rows")
