from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.config import EXPORTS_DIR
from app.core.db import SessionLocal
from app.main import app
from app.modules.opportunity_intake.models import Opportunity
from app.modules.proposal_builder.client_profiles import ClientProfileService
from app.modules.proposal_builder.schemas import OpportunityProposalConfigSelectionRequest
from app.modules.proposal_builder.service import ProposalBuilderError, ProposalBuilderService
from app.modules.rfp_parser.service import RfpParserService
from app.modules.rfp_parser.schemas import RfpStructuredFields


SOURCE_DIR = Path(r"C:\Users\timot\Downloads\ppgrfp")
SOURCE_FILENAMES = [
    "2026_PIT_Security_RFP_for_PPG_Place__625_Liberty_2-20-2026.pdf",
    "consolidated questions.pdf",
    "2._Highwoods_Vendor_Qualification_Form.pdf",
    "5._EXHIBIT_C_both_properties.pdf",
]
PROFILE_NAME = "St. Moritz Security Services, Inc."
BUYER_NAME = "Highwoods Properties"
OPPORTUNITY_NAME = "Security Services at PPG Place and 625 Liberty Avenue"
WORKING_SOLICITATION_LABEL = "2026 PIT Security RFP"
PROPOSAL_DUE_DATE = "March 10, 2026"
PROPOSAL_DUE_TIME = "Close of business"
CONTRACT_TERM = "Three-year period unless terminated, with or without cause, by either party with thirty (30) days' written notice."
SUBMISSION_METHOD = "All submissions must be made electronically through the Prism platform."


def _load_files() -> list[tuple[str, bytes]]:
    files: list[tuple[str, bytes]] = []
    for filename in SOURCE_FILENAMES:
        path = SOURCE_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing source file: {path}")
        files.append((path.name, path.read_bytes()))
    return files


def _normalize_demo_metadata(opportunity_id: str) -> None:
    with SessionLocal() as db:
        opportunity = db.get(Opportunity, opportunity_id)
        if not opportunity:
            raise RuntimeError(f"Opportunity {opportunity_id} was not found.")
        opportunity.name = OPPORTUNITY_NAME
        opportunity.client = BUYER_NAME

        parser_service = RfpParserService(db)
        solicitation = parser_service.get_latest_solicitation(opportunity_id)
        if not solicitation:
            raise RuntimeError("No solicitation was found after intake.")

        structured_fields = RfpStructuredFields.model_validate(json.loads(solicitation.structured_fields_json or "{}"))
        structured_fields.client_name = BUYER_NAME
        structured_fields.opportunity_name = OPPORTUNITY_NAME
        structured_fields.solicitation_number = WORKING_SOLICITATION_LABEL
        structured_fields.proposal_due_date = structured_fields.proposal_due_date or PROPOSAL_DUE_DATE
        structured_fields.proposal_due_time = structured_fields.proposal_due_time or PROPOSAL_DUE_TIME
        structured_fields.contract_term = CONTRACT_TERM
        structured_fields.submission_method = SUBMISSION_METHOD
        solicitation.structured_fields_json = json.dumps(structured_fields.model_dump())
        solicitation.extracted_deadline = structured_fields.proposal_due_date

        provenance = json.loads(solicitation.field_provenance_json or "{}")
        if not isinstance(provenance, dict):
            provenance = {}
        provenance["client_name"] = list(dict.fromkeys(list(provenance.get("client_name", [])) + ["Demo normalization: Highwoods Properties"]))
        provenance["opportunity_name"] = list(dict.fromkeys(list(provenance.get("opportunity_name", [])) + [f"Demo normalization: {OPPORTUNITY_NAME}"]))
        provenance["solicitation_number"] = list(
            dict.fromkeys(list(provenance.get("solicitation_number", [])) + [f"Demo normalization: {WORKING_SOLICITATION_LABEL}"])
        )
        provenance["proposal_due_time"] = list(
            dict.fromkeys(list(provenance.get("proposal_due_time", [])) + [f"Demo normalization: {PROPOSAL_DUE_TIME}"])
        )
        solicitation.field_provenance_json = json.dumps(provenance)
        db.commit()


def _apply_st_moritz_profile(opportunity_id: str) -> None:
    with SessionLocal() as db:
        service = ClientProfileService(db)
        profiles = service.list_profiles()
        profile = next((item for item in profiles if item.display_name == PROFILE_NAME), None)
        if not profile:
            raise RuntimeError(f"Client profile '{PROFILE_NAME}' was not found.")
        service.select_profile(
            opportunity_id,
            OpportunityProposalConfigSelectionRequest(actor="operator", target_id=profile.id),
        )


def build_demo() -> dict[str, object]:
    files = _load_files()

    with SessionLocal() as db:
        service = ProposalBuilderService(db)
        start = service.start_from_inputs(actor="operator", files=files)
        if not start.opportunity_id:
            raise RuntimeError(f"Builder start did not return an opportunity id: {start.model_dump()}")
        opportunity_id = start.opportunity_id

    _apply_st_moritz_profile(opportunity_id)
    _normalize_demo_metadata(opportunity_id)

    with SessionLocal() as db:
        service = ProposalBuilderService(db)
        service.run_extract_stage(opportunity_id, actor="operator")
        service.run_skeleton_stage(opportunity_id, actor="operator")
        draft = service.run_draft_stage(opportunity_id, actor="operator")
        workspace = service.get_workspace(opportunity_id)

    preview_url = f"/opportunities/{opportunity_id}/proposal-builder/preview"
    preview_dir = EXPORTS_DIR / opportunity_id / "preexport-preview"
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_path = preview_dir / "proposal-preview-before-export.html"
    with TestClient(app) as client:
        response = client.get(preview_url)
        response.raise_for_status()
        preview_path.write_text(response.text, encoding="utf-8")

    with SessionLocal() as db:
        service = ProposalBuilderService(db)
        export = service.run_export_stage(opportunity_id, actor="operator")
        workspace = service.get_workspace(opportunity_id)

    manifest = export.export_manifest.model_dump() if export.export_manifest else {}
    summary = workspace.opportunity_summary.model_dump() if workspace.opportunity_summary else {}
    result = {
        "opportunity_id": opportunity_id,
        "preview_url": preview_url,
        "preview_path_before_export": preview_path.as_posix(),
        "export_manifest": manifest,
        "draft_warnings": draft.warnings,
        "document_gaps": workspace.document_gaps,
        "summary": summary,
        "generated_at": datetime.now(UTC).isoformat(),
    }

    summary_path = Path(manifest.get("export_directory", preview_dir.as_posix())) / "rapid-build-summary.json"
    summary_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    result["summary_path"] = summary_path.as_posix()
    return result


if __name__ == "__main__":
    try:
        result = build_demo()
    except (ProposalBuilderError, FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1) from exc

    print("Rapid proposal build complete.")
    print(f"Opportunity ID: {result['opportunity_id']}")
    print(f"HTML preview URL: {result['preview_url']}")
    print(f"HTML preview snapshot: {result['preview_path_before_export']}")
    manifest = result.get("export_manifest", {})
    print(f"Word draft: {manifest.get('client_docx_path')}")
    print(f"Export HTML preview: {manifest.get('html_preview_path')}")
    print(f"Missing-input checklist: {manifest.get('missing_input_checklist_path')}")
    print(f"Support bundle: {manifest.get('support_bundle_zip_path')}")
    print(f"Summary JSON: {result.get('summary_path')}")
