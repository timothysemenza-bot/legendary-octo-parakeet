import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class LessonsLearnedRecord(Base):
    __tablename__ = "lessons_learned_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    outcome: Mapped[str] = mapped_column(String(30), nullable=False)  # WIN|LOSS|NO_AWARD|WITHDRAWN
    root_causes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    actions_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")  # DRAFT|APPROVED
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    promotions: Mapped[list["KnowledgePromotion"]] = relationship(back_populates="record")


class KnowledgePromotion(Base):
    __tablename__ = "knowledge_promotions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lessons_record_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("lessons_learned_records.id"), nullable=False, index=True
    )
    asset_title: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    promotion_status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    decided_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    record: Mapped[LessonsLearnedRecord] = relationship(back_populates="promotions")

