from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.modules.opportunity_intake.models import Opportunity
from app.modules.rfp_parser.models import ComplianceMatrixRow, Requirement, Solicitation
from app.modules.rfp_parser.parser import parse_rfp_text
from app.modules.rfp_parser.schemas import RfpParseRequest, RfpParseResponse


class RfpParserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def parse_and_persist(self, opportunity_id: str, payload: RfpParseRequest) -> RfpParseResponse:
        opportunity = self.db.get(Opportunity, opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found.")

        parsed = parse_rfp_text(payload.raw_text)
        solicitation = Solicitation(
            opportunity_id=opportunity_id,
            source_filename=payload.source_filename,
            content_text=payload.raw_text,
            extracted_deadline=parsed["deadline"],
            extracted_evaluation_criteria=parsed["evaluation_criteria"],
            extracted_submission_instructions=parsed["submission_instructions"],
        )
        self.db.add(solicitation)
        self.db.flush()

        req_models: list[Requirement] = []
        for req in parsed["requirements"]:
            req_model = Requirement(
                solicitation_id=solicitation.id,
                requirement_code=req["requirement_code"],
                requirement_text=req["requirement_text"],
                category=req["category"],
                requirement_type=req["requirement_type"],
                mandatory=req["mandatory"],
            )
            self.db.add(req_model)
            self.db.flush()
            req_models.append(req_model)
            if req["requirement_type"] != "CONTEXT_ONLY":
                self.db.add(
                    ComplianceMatrixRow(
                        opportunity_id=opportunity_id,
                        requirement_id=req_model.id,
                        proposal_section=req["proposal_section"],
                        owner="UNASSIGNED",
                        status="UNMAPPED",
                    )
                )

        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=payload.actor,
            action="rfp_parsed",
            after_state_json=f'{{"solicitation_id":"{solicitation.id}","requirements":{len(req_models)}}}',
        )

        self.db.commit()
        return RfpParseResponse(
            solicitation_id=solicitation.id,
            opportunity_id=opportunity_id,
            requirement_count=len(req_models),
            extracted_deadline=solicitation.extracted_deadline,
            extracted_evaluation_criteria=solicitation.extracted_evaluation_criteria,
            extracted_submission_instructions=solicitation.extracted_submission_instructions,
            requirements=req_models,
        )

    def get_latest_solicitation(self, opportunity_id: str) -> Solicitation | None:
        stmt = (
            select(Solicitation)
            .where(Solicitation.opportunity_id == opportunity_id)
            .order_by(Solicitation.created_at.desc())
        )
        return self.db.scalars(stmt).first()
