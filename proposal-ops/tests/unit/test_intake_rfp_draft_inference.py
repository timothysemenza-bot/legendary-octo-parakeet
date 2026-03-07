from datetime import date

from app.modules.opportunity_intake.draft_inference import infer_intake_draft_fields


def test_infer_intake_draft_fields_extracts_title_client_value_and_lead_time() -> None:
    combined_text = """
    Source file: regional-ops-rfp.pdf
    REQUEST FOR PROPOSALS
    Regional Operations Support Services
    Issued by: City of Springfield
    The estimated contract value is $1,250,000.
    Proposal due date is 2026-04-20.
    The contractor shall provide a staffing plan.
    """

    result = infer_intake_draft_fields(
        combined_text,
        ["regional-ops-rfp.pdf"],
        today=date(2026, 3, 6),
    )

    assert result.suggested_fields["name"] == "Regional Operations Support Services"
    assert result.suggested_fields["client"] == "City of Springfield"
    assert result.suggested_fields["estimated_contract_value"] == 1_250_000
    assert result.suggested_fields["lead_time_days"] == 45
    assert result.field_statuses["name"] == "INFERRED"
    assert result.field_statuses["client"] == "INFERRED"
    assert result.field_statuses["estimated_contract_value"] == "INFERRED"
    assert result.field_statuses["lead_time_days"] == "INFERRED"


def test_infer_intake_draft_fields_falls_back_to_filename_for_name() -> None:
    combined_text = """
    Source file: emergency-response-rfp-v2.docx
    REQUEST FOR PROPOSALS
    Proposal due date is 2026-05-01.
    The contractor shall provide a mobilization plan.
    """

    result = infer_intake_draft_fields(
        combined_text,
        ["emergency-response-rfp-v2.docx"],
        today=date(2026, 3, 6),
    )

    assert result.suggested_fields["name"] == "Emergency Response Rfp V2"
    assert result.field_statuses["name"] == "INFERRED"
    assert result.suggested_fields["client"] is None
    assert result.field_statuses["client"] == "MISSING"


def test_infer_intake_draft_fields_only_uses_contract_value_with_strong_cues() -> None:
    combined_text = """
    Source file: no-budget-rfp.txt
    Operations Modernization Support
    City of Springfield
    Pricing sheet value is $800,000.
    Proposal due date is 2026-05-30.
    The contractor shall provide a staffing plan.
    """

    result = infer_intake_draft_fields(
        combined_text,
        ["no-budget-rfp.txt"],
        today=date(2026, 3, 6),
    )

    assert result.suggested_fields["estimated_contract_value"] is None
    assert result.field_statuses["estimated_contract_value"] == "MISSING"


def test_infer_intake_draft_fields_applies_conservative_internal_defaults() -> None:
    combined_text = """
    Source file: simple-rfp.txt
    Operations Support Services
    Proposal due date is 2026-03-05.
    The contractor shall provide a staffing plan.
    """

    result = infer_intake_draft_fields(
        combined_text,
        ["simple-rfp.txt"],
        today=date(2026, 3, 6),
    )

    assert result.suggested_fields["incumbent_status"] is False
    assert result.suggested_fields["strategic_alignment"] == 3
    assert result.suggested_fields["estimated_probability_win"] == 50
    assert result.field_statuses["incumbent_status"] == "DEFAULTED"
    assert result.field_statuses["strategic_alignment"] == "DEFAULTED"
    assert result.field_statuses["estimated_probability_win"] == "DEFAULTED"
    assert result.suggested_fields["lead_time_days"] is None
    assert result.field_statuses["lead_time_days"] == "MISSING"


def test_infer_intake_draft_fields_skips_page_headers_and_combines_code_with_title() -> None:
    combined_text = """
    Source file: 26-0198 Facilities Management.PDF
    Page 1 of 46
    REQUEST FOR PROPOSAL (RFP)
    26-0198
    Facilities Management
    RFP Release Date: November 18, 2025
    Proposals Due: January 5, 2026
    Detroit Public Schools Community District
    The contractor shall provide a staffing plan.
    """

    result = infer_intake_draft_fields(
        combined_text,
        ["26-0198 Facilities Management.PDF"],
        today=date(2026, 3, 6),
    )

    assert result.suggested_fields["name"] == "26-0198 Facilities Management"
    assert result.field_statuses["name"] == "INFERRED"
    assert result.suggested_fields["client"] == "Detroit Public Schools Community District"
    assert result.extracted_deadline == "January 5, 2026"
    assert result.suggested_fields["lead_time_days"] is None
    assert result.field_statuses["lead_time_days"] == "MISSING"
