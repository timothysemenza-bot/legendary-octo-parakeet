import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class SignalSource(Base):
    __tablename__ = "signal_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, default="OTHER", index=True)
    region: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    owner_scope: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    source_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    signal_events: Mapped[list["SignalEvent"]] = relationship(back_populates="source")


class SignalEvent(Base):
    __tablename__ = "signal_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("signal_sources.id"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(40), nullable=False, default="OTHER", index=True)
    signal_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    agency_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    program_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM", index=True)
    source_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    source: Mapped[SignalSource] = relationship(back_populates="signal_events")
    hypotheses: Mapped[list["OpportunityHypothesis"]] = relationship(back_populates="primary_signal_event")


class OpportunityHypothesis(Base):
    __tablename__ = "opportunity_hypotheses"
    __table_args__ = (
        UniqueConstraint("title", "buying_organization", name="uq_hypothesis_title_buying_org"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    geography: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    buying_organization: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    buying_organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    service_line: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    stage: Mapped[str] = mapped_column(String(40), nullable=False, default="MONITORING", index=True)
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIUM", index=True)
    expected_release_start: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    expected_release_end: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_signal_event_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("signal_events.id"),
        nullable=True,
        index=True,
    )
    recommended_contractor_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("contractors.id"),
        nullable=True,
        index=True,
    )
    converted_opportunity_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("opportunities.id"),
        nullable=True,
        index=True,
    )
    converted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    primary_signal_event: Mapped[SignalEvent | None] = relationship(back_populates="hypotheses")
    recommended_contractor: Mapped["Contractor | None"] = relationship(
        foreign_keys=[recommended_contractor_id]
    )
    converted_opportunity: Mapped["Opportunity | None"] = relationship(foreign_keys=[converted_opportunity_id])
