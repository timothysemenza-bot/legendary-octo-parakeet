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

