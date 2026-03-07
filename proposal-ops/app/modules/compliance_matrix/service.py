from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.modules.rfp_parser.models import ComplianceMatrixRow, Requirement, Solicitation


class ComplianceMatrixService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_rows(self, opportunity_id: str, *, include_context: bool = False) -> list[dict]:
        latest_solicitation = (
            self.db.query(Solicitation)
            .filter(Solicitation.opportunity_id == opportunity_id)
            .order_by(Solicitation.version.desc(), Solicitation.created_at.desc())
            .first()
        )
        if not latest_solicitation:
            return []

        stmt = (
            select(ComplianceMatrixRow, Requirement)
            .join(Requirement, ComplianceMatrixRow.requirement_id == Requirement.id)
            .where(ComplianceMatrixRow.opportunity_id == opportunity_id)
            .where(Requirement.solicitation_id == latest_solicitation.id)
            .order_by(Requirement.requirement_code.asc())
        )
        if include_context:
            pass
        else:
            stmt = stmt.where(Requirement.requirement_type != "CONTEXT_ONLY")
        rows = []
        for matrix_row, requirement in self.db.execute(stmt).all():
            rows.append(
                {
                    "id": matrix_row.id,
                    "opportunity_id": matrix_row.opportunity_id,
                    "requirement_id": matrix_row.requirement_id,
                    "requirement_code": requirement.requirement_code,
                    "requirement_text": requirement.requirement_text,
                    "requirement_type": requirement.requirement_type,
                    "proposal_section": matrix_row.proposal_section,
                    "owner": matrix_row.owner,
                    "status": matrix_row.status,
                    "updated_at": matrix_row.updated_at,
                }
            )
        return rows

    def matrix_quality(self, opportunity_id: str) -> dict:
        rows = self.list_rows(opportunity_id, include_context=False)
        total_rows = len(rows)
        compliance_required_rows = sum(1 for r in rows if r["requirement_type"] == "COMPLIANCE_REQUIRED")
        evaluation_signal_rows = sum(1 for r in rows if r["requirement_type"] == "EVALUATION_SIGNAL")
        complete_rows = sum(1 for r in rows if r["status"] == "COMPLETE")
        in_progress_rows = sum(1 for r in rows if r["status"] == "IN_PROGRESS")
        unmapped_rows = sum(1 for r in rows if r["status"] == "UNMAPPED")
        blocked_rows = sum(1 for r in rows if r["status"] == "BLOCKED")
        missing_owner_rows = sum(1 for r in rows if not r["owner"] or r["owner"].strip().upper() == "UNASSIGNED")

        blockers: list[str] = []
        if total_rows == 0:
            blockers.append("No compliance matrix rows generated.")
        if compliance_required_rows == 0 and total_rows > 0:
            blockers.append("No COMPLIANCE_REQUIRED rows found.")
        if unmapped_rows > 0:
            blockers.append(f"{unmapped_rows} rows remain UNMAPPED.")
        if blocked_rows > 0:
            blockers.append(f"{blocked_rows} rows are BLOCKED.")
        if missing_owner_rows > 0:
            blockers.append(f"{missing_owner_rows} rows have no assigned owner.")

        gate_c_ready = len(blockers) == 0
        return {
            "opportunity_id": opportunity_id,
            "total_rows": total_rows,
            "compliance_required_rows": compliance_required_rows,
            "evaluation_signal_rows": evaluation_signal_rows,
            "complete_rows": complete_rows,
            "in_progress_rows": in_progress_rows,
            "unmapped_rows": unmapped_rows,
            "blocked_rows": blocked_rows,
            "missing_owner_rows": missing_owner_rows,
            "gate_c_ready": gate_c_ready,
            "gate_c_blockers": blockers,
        }

    def update_row(
        self,
        row_id: str,
        *,
        proposal_section: str,
        owner: str,
        status: str,
        actor: str,
    ) -> dict | None:
        row = self.db.get(ComplianceMatrixRow, row_id)
        if not row:
            return None
        before_state = {
            "proposal_section": row.proposal_section,
            "owner": row.owner,
            "status": row.status,
        }
        row.proposal_section = proposal_section
        row.owner = owner
        row.status = status
        self.db.flush()

        log_audit_event(
            self.db,
            opportunity_id=row.opportunity_id,
            actor=actor,
            action="compliance_matrix_row_updated",
            before_state_json=str(before_state),
            after_state_json=str(
                {
                    "proposal_section": row.proposal_section,
                    "owner": row.owner,
                    "status": row.status,
                }
            ),
        )
        self.db.commit()

        req = self.db.get(Requirement, row.requirement_id)
        return {
            "id": row.id,
            "opportunity_id": row.opportunity_id,
            "requirement_id": row.requirement_id,
            "requirement_code": req.requirement_code if req else "UNKNOWN",
            "requirement_text": req.requirement_text if req else "",
            "requirement_type": req.requirement_type if req else "COMPLIANCE_REQUIRED",
            "proposal_section": row.proposal_section,
            "owner": row.owner,
            "status": row.status,
            "updated_at": row.updated_at,
        }
