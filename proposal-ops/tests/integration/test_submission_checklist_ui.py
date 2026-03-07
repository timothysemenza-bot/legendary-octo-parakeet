from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "UI Submission Pursuit",
            "client": "Metro Utilities",
            "estimated_contract_value": 510000,
            "lead_time_days": 28,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 61,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def _prepare_outline(client: TestClient, opportunity_id: str) -> list[str]:
    parsed = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": (
                "Proposal due date is 2026-05-30 and submissions must be uploaded electronically.\n"
                "Evaluation criteria include technical approach, management, and pricing.\n"
                "The contractor shall provide a staffing plan and must submit past performance references.\n"
                "Offeror must provide a detailed pricing narrative."
            ),
            "source_filename": "rfp.txt",
            "actor": "operator",
        },
    )
    assert parsed.status_code == 200
    rows = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix").json()
    assert len(rows) >= 2
    outline = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-outline/manual",
        json={
            "actor": "operator",
            "sections": [
                {
                    "sequence": 1,
                    "proposal_section": "Executive Summary",
                    "owner": "Proposal Manager",
                    "requirement_ids": [rows[0]["requirement_id"]],
                },
                {
                    "sequence": 2,
                    "proposal_section": "Technical Approach",
                    "owner": "Section Owner",
                    "requirement_ids": [rows[1]["requirement_id"]],
                },
            ],
        },
    )
    assert outline.status_code == 200
    return [section["proposal_section"] for section in outline.json()["sections"]]


def test_submission_dashboard_renders(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    page = client.get(f"/opportunities/{opportunity_id}/submission")
    assert page.status_code == 200
    assert "Submission Readiness" in page.text
    assert "Checklist Items" in page.text


def test_submission_filename_validation_web_flow(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    post = client.post(
        f"/opportunities/{opportunity_id}/submission/validate-filenames",
        data={"file_names": "Proposal_Main.docx\nPricing_Sheet.xlsx", "actor": "operator"},
        follow_redirects=False,
    )
    assert post.status_code == 303
    refreshed = client.get(f"/opportunities/{opportunity_id}/submission")
    assert refreshed.status_code == 200
    assert "FILE_NAMING_VALIDATED" in refreshed.text


def test_submission_package_validation_web_flow(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    sections = _prepare_outline(client, opportunity_id)
    post = client.post(
        f"/opportunities/{opportunity_id}/submission/validate-package",
        data={"section_names": "\n".join(sections), "actor": "operator"},
        follow_redirects=False,
    )
    assert post.status_code == 303

    refreshed = client.get(f"/opportunities/{opportunity_id}/submission")
    assert refreshed.status_code == 200
    assert "Package Structure Validation" in refreshed.text
    assert "DOCUMENT_STRUCTURE_VALIDATED" in refreshed.text
    assert "Validated against outline v1" in refreshed.text
