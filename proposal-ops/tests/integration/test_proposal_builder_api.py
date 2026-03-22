import json

from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.modules.rfp_parser.models import Solicitation
from app.modules.proposal_builder.openai_client import OpenAIStructuredOutputError
from app.modules.proposal_builder.service import ProposalBuilderService


class _FakeOpenAIClient:
    available = True
    model = "gpt-5.4"

    def generate_json(self, *, schema_name: str, **_kwargs):  # type: ignore[no-untyped-def]
        if schema_name == "proposal_builder_extract_stage":
            return {
                "opportunity_summary": {
                    "client_name": "Metro Regional Airport Authority",
                    "opportunity_name": "Airport Terminal Janitorial and Day Porter Services",
                    "solicitation_number": "MR-AA-2026-041",
                    "issue_date": "March 18, 2026",
                    "questions_due_date": "March 26, 2026",
                    "proposal_due_date": "April 10, 2026",
                    "proposal_due_time": "2:00 PM ET",
                    "contract_term": "Three-year base term with two one-year renewal options",
                    "site_geography": ["Main terminal", "Baggage claim"],
                    "scope_summary": "Janitorial, day porter, and terminal support services.",
                    "submission_method": "Upload through the procurement portal.",
                    "strategic_fit": "Good fit.",
                    "geographic_fit": "Known geography.",
                    "operational_fit": "Operational fit is clear.",
                    "revenue_scale_signal": "Material pursuit.",
                    "complexity_level": "Moderate",
                    "risk_level": "Medium",
                    "recommended_next_action": "Proceed.",
                    "missing_information": [],
                    "uncertainty_notes": [],
                },
                "evaluation_criteria": [
                    {"criterion": "Technical approach", "description": "Technical approach and staffing plan.", "source_snippet": "Evaluation criteria include technical approach."}
                ],
                "submission_instructions": [
                    {"instruction_type": "Submission method", "instruction": "Upload through the procurement portal.", "source_snippet": "Proposals must be submitted electronically through the Authority procurement portal."}
                ],
                "normalized_requirements": [
                    {
                        "requirement_code": "REQ-003",
                        "normalized_requirement_text": "Provide a proposal-stage mobilization approach summary and note that the formal transition plan is due within ten calendar days after notice of intent to award.",
                        "category": "GENERAL",
                        "requirement_type": "CONTEXT_ONLY",
                        "proposal_section": "Transition and Mobilization Plan",
                        "source_excerpt": "The offeror must submit a transition and mobilization plan within ten calendar days of notice of intent to award.",
                        "confidence": "high",
                    },
                    {
                        "requirement_code": "REQ-005",
                        "normalized_requirement_text": "Submit three comparable multi-site airport, transportation, or public-facing janitorial references.",
                        "category": "PAST_PERFORMANCE",
                        "requirement_type": "COMPLIANCE_REQUIRED",
                        "proposal_section": "Past Performance",
                        "source_excerpt": "The offeror must submit three references for comparable multi-site facilities or transportation janitorial contracts.",
                        "confidence": "high",
                    },
                ],
                "warnings": [],
            }
        if schema_name == "proposal_builder_skeleton_stage":
            return {
                "proposal_outline": [
                    {
                        "sequence": 1,
                        "proposal_section": "Executive Summary",
                        "owner_role": "Proposal Lead",
                        "section_purpose": "Frame the opportunity.",
                        "requirement_codes": ["REQ-001"],
                    },
                    {
                        "sequence": 2,
                        "proposal_section": "Technical Approach",
                        "owner_role": "Operations Lead",
                        "section_purpose": "Describe delivery.",
                        "requirement_codes": ["REQ-002"],
                    },
                ],
                "win_themes": [
                    {"title": "Low-Risk Mobilization", "rationale": "Clear mobilization plan.", "supporting_requirement_codes": ["REQ-001"], "supporting_evaluation_criteria": ["Technical approach"]}
                ],
                "section_drafting_plan": [
                    {"proposal_section": "Executive Summary", "owner_role": "Proposal Lead", "objective": "Frame the opportunity.", "source_requirement_codes": ["REQ-001"], "candidate_content_block_ids": [], "notes": []},
                    {"proposal_section": "Technical Approach", "owner_role": "Operations Lead", "objective": "Describe delivery.", "source_requirement_codes": ["REQ-002"], "candidate_content_block_ids": [], "notes": []},
                ],
                "warnings": [],
            }
        if schema_name == "proposal_builder_draft_stage":
            return {
                "draft_package": {
                    "sections": [
                        {"section_title": "Executive Summary", "body_markdown": "Live executive summary.", "used_content_block_ids": [], "cited_requirement_codes": ["REQ-001"]},
                        {"section_title": "Technical Approach", "body_markdown": "Live technical approach.", "used_content_block_ids": [], "cited_requirement_codes": ["REQ-002"]},
                    ],
                    "unresolved_items": ["Confirm pricing inputs."],
                    "internal_notes": ["Insert approved local office details."],
                    "editor_notes": "Use the support bundle to finish pricing inputs.",
                    "used_content_block_ids": [],
                    "cited_requirement_codes": ["REQ-001", "REQ-002"],
                },
                "warnings": [],
            }
        raise AssertionError(f"Unexpected schema_name: {schema_name}")


class _UnavailableOpenAIClient:
    available = False
    model = "gpt-5.4"
    timeout_seconds = 300


class _TimeoutOpenAIClient:
    available = True
    model = "gpt-5.4"
    timeout_seconds = 300

    def generate_json(self, **_kwargs):  # type: ignore[no-untyped-def]
        raise OpenAIStructuredOutputError("OpenAI request timed out after 300 seconds.")


class _InvalidJsonOpenAIClient:
    available = True
    model = "gpt-5.4"
    timeout_seconds = 300

    def generate_json(self, *, schema_name: str, **_kwargs):  # type: ignore[no-untyped-def]
        if schema_name == "proposal_builder_extract_stage":
            raise OpenAIStructuredOutputError("OpenAI response returned invalid JSON.")
        raise AssertionError(f"Unexpected schema_name: {schema_name}")


class _DraftInvalidJsonOpenAIClient(_FakeOpenAIClient):
    timeout_seconds = 300

    def generate_json(self, *, schema_name: str, **_kwargs):  # type: ignore[no-untyped-def]
        if schema_name == "proposal_builder_draft_stage":
            raise OpenAIStructuredOutputError("OpenAI response JSON root must be an object.")
        return super().generate_json(schema_name=schema_name, **_kwargs)


def test_proposal_builder_api_supports_monkeypatched_live_generation(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _FakeOpenAIClient())

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    extracted = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-builder/extract",
        json={"actor": "operator"},
    )
    assert extracted.status_code == 200
    assert extracted.json()["generation_mode"] == "LIVE"
    assert extracted.json()["generation_reason"] == "live_model"

    skeleton = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-builder/skeleton",
        json={"actor": "operator"},
    )
    assert skeleton.status_code == 200
    assert skeleton.json()["generation_mode"] == "LIVE"
    assert skeleton.json()["generation_reason"] == "live_model"

    draft = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-builder/draft",
        json={"actor": "operator"},
    )
    assert draft.status_code == 200
    assert draft.json()["generation_mode"] == "LIVE"
    assert draft.json()["generation_reason"] == "live_model"

    workspace = client.get(f"/api/opportunities/{opportunity_id}/proposal-builder")
    assert workspace.status_code == 200
    payload = workspace.json()
    assert payload["proposal_outline"]["sections"]
    assert payload["draft_package"]["sections"]
    assert payload["client_sections"]
    assert payload["follow_up_actions"]
    assert payload["generation_reason"] == "live_model"


def test_proposal_builder_api_best_draft_runs_through_export(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _FakeOpenAIClient())

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    best_draft = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-builder/best-draft",
        json={"actor": "operator"},
    )
    assert best_draft.status_code == 200
    payload = best_draft.json()
    assert payload["status"] == "EXPORTED"
    assert payload["export_manifest"]["client_docx_path"]
    assert payload["draft_package"]["sections"]


def test_proposal_builder_api_section_edit_invalidates_export_until_refreshed(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _FakeOpenAIClient())

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    best_draft = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-builder/best-draft",
        json={"actor": "operator"},
    )
    assert best_draft.status_code == 200
    assert best_draft.json()["export_manifest"]["client_docx_path"]

    updated = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-builder/sections/0",
        json={
            "actor": "operator",
            "section_index": 0,
            "body_markdown": "Rewritten executive summary for preview editing.",
        },
    )
    assert updated.status_code == 200
    payload = updated.json()
    assert payload["status"] == "DRAFT_READY"
    assert payload["export_manifest"] is None
    assert payload["client_sections"][0]["body_markdown"] == "Rewritten executive summary for preview editing."


def test_proposal_builder_extract_stage_applies_ai_requirement_normalization(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _FakeOpenAIClient())

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    extracted = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-builder/extract",
        json={"actor": "operator"},
    )
    assert extracted.status_code == 200

    workspace = client.get(f"/api/opportunities/{opportunity_id}/proposal-builder")
    assert workspace.status_code == 200
    payload = workspace.json()

    requirements_by_code = {item["requirement_code"]: item for item in payload["requirements_list"]}
    matrix_by_code = {item["requirement_code"]: item for item in payload["compliance_matrix"]}

    assert requirements_by_code["REQ-003"]["requirement_type"] == "CONTEXT_ONLY"
    assert "proposal-stage mobilization approach summary" in requirements_by_code["REQ-003"]["requirement_text"]
    assert "REQ-003" not in matrix_by_code

    assert requirements_by_code["REQ-005"]["category"] == "PAST_PERFORMANCE"
    assert requirements_by_code["REQ-005"]["requirement_type"] == "COMPLIANCE_REQUIRED"
    assert matrix_by_code["REQ-005"]["proposal_section"] == "Past Performance"
    assert "three comparable multi-site airport" in matrix_by_code["REQ-005"]["requirement_text"]


def test_proposal_builder_extract_stage_repairs_missing_canonical_due_fields_from_ai_summary(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _FakeOpenAIClient())

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    with SessionLocal() as db:
        solicitation = db.query(Solicitation).filter(Solicitation.opportunity_id == opportunity_id).order_by(Solicitation.version.desc()).first()
        assert solicitation is not None
        payload = solicitation.structured_fields_json
        assert payload is not None
        structured_fields = json.loads(payload)
        structured_fields["proposal_due_date"] = None
        structured_fields["proposal_due_time"] = None
        solicitation.structured_fields_json = json.dumps(structured_fields)
        solicitation.extracted_deadline = None
        db.commit()

    extracted = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-builder/extract",
        json={"actor": "operator"},
    )
    assert extracted.status_code == 200

    workspace = client.get(f"/api/opportunities/{opportunity_id}/proposal-builder")
    assert workspace.status_code == 200
    payload = workspace.json()
    assert payload["structured_fields"]["proposal_due_date"] == "April 10, 2026"
    assert payload["structured_fields"]["proposal_due_time"] == "2:00 PM ET"
    assert payload["opportunity_summary"]["proposal_due_date"] == "April 10, 2026"

    with SessionLocal() as db:
        solicitation = db.query(Solicitation).filter(Solicitation.opportunity_id == opportunity_id).order_by(Solicitation.version.desc()).first()
        assert solicitation is not None
        assert solicitation.extracted_deadline == "April 10, 2026"
        assert solicitation.structured_fields_json is not None
        repaired_fields = json.loads(solicitation.structured_fields_json)
        assert repaired_fields["proposal_due_date"] == "April 10, 2026"
        assert repaired_fields["proposal_due_time"] == "2:00 PM ET"


def test_proposal_builder_api_reports_missing_key_reason_for_demo_fallback(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _UnavailableOpenAIClient())

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    workspace = client.get(f"/api/opportunities/{opportunity_id}/proposal-builder")
    assert workspace.status_code == 200
    payload = workspace.json()
    assert payload["generation_mode"] == "FALLBACK_SAMPLE"
    assert payload["generation_reason"] == "missing_api_key"


def test_proposal_builder_api_returns_error_instead_of_deterministic_fallback_on_live_timeout(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _TimeoutOpenAIClient())

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    draft = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-builder/draft",
        json={"actor": "operator"},
    )
    assert draft.status_code == 409
    assert "did not generate a deterministic fallback" in draft.json()["detail"]

    workspace = client.get(f"/api/opportunities/{opportunity_id}/proposal-builder")
    assert workspace.status_code == 200
    payload = workspace.json()
    assert payload["generation_mode"] == "ERROR"
    assert payload["generation_reason"] == "timeout"


def test_proposal_builder_extract_stage_keeps_baseline_when_live_structured_output_is_invalid(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _InvalidJsonOpenAIClient())

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    extracted = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-builder/extract",
        json={"actor": "operator"},
    )
    assert extracted.status_code == 200
    payload = extracted.json()
    assert payload["generation_mode"] == "FALLBACK_BASELINE"
    assert payload["generation_reason"] == "structured_output_validation_failed"
    assert any("deterministic RFP extraction" in item for item in payload["warnings"])
    assert payload["status"] == "REQUIREMENTS_READY"
    assert payload["opportunity_summary"]["proposal_due_date"] == "April 10, 2026"


def test_proposal_builder_draft_stage_keeps_baseline_when_live_structured_output_root_is_invalid(
    client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _DraftInvalidJsonOpenAIClient())

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    draft = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-builder/draft",
        json={"actor": "operator"},
    )
    assert draft.status_code == 200
    payload = draft.json()
    assert payload["generation_mode"] == "FALLBACK_BASELINE"
    assert payload["generation_reason"] == "structured_output_validation_failed"
    assert any("baseline Word-ready draft" in item for item in payload["warnings"])
    assert payload["status"] == "DRAFT_READY"
    assert payload["draft_package"]["sections"]
