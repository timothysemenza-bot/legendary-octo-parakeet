import json
import re
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.modules.compliance_matrix.service import ComplianceMatrixService
from app.modules.review_manager.service import ReviewManagerService
from app.modules.rfp_parser.models import Solicitation
from app.modules.submission_checklist.models import SubmissionChecklist, SubmissionChecklistItem
from app.modules.submission_checklist.schemas import (
    FileNameValidationRequest,
    FileNameValidationResponse,
    SubmissionChecklistItemUpdateRequest,
    SubmissionReadinessResponse,
)

DEFAULT_CHECKLIST_ITEMS = [
    ("SUBMISSION_CHECKLIST_REVIEWED", "Submission checklist reviewed and confirmed", "PROCESS"),
    ("COMPLIANCE_CERT_SIGNED", "Final compliance certification signed", "COMPLIANCE"),
    ("EXEC_APPROVAL_RECORDED", "Executive submission approval recorded", "APPROVAL"),
    ("FILE_NAMING_VALIDATED", "All file names validated against naming policy", "FILES"),
    ("DOCUMENT_STRUCTURE_VALIDATED", "Document structure/package validated", "FILES"),
    ("DEADLINE_CONFIRMED", "Submission deadline and timezone confirmed", "DEADLINE"),
]

FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+\.(pdf|docx|xlsx|xls|pptx|txt)$", re.IGNORECASE)


def _parse_deadline(raw: str | None) -> date | None:
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


class SubmissionChecklistService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _latest_solicitation(self, opportunity_id: str) -> Solicitation | None:
        stmt = (
            select(Solicitation)
            .where(Solicitation.opportunity_id == opportunity_id)
            .order_by(Solicitation.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def get_or_create_checklist(self, opportunity_id: str) -> SubmissionChecklist:
        stmt = (
            select(SubmissionChecklist)
            .where(SubmissionChecklist.opportunity_id == opportunity_id)
            .order_by(SubmissionChecklist.created_at.desc())
        )
        checklist = self.db.scalars(stmt).first()
        if checklist:
            return checklist

        checklist = SubmissionChecklist(opportunity_id=opportunity_id, status="OPEN")
        self.db.add(checklist)
        self.db.flush()
        for code, label, category in DEFAULT_CHECKLIST_ITEMS:
            self.db.add(
                SubmissionChecklistItem(
                    checklist_id=checklist.id,
                    item_code=code,
                    item_label=label,
                    category=category,
                    required=True,
                    status="PENDING",
                    updated_by="system",
                )
            )
        self.db.flush()
        self.db.commit()
        return checklist

    def list_checklist_items(self, opportunity_id: str) -> tuple[SubmissionChecklist, list[SubmissionChecklistItem]]:
        checklist = self.get_or_create_checklist(opportunity_id)
        stmt = (
            select(SubmissionChecklistItem)
            .where(SubmissionChecklistItem.checklist_id == checklist.id)
            .order_by(SubmissionChecklistItem.created_at.asc())
        )
        items = list(self.db.scalars(stmt))
        return checklist, items

    def update_item(
        self, opportunity_id: str, item_id: str, payload: SubmissionChecklistItemUpdateRequest
    ) -> SubmissionChecklistItem | None:
        checklist, _ = self.list_checklist_items(opportunity_id)
        item = self.db.get(SubmissionChecklistItem, item_id)
        if not item or item.checklist_id != checklist.id:
            return None

        before = {"status": item.status, "details": item.details}
        item.status = payload.status
        item.details = payload.details
        item.updated_by = payload.actor
        self.db.flush()

        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=payload.actor,
            action="submission_checklist_item_updated",
            before_state_json=json.dumps(before),
            after_state_json=json.dumps({"item_code": item.item_code, "status": item.status, "details": item.details}),
        )
        self.db.commit()
        return item

    def validate_file_names(
        self, opportunity_id: str, payload: FileNameValidationRequest
    ) -> FileNameValidationResponse:
        invalid = [name for name in payload.file_names if not FILENAME_PATTERN.match(name)]
        valid = len(invalid) == 0 and len(payload.file_names) > 0
        checklist, items = self.list_checklist_items(opportunity_id)
        file_item = next((i for i in items if i.item_code == "FILE_NAMING_VALIDATED"), None)
        if file_item:
            file_item.status = "COMPLETE" if valid else "BLOCKED"
            file_item.details = (
                f"Validated files: {', '.join(payload.file_names)}"
                if valid
                else f"Invalid names: {', '.join(invalid)}"
            )
            file_item.updated_by = payload.actor
            self.db.flush()

        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=payload.actor,
            action="submission_filename_validation_ran",
            after_state_json=json.dumps({"valid": valid, "invalid_names": invalid}),
        )
        self.db.commit()
        message = "All file names valid." if valid else "One or more file names failed validation."
        return FileNameValidationResponse(valid=valid, invalid_names=invalid, message=message)

    def readiness(self, opportunity_id: str) -> SubmissionReadinessResponse:
        checklist, items = self.list_checklist_items(opportunity_id)
        required_items = [i for i in items if i.required]
        required_complete = sum(1 for i in required_items if i.status == "COMPLETE")
        blocked_items = sum(1 for i in required_items if i.status == "BLOCKED")
        blockers: list[str] = []

        incomplete = [i.item_label for i in required_items if i.status != "COMPLETE"]
        if incomplete:
            blockers.append(f"{len(incomplete)} required checklist items are incomplete.")
        if blocked_items:
            blockers.append(f"{blocked_items} checklist items are BLOCKED.")

        compliance_quality = ComplianceMatrixService(self.db).matrix_quality(opportunity_id)
        if not compliance_quality["gate_c_ready"]:
            blockers.append(f"Compliance readiness not met: {'; '.join(compliance_quality['gate_c_blockers'])}")

        review_readiness = ReviewManagerService(self.db).review_readiness(opportunity_id)
        if not review_readiness.gate_d_ready:
            blockers.append(f"Gate D review readiness not met: {'; '.join(review_readiness.gate_d_blockers)}")
        if not review_readiness.gate_e_ready:
            blockers.append(f"Gate E review readiness not met: {'; '.join(review_readiness.gate_e_blockers)}")

        latest = self._latest_solicitation(opportunity_id)
        deadline = _parse_deadline(latest.extracted_deadline if latest else None)
        days_to_deadline = None
        if deadline:
            days_to_deadline = (deadline - date.today()).days
            if days_to_deadline < 0:
                blockers.append("Submission deadline has passed.")
        else:
            blockers.append("No parsed submission deadline available.")

        ready = len(blockers) == 0
        return SubmissionReadinessResponse(
            opportunity_id=opportunity_id,
            deadline=deadline,
            days_to_deadline=days_to_deadline,
            required_total=len(required_items),
            required_complete=required_complete,
            blocked_items=blocked_items,
            ready_for_gate_f=ready,
            blockers=blockers,
        )
