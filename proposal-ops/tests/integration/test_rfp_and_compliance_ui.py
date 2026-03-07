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
    assert "Parsed Solicitation Versions" in page.text


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

    upload_page = client.get(f"/opportunities/{opportunity_id}/rfp-upload")
    assert upload_page.status_code == 200
    assert "Version" in upload_page.text
    assert "Reparse This Version" in upload_page.text
    assert "Reparse Edited Document Set" in upload_page.text
    assert "Compare Versions" in upload_page.text
    assert "Parsed documents only" in upload_page.text
    assert "Retain source documents" in upload_page.text

    source_versions = client.get(f"/api/opportunities/{opportunity_id}/rfp/versions")
    assert source_versions.status_code == 200
    first_version = source_versions.json()[0]
    retained_document_id = first_version["source_documents"][0]["id"]

    reparse = client.post(
        f"/opportunities/{opportunity_id}/rfp/reparse-document-set",
        data={
            "actor": "operator",
            "source_solicitation_id": first_version["solicitation_id"],
            "retain_document_ids": [retained_document_id],
        },
        files=[
            (
                "files",
                (
                    "pricing-ui.txt",
                    (
                        "Evaluation criteria include pricing.\n"
                        "The offeror must submit a pricing narrative.\n"
                    ).encode("utf-8"),
                    "text/plain",
                ),
            )
        ],
        follow_redirects=False,
    )
    assert reparse.status_code == 303

    upload_page_after = client.get(f"/opportunities/{opportunity_id}/rfp-upload")
    assert upload_page_after.status_code == 200
    assert "Version" in upload_page_after.text
    assert upload_page_after.text.count("Reparse This Version") == 2
    assert "Version Comparison" in upload_page_after.text
    assert "Changed Requirements" in upload_page_after.text
    assert "pricing-ui.txt" in upload_page_after.text
    assert "Document Diff Records" in upload_page_after.text

    third_parse = client.post(
        f"/opportunities/{opportunity_id}/rfp-upload",
        data={
            "raw_text": (
                "Proposal due date is 2026-08-05.\n"
                "Contractor shall provide staffing plan.\n"
                "Contractor must submit pricing narrative.\n"
                "Contractor shall provide a management transition checklist.\n"
            ),
            "source_filename": "ui-rfp-v3.txt",
            "actor": "operator",
        },
        follow_redirects=False,
    )
    assert third_parse.status_code == 303

    versions_after = client.get(f"/api/opportunities/{opportunity_id}/rfp/versions")
    assert versions_after.status_code == 200
    latest_version = versions_after.json()[0]

    compared_page = client.get(
        f"/opportunities/{opportunity_id}/rfp-upload",
        params={
            "base_solicitation_id": first_version["solicitation_id"],
            "compare_solicitation_id": latest_version["solicitation_id"],
        },
    )
    assert compared_page.status_code == 200
    assert "Compare Versions" in compared_page.text
    assert "Version 3 compared to Version 1" in compared_page.text


def test_rfp_upload_page_shows_download_and_replace_for_stored_binary_documents(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    parsed = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        files={
            "file": (
                "stored-ui.txt",
                (
                    "Proposal due date is 2026-08-09.\n"
                    "The offeror shall provide a management transition plan.\n"
                ).encode("utf-8"),
                "text/plain",
            )
        },
        data={"actor": "operator"},
    )
    assert parsed.status_code == 200
    payload = parsed.json()
    source_document_id = payload["source_documents"][0]["id"]

    page = client.get(f"/opportunities/{opportunity_id}/rfp-upload")
    assert page.status_code == 200
    assert "Download Original" in page.text
    assert "Replace This Document" in page.text
    assert "stored binary" in page.text

    download = client.get(f"/api/opportunities/{opportunity_id}/rfp/source-documents/{source_document_id}/download")
    assert download.status_code == 200
    assert b"management transition plan" in download.content

    replaced = client.post(
        f"/opportunities/{opportunity_id}/rfp/source-documents/{source_document_id}/replace",
        data={
            "actor": "operator",
            "source_solicitation_id": payload["solicitation_id"],
        },
        files={
            "file": (
                "stored-ui-v2.txt",
                (
                    "Proposal due date is 2026-08-09.\n"
                    "The offeror shall provide a management transition plan within 5 days.\n"
                ).encode("utf-8"),
                "text/plain",
            )
        },
        follow_redirects=False,
    )
    assert replaced.status_code == 303

    page_after = client.get(f"/opportunities/{opportunity_id}/rfp-upload")
    assert page_after.status_code == 200
    assert "stored-ui-v2.txt" in page_after.text
