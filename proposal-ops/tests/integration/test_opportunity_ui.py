from fastapi.testclient import TestClient


def test_intake_form_renders(client: TestClient) -> None:
    response = client.get("/intake")
    assert response.status_code == 200
    assert "Opportunity Intake" in response.text
    assert "Start From RFP Files" in response.text
    assert "Manual Intake Backup" in response.text
    assert "Build Intake Draft From RFP Files" in response.text


def test_successful_web_submission_shows_score(client: TestClient) -> None:
    response = client.post(
        "/intake",
        data={
            "name": "Operations Pursuit",
            "client": "Metro Transit",
            "estimated_contract_value": "900000",
            "lead_time_days": "35",
            "strategic_alignment": "4",
            "estimated_probability_win": "70",
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    assert "Intake Result" in response.text
    assert "Qualification Score" in response.text


def test_rfp_first_web_submission_redirects_to_review_draft(client: TestClient) -> None:
    response = client.post(
        "/intake/rfp-drafts",
        data={"actor": "operator"},
        files=[
            (
                "files",
                (
                    "regional-ops-rfp.txt",
                    (
                        "REQUEST FOR PROPOSALS\n"
                        "Regional Operations Support Services\n"
                        "Issued by: City of Springfield\n"
                        "The estimated contract value is $1,250,000.\n"
                        "Proposal due date is 2026-04-20.\n"
                        "The contractor shall provide a staffing plan.\n"
                    ).encode("utf-8"),
                    "text/plain",
                ),
            ),
            ("files", ("legacy.xls", b"binary", "application/vnd.ms-excel")),
        ],
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/intake/rfp-drafts/" in response.headers["location"]

    review = client.get(response.headers["location"])
    assert review.status_code == 200
    assert "Review Intake Draft" in review.text
    assert "Regional Operations Support Services" in review.text
    assert "legacy.xls" in review.text
    assert "DEFAULTED" in review.text
    assert "Source Document Manifest" in review.text
    assert "application/vnd.ms-excel" in review.text


def test_rfp_first_review_confirm_creates_opportunity(client: TestClient) -> None:
    create = client.post(
        "/intake/rfp-drafts",
        data={"actor": "operator"},
        files=[
            (
                "files",
                (
                    "regional-ops-rfp.txt",
                    (
                        "REQUEST FOR PROPOSALS\n"
                        "Regional Operations Support Services\n"
                        "Issued by: City of Springfield\n"
                        "The estimated contract value is $1,250,000.\n"
                        "Proposal due date is 2026-04-20.\n"
                        "Evaluation criteria include technical approach and pricing.\n"
                        "The contractor shall provide a staffing plan.\n"
                    ).encode("utf-8"),
                    "text/plain",
                ),
            ),
        ],
        follow_redirects=False,
    )
    draft_path = create.headers["location"]
    draft_page = client.get(draft_path)
    assert draft_page.status_code == 200

    confirm = client.post(
        f"{draft_path}/confirm",
        data={
            "name": "Regional Operations Support Services",
            "client": "City of Springfield",
            "estimated_contract_value": "1250000",
            "lead_time_days": "45",
            "strategic_alignment": "3",
            "estimated_probability_win": "50",
            "actor": "operator",
        },
    )
    assert confirm.status_code == 200
    assert "Intake Result" in confirm.text
    assert "RFP Parse Summary" in confirm.text
    assert "Source Document Manifest" in confirm.text
    assert "Open Compliance Matrix" in confirm.text


def test_rfp_first_review_blocks_missing_required_fields(client: TestClient) -> None:
    create = client.post(
        "/intake/rfp-drafts",
        data={"actor": "operator"},
        files=[
            (
                "files",
                (
                    "minimal-rfp.txt",
                    (
                        "REQUEST FOR PROPOSALS\n"
                        "Operations Support Services\n"
                        "Proposal due date is 2026-04-20.\n"
                        "The contractor shall provide a staffing plan.\n"
                    ).encode("utf-8"),
                    "text/plain",
                ),
            ),
        ],
        follow_redirects=False,
    )
    draft_path = create.headers["location"]

    confirm = client.post(
        f"{draft_path}/confirm",
        data={
            "name": "Operations Support Services",
            "client": "",
            "estimated_contract_value": "",
            "lead_time_days": "45",
            "strategic_alignment": "3",
            "estimated_probability_win": "50",
            "actor": "operator",
        },
    )
    assert confirm.status_code == 422
    assert "Submission Errors" in confirm.text
    assert "Client:" in confirm.text
    assert "Estimated Contract Value:" in confirm.text
    assert "MISSING" in confirm.text

    listing = client.get("/api/opportunities")
    assert listing.status_code == 200
    assert listing.json() == []


def test_successful_web_submission_with_rfp_batch_shows_parse_summary(client: TestClient) -> None:
    response = client.post(
        "/intake-with-rfp",
        data={
            "name": "Operations Pursuit",
            "client": "Metro Transit",
            "estimated_contract_value": "900000",
            "lead_time_days": "35",
            "strategic_alignment": "4",
            "estimated_probability_win": "70",
            "actor": "operator",
        },
        files=[
            (
                "files",
                (
                    "scope.txt",
                    (
                        "Proposal due date is 2026-08-01.\n"
                        "Evaluation criteria include technical approach and pricing.\n"
                        "The contractor shall provide staffing plan.\n"
                    ).encode("utf-8"),
                    "text/plain",
                ),
            ),
            ("files", ("legacy.xls", b"binary", "application/vnd.ms-excel")),
        ],
    )
    assert response.status_code == 200
    assert "RFP Parse Summary" in response.text
    assert "Source Document Manifest" in response.text
    assert "scope.txt" in response.text
    assert "legacy.xls" in response.text
    assert "Open Compliance Matrix" in response.text


def test_web_submission_with_only_invalid_rfp_files_returns_form_errors(client: TestClient) -> None:
    response = client.post(
        "/intake-with-rfp",
        data={
            "name": "Operations Pursuit",
            "client": "Metro Transit",
            "estimated_contract_value": "900000",
            "lead_time_days": "35",
            "strategic_alignment": "4",
            "estimated_probability_win": "70",
            "actor": "operator",
        },
        files=[("files", ("legacy.xls", b"binary", "application/vnd.ms-excel"))],
    )
    assert response.status_code == 422
    assert "Submission Errors" in response.text
    assert "No uploaded RFP files produced parsable text." in response.text
    assert "Unsupported file type" in response.text

    listing = client.get("/api/opportunities")
    assert listing.status_code == 200
    assert listing.json() == []


def test_detail_page_shows_gate_decision_history(client: TestClient) -> None:
    intake = client.post(
        "/api/opportunities/intake",
        json={
            "name": "Transit Security RFP",
            "client": "Metro Transit",
            "estimated_contract_value": 400000,
            "lead_time_days": 25,
            "incumbent_status": True,
            "strategic_alignment": 3,
            "estimated_probability_win": 55,
            "actor": "operator",
        },
    ).json()

    decision = client.post(
        f"/opportunities/{intake['id']}/gate-decisions",
        data={
            "decision": "REWORK_REQUIRED",
            "decider": "lead-consultant",
            "rationale": "Need stronger win themes before approval.",
            "gate_code": "BID_NO_BID",
            "rework_instructions": "Draft stronger customer-specific win themes.",
        },
        follow_redirects=False,
    )
    assert decision.status_code == 303

    detail = client.get(f"/opportunities/{intake['id']}")
    assert detail.status_code == 200
    assert "Gate Decisions" in detail.text
    assert "REWORK_REQUIRED" in detail.text


def test_gate_inbox_page_renders_and_accepts_decision(client: TestClient) -> None:
    intake = client.post(
        "/api/opportunities/intake",
        json={
            "name": "Airport Operations RFP",
            "client": "Metro Airport",
            "estimated_contract_value": 725000,
            "lead_time_days": 35,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 62,
            "actor": "operator",
        },
    ).json()

    inbox = client.get("/gates/inbox")
    assert inbox.status_code == 200
    assert "Gate Inbox" in inbox.text
    assert "Airport Operations RFP" in inbox.text

    decide = client.post(
        "/gates/inbox/decide",
        data={
            "opportunity_id": intake["id"],
            "gate_code": "GATE_A",
            "decision": "APPROVED",
            "decider": "lead-consultant",
            "rationale": "Qualified for strategy.",
        },
        follow_redirects=False,
    )
    assert decide.status_code == 303

    detail = client.get(f"/api/opportunities/{intake['id']}").json()
    assert detail["stage"] == "STRATEGY"


def test_workflow_timeline_page_renders_and_filters(client: TestClient) -> None:
    intake = client.post(
        "/api/opportunities/intake",
        json={
            "name": "Timeline Pursuit",
            "client": "Timeline Client",
            "estimated_contract_value": 500000,
            "lead_time_days": 30,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 60,
            "actor": "operator",
        },
    ).json()

    page = client.get(f"/opportunities/{intake['id']}/timeline")
    assert page.status_code == 200
    assert "Workflow Timeline" in page.text
    assert "Category" in page.text

    filtered = client.get(f"/opportunities/{intake['id']}/timeline?category=GATE")
    assert filtered.status_code == 200
    assert "Workflow Timeline" in filtered.text
