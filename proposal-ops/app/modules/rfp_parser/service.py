import json
import mimetypes
import re
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.core.config import RFP_SOURCE_STORAGE_DIR
from app.modules.opportunity_intake.models import Opportunity
from app.modules.rfp_parser.document_reader import extract_text_from_upload, extract_text_from_upload_batch
from app.modules.rfp_parser.models import ComplianceMatrixRow, Requirement, RfpSourceDocument, Solicitation
from app.modules.rfp_parser.parser import parse_rfp_text
from app.modules.rfp_parser.schemas import (
    RequirementTextChangeRecord,
    RfpParseRequest,
    RfpParseResponse,
    RfpReparseRequest,
    RfpStructuredFields,
    SourceDocumentDiffRecord,
    RfpSourceDocumentInput,
    RfpSourceDocumentRecord,
    SolicitationComparisonResponse,
    SolicitationVersionRecord,
)


SIMILARITY_STOPWORDS = {
    "the",
    "a",
    "an",
    "of",
    "to",
    "for",
    "and",
    "or",
    "in",
    "on",
    "by",
    "with",
    "as",
    "at",
    "be",
    "is",
    "are",
    "that",
    "this",
    "these",
    "those",
    "it",
    "its",
    "their",
    "all",
    "any",
    "from",
    "within",
    "through",
}


def _default_content_type(source_filename: str) -> str:
    guessed, _encoding = mimetypes.guess_type(source_filename)
    return guessed or "text/plain"


def _normalize_requirement_text(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"\s+", " ", lowered)
    lowered = re.sub(r"[^a-z0-9\s]", "", lowered)
    return lowered


def _requirement_similarity_tokens(value: str) -> set[str]:
    normalized = _normalize_requirement_text(value)
    tokens = []
    for token in normalized.split():
        if token.isdigit():
            continue
        if token in SIMILARITY_STOPWORDS:
            continue
        if len(token) > 4 and token.endswith("s"):
            token = token[:-1]
        tokens.append(token)
    return set(tokens)


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


def _storage_relative_path_for_sha(source_sha256: str) -> str:
    return f"rfp_source_documents/{source_sha256}.bin"


def _document_family_id(value: RfpSourceDocument | RfpSourceDocumentInput) -> str:
    family_id = getattr(value, "document_family_id", None)
    row_id = getattr(value, "id", None)
    return family_id or row_id or str(uuid4())


def _safe_json_object(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


class RfpParserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _latest_solicitation_stmt(self, opportunity_id: str):
        return (
            select(Solicitation)
            .where(Solicitation.opportunity_id == opportunity_id)
            .order_by(Solicitation.version.desc(), Solicitation.created_at.desc())
        )

    def _next_solicitation_version(self, opportunity_id: str) -> int:
        latest = self.db.scalars(self._latest_solicitation_stmt(opportunity_id)).first()
        return 1 if latest is None else latest.version + 1

    def _default_source_documents(self, payload: RfpParseRequest) -> list[RfpSourceDocumentInput]:
        return [
            RfpSourceDocumentInput(
                source_filename=payload.source_filename,
                content_type=_default_content_type(payload.source_filename),
                parse_status="PARSED",
                skip_reason=None,
                document_family_id=None,
                upload_order=1,
                source_size_bytes=len(payload.raw_text.encode("utf-8")),
                extracted_text_length=len(payload.raw_text.strip()),
                content_text=payload.raw_text.strip(),
            )
        ]

    def _write_source_payload(self, payload: bytes) -> tuple[str, str]:
        source_sha256 = sha256(payload).hexdigest()
        relative_path = _storage_relative_path_for_sha(source_sha256)
        RFP_SOURCE_STORAGE_DIR.mkdir(exist_ok=True)
        file_path = RFP_SOURCE_STORAGE_DIR / f"{source_sha256}.bin"
        if not file_path.exists():
            file_path.write_bytes(payload)
        return source_sha256, relative_path

    def _read_source_payload(self, storage_path: str | None) -> bytes | None:
        if not storage_path:
            return None
        file_path = Path(RFP_SOURCE_STORAGE_DIR.parent / storage_path)
        if not file_path.exists():
            return None
        return file_path.read_bytes()

    def _build_parse_response(
        self,
        *,
        opportunity_id: str,
        solicitation: Solicitation,
        requirements: list[Requirement],
        source_document_rows: list[RfpSourceDocument],
    ) -> RfpParseResponse:
        return RfpParseResponse(
            solicitation_id=solicitation.id,
            opportunity_id=opportunity_id,
            solicitation_version=solicitation.version,
            requirement_count=len(requirements),
            extracted_deadline=solicitation.extracted_deadline,
            extracted_evaluation_criteria=solicitation.extracted_evaluation_criteria,
            extracted_submission_instructions=solicitation.extracted_submission_instructions,
            structured_fields=RfpStructuredFields.model_validate(_safe_json_object(solicitation.structured_fields_json))
            if solicitation.structured_fields_json
            else None,
            field_provenance={
                key: [str(value) for value in values]
                for key, values in _safe_json_object(solicitation.field_provenance_json).items()
                if isinstance(values, list)
            },
            requirements=requirements,
            source_documents=[
                RfpSourceDocumentRecord.model_validate(row, from_attributes=True) for row in source_document_rows
            ],
        )

    def _source_document_inputs_from_rows(self, rows: list[RfpSourceDocument]) -> list[RfpSourceDocumentInput]:
        return [
            RfpSourceDocumentInput(
                source_filename=row.source_filename,
                content_type=row.content_type,
                parse_status=row.parse_status,
                skip_reason=row.skip_reason,
                document_family_id=_document_family_id(row),
                upload_order=row.upload_order,
                source_size_bytes=row.source_size_bytes,
                extracted_text_length=row.extracted_text_length,
                content_text=row.content_text,
                source_sha256=row.source_sha256,
                storage_path=row.storage_path,
            )
            for row in rows
        ]

    def _persist_source_documents(
        self,
        *,
        intake_rfp_draft_id: str | None = None,
        solicitation_id: str | None = None,
        source_documents: list[RfpSourceDocumentInput],
    ) -> list[RfpSourceDocument]:
        rows: list[RfpSourceDocument] = []
        for item in source_documents:
            source_sha256 = item.source_sha256
            storage_path = item.storage_path
            if item.source_payload is not None:
                source_sha256, storage_path = self._write_source_payload(item.source_payload)
            row = RfpSourceDocument(
                intake_rfp_draft_id=intake_rfp_draft_id,
                solicitation_id=solicitation_id,
                source_filename=item.source_filename,
                content_type=item.content_type,
                parse_status=item.parse_status,
                skip_reason=item.skip_reason,
                document_family_id=item.document_family_id or str(uuid4()),
                upload_order=item.upload_order,
                source_size_bytes=item.source_size_bytes,
                extracted_text_length=item.extracted_text_length,
                content_text=item.content_text,
                source_sha256=source_sha256,
                storage_path=storage_path,
            )
            self.db.add(row)
            self.db.flush()
            rows.append(row)
        return rows

    def _requirement_codes_for_solicitation(self, solicitation_id: str) -> list[str]:
        stmt = (
            select(Requirement.requirement_code)
            .where(Requirement.solicitation_id == solicitation_id)
            .order_by(Requirement.requirement_code.asc())
        )
        return list(self.db.scalars(stmt))

    def _requirements_for_solicitation(self, solicitation_id: str) -> list[Requirement]:
        stmt = (
            select(Requirement)
            .where(Requirement.solicitation_id == solicitation_id)
            .order_by(Requirement.requirement_code.asc(), Requirement.created_at.asc())
        )
        return list(self.db.scalars(stmt))

    def _extract_document_text_from_combined_text(
        self,
        *,
        combined_text: str,
        filename: str,
        next_filename: str | None,
    ) -> str | None:
        marker = f"Source file: {filename}\n"
        start = combined_text.find(marker)
        if start < 0:
            return None
        content_start = start + len(marker)
        if next_filename:
            next_marker = f"\n\nSource file: {next_filename}\n"
            end = combined_text.find(next_marker, content_start)
            if end >= 0:
                return combined_text[content_start:end].strip() or None
        return combined_text[content_start:].strip() or None

    def _resolved_source_document_inputs(
        self,
        *,
        solicitation: Solicitation,
        rows: list[RfpSourceDocument],
    ) -> list[RfpSourceDocumentInput]:
        parsed_rows = [row for row in rows if row.parse_status == "PARSED"]
        parsed_index = {row.id: idx for idx, row in enumerate(parsed_rows)}
        resolved: list[RfpSourceDocumentInput] = []
        for row in rows:
            content_text = row.content_text
            if row.parse_status == "PARSED":
                payload = self._read_source_payload(row.storage_path)
                if payload is not None:
                    try:
                        content_text = extract_text_from_upload(row.source_filename, payload).strip() or content_text
                    except RuntimeError:
                        content_text = content_text
                if not content_text:
                    next_filename = None
                    if row.id in parsed_index:
                        idx = parsed_index[row.id]
                        if idx + 1 < len(parsed_rows):
                            next_filename = parsed_rows[idx + 1].source_filename
                    content_text = self._extract_document_text_from_combined_text(
                        combined_text=solicitation.content_text,
                        filename=row.source_filename,
                        next_filename=next_filename,
                    )
            resolved.append(
                RfpSourceDocumentInput(
                    source_filename=row.source_filename,
                    content_type=row.content_type,
                    parse_status=row.parse_status,
                    skip_reason=row.skip_reason,
                    document_family_id=_document_family_id(row),
                    upload_order=row.upload_order,
                    source_size_bytes=row.source_size_bytes,
                    extracted_text_length=row.extracted_text_length,
                    content_text=content_text,
                    source_sha256=row.source_sha256,
                    storage_path=row.storage_path,
                )
            )
        return resolved

    def _combined_text_from_source_documents(self, source_documents: list[RfpSourceDocumentInput]) -> str:
        parsed_items = [
            item
            for item in sorted(source_documents, key=lambda row: row.upload_order)
            if item.parse_status == "PARSED" and item.content_text and item.content_text.strip()
        ]
        combined_parts = [f"Source file: {item.source_filename}\n{item.content_text.strip()}" for item in parsed_items]
        return "\n\n".join(combined_parts)

    def _source_filename_for_documents(
        self,
        *,
        source_documents: list[RfpSourceDocumentInput],
        fallback_source_filename: str,
    ) -> str:
        parsed_filenames = [
            item.source_filename
            for item in sorted(source_documents, key=lambda row: row.upload_order)
            if item.parse_status == "PARSED" and item.content_text and item.content_text.strip()
        ]
        if len(parsed_filenames) == 1:
            return parsed_filenames[0]
        if len(parsed_filenames) > 1:
            return f"reparse-batch-{len(parsed_filenames)}-files.txt"
        return fallback_source_filename

    def _source_document_display_label(
        self,
        *,
        base_row: RfpSourceDocument | None,
        compare_row: RfpSourceDocument | None,
        base_filename_counts: dict[str, int],
        compare_filename_counts: dict[str, int],
    ) -> str:
        if base_row and compare_row and base_row.source_filename != compare_row.source_filename:
            return f"{base_row.source_filename} -> {compare_row.source_filename}"

        row = compare_row or base_row
        if row is None:
            return "unknown document"

        label = row.source_filename
        if base_row and compare_row:
            if base_filename_counts.get(label, 0) == 1 and compare_filename_counts.get(label, 0) == 1:
                return label
        if (base_filename_counts.get(label, 0) + compare_filename_counts.get(label, 0)) > 1:
            label = f"{label} [{_document_family_id(row)[:8]}]"
        return label

    def _source_document_diff_record(
        self,
        *,
        base_row: RfpSourceDocument | None,
        compare_row: RfpSourceDocument | None,
        base_filename_counts: dict[str, int],
        compare_filename_counts: dict[str, int],
    ) -> SourceDocumentDiffRecord:
        row = compare_row or base_row
        if row is None:
            raise ValueError("A base or compare document is required.")
        return SourceDocumentDiffRecord(
            document_family_id=_document_family_id(row),
            label=self._source_document_display_label(
                base_row=base_row,
                compare_row=compare_row,
                base_filename_counts=base_filename_counts,
                compare_filename_counts=compare_filename_counts,
            ),
            base_source_document_id=base_row.id if base_row else None,
            compare_source_document_id=compare_row.id if compare_row else None,
            base_source_filename=base_row.source_filename if base_row else None,
            compare_source_filename=compare_row.source_filename if compare_row else None,
            base_has_stored_binary=base_row.has_stored_binary if base_row else False,
            compare_has_stored_binary=compare_row.has_stored_binary if compare_row else False,
        )

    def _build_uploaded_source_document_input(
        self,
        *,
        filename: str,
        payload: bytes,
        upload_order: int,
        document_family_id: str | None = None,
    ) -> RfpSourceDocumentInput:
        batch = extract_text_from_upload_batch([(filename, payload)])
        if not batch.documents:
            raise ValueError("No uploaded source document was provided.")
        item = batch.documents[0]
        if item.parse_status != "PARSED" or not item.content_text:
            raise ValueError(item.skip_reason or "Uploaded source document could not be parsed.")
        return RfpSourceDocumentInput(
            source_filename=item.source_filename,
            content_type=item.content_type,
            parse_status=item.parse_status,
            skip_reason=item.skip_reason,
            document_family_id=document_family_id,
            upload_order=upload_order,
            source_size_bytes=item.source_size_bytes,
            extracted_text_length=item.extracted_text_length,
            content_text=item.content_text,
            source_payload=item.source_payload,
        )

    def _requirement_change_records(
        self,
        *,
        base_requirements: list[Requirement],
        compare_requirements: list[Requirement],
    ) -> list[RequirementTextChangeRecord]:
        changes: list[RequirementTextChangeRecord] = []
        matched_base_codes: set[str] = set()
        matched_compare_codes: set[str] = set()

        base_by_code = {row.requirement_code: row for row in base_requirements}
        compare_by_code = {row.requirement_code: row for row in compare_requirements}
        for code in sorted(base_by_code.keys() & compare_by_code.keys()):
            base_row = base_by_code[code]
            compare_row = compare_by_code[code]
            if _normalize_requirement_text(base_row.requirement_text) == _normalize_requirement_text(
                compare_row.requirement_text
            ):
                continue
            changes.append(
                RequirementTextChangeRecord(
                    base_requirement_code=base_row.requirement_code,
                    compare_requirement_code=compare_row.requirement_code,
                    base_requirement_text=base_row.requirement_text,
                    compare_requirement_text=compare_row.requirement_text,
                )
            )
            matched_base_codes.add(base_row.requirement_code)
            matched_compare_codes.add(compare_row.requirement_code)

        unmatched_base = [row for row in base_requirements if row.requirement_code not in matched_base_codes]
        unmatched_compare = [row for row in compare_requirements if row.requirement_code not in matched_compare_codes]

        candidate_pairs: list[tuple[float, Requirement, Requirement]] = []
        for base_row in unmatched_base:
            base_tokens = _requirement_similarity_tokens(base_row.requirement_text)
            for compare_row in unmatched_compare:
                if base_row.category != compare_row.category:
                    continue
                compare_tokens = _requirement_similarity_tokens(compare_row.requirement_text)
                similarity = _jaccard_similarity(base_tokens, compare_tokens)
                if similarity >= 0.45:
                    candidate_pairs.append((similarity, base_row, compare_row))

        used_base: set[str] = set()
        used_compare: set[str] = set()
        for _score, base_row, compare_row in sorted(
            candidate_pairs,
            key=lambda item: (
                -item[0],
                item[1].requirement_code,
                item[2].requirement_code,
            ),
        ):
            if base_row.requirement_code in used_base or compare_row.requirement_code in used_compare:
                continue
            if _normalize_requirement_text(base_row.requirement_text) == _normalize_requirement_text(
                compare_row.requirement_text
            ):
                continue
            changes.append(
                RequirementTextChangeRecord(
                    base_requirement_code=base_row.requirement_code,
                    compare_requirement_code=compare_row.requirement_code,
                    base_requirement_text=base_row.requirement_text,
                    compare_requirement_text=compare_row.requirement_text,
                )
            )
            used_base.add(base_row.requirement_code)
            used_compare.add(compare_row.requirement_code)

        return sorted(changes, key=lambda row: (row.base_requirement_code, row.compare_requirement_code))

    def persist_draft_source_documents(
        self, draft_id: str, source_documents: list[RfpSourceDocumentInput]
    ) -> list[RfpSourceDocument]:
        return self._persist_source_documents(
            intake_rfp_draft_id=draft_id,
            source_documents=source_documents,
        )

    def list_source_documents_for_draft(self, draft_id: str) -> list[RfpSourceDocument]:
        stmt = (
            select(RfpSourceDocument)
            .where(RfpSourceDocument.intake_rfp_draft_id == draft_id)
            .order_by(RfpSourceDocument.upload_order.asc(), RfpSourceDocument.created_at.asc())
        )
        return list(self.db.scalars(stmt))

    def list_source_documents_for_solicitation(self, solicitation_id: str) -> list[RfpSourceDocument]:
        stmt = (
            select(RfpSourceDocument)
            .where(RfpSourceDocument.solicitation_id == solicitation_id)
            .order_by(RfpSourceDocument.upload_order.asc(), RfpSourceDocument.created_at.asc())
        )
        return list(self.db.scalars(stmt))

    def get_source_document_for_opportunity(
        self,
        opportunity_id: str,
        source_document_id: str,
    ) -> RfpSourceDocument | None:
        stmt = (
            select(RfpSourceDocument)
            .join(Solicitation, RfpSourceDocument.solicitation_id == Solicitation.id)
            .where(Solicitation.opportunity_id == opportunity_id)
            .where(RfpSourceDocument.id == source_document_id)
        )
        return self.db.scalars(stmt).first()

    def get_source_document_download_path(
        self,
        opportunity_id: str,
        source_document_id: str,
    ) -> tuple[Path, str] | None:
        row = self.get_source_document_for_opportunity(opportunity_id, source_document_id)
        if not row or not row.storage_path:
            return None
        path = Path(RFP_SOURCE_STORAGE_DIR.parent / row.storage_path)
        if not path.exists():
            return None
        return path, row.source_filename

    def parse_and_persist(
        self,
        opportunity_id: str,
        payload: RfpParseRequest,
        *,
        commit: bool = True,
    ) -> RfpParseResponse:
        opportunity = self.db.get(Opportunity, opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found.")

        parsed = parse_rfp_text(payload.raw_text)
        solicitation = Solicitation(
            opportunity_id=opportunity_id,
            version=self._next_solicitation_version(opportunity_id),
            source_filename=payload.source_filename,
            content_text=payload.raw_text,
            extracted_deadline=parsed["deadline"],
            extracted_evaluation_criteria=parsed["evaluation_criteria"],
            extracted_submission_instructions=parsed["submission_instructions"],
            structured_fields_json=json.dumps(parsed["structured_fields"]),
            field_provenance_json=json.dumps(parsed["field_provenance"]),
        )
        self.db.add(solicitation)
        self.db.flush()

        source_documents = payload.source_documents or self._default_source_documents(payload)
        source_document_rows = self._persist_source_documents(
            solicitation_id=solicitation.id,
            source_documents=source_documents,
        )

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

        if commit:
            self.db.commit()
        return self._build_parse_response(
            opportunity_id=opportunity_id,
            solicitation=solicitation,
            requirements=req_models,
            source_document_rows=source_document_rows,
        )

    def get_latest_solicitation(self, opportunity_id: str) -> Solicitation | None:
        return self.db.scalars(self._latest_solicitation_stmt(opportunity_id)).first()

    def get_solicitation(self, opportunity_id: str, solicitation_id: str) -> Solicitation | None:
        stmt = (
            select(Solicitation)
            .where(Solicitation.opportunity_id == opportunity_id)
            .where(Solicitation.id == solicitation_id)
        )
        return self.db.scalars(stmt).first()

    def list_versions(self, opportunity_id: str) -> list[SolicitationVersionRecord]:
        solicitations = list(self.db.scalars(self._latest_solicitation_stmt(opportunity_id)))
        items: list[SolicitationVersionRecord] = []
        for solicitation in solicitations:
            requirement_count = self.db.query(Requirement).filter(Requirement.solicitation_id == solicitation.id).count()
            source_documents = self.list_source_documents_for_solicitation(solicitation.id)
            items.append(
                SolicitationVersionRecord(
                    solicitation_id=solicitation.id,
                    opportunity_id=opportunity_id,
                    version=solicitation.version,
                    source_filename=solicitation.source_filename,
                    requirement_count=requirement_count,
                    source_documents=[
                        RfpSourceDocumentRecord.model_validate(row, from_attributes=True) for row in source_documents
                    ],
                    created_at=solicitation.created_at,
                )
            )
        return items

    def reparse_solicitation(
        self,
        opportunity_id: str,
        payload: RfpReparseRequest,
        *,
        commit: bool = True,
    ) -> RfpParseResponse:
        source = (
            self.get_solicitation(opportunity_id, payload.source_solicitation_id)
            if payload.source_solicitation_id
            else self.get_latest_solicitation(opportunity_id)
        )
        if not source:
            raise ValueError("No solicitation is available to reparse.")

        source_documents = self.list_source_documents_for_solicitation(source.id)
        effective_source_documents = (
            payload.source_documents
            if payload.source_documents
            else self._resolved_source_document_inputs(solicitation=source, rows=source_documents)
        )
        raw_text = self._combined_text_from_source_documents(effective_source_documents) or source.content_text
        source_filename = self._source_filename_for_documents(
            source_documents=effective_source_documents,
            fallback_source_filename=source.source_filename,
        )
        parse_result = self.parse_and_persist(
            opportunity_id,
            RfpParseRequest(
                raw_text=raw_text,
                source_filename=source_filename,
                actor=payload.actor,
                source_documents=effective_source_documents,
            ),
            commit=False,
        )
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=payload.actor,
            action="rfp_reparsed",
            after_state_json=(
                f'{{"source_solicitation_id":"{source.id}","source_version":{source.version},'
                f'"new_solicitation_id":"{parse_result.solicitation_id}","new_version":{parse_result.solicitation_version}}}'
            ),
        )
        if commit:
            self.db.commit()
        return parse_result

    def reparse_with_document_set(
        self,
        opportunity_id: str,
        *,
        actor: str,
        source_solicitation_id: str | None,
        retained_document_ids: list[str] | None,
        uploads: list[tuple[str, bytes]],
        commit: bool = True,
    ) -> RfpParseResponse:
        source = (
            self.get_solicitation(opportunity_id, source_solicitation_id)
            if source_solicitation_id
            else self.get_latest_solicitation(opportunity_id)
        )
        if not source:
            raise ValueError("No solicitation is available to reparse.")

        source_rows = self.list_source_documents_for_solicitation(source.id)
        retain_ids = set(retained_document_ids or [])
        retained_rows = [row for row in source_rows if row.id in retain_ids]
        effective_source_documents = self._resolved_source_document_inputs(solicitation=source, rows=retained_rows)

        if uploads:
            batch = extract_text_from_upload_batch(uploads)
            next_upload_order = len(effective_source_documents) + 1
            for offset, item in enumerate(batch.documents, start=next_upload_order):
                effective_source_documents.append(
                    RfpSourceDocumentInput(
                        source_filename=item.source_filename,
                        content_type=item.content_type,
                        parse_status=item.parse_status,
                        skip_reason=item.skip_reason,
                        upload_order=offset,
                        source_size_bytes=item.source_size_bytes,
                        extracted_text_length=item.extracted_text_length,
                        content_text=item.content_text,
                        source_payload=item.source_payload,
                    )
                )

        if not any(
            item.parse_status == "PARSED" and item.content_text and item.content_text.strip()
            for item in effective_source_documents
        ):
            raise ValueError("At least one parsed source document is required to reparse.")

        return self.reparse_solicitation(
            opportunity_id,
            RfpReparseRequest(
                actor=actor,
                source_solicitation_id=source.id,
                source_documents=effective_source_documents,
            ),
            commit=commit,
        )

    def replace_source_document(
        self,
        opportunity_id: str,
        *,
        actor: str,
        source_solicitation_id: str | None,
        source_document_id: str,
        replacement_upload: tuple[str, bytes],
        commit: bool = True,
    ) -> RfpParseResponse:
        source = (
            self.get_solicitation(opportunity_id, source_solicitation_id)
            if source_solicitation_id
            else self.get_latest_solicitation(opportunity_id)
        )
        if not source:
            raise ValueError("No solicitation is available to reparse.")

        source_rows = self.list_source_documents_for_solicitation(source.id)
        target_row = next((row for row in source_rows if row.id == source_document_id), None)
        if target_row is None:
            raise ValueError("Source document not found for the selected solicitation version.")

        replacement_filename, replacement_payload = replacement_upload
        effective_source_documents: list[RfpSourceDocumentInput] = []
        for row in source_rows:
            if row.id == target_row.id:
                effective_source_documents.append(
                    self._build_uploaded_source_document_input(
                        filename=replacement_filename,
                        payload=replacement_payload,
                        upload_order=row.upload_order,
                        document_family_id=_document_family_id(row),
                    )
                )
                continue
            effective_source_documents.extend(self._resolved_source_document_inputs(solicitation=source, rows=[row]))

        parse_result = self.reparse_solicitation(
            opportunity_id,
            RfpReparseRequest(
                actor=actor,
                source_solicitation_id=source.id,
                source_documents=effective_source_documents,
            ),
            commit=False,
        )
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=actor,
            action="rfp_source_document_replaced",
            after_state_json=(
                f'{{"source_solicitation_id":"{source.id}","source_document_id":"{target_row.id}",'
                f'"document_family_id":"{_document_family_id(target_row)}","new_solicitation_id":"{parse_result.solicitation_id}"}}'
            ),
        )
        if commit:
            self.db.commit()
        return parse_result

    def compare_versions(
        self,
        opportunity_id: str,
        *,
        base_solicitation_id: str,
        compare_solicitation_id: str,
    ) -> SolicitationComparisonResponse:
        base = self.get_solicitation(opportunity_id, base_solicitation_id)
        compare = self.get_solicitation(opportunity_id, compare_solicitation_id)
        if not base or not compare:
            raise ValueError("Both solicitation versions must exist for this opportunity.")

        base_codes = set(self._requirement_codes_for_solicitation(base.id))
        compare_codes = set(self._requirement_codes_for_solicitation(compare.id))
        base_requirements = self._requirements_for_solicitation(base.id)
        compare_requirements = self._requirements_for_solicitation(compare.id)

        base_doc_rows = self.list_source_documents_for_solicitation(base.id)
        compare_doc_rows = self.list_source_documents_for_solicitation(compare.id)
        base_docs = {_document_family_id(row): row for row in base_doc_rows}
        compare_docs = {_document_family_id(row): row for row in compare_doc_rows}
        base_filename_counts: dict[str, int] = {}
        compare_filename_counts: dict[str, int] = {}
        for row in base_doc_rows:
            base_filename_counts[row.source_filename] = base_filename_counts.get(row.source_filename, 0) + 1
        for row in compare_doc_rows:
            compare_filename_counts[row.source_filename] = compare_filename_counts.get(row.source_filename, 0) + 1

        changed_document_records: list[SourceDocumentDiffRecord] = []
        changed_documents: list[str] = []
        matched_base_families: set[str] = set()
        matched_compare_families: set[str] = set()
        for family_id in sorted(base_docs.keys() & compare_docs.keys()):
            base_row = base_docs[family_id]
            compare_row = compare_docs[family_id]
            matched_base_families.add(family_id)
            matched_compare_families.add(family_id)
            if (
                base_row.source_filename != compare_row.source_filename
                or base_row.document_family_id != compare_row.document_family_id
                or base_row.parse_status != compare_row.parse_status
                or base_row.skip_reason != compare_row.skip_reason
                or base_row.content_type != compare_row.content_type
                or base_row.source_size_bytes != compare_row.source_size_bytes
                or base_row.extracted_text_length != compare_row.extracted_text_length
                or (base_row.content_text or "") != (compare_row.content_text or "")
                or (base_row.source_sha256 or "") != (compare_row.source_sha256 or "")
                or bool(base_row.storage_path) != bool(compare_row.storage_path)
            ):
                diff_record = self._source_document_diff_record(
                    base_row=base_row,
                    compare_row=compare_row,
                    base_filename_counts=base_filename_counts,
                    compare_filename_counts=compare_filename_counts,
                )
                changed_documents.append(diff_record.label)
                changed_document_records.append(diff_record)

        unmatched_base_rows = [row for family_id, row in base_docs.items() if family_id not in matched_base_families]
        unmatched_compare_rows = [row for family_id, row in compare_docs.items() if family_id not in matched_compare_families]
        unmatched_base_by_filename: dict[str, list[RfpSourceDocument]] = {}
        unmatched_compare_by_filename: dict[str, list[RfpSourceDocument]] = {}
        for row in unmatched_base_rows:
            unmatched_base_by_filename.setdefault(row.source_filename, []).append(row)
        for row in unmatched_compare_rows:
            unmatched_compare_by_filename.setdefault(row.source_filename, []).append(row)

        for filename in sorted(unmatched_base_by_filename.keys() & unmatched_compare_by_filename.keys()):
            base_rows = unmatched_base_by_filename[filename]
            compare_rows = unmatched_compare_by_filename[filename]
            if len(base_rows) != 1 or len(compare_rows) != 1:
                continue
            base_row = base_rows[0]
            compare_row = compare_rows[0]
            matched_base_families.add(_document_family_id(base_row))
            matched_compare_families.add(_document_family_id(compare_row))
            if (
                base_row.parse_status != compare_row.parse_status
                or base_row.skip_reason != compare_row.skip_reason
                or base_row.content_type != compare_row.content_type
                or base_row.source_size_bytes != compare_row.source_size_bytes
                or base_row.extracted_text_length != compare_row.extracted_text_length
                or (base_row.content_text or "") != (compare_row.content_text or "")
                or (base_row.source_sha256 or "") != (compare_row.source_sha256 or "")
                or bool(base_row.storage_path) != bool(compare_row.storage_path)
            ):
                diff_record = self._source_document_diff_record(
                    base_row=base_row,
                    compare_row=compare_row,
                    base_filename_counts=base_filename_counts,
                    compare_filename_counts=compare_filename_counts,
                )
                changed_documents.append(diff_record.label)
                changed_document_records.append(diff_record)

        added_document_records = [
            self._source_document_diff_record(
                base_row=None,
                compare_row=compare_docs[family_id],
                base_filename_counts=base_filename_counts,
                compare_filename_counts=compare_filename_counts,
            )
            for family_id in sorted(compare_docs.keys() - matched_compare_families)
        ]
        removed_document_records = [
            self._source_document_diff_record(
                base_row=base_docs[family_id],
                compare_row=None,
                base_filename_counts=base_filename_counts,
                compare_filename_counts=compare_filename_counts,
            )
            for family_id in sorted(base_docs.keys() - matched_base_families)
        ]

        return SolicitationComparisonResponse(
            base_solicitation_id=base.id,
            compare_solicitation_id=compare.id,
            base_version=base.version,
            compare_version=compare.version,
            added_requirement_codes=sorted(compare_codes - base_codes),
            removed_requirement_codes=sorted(base_codes - compare_codes),
            added_documents=[row.label for row in added_document_records],
            removed_documents=[row.label for row in removed_document_records],
            changed_documents=changed_documents,
            added_document_records=added_document_records,
            removed_document_records=removed_document_records,
            changed_document_records=changed_document_records,
            changed_requirements=self._requirement_change_records(
                base_requirements=base_requirements,
                compare_requirements=compare_requirements,
            ),
        )
