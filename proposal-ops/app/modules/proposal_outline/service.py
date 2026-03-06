import json
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.modules.proposal_outline.models import ProposalOutline
from app.modules.proposal_outline.schemas import ProposalOutlineGenerateRequest, ProposalOutlineSection
from app.modules.rfp_parser.models import ComplianceMatrixRow, Requirement


class ProposalOutlineService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest(self, opportunity_id: str) -> ProposalOutline | None:
        stmt = (
            select(ProposalOutline)
            .where(ProposalOutline.opportunity_id == opportunity_id)
            .order_by(ProposalOutline.version.desc(), ProposalOutline.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def list_versions(self, opportunity_id: str) -> list[ProposalOutline]:
        stmt = (
            select(ProposalOutline)
            .where(ProposalOutline.opportunity_id == opportunity_id)
            .order_by(ProposalOutline.version.desc(), ProposalOutline.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def parse_sections(self, outline: ProposalOutline) -> list[ProposalOutlineSection]:
        raw = json.loads(outline.sections_json)
        return [ProposalOutlineSection(**row) for row in raw]

    def _build_sections(self, opportunity_id: str, *, include_unmapped: bool) -> list[ProposalOutlineSection]:
        stmt = (
            select(ComplianceMatrixRow, Requirement)
            .join(Requirement, ComplianceMatrixRow.requirement_id == Requirement.id)
            .where(ComplianceMatrixRow.opportunity_id == opportunity_id)
            .order_by(ComplianceMatrixRow.proposal_section.asc(), Requirement.requirement_code.asc())
        )
        rows = self.db.execute(stmt).all()
        grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
        for matrix_row, _req in rows:
            if not include_unmapped and matrix_row.status == "UNMAPPED":
                continue
            key = (matrix_row.proposal_section, matrix_row.owner)
            grouped[key].append(matrix_row.requirement_id)

        sections: list[ProposalOutlineSection] = []
        for idx, ((proposal_section, owner), requirement_ids) in enumerate(grouped.items(), start=1):
            sections.append(
                ProposalOutlineSection(
                    sequence=idx,
                    proposal_section=proposal_section,
                    owner=owner,
                    requirement_ids=requirement_ids,
                    requirement_count=len(requirement_ids),
                )
            )
        return sections

    def generate(self, opportunity_id: str, payload: ProposalOutlineGenerateRequest) -> ProposalOutline:
        sections = self._build_sections(opportunity_id, include_unmapped=payload.include_unmapped)
        if not sections:
            raise ValueError("No compliance matrix rows available to generate outline")
        latest = self.get_latest(opportunity_id)
        next_version = 1 if latest is None else latest.version + 1
        outline = ProposalOutline(
            opportunity_id=opportunity_id,
            version=next_version,
            source="GENERATED",
            sections_json=json.dumps([s.model_dump() for s in sections]),
        )
        self.db.add(outline)
        self.db.flush()
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=payload.actor,
            action="proposal_outline_generated",
            before_state_json=json.dumps(
                {"previous_outline_id": latest.id if latest else None, "previous_version": latest.version if latest else None}
            ),
            after_state_json=json.dumps({"outline_id": outline.id, "version": outline.version, "section_count": len(sections)}),
        )
        self.db.commit()
        self.db.refresh(outline)
        return outline
