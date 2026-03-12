from fastapi.testclient import TestClient


def test_opportunity_intelligence_ui_workflow(client: TestClient) -> None:
    organization = client.post(
        "/api/organizations",
        json={
            "name": "Regional School Districts",
            "organization_type": "SCHOOL_DISTRICT",
            "city": "Harrisburg",
            "state": "PA",
        },
    )
    assert organization.status_code == 200
    organization_id = organization.json()["id"]

    contractor = client.post(
        "/api/contractors",
        json={
            "name": "School Support Partner",
            "service_geographies": "PA NJ",
            "headquarters_city": "Philadelphia",
            "headquarters_state": "PA",
            "vertical_experience": "education operations",
            "labor_profile": "W2 self-perform",
            "union_profile": "mixed",
            "scale_band": "REGIONAL",
            "relationship_strength": 3,
            "prospect_stage": "QUALIFIED",
            "relationship_notes": "Education-adjacent operating partner.",
            "strategic_fit_notes": "Good district support-services fit.",
        },
    )
    assert contractor.status_code == 200
    contractor_id = contractor.json()["id"]

    page = client.get("/intelligence")
    assert page.status_code == 200
    assert "Opportunity Intelligence" in page.text
    assert "Create Signal Source" in page.text
    assert "Log Signal Event" in page.text
    assert "Create Opportunity Hypothesis" in page.text
    assert '<select name="buying_organization_id">' in page.text
    assert "Load Example" in page.text
    assert "Clear Example" in page.text

    source = client.post(
        "/intelligence/sources",
        data={
            "name": "State Budget Hearing Tracker",
            "source_type": "BUDGET",
            "region": "Mid-Atlantic",
            "owner_scope": "State",
            "source_url": "https://example.org/budgets",
            "notes": "Tracks adopted and proposed budget hearings.",
        },
        follow_redirects=True,
    )
    assert source.status_code == 200
    assert "State Budget Hearing Tracker" in source.text

    source_id = client.get("/api/intelligence/sources").json()[0]["id"]
    signal = client.post(
        "/intelligence/signals",
        data={
            "source_id": source_id,
            "title": "Committee hearing signals expansion in school support funding",
            "signal_type": "FUNDING",
            "signal_date": "2026-03-02",
            "jurisdiction": "PA",
            "agency_name": "State Department of Education",
            "program_name": "Student Support Services",
            "summary": "Budget testimony indicates likely downstream outsourcing and grant activity for support services.",
            "confidence_level": "MEDIUM",
            "source_url": "https://example.org/budgets/hearing",
            "source_reference": "Education committee hearing",
            "recommended_action": "Map district pass-through paths and likely program administrators.",
        },
        follow_redirects=True,
    )
    assert signal.status_code == 200
    assert "Committee hearing signals expansion in school support funding" in signal.text

    signal_id = client.get("/api/intelligence/signals").json()[0]["id"]
    hypothesis = client.post(
        "/intelligence/hypotheses",
        data={
            "title": "District support-services procurement likely after state allocation",
            "sector": "Education Services",
            "geography": "Pennsylvania",
            "buying_organization_id": organization_id,
            "service_line": "Student Support and Operations",
            "stage": "MONITORING",
            "confidence_level": "MEDIUM",
            "expected_release_start": "2026-06-01",
            "expected_release_end": "2026-09-30",
            "summary": "State allocation pattern suggests district-level service buys later in the fiscal cycle.",
            "recommended_action": "Track district board agendas and current grant administration decisions.",
            "primary_signal_event_id": signal_id,
            "recommended_contractor_id": contractor_id,
        },
        follow_redirects=True,
    )
    assert hypothesis.status_code == 200
    assert "District support-services procurement likely after state allocation" in hypothesis.text
    assert "School Support Partner" in hypothesis.text

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "Opportunity Intelligence Snapshot" in dashboard.text
    assert "District support-services procurement likely after state allocation" in dashboard.text


def test_opportunity_hypothesis_convert_to_pursuit_ui(client: TestClient) -> None:
    organization = client.post(
        "/api/organizations",
        json={
            "name": "Regional Transit Authority",
            "organization_type": "OTHER",
            "city": "Philadelphia",
            "state": "PA",
        },
    )
    assert organization.status_code == 200
    organization_id = organization.json()["id"]

    contractor_id = client.post(
        "/api/contractors",
        json={
            "name": "Regional Capture Teammate",
            "service_geographies": "PA NJ",
            "headquarters_city": "Philadelphia",
            "headquarters_state": "PA",
            "vertical_experience": "transit facilities",
            "labor_profile": "W2 self-perform",
            "union_profile": "mixed",
            "scale_band": "REGIONAL",
            "relationship_strength": 4,
            "prospect_stage": "ENGAGED",
            "relationship_notes": "Preferred transit operator partner.",
            "strategic_fit_notes": "Strong local mobilization capacity.",
        },
    ).json()["id"]

    source_id = client.post(
        "/api/intelligence/sources",
        json={
            "name": "Board Packet Watch",
            "source_type": "BOARD_PACKET",
            "region": "Mid-Atlantic",
            "owner_scope": "Authority",
        },
    ).json()["id"]
    event_id = client.post(
        "/api/intelligence/signals",
        json={
            "source_id": source_id,
            "title": "Authority packet highlights custodial outsourcing pressure",
            "signal_type": "GOVERNANCE",
            "signal_date": "2026-03-04",
            "agency_name": "Regional Transit Authority",
            "summary": "Operating packet flags service-level pressure and contractor performance scrutiny.",
            "confidence_level": "MEDIUM",
        },
    ).json()["id"]
    hypothesis_id = client.post(
        "/api/intelligence/hypotheses",
        json={
            "title": "Regional transit facilities support procurement likely",
            "sector": "Facilities Services",
            "geography": "Pennsylvania",
            "buying_organization_id": organization_id,
            "service_line": "Custodial and Porter",
            "stage": "QUALIFIED",
            "confidence_level": "MEDIUM",
            "expected_release_start": "2026-07-01",
            "expected_release_end": "2026-09-01",
            "summary": "Governance pressure points suggest a downstream competitive buy for facilities support.",
            "recommended_action": "Shift to structured pre-RFP capture work.",
            "primary_signal_event_id": event_id,
            "recommended_contractor_id": contractor_id,
        },
    ).json()["id"]

    intelligence_page = client.get("/intelligence")
    assert intelligence_page.status_code == 200
    assert "Regional Capture Teammate" in intelligence_page.text

    converted = client.post(
        f"/intelligence/hypotheses/{hypothesis_id}/convert-to-pursuit",
        data={
            "name": "Regional Transit Capture Pursuit",
            "client_name": "Regional Transit Authority",
            "estimated_contract_value": "1800000",
            "lead_time_days": "95",
            "strategic_alignment": "4",
            "estimated_probability_win": "58",
            "pursuit_stage": "EARLY_QUALIFICATION",
            "actor": "operator",
        },
        follow_redirects=False,
    )
    assert converted.status_code == 303
    assert "/capture-workbench" in converted.headers["location"]

    opportunity = client.get(converted.headers["location"])
    assert opportunity.status_code == 200
    assert "Regional Transit Capture Pursuit" in opportunity.text
    assert "Advised Contractor Context" in opportunity.text
    assert "Regional Capture Teammate" in opportunity.text

    refreshed = client.get("/intelligence")
    assert refreshed.status_code == 200
    assert "Converted: Regional Transit Capture Pursuit" in refreshed.text
