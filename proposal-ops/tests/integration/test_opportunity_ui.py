from fastapi.testclient import TestClient


def test_intake_form_renders(client: TestClient) -> None:
    response = client.get("/intake")
    assert response.status_code == 200
    assert "Opportunity Intake" in response.text


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
