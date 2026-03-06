from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "UI Flow Pursuit",
            "client": "Transit Authority",
            "estimated_contract_value": 500000,
            "lead_time_days": 30,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 60,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_rfp_upload_page_renders(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    page = client.get(f"/opportunities/{opportunity_id}/rfp-upload")
    assert page.status_code == 200
    assert "RFP Parser" in page.text


def test_compliance_matrix_page_after_parse(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    post = client.post(
        f"/opportunities/{opportunity_id}/rfp-upload",
        data={
            "raw_text": "Proposal due date is 2026-08-01. Contractor shall provide staffing plan. Contractor must submit pricing narrative.",
            "source_filename": "ui-rfp.txt",
            "actor": "operator",
        },
        follow_redirects=False,
    )
    assert post.status_code == 303
    matrix = client.get(f"/opportunities/{opportunity_id}/compliance-matrix")
    assert matrix.status_code == 200
    assert "Compliance Matrix" in matrix.text
    assert "REQ-" in matrix.text

