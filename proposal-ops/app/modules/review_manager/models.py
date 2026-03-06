import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ReviewCycle(Base):
    __tablename__ = "review_cycles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    review_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # PINK|RED|GOLD
    round_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")  # OPEN|CLOSED
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    comments: Mapped[list["ReviewComment"]] = relationship(back_populates="cycle")


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    review_cycle_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("review_cycles.id"), nullable=False, index=True
    )
    requirement_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("requirements.id"), nullable=True, index=True
    )
    section_code: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # LOW|MEDIUM|HIGH|CRITICAL
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN")  # OPEN|RESOLVED
    owner: Mapped[str] = mapped_column(String(100), nullable=False, default="UNASSIGNED")
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    cycle: Mapped[ReviewCycle] = relationship(back_populates="comments")

