from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    body = {
        "name": "Regional Facilities Proposal",
        "client": "Metro County",
        "estimated_contract_value": 950000,
        "lead_time_days": 40,
        "incumbent_status": False,
        "strategic_alignment": 4,
        "estimated_probability_win": 68,
        "actor": "operator",
    }
    response = client.post("/api/opportunities/intake", json=body)
    assert response.status_code == 200
    return response.json()["id"]


def test_rfp_parse_generates_requirements_and_matrix(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    raw_text = """
    Proposal due date is 2026-07-15.
    Evaluation criteria include technical approach and pricing.
    The offeror shall provide a technical transition plan.
    The offeror must submit past performance references.
    """
    parsed = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": raw_text,
            "source_filename": "sample-rfp.txt",
            "actor": "operator",
        },
    )
    assert parsed.status_code == 200
    payload = parsed.json()
    assert payload["requirement_count"] >= 2
    assert payload["solicitation_id"]
    assert payload["solicitation_version"] == 1
    assert len(payload["source_documents"]) == 1
    assert payload["source_documents"][0]["source_filename"] == "sample-rfp.txt"
    assert payload["source_documents"][0]["parse_status"] == "PARSED"
    assert payload["source_documents"][0]["has_stored_binary"] is False
    assert payload["source_documents"][0]["document_family_id"]

    matrix = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix")
    assert matrix.status_code == 200
    rows = matrix.json()
    assert len(rows) == payload["requirement_count"]
    assert "proposal_section" in rows[0]
    assert "requirement_type" in rows[0]


def test_rfp_reparse_creates_new_solicitation_version_and_preserves_history(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    raw_text = (
        "Proposal due date is 2026-07-15.\n"
        "Evaluation criteria include technical approach and pricing.\n"
        "The offeror shall provide a technical transition plan.\n"
        "The offeror must submit past performance references.\n"
    )
    first = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": raw_text,
            "source_filename": "sample-rfp.txt",
            "actor": "operator",
        },
    )
    assert first.status_code == 200
    first_payload = first.json()

    versions_before = client.get(f"/api/opportunities/{opportunity_id}/rfp/versions")
    assert versions_before.status_code == 200
    assert [row["version"] for row in versions_before.json()] == [1]

    reparsed = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/reparse",
        json={"actor": "operator"},
    )
    assert reparsed.status_code == 200
    reparsed_payload = reparsed.json()
    assert reparsed_payload["solicitation_version"] == 2
    assert reparsed_payload["solicitation_id"] != first_payload["solicitation_id"]
    assert reparsed_payload["requirement_count"] == first_payload["requirement_count"]
    assert reparsed_payload["source_documents"][0]["source_filename"] == "sample-rfp.txt"

    versions_after = client.get(f"/api/opportunities/{opportunity_id}/rfp/versions")
    assert versions_after.status_code == 200
    versions = versions_after.json()
    assert [row["version"] for row in versions] == [2, 1]
    assert versions[0]["requirement_count"] == reparsed_payload["requirement_count"]
    assert versions[1]["solicitation_id"] == first_payload["solicitation_id"]

    matrix = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix")
    assert matrix.status_code == 200
    assert len(matrix.json()) == reparsed_payload["requirement_count"]

    detail = client.get(f"/api/opportunities/{opportunity_id}").json()
    actions = [event["action"] for event in detail["audit_events"]]
    assert "rfp_reparsed" in actions


def test_rfp_file_upload_persists_binary_provenance_and_supports_binary_reparse(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    parsed = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        files={
            "file": (
                "uploaded-rfp.txt",
                (
                    "Proposal due date is 2026-09-01.\n"
                    "The offeror shall provide a transition plan.\n"
                ).encode("utf-8"),
                "text/plain",
            )
        },
        data={"actor": "operator"},
    )
    assert parsed.status_code == 200
    payload = parsed.json()
    assert payload["source_documents"][0]["has_stored_binary"] is True
    assert payload["source_documents"][0]["source_sha256"]
    assert payload["source_documents"][0]["document_family_id"]

    retained_document_id = payload["source_documents"][0]["id"]
    retained_document_family_id = payload["source_documents"][0]["document_family_id"]
    download = client.get(
        f"/api/opportunities/{opportunity_id}/rfp/source-documents/{retained_document_id}/download"
    )
    assert download.status_code == 200
    assert b"transition plan" in download.content

    reparsed = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/reparse-document-set",
        data={
            "actor": "operator",
            "source_solicitation_id": payload["solicitation_id"],
            "retain_document_ids": [retained_document_id],
        },
    )
    assert reparsed.status_code == 200
    reparsed_payload = reparsed.json()
    assert reparsed_payload["solicitation_version"] == 2
    assert reparsed_payload["source_documents"][0]["has_stored_binary"] is True
    assert reparsed_payload["source_documents"][0]["source_sha256"] == payload["source_documents"][0]["source_sha256"]
    assert reparsed_payload["source_documents"][0]["document_family_id"] == retained_document_family_id


def test_rfp_compare_and_reparse_with_manifest_overrides(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    first = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": (
                "Proposal due date is 2026-07-15.\n"
                "Evaluation criteria include technical approach and pricing.\n"
                "The offeror shall provide a technical transition plan within 30 days.\n"
            ),
            "source_filename": "scope.txt",
            "actor": "operator",
        },
    )
    assert first.status_code == 200
    first_payload = first.json()

    second = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": (
                "Proposal due date is 2026-07-15.\n"
                "Evaluation criteria include technical approach, pricing, and management.\n"
                "The offeror shall provide a technical transition plan within 15 days.\n"
                "The offeror must submit past performance references.\n"
            ),
            "source_filename": "scope.txt",
            "actor": "operator",
        },
    )
    assert second.status_code == 200
    second_payload = second.json()

    comparison = client.get(
        f"/api/opportunities/{opportunity_id}/rfp/compare",
        params={
            "base_solicitation_id": first_payload["solicitation_id"],
            "compare_solicitation_id": second_payload["solicitation_id"],
        },
    )
    assert comparison.status_code == 200
    comparison_payload = comparison.json()
    assert comparison_payload["base_version"] == 1
    assert comparison_payload["compare_version"] == 2
    assert comparison_payload["added_requirement_codes"]
    assert comparison_payload["added_documents"] == []
    assert comparison_payload["removed_documents"] == []
    assert comparison_payload["changed_documents"] == ["scope.txt"]
    assert len(comparison_payload["changed_document_records"]) == 1
    assert comparison_payload["changed_document_records"][0]["label"] == "scope.txt"
    assert len(comparison_payload["changed_requirements"]) == 1
    assert comparison_payload["changed_requirements"][0]["base_requirement_code"] == "REQ-001"
    assert "30 days" in comparison_payload["changed_requirements"][0]["base_requirement_text"]
    assert "15 days" in comparison_payload["changed_requirements"][0]["compare_requirement_text"]

    reparsed = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/reparse",
        json={
            "actor": "operator",
            "source_solicitation_id": second_payload["solicitation_id"],
            "source_documents": [
                {
                    "source_filename": "scope-v2-reparsed.txt",
                    "content_type": "text/plain",
                    "parse_status": "PARSED",
                    "skip_reason": None,
                    "upload_order": 1,
                    "source_size_bytes": 999,
                    "extracted_text_length": 123,
                    "content_text": (
                        "Proposal due date is 2026-07-15.\n"
                        "Evaluation criteria include technical approach, pricing, and management.\n"
                        "The offeror shall provide a technical transition plan within 10 days.\n"
                        "The offeror must submit past performance references.\n"
                    ),
                }
            ],
        },
    )
    assert reparsed.status_code == 200
    reparsed_payload = reparsed.json()
    assert reparsed_payload["solicitation_version"] == 3
    assert reparsed_payload["source_documents"][0]["source_filename"] == "scope-v2-reparsed.txt"
    assert reparsed_payload["source_documents"][0]["source_size_bytes"] == 999


def test_rfp_reparse_document_set_supports_removals_and_new_uploads(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    initial = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": (
                "Proposal due date is 2026-07-15.\n"
                "The offeror shall provide a technical transition plan.\n"
            ),
            "source_filename": "scope.txt",
            "actor": "operator",
        },
    )
    assert initial.status_code == 200
    initial_payload = initial.json()
    retained_document_id = initial_payload["source_documents"][0]["id"]

    reparsed = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/reparse-document-set",
        data={
            "actor": "operator",
            "source_solicitation_id": initial_payload["solicitation_id"],
            "retain_document_ids": [retained_document_id],
        },
        files=[
            (
                "files",
                (
                    "pricing.txt",
                    (
                        "Evaluation criteria include pricing.\n"
                        "The offeror must submit a pricing narrative.\n"
                    ).encode("utf-8"),
                    "text/plain",
                ),
            )
        ],
    )
    assert reparsed.status_code == 200
    payload = reparsed.json()
    assert payload["solicitation_version"] == 2
    assert {row["source_filename"] for row in payload["source_documents"]} == {"scope.txt", "pricing.txt"}
    assert payload["requirement_count"] >= 2

    replacement = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/reparse-document-set",
        data={
            "actor": "operator",
            "source_solicitation_id": payload["solicitation_id"],
        },
        files=[
            (
                "files",
                (
                    "replacement.txt",
                    (
                        "Proposal due date is 2026-08-01.\n"
                        "The contractor shall provide a management staffing plan.\n"
                    ).encode("utf-8"),
                    "text/plain",
                ),
            )
        ],
    )
    assert replacement.status_code == 200
    replacement_payload = replacement.json()
    assert replacement_payload["solicitation_version"] == 3
    assert [row["source_filename"] for row in replacement_payload["source_documents"]] == ["replacement.txt"]
    assert replacement_payload["source_documents"][0]["has_stored_binary"] is True


def test_rfp_compare_uses_document_family_ids_for_duplicate_filenames(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    first = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        files={
            "file": (
                "scope.txt",
                (
                    "Proposal due date is 2026-07-15.\n"
                    "The offeror shall provide a technical transition plan.\n"
                ).encode("utf-8"),
                "text/plain",
            )
        },
        data={"actor": "operator"},
    )
    assert first.status_code == 200
    first_payload = first.json()
    retained_document_id = first_payload["source_documents"][0]["id"]

    second = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/reparse-document-set",
        data={
            "actor": "operator",
            "source_solicitation_id": first_payload["solicitation_id"],
            "retain_document_ids": [retained_document_id],
        },
        files=[
            (
                "files",
                (
                    "scope.txt",
                    (
                        "Evaluation criteria include pricing.\n"
                        "The offeror must submit a pricing narrative.\n"
                    ).encode("utf-8"),
                    "text/plain",
                ),
            )
        ],
    )
    assert second.status_code == 200
    second_payload = second.json()

    comparison = client.get(
        f"/api/opportunities/{opportunity_id}/rfp/compare",
        params={
            "base_solicitation_id": first_payload["solicitation_id"],
            "compare_solicitation_id": second_payload["solicitation_id"],
        },
    )
    assert comparison.status_code == 200
    payload = comparison.json()
    assert payload["added_document_records"]
    assert payload["added_document_records"][0]["base_source_document_id"] is None
    assert payload["added_document_records"][0]["label"].startswith("scope.txt")
    assert payload["added_document_records"][0]["document_family_id"] != first_payload["source_documents"][0][
        "document_family_id"
    ]


def test_rfp_replace_source_document_creates_new_version_and_preserves_family_id(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    initial = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        files={
            "file": (
                "scope.txt",
                (
                    "Proposal due date is 2026-07-15.\n"
                    "The offeror shall provide a technical transition plan.\n"
                ).encode("utf-8"),
                "text/plain",
            )
        },
        data={"actor": "operator"},
    )
    assert initial.status_code == 200
    initial_payload = initial.json()
    source_document = initial_payload["source_documents"][0]

    replaced = client.post(
        f"/api/opportunities/{opportunity_id}/rfp/source-documents/{source_document['id']}/replace",
        data={
            "actor": "operator",
            "source_solicitation_id": initial_payload["solicitation_id"],
        },
        files={
            "file": (
                "scope-replaced.txt",
                (
                    "Proposal due date is 2026-07-15.\n"
                    "The offeror shall provide a technical transition plan within 7 days.\n"
                ).encode("utf-8"),
                "text/plain",
            )
        },
    )
    assert replaced.status_code == 200
    replaced_payload = replaced.json()
    assert replaced_payload["solicitation_version"] == 2
    assert replaced_payload["source_documents"][0]["source_filename"] == "scope-replaced.txt"
    assert replaced_payload["source_documents"][0]["document_family_id"] == source_document["document_family_id"]

    comparison = client.get(
        f"/api/opportunities/{opportunity_id}/rfp/compare",
        params={
            "base_solicitation_id": initial_payload["solicitation_id"],
            "compare_solicitation_id": replaced_payload["solicitation_id"],
        },
    )
    assert comparison.status_code == 200
    comparison_payload = comparison.json()
    assert comparison_payload["added_documents"] == []
    assert comparison_payload["removed_documents"] == []
    assert comparison_payload["changed_document_records"][0]["base_source_filename"] == "scope.txt"
    assert comparison_payload["changed_document_records"][0]["compare_source_filename"] == "scope-replaced.txt"


def test_compliance_row_update(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": "The contractor shall provide a staffing plan and must submit pricing narrative by 05/20/2026.",
            "source_filename": "rfp.txt",
            "actor": "operator",
        },
    )
    rows = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix").json()
    row_id = rows[0]["id"]
    updated = client.patch(
        f"/api/compliance-matrix/{row_id}",
        json={
            "proposal_section": "Management Plan",
            "owner": "Jane Reviewer",
            "status": "IN_PROGRESS",
            "actor": "operator",
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["owner"] == "Jane Reviewer"
    assert body["status"] == "IN_PROGRESS"


def test_compliance_matrix_hides_context_only_by_default(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": (
                "Dealer/Distributor – means a relationship definition.\n"
                "The Bidder must submit its pricing using the State-Supplied Price Sheet."
            ),
            "source_filename": "rfp.txt",
            "actor": "operator",
        },
    )

    default_rows = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix").json()
    assert len(default_rows) >= 1
    assert all(row["requirement_type"] != "CONTEXT_ONLY" for row in default_rows)

    with_context = client.get(
        f"/api/opportunities/{opportunity_id}/compliance-matrix?include_context=true"
    ).json()
    # No context matrix rows are generated; context stays in parsed requirements only.
    assert len(with_context) == len(default_rows)


def test_compliance_matrix_quality_endpoint_reports_gate_c_readiness(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": (
                "The Bidder must submit pricing sheet.\n"
                "The Contractor shall provide staffing plan.\n"
            ),
            "source_filename": "rfp.txt",
            "actor": "operator",
        },
    )

    quality = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix/quality")
    assert quality.status_code == 200
    payload = quality.json()
    assert payload["gate_c_ready"] is False
    assert payload["unmapped_rows"] >= 1
    assert payload["missing_owner_rows"] >= 1

    rows = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix").json()
    for row in rows:
        update = client.patch(
            f"/api/compliance-matrix/{row['id']}",
            json={
                "proposal_section": row["proposal_section"],
                "owner": "Compliance Lead",
                "status": "COMPLETE",
                "actor": "operator",
            },
        )
        assert update.status_code == 200

    quality_after = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix/quality")
    assert quality_after.status_code == 200
    payload_after = quality_after.json()
    assert payload_after["gate_c_ready"] is True
    assert payload_after["unmapped_rows"] == 0
    assert payload_after["missing_owner_rows"] == 0
