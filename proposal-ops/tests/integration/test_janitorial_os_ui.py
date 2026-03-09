from datetime import date, datetime, time, timedelta

from fastapi.testclient import TestClient


def test_dashboard_and_seed_demo_ui(client: TestClient) -> None:
    overdue_follow_up = (date.today() - timedelta(days=7)).isoformat()

    page = client.get("/dashboard")
    assert page.status_code == 200
    assert "Janitorial Capture Dashboard" in page.text
    assert "Live Pursuit Readiness" in page.text

    seeded = client.post("/dashboard/seed-demo", follow_redirects=True)
    assert seeded.status_code == 200
    assert "Upcoming Rebids" in seeded.text
    assert "South Jersey Regional Airport" in seeded.text
    assert "Upcoming Contractor Follow-Ups" in seeded.text
    assert "Garden State Facility Services" in seeded.text
    assert "Live Pursuit Readiness" in seeded.text

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
    assert '<select name="source_type">' in detail.text
    assert '<select name="pursuit_stage">' in detail.text
    assert '<select name="confidence_level">' in detail.text
    assert '<select name="strategic_fit">' in detail.text

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
    contractors = client.get("/api/contractors").json()
    advised_contractor_id = contractors[0]["id"]
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
    assert '<select name="contact_source_type">' in workbench.text
    assert '<select name="contact_side">' in workbench.text
    assert '<select name="source_type">' in workbench.text
    assert '<select name="note_type">' in workbench.text
    assert '<select name="source_class">' in workbench.text
    assert '<select name="action_type">' in workbench.text
    assert '<select name="status">' in workbench.text
    assert '<select name="success_fee_type">' in workbench.text

    refresh = client.post(f"{workbench_path}/matches", follow_redirects=True)
    assert refresh.status_code == 200
    assert "Contractor Matching" in refresh.text

    add_contact = client.post(
        f"{workbench_path}/contacts",
        data={
            "organization_id": pursuit["buying_organization_id"],
            "contractor_id": advised_contractor_id,
            "full_name": "Riley Partner",
            "role_title": "Regional Growth Lead",
            "contact_side": "CONTRACTOR",
            "source_type": "DIRECT_CONVERSATION",
            "confidence_level": "HIGH",
            "notes": "Advised contractor aligned on the pursuit.",
        },
        follow_redirects=True,
    )
    assert add_contact.status_code == 200
    assert "Riley Partner" in add_contact.text
    assert "DIRECT_CONVERSATION" in add_contact.text

    add_buyer_contact = client.post(
        f"{workbench_path}/contacts",
        data={
            "organization_id": pursuit["buying_organization_id"],
            "full_name": "Dana Procurement",
            "role_title": "Procurement Director",
            "contact_side": "BUYER",
            "source_type": "PUBLIC",
            "confidence_level": "MEDIUM",
            "notes": "Active buying contact for the pursuit.",
        },
        follow_redirects=True,
    )
    assert add_buyer_contact.status_code == 200
    assert "Dana Procurement" in add_buyer_contact.text

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

    add_evidence = client.post(
        f"{workbench_path}/evidence",
        data={
            "contract_id": contract["id"],
            "source_class": "PUBLIC",
            "confidence_level": "HIGH",
            "source_url": "https://example.org/board-packet",
            "provenance": "Public board packet and contract record review.",
            "summary": "Board packet reinforces transition-speed concerns.",
        },
        follow_redirects=True,
    )
    assert add_evidence.status_code == 200
    assert "Board packet reinforces transition-speed concerns." in add_evidence.text

    add_action = client.post(
        f"{workbench_path}/actions",
        data={
            "title": "Follow up with advised contractor",
            "action_type": "FOLLOW_UP",
            "status": "IN_PROGRESS",
            "owner": "operator",
            "notes": "Lock the next capture meeting.",
        },
        follow_redirects=True,
    )
    assert add_action.status_code == 200
    assert "Follow up with advised contractor" in add_action.text
    assert "FOLLOW_UP" in add_action.text
    assert "IN_PROGRESS" in add_action.text

    client.post(
        f"/api/opportunities/{pursuit['id']}/contacts",
        json={
            "organization_id": pursuit["buying_organization_id"],
            "full_name": "Dana Procurement",
            "role_title": "Procurement Director",
            "contact_side": "BUYER",
            "source_type": "PUBLIC",
            "confidence_level": "LOW",
        },
    )
    client.post(
        f"/api/opportunities/{pursuit['id']}/intelligence",
        json={
            "title": "Transition risk note",
            "note_type": "RISK",
            "note_text": "Compressed transition could create staffing strain.",
            "source_class": "PUBLIC",
            "provenance": "Public contract dates.",
            "confidence_level": "LOW",
        },
    )
    client.post(
        f"/api/opportunities/{pursuit['id']}/capture-actions",
        json={
            "title": "Open research task",
            "action_type": "RESEARCH",
            "status": "OPEN",
            "owner": "operator",
        },
    )

    filtered = client.get(
        workbench_path,
        params={
            "contact_side": "CONTRACTOR",
            "contact_source_type": "DIRECT_CONVERSATION",
            "contact_confidence_level": "",
            "note_type": "POSITIONING",
            "note_source_class": "",
            "action_status": "IN_PROGRESS",
        },
    )
    assert filtered.status_code == 200
    assert "Riley Partner" in filtered.text
    assert "Dana Procurement" not in filtered.text
    assert "Evaluator hypothesis" in filtered.text
    assert "Transition risk note" not in filtered.text
    assert "Follow up with advised contractor" in filtered.text
    assert "Open research task" not in filtered.text

    add_commercial = client.post(
        f"{workbench_path}/commercials",
        data={
            "contractor_id": advised_contractor_id,
            "retainer_amount": "6000",
            "success_fee_type": "fixed",
            "success_fee_value": "12000",
            "notes": "Managed pursuit model",
        },
        follow_redirects=True,
    )
    assert add_commercial.status_code == 200
    assert "Weighted Expected Value" in add_commercial.text
    assert "FIXED" in add_commercial.text

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "Live Pursuit Readiness" in dashboard.text
    assert "Workbench Pursuit" in dashboard.text
    assert "Ready (6/6)" in dashboard.text


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

    filtered = client.get("/contractors", params={"prospect_stage": "OUTREACH", "follow_up_before": ""})
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


def test_contractor_handoff_ui(client: TestClient) -> None:
    client.post("/api/dashboard/seed-demo")
    today = date.today()
    touchpoint_at = datetime.combine(today, time(hour=10, minute=15)).isoformat()

    contractor = client.post(
        "/api/contractors",
        json={
            "name": "UI Handoff Services",
            "service_geographies": "NJ",
            "headquarters_city": "Trenton",
            "headquarters_state": "NJ",
            "vertical_experience": "airport",
            "labor_profile": "W2 self-perform",
            "union_profile": "non-union",
            "diversity_certs": "WBE",
            "airport_experience": True,
            "healthcare_experience": False,
            "education_experience": False,
            "municipal_experience": False,
            "scale_band": "REGIONAL",
            "relationship_strength": 4,
            "prospect_stage": "ENGAGED",
            "next_follow_up_date": (today + timedelta(days=7)).isoformat(),
            "relationship_notes": "Ready to move into active pursuit work.",
            "strategic_fit_notes": "Strong airport positioning.",
        },
    ).json()
    touchpoint = client.post(
        f"/api/contractors/{contractor['id']}/touchpoints",
        json={
            "contact_name": "Jordan Lee",
            "touchpoint_type": "MEETING",
            "touchpoint_at": touchpoint_at,
            "summary": "Reviewed capture posture and transition expectations.",
            "next_step": "Move contractor into active pursuit planning.",
            "next_follow_up_date": (today + timedelta(days=5)).isoformat(),
        },
    )
    assert touchpoint.status_code == 200
    contract = client.get("/api/contracts").json()[0]

    detail_path = f"/contractors/{contractor['id']}"
    detail = client.get(detail_path)
    assert detail.status_code == 200
    assert "Create Pursuit Handoff" in detail.text
    assert "Link To Existing Opportunity" in detail.text
    assert "Linked Opportunities" in detail.text
    assert '<select name="pursuit_stage">' in detail.text
    assert '<select name="confidence_level">' in detail.text
    assert '<select name="strategic_fit">' in detail.text

    handoff = client.post(
        f"{detail_path}/pursuits",
        data={
            "contract_id": contract["id"],
            "title": "UI Handoff Pursuit",
            "primary_facility_id": contract["facility_ids"][0],
            "pursuit_stage": "PRE_RFP_CAPTURE",
            "confidence_level": "HIGH",
            "expected_rfp_date": (today + timedelta(days=45)).isoformat(),
            "provenance_summary": "Created from the contractor detail handoff form.",
            "strategic_fit": "4",
            "incumbent_vulnerability": "3",
            "rebid_probability": "4",
            "relationship_access": "4",
            "contractor_fit": "5",
            "operational_complexity": "3",
            "margin_potential": "4",
            "pre_rfp_influence": "4",
            "timeline_urgency": "3",
            "actor": "operator",
        },
        follow_redirects=False,
    )
    assert handoff.status_code == 303
    assert "/capture-workbench" in handoff.headers["location"]

    workbench = client.get(handoff.headers["location"])
    assert workbench.status_code == 200
    assert "UI Handoff Pursuit" in workbench.text
    assert "Advised Contractor Context" in workbench.text
    assert "UI Handoff Services" in workbench.text
    assert "Reviewed capture posture and transition expectations." in workbench.text
    assert f"/contractors/{contractor['id']}" in workbench.text

    seeded_commercial_update = client.post(
        f"{handoff.headers['location']}/commercials",
        data={
            "contractor_id": contractor["id"],
            "retainer_amount": "5000",
            "success_fee_type": "FIXED",
            "success_fee_value": "10000",
            "notes": "Seeded handoff commercial updated through the workbench.",
        },
        follow_redirects=True,
    )
    assert seeded_commercial_update.status_code == 200
    assert "Weighted Expected Value" in seeded_commercial_update.text
    assert "FIXED" in seeded_commercial_update.text

    refreshed_detail = client.get(detail_path)
    assert refreshed_detail.status_code == 200
    assert "UI Handoff Pursuit" in refreshed_detail.text
    assert "/capture-workbench" in refreshed_detail.text
    assert "Weighted Pipeline" in refreshed_detail.text

    existing = client.post(
        f"/api/contracts/{contract['id']}/pursuits",
        json={
            "title": "Existing UI Linked Pursuit",
            "primary_facility_id": contract["facility_ids"][0],
            "pursuit_stage": "INTELLIGENCE",
            "confidence_level": "MEDIUM",
            "expected_rfp_date": (today + timedelta(days=60)).isoformat(),
            "provenance_summary": "Created to test contractor linking.",
            "strategic_fit": 3,
            "incumbent_vulnerability": 3,
            "rebid_probability": 3,
            "relationship_access": 2,
            "contractor_fit": 2,
            "operational_complexity": 3,
            "margin_potential": 3,
            "pre_rfp_influence": 2,
            "timeline_urgency": 2,
            "actor": "operator",
        },
    ).json()

    linked = client.post(
        f"{detail_path}/opportunity-links",
        data={"opportunity_id": existing["id"], "actor": "operator"},
        follow_redirects=True,
    )
    assert linked.status_code == 200
    assert "Existing UI Linked Pursuit" in linked.text


def test_ux_friction_panel_and_feedback_ui(client: TestClient) -> None:
    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "Operator Friction Summary" in dashboard.text
    assert "Share workflow friction" in dashboard.text
    assert "This was confusing" in dashboard.text
    assert "No passive audio is captured." in dashboard.text

    session_id = "ui-friction-session-001"
    client.post(
        "/api/ux/events",
        json={
            "session_id": session_id,
            "event_type": "PAGE_VIEW",
            "page_key": "/contractors",
            "path": "/contractors",
            "metadata_json": {"page_title": "Contractors"},
        },
    )
    client.post(
        "/api/ux/events",
        json={
            "session_id": session_id,
            "event_type": "VALIDATION_FAILURE",
            "page_key": "/contractors",
            "path": "/contractors",
            "form_name": "contractor_create",
            "count_value": 3,
            "metadata_json": {"field_names": ["name"]},
        },
    )
    client.post(
        "/api/ux/feedback",
        json={
            "session_id": session_id,
            "feedback_type": "TOOK_TOO_LONG",
            "page_key": "/contractors",
            "path": "/contractors",
            "form_name": "contractor_create",
            "note_text": "This screen takes too long to complete when starting from scratch.",
            "context_json": {"source": "ui-test"},
            "voice_note_status": "NOT_PROVIDED",
        },
    )

    friction = client.get("/ux/friction")
    assert friction.status_code == 200
    assert "Operator Friction Summary" in friction.text
    assert "Recommendations are surfaced for approval only." in friction.text
    assert "Reduce time-to-complete" in friction.text
    assert "This screen takes too long to complete when starting from scratch." in friction.text

    refreshed_dashboard = client.get("/dashboard")
    assert refreshed_dashboard.status_code == 200
    assert "Reduce time-to-complete" in refreshed_dashboard.text
    assert "Open detailed friction view" in refreshed_dashboard.text
