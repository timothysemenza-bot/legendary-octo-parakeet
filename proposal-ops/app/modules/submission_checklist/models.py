import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class SubmissionChecklist(Base):
    __tablename__ = "submission_checklists"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")  # OPEN|READY|LOCKED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    items: Mapped[list["SubmissionChecklistItem"]] = relationship(back_populates="checklist")


class SubmissionChecklistItem(Base):
    __tablename__ = "submission_checklist_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    checklist_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("submission_checklists.id"), nullable=False, index=True
    )
    item_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    item_label: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")  # PENDING|COMPLETE|BLOCKED
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    checklist: Mapped[SubmissionChecklist] = relationship(back_populates="items")

