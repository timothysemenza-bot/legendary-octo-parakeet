from datetime import date, datetime, time, timedelta

from fastapi.testclient import TestClient


def test_dashboard_and_seed_demo_ui(client: TestClient) -> None:
    overdue_follow_up = (date.today() - timedelta(days=7)).isoformat()

    page = client.get("/dashboard")
    assert page.status_code == 200
    assert "Janitorial Capture Dashboard" in page.text

    seeded = client.post("/dashboard/seed-demo", follow_redirects=True)
    assert seeded.status_code == 200
    assert "Upcoming Rebids" in seeded.text
    assert "South Jersey Regional Airport" in seeded.text
    assert "Upcoming Contractor Follow-Ups" in seeded.text
    assert "Garden State Facility Services" in seeded.text

    overdue = client.post(
        "/api/contractors",
        json={
            "name": "Escalation Janitorial Prospect",
            "service_geographies": "NJ",
            "headquarters_city": "Trenton",
            "headquarters_state": "NJ",
            "vertical_experience": "education",
            "labor_profile": "W2 self-perform",
            "union_profile": "non-union",
            "diversity_certs": "",
            "airport_experience": False,
            "healthcare_experience": False,
            "education_experience": True,
            "municipal_experience": False,
            "scale_band": "LOCAL",
            "relationship_strength": 2,
            "prospect_stage": "OUTREACH",
            "next_follow_up_date": overdue_follow_up,
            "relationship_notes": "Missed callback window.",
            "strategic_fit_notes": "Possible subcontractor path.",
        },
    )
    assert overdue.status_code == 200

    refreshed = client.get("/dashboard")
    assert refreshed.status_code == 200
    assert "Overdue Contractor Follow-Ups" in refreshed.text
    assert "Escalation Janitorial Prospect" in refreshed.text


def test_contract_radar_ui_and_create_pursuit_from_contract_flow(client: TestClient) -> None:
    client.post("/api/dashboard/seed-demo")

    contracts = client.get("/contracts")
    assert contracts.status_code == 200
    assert "Contract Radar" in contracts.text
    assert "Create Contract" in contracts.text

    contract_list = client.get("/api/contracts").json()
    contract = contract_list[0]
    detail = client.get(f"/contracts/{contract['id']}")
    assert detail.status_code == 200
    assert "Create Pursuit From Contract" in detail.text

    create = client.post(
        f"/contracts/{contract['id']}/pursuits",
        data={
            "title": "Airport Capture Pursuit",
            "primary_facility_id": contract["facility_ids"][0],
            "pursuit_stage": "INTELLIGENCE",
            "confidence_level": "HIGH",
            "expected_rfp_date": "2026-08-15",
            "provenance_summary": "Created from public radar record.",
            "strategic_fit": "4",
            "incumbent_vulnerability": "3",
            "rebid_probability": "4",
            "relationship_access": "3",
            "contractor_fit": "3",
            "operational_complexity": "4",
            "margin_potential": "3",
            "pre_rfp_influence": "4",
            "timeline_urgency": "4",
            "actor": "operator",
        },
        follow_redirects=False,
    )
    assert create.status_code == 303
    assert "/opportunities/" in create.headers["location"]

    opp_detail = client.get(create.headers["location"])
    assert opp_detail.status_code == 200
    assert "Capture Workbench" in opp_detail.text
    assert "Airport Capture Pursuit" in opp_detail.text


def test_capture_workbench_ui_forms(client: TestClient) -> None:
    client.post("/api/dashboard/seed-demo")
    contract = client.get("/api/contracts").json()[0]
    pursuit = client.post(
        f"/api/contracts/{contract['id']}/pursuits",
        json={
            "title": "Workbench Pursuit",
            "primary_facility_id": contract["facility_ids"][0],
            "pursuit_stage": "INTELLIGENCE",
            "confidence_level": "MEDIUM",
            "expected_rfp_date": "2026-08-15",
            "provenance_summary": "Public source trail.",
            "strategic_fit": 4,
            "incumbent_vulnerability": 3,
            "rebid_probability": 4,
            "relationship_access": 3,
            "contractor_fit": 3,
            "operational_complexity": 4,
            "margin_potential": 3,
            "pre_rfp_influence": 4,
            "timeline_urgency": 4,
            "actor": "operator",
        },
    ).json()

    workbench_path = f"/opportunities/{pursuit['id']}/capture-workbench"
    workbench = client.get(workbench_path)
    assert workbench.status_code == 200
    assert "Capture Workbench" in workbench.text
    assert "Use only lawful and ethical intelligence sources." in workbench.text

    refresh = client.post(f"{workbench_path}/matches", follow_redirects=True)
    assert refresh.status_code == 200
    assert "Contractor Matching" in refresh.text

    add_note = client.post(
        f"{workbench_path}/intelligence",
        data={
            "title": "Evaluator hypothesis",
            "note_type": "POSITIONING",
            "note_text": "Likely emphasis on visible cleanliness and transition speed.",
            "source_class": "INFERRED",
            "provenance": "Public board commentary and current contract complaints.",
            "confidence_level": "MEDIUM",
        },
        follow_redirects=True,
    )
    assert add_note.status_code == 200
    assert "Evaluator hypothesis" in add_note.text

    add_commercial = client.post(
        f"{workbench_path}/commercials",
        data={
            "retainer_amount": "6000",
            "success_fee_type": "FIXED",
            "success_fee_value": "12000",
            "notes": "Managed pursuit model",
        },
        follow_redirects=True,
    )
    assert add_commercial.status_code == 200
    assert "Weighted Expected Value" in add_commercial.text


def test_contractor_prospecting_ui(client: TestClient) -> None:
    initial_follow_up = (date.today() + timedelta(days=33)).isoformat()
    next_follow_up = (date.today() + timedelta(days=10)).isoformat()
    touchpoint_at = datetime.combine(date.today(), time(hour=9, minute=30)).strftime("%Y-%m-%dT%H:%M")

    contractors = client.get("/contractors")
    assert contractors.status_code == 200
    assert "Create Contractor Prospect" in contractors.text
    assert '<select name="scale_band">' in contractors.text
    assert '<select name="prospect_stage">' in contractors.text

    created = client.post(
        "/contractors",
        data={
            "name": "Prospect Building Services",
            "service_geographies": "NJ PA",
            "headquarters_city": "Camden",
            "headquarters_state": "NJ",
            "vertical_experience": "education municipal",
            "labor_profile": "W2 self-perform",
            "union_profile": "non-union",
            "diversity_certs": "WBE",
            "scale_band": "REGIONAL",
            "relationship_strength": "2",
            "prospect_stage": "OUTREACH",
            "next_follow_up_date": initial_follow_up,
            "relationship_notes": "Intro pending from broker relationship.",
            "strategic_fit_notes": "Could fit mid-market public portfolio work.",
        },
        follow_redirects=True,
    )
    assert created.status_code == 200
    assert "Prospect Building Services" in created.text
    assert "OUTREACH" in created.text

    filtered = client.get("/contractors", params={"prospect_stage": "OUTREACH"})
    assert filtered.status_code == 200
    assert "Prospect Building Services" in filtered.text

    contractor = client.get("/api/contractors", params={"prospect_stage": "OUTREACH"}).json()[0]
    detail_path = f"/contractors/{contractor['id']}"
    detail = client.get(detail_path)
    assert detail.status_code == 200
    assert "Touchpoints" in detail.text
    assert "Next Follow Up" in detail.text
    assert '<select name="labor_profile">' in detail.text
    assert '<select name="touchpoint_type">' in detail.text

    touchpoint = client.post(
        f"{detail_path}/touchpoints",
        data={
            "contact_name": "Alex Rivera",
            "touchpoint_type": "CALL",
            "touchpoint_at": touchpoint_at,
            "summary": "Intro call completed with regional growth lead.",
            "next_step": "Send airport case-study summary.",
            "next_follow_up_date": next_follow_up,
        },
        follow_redirects=True,
    )
    assert touchpoint.status_code == 200
    assert "Intro call completed with regional growth lead." in touchpoint.text
    assert "Last Touch" in touchpoint.text
