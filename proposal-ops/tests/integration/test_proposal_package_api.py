import time

from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.modules.proposal_builder.models import ClientPricingModel
from app.modules.proposal_builder.package_service import ProposalPackageService
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
        raise AssertionError(f"Unexpected schema_name: {schema_name}")


def _fake_package_ai(self, *, stage_name: str, **_kwargs):  # type: ignore[no-untyped-def]
    if stage_name == "customer_strategy":
        return (
            {
                "buyer_priorities": ["Technical approach", "Staffing plan", "Mobilization"],
                "strategic_positioning": "Lead with visible supervision, mobilization control, and evaluator-ready responsiveness.",
                "bid_recommendation": "Proceed",
                "value_propositions": [
                    {
                        "title": "Operational Control",
                        "buyer_outcome": "Consistent service quality and rapid issue handling.",
                        "differentiators": ["Visible supervision", "Quality inspections"],
                        "supporting_requirement_codes": ["REQ-001"],
                        "supporting_asset_ids": ["company-overview-airside-facilities"],
                    }
                ],
                "proof_points": [
                    {
                        "title": "Comparable Airport Experience",
                        "statement": "Use airport reference material to reinforce execution confidence.",
                        "supporting_asset_ids": ["reference-regional-airport"],
                        "supporting_requirement_codes": ["REQ-002"],
                    }
                ],
                "win_theme_titles": ["Low-Risk Mobilization"],
                "apmp_findings": [],
            },
            {"response_id": "resp_strategy", "usage": {"total_tokens": 1200}},
        )
    if stage_name == "content_plan":
        return (
            {
                "section_briefs": [
                    {
                        "section_title": "Executive Summary",
                        "objective": "Open with buyer priorities and differentiators.",
                        "evaluator_priorities": ["Technical approach"],
                        "win_themes": ["Low-Risk Mobilization"],
                        "value_propositions": ["Operational Control"],
                        "proof_points": ["Comparable Airport Experience"],
                        "cited_requirement_codes": ["REQ-001"],
                        "approved_asset_ids": ["company-overview-airside-facilities", "executive-summary-operations-control"],
                        "required_graphics_or_actions": ["Insert mobilization timeline graphic."],
                        "drafting_instructions": ["Keep the narrative buyer-facing."],
                    },
                    {
                        "section_title": "Technical Approach",
                        "objective": "Describe delivery controls.",
                        "evaluator_priorities": ["Technical approach"],
                        "win_themes": ["Low-Risk Mobilization"],
                        "value_propositions": ["Operational Control"],
                        "proof_points": ["Comparable Airport Experience"],
                        "cited_requirement_codes": ["REQ-002"],
                        "approved_asset_ids": ["service-description-janitorial-dayporter"],
                        "required_graphics_or_actions": ["Insert service controls graphic."],
                        "drafting_instructions": ["Tie the writing to service routines."],
                    },
                ],
                "missing_asset_inputs": [],
                "apmp_findings": [],
            },
            {"response_id": "resp_plan", "usage": {"total_tokens": 1400}},
        )
    if stage_name == "full_draft":
        return (
            {
                "draft_package": {
                    "sections": [
                        {"section_title": "Executive Summary", "body_markdown": "Buyer-facing executive summary.", "used_content_block_ids": ["company-overview-airside-facilities"], "cited_requirement_codes": ["REQ-001"]},
                        {"section_title": "Technical Approach", "body_markdown": "Buyer-facing technical approach.", "used_content_block_ids": ["service-description-janitorial-dayporter"], "cited_requirement_codes": ["REQ-002"]},
                        {"section_title": "Management and Staffing Plan", "body_markdown": "Management and staffing narrative.", "used_content_block_ids": ["resume-operations-director"], "cited_requirement_codes": ["REQ-002"]},
                        {"section_title": "Transition and Mobilization Plan", "body_markdown": "Transition and mobilization narrative.", "used_content_block_ids": ["executive-summary-operations-control"], "cited_requirement_codes": ["REQ-001"]},
                    ],
                    "client_sections": [
                        {"section_title": "Executive Summary", "body_markdown": "Buyer-facing executive summary.", "used_content_block_ids": ["company-overview-airside-facilities"], "cited_requirement_codes": ["REQ-001"]},
                        {"section_title": "Technical Approach", "body_markdown": "Buyer-facing technical approach.", "used_content_block_ids": ["service-description-janitorial-dayporter"], "cited_requirement_codes": ["REQ-002"]},
                        {"section_title": "Management and Staffing Plan", "body_markdown": "Management and staffing narrative.", "used_content_block_ids": ["resume-operations-director"], "cited_requirement_codes": ["REQ-002"]},
                        {"section_title": "Transition and Mobilization Plan", "body_markdown": "Transition and mobilization narrative.", "used_content_block_ids": ["executive-summary-operations-control"], "cited_requirement_codes": ["REQ-001"]},
                    ],
                    "internal_notes": ["Validate final named resumes and references."],
                    "unresolved_items": [],
                    "editor_notes": "Tighten final language and confirm the remaining attachments.",
                    "used_content_block_ids": ["company-overview-airside-facilities"],
                    "cited_requirement_codes": ["REQ-001", "REQ-002"],
                },
                "warnings": [],
            },
            {"response_id": "resp_draft", "usage": {"total_tokens": 2600}},
        )
    if stage_name in {"pink_team_review", "red_team_review", "gold_team_production_review"}:
        return (
            {
                "findings": [
                    {
                        "review_stage": stage_name,
                        "title": "Overall quality is strong",
                        "severity": "low",
                        "disposition": "pass",
                        "recommendation": "Proceed to the next stage.",
                        "apmp_topic_id": "proposal_organization",
                        "section_title": "Executive Summary",
                        "source_refs": ["Executive Summary"],
                    }
                ]
            },
            {"response_id": f"resp_{stage_name}", "usage": {"total_tokens": 800}},
        )
    raise AssertionError(f"Unexpected package stage: {stage_name}")


def _fake_package_ai_with_blocked_pink(self, *, stage_name: str, **_kwargs):  # type: ignore[no-untyped-def]
    if stage_name == "pink_team_review":
        return (
            {
                "findings": [
                    {
                        "review_stage": stage_name,
                        "title": "Missing named staffing inputs",
                        "severity": "high",
                        "disposition": "fail",
                        "recommendation": "Finalize staffing quantities and named supervisors before moving to production review.",
                        "apmp_topic_id": "review_management",
                        "section_title": "Management and Staffing Plan",
                        "source_refs": ["Management and Staffing Plan"],
                    }
                ]
            },
            {"response_id": "resp_blocked_pink", "usage": {"total_tokens": 900}},
        )
    return _fake_package_ai(self, stage_name=stage_name, **_kwargs)


def _wait_for_status(client: TestClient, opportunity_id: str, run_id: str, expected_status: str, timeout_seconds: float = 8.0) -> dict:
    deadline = time.time() + timeout_seconds
    latest = {}
    while time.time() < deadline:
        response = client.get(f"/api/opportunities/{opportunity_id}/proposal-package/runs/{run_id}")
        assert response.status_code == 200
        latest = response.json()
        if latest.get("status") == expected_status:
            return latest
        time.sleep(0.1)
    raise AssertionError(f"Timed out waiting for package run status {expected_status}. Last payload: {latest}")


def test_proposal_package_run_supports_background_stage_flow(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _FakeOpenAIClient())
    monkeypatch.setattr(ProposalPackageService, "_run_ai_structured_stage", _fake_package_ai)

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    started_run = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-package/runs",
        json={"actor": "operator"},
    )
    assert started_run.status_code == 200
    run = started_run.json()
    run_id = run["id"]

    payload = _wait_for_status(client, opportunity_id, run_id, "AWAITING_PRICING_APPROVAL")
    assert payload["status"] == "AWAITING_PRICING_APPROVAL"
    assert payload["pricing_package"]["annual_total"] > 0

    approved_pricing = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-package/runs/{run_id}/approve-stage",
        json={"actor": "operator", "stage_name": "pricing"},
    )
    assert approved_pricing.status_code == 200

    export_payload = _wait_for_status(client, opportunity_id, run_id, "AWAITING_EXPORT_APPROVAL")
    assert export_payload["status"] == "AWAITING_EXPORT_APPROVAL"
    assert export_payload["form_package"]["completed_forms"]
    assert not any(stage["stage_name"] == "pink_team_review" for stage in export_payload["stages"])
    assert not export_payload["review_findings"]

    approved_export = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-package/runs/{run_id}/approve-stage",
        json={"actor": "operator", "stage_name": "export_package"},
    )
    assert approved_export.status_code == 200

    completed_payload = _wait_for_status(client, opportunity_id, run_id, "COMPLETED")
    assert completed_payload["status"] == "COMPLETED"
    assert completed_payload["export_manifest"]["client_docx_path"]
    assert completed_payload["export_manifest"]["pricing_workbook_path"]


def test_proposal_package_allows_new_run_while_waiting_for_pricing_approval(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _FakeOpenAIClient())
    monkeypatch.setattr(ProposalPackageService, "_run_ai_structured_stage", _fake_package_ai)

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    first_run = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-package/runs",
        json={"actor": "operator"},
    )
    assert first_run.status_code == 200
    first_run_id = first_run.json()["id"]

    first_payload = _wait_for_status(client, opportunity_id, first_run_id, "AWAITING_PRICING_APPROVAL")
    assert first_payload["status"] == "AWAITING_PRICING_APPROVAL"

    second_run = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-package/runs",
        json={"actor": "operator"},
    )
    assert second_run.status_code == 200
    second_run_id = second_run.json()["id"]
    assert second_run_id != first_run_id

    second_payload = _wait_for_status(client, opportunity_id, second_run_id, "AWAITING_PRICING_APPROVAL")
    assert second_payload["status"] == "AWAITING_PRICING_APPROVAL"


def test_proposal_package_skips_color_team_reviews_by_default(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _FakeOpenAIClient())
    monkeypatch.setattr(ProposalPackageService, "_run_ai_structured_stage", _fake_package_ai_with_blocked_pink)

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    started_run = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-package/runs",
        json={"actor": "operator"},
    )
    assert started_run.status_code == 200
    run_id = started_run.json()["id"]

    payload = _wait_for_status(client, opportunity_id, run_id, "AWAITING_PRICING_APPROVAL")
    assert payload["status"] == "AWAITING_PRICING_APPROVAL"

    approved_pricing = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-package/runs/{run_id}/approve-stage",
        json={"actor": "operator", "stage_name": "pricing"},
    )
    assert approved_pricing.status_code == 200

    export_payload = _wait_for_status(client, opportunity_id, run_id, "AWAITING_EXPORT_APPROVAL")
    assert export_payload["status"] == "AWAITING_EXPORT_APPROVAL"
    stage_names = [stage["stage_name"] for stage in export_payload["stages"]]
    assert "pink_team_review" not in stage_names
    assert "red_team_review" not in stage_names
    assert "gold_team_production_review" not in stage_names


def test_proposal_package_demo_mode_allows_draft_pricing_model(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _FakeOpenAIClient())
    monkeypatch.setattr(ProposalPackageService, "_run_ai_structured_stage", _fake_package_ai)

    profile = client.post(
        "/api/client-profiles",
        json={
            "display_name": "Metro Regional Airport Authority",
            "aliases": ["Metro Airport Authority"],
            "approved_content_tags": ["airport", "janitorial"],
            "region_tags": ["northeast"],
            "service_tags": ["janitorial", "day-porter"],
        },
    ).json()

    pricing_model = client.post(
        f"/api/client-profiles/{profile['id']}/pricing-models",
        json={
            "name": "Draft Airport Pricing Model",
            "assumptions": ["Dummy pricing assumptions for testing."],
            "service_tags": ["janitorial", "day-porter"],
            "region_tags": ["northeast"],
            "site_multiplier": 1.0,
            "continuous_coverage_multiplier": 1.35,
            "labor_categories": [
                {
                    "code": "janitor",
                    "label": "Janitor",
                    "hourly_rate": 20.5,
                    "burden_factor": 1.27,
                    "markup_factor": 1.18,
                    "default_hours_per_week": 160,
                },
                {
                    "code": "day_porter",
                    "label": "Day Porter",
                    "hourly_rate": 22.0,
                    "burden_factor": 1.24,
                    "markup_factor": 1.16,
                    "default_hours_per_week": 80,
                },
            ],
        },
    ).json()

    with SessionLocal() as db:
        row = db.get(ClientPricingModel, pricing_model["id"])
        assert row is not None
        row.status = "DRAFT"
        db.commit()

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    profile_selected = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-config/select-profile",
        json={"actor": "operator", "target_id": profile["id"]},
    )
    assert profile_selected.status_code == 200

    pricing_selected = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-config/select-pricing-model",
        json={"actor": "operator", "target_id": pricing_model["id"]},
    )
    assert pricing_selected.status_code == 200
    assert any("not approved" in item.lower() for item in pricing_selected.json()["validation_errors"])

    started_run = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-package/runs",
        json={"actor": "operator", "demo_mode": True},
    )
    assert started_run.status_code == 200
    run_id = started_run.json()["id"]

    payload = _wait_for_status(client, opportunity_id, run_id, "AWAITING_PRICING_APPROVAL")
    assert payload["status"] == "AWAITING_PRICING_APPROVAL"
    pricing_stage = next(stage for stage in payload["stages"] if stage["stage_name"] == "pricing")
    assert any("draft pricing model" in warning.lower() for warning in pricing_stage["warnings"])


def test_proposal_package_rerun_can_enable_demo_mode_for_blocked_pricing(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _FakeOpenAIClient())
    monkeypatch.setattr(ProposalPackageService, "_run_ai_structured_stage", _fake_package_ai)

    profile = client.post(
        "/api/client-profiles",
        json={
            "display_name": "Metro Regional Airport Authority",
            "aliases": ["Metro Airport Authority"],
            "approved_content_tags": ["airport", "janitorial"],
            "region_tags": ["northeast"],
            "service_tags": ["janitorial", "day-porter"],
        },
    ).json()

    pricing_model = client.post(
        f"/api/client-profiles/{profile['id']}/pricing-models",
        json={
            "name": "Draft Airport Pricing Model",
            "assumptions": ["Dummy pricing assumptions for testing."],
            "service_tags": ["janitorial", "day-porter"],
            "region_tags": ["northeast"],
            "site_multiplier": 1.0,
            "continuous_coverage_multiplier": 1.35,
            "labor_categories": [
                {
                    "code": "janitor",
                    "label": "Janitor",
                    "hourly_rate": 20.5,
                    "burden_factor": 1.27,
                    "markup_factor": 1.18,
                    "default_hours_per_week": 160,
                }
            ],
        },
    ).json()

    with SessionLocal() as db:
        row = db.get(ClientPricingModel, pricing_model["id"])
        assert row is not None
        row.status = "DRAFT"
        db.commit()

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    assert client.post(
        f"/api/opportunities/{opportunity_id}/proposal-config/select-profile",
        json={"actor": "operator", "target_id": profile["id"]},
    ).status_code == 200
    assert client.post(
        f"/api/opportunities/{opportunity_id}/proposal-config/select-pricing-model",
        json={"actor": "operator", "target_id": pricing_model["id"]},
    ).status_code == 200

    started_run = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-package/runs",
        json={"actor": "operator", "demo_mode": False},
    )
    assert started_run.status_code == 200
    run_id = started_run.json()["id"]

    initial_payload = _wait_for_status(client, opportunity_id, run_id, "AWAITING_PRICING_APPROVAL")
    assert initial_payload["current_stage"] == "pricing"
    initial_pricing_stage = next(stage for stage in initial_payload["stages"] if stage["stage_name"] == "pricing")
    assert any("not approved" in warning.lower() for warning in initial_pricing_stage["warnings"])

    rerun = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-package/runs/{run_id}/rerun-stage",
        json={"actor": "operator", "stage_name": "pricing", "demo_mode": True},
    )
    assert rerun.status_code == 200

    payload = _wait_for_status(client, opportunity_id, run_id, "AWAITING_PRICING_APPROVAL")
    pricing_stage = next(stage for stage in payload["stages"] if stage["stage_name"] == "pricing")
    assert any("draft pricing model" in warning.lower() for warning in pricing_stage["warnings"])
