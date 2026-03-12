from fastapi.testclient import TestClient


def test_opportunity_intelligence_api_crud_and_dashboard_summary(client: TestClient) -> None:
    organization = client.post(
        "/api/organizations",
        json={
            "name": "Atlantic City",
            "organization_type": "MUNICIPALITY",
            "city": "Atlantic City",
            "state": "NJ",
        },
    )
    assert organization.status_code == 200
    organization_id = organization.json()["id"]

    contractor_id = client.post(
        "/api/contractors",
        json={
            "name": "Policy-Informed Facilities Partner",
            "service_geographies": "NJ DE",
            "headquarters_city": "Camden",
            "headquarters_state": "NJ",
            "vertical_experience": "facilities municipal",
            "labor_profile": "W2 self-perform",
            "union_profile": "mixed",
            "scale_band": "REGIONAL",
            "relationship_strength": 4,
            "prospect_stage": "ENGAGED",
            "relationship_notes": "Trusted early-stage partner for local public-sector work.",
            "strategic_fit_notes": "Strong mobilization and transition depth.",
        },
    ).json()["id"]

    source = client.post(
        "/api/intelligence/sources",
        json={
            "name": "Mid-Atlantic Council Agenda Watch",
            "source_type": "AGENDA",
            "region": "Mid-Atlantic",
            "owner_scope": "Municipal",
            "source_url": "https://example.org/agendas",
            "notes": "Tracks public committee and board actions.",
        },
    )
    assert source.status_code == 200
    source_id = source.json()["id"]

    event = client.post(
        "/api/intelligence/signals",
        json={
            "source_id": source_id,
            "title": "City council packet expands outsourced facilities budget",
            "signal_type": "FUNDING",
            "signal_date": "2026-03-01",
            "jurisdiction": "NJ",
            "agency_name": "Atlantic City",
            "program_name": "Facilities Operations",
            "summary": "Budget workshop adds operating dollars tied to custodial and day porter support.",
            "confidence_level": "HIGH",
            "source_url": "https://example.org/agendas/facilities",
            "source_reference": "Council packet item 7A",
            "recommended_action": "Qualify likely buying department and rebid window.",
        },
    )
    assert event.status_code == 200
    event_id = event.json()["id"]
    assert event.json()["source_name"] == "Mid-Atlantic Council Agenda Watch"

    hypothesis = client.post(
        "/api/intelligence/hypotheses",
        json={
            "title": "Atlantic City facilities support procurement likely in summer window",
            "sector": "Facilities Services",
            "geography": "New Jersey",
            "buying_organization_id": organization_id,
            "service_line": "Janitorial and Day Porter",
            "stage": "QUALIFIED",
            "confidence_level": "HIGH",
            "expected_release_start": "2026-06-01",
            "expected_release_end": "2026-08-31",
            "summary": "Budget and governance signals indicate likely outsourced facilities support activity before peak season.",
            "recommended_action": "Map operations stakeholders and qualifying incumbency before any pre-solicitation notice.",
            "primary_signal_event_id": event_id,
            "recommended_contractor_id": contractor_id,
        },
    )
    assert hypothesis.status_code == 200
    assert hypothesis.json()["primary_signal_event_title"] == "City council packet expands outsourced facilities budget"
    assert hypothesis.json()["buying_organization_id"] == organization_id
    assert hypothesis.json()["buying_organization_name"] == "Atlantic City"
    assert hypothesis.json()["recommended_contractor_id"] == contractor_id
    assert hypothesis.json()["recommended_contractor_name"] == "Policy-Informed Facilities Partner"

    summary = client.get("/api/intelligence/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["signal_sources_total"] == 1
    assert body["signal_events_total"] == 1
    assert body["open_hypotheses_total"] == 1
    assert body["recent_signal_events"][0]["id"] == event_id
    assert body["active_hypotheses"][0]["recommended_contractor_name"] == "Policy-Informed Facilities Partner"

    dashboard = client.get("/api/dashboard/summary")
    assert dashboard.status_code == 200
    dashboard_body = dashboard.json()
    assert dashboard_body["intelligence_summary"]["signal_sources_total"] == 1
    assert dashboard_body["intelligence_summary"]["active_hypotheses"][0]["id"] == hypothesis.json()["id"]


def test_opportunity_hypothesis_convert_to_pursuit_api(client: TestClient) -> None:
    organization = client.post(
        "/api/organizations",
        json={
            "name": "Metro Facilities Agency",
            "organization_type": "OTHER",
            "city": "Newark",
            "state": "NJ",
        },
    )
    assert organization.status_code == 200
    organization_id = organization.json()["id"]

    contractor_id = client.post(
        "/api/contractors",
        json={
            "name": "Upstream Capture Partner",
            "service_geographies": "NJ PA",
            "headquarters_city": "Trenton",
            "headquarters_state": "NJ",
            "vertical_experience": "facilities municipal",
            "labor_profile": "W2 self-perform",
            "union_profile": "mixed",
            "scale_band": "REGIONAL",
            "relationship_strength": 4,
            "prospect_stage": "ENGAGED",
            "relationship_notes": "Preferred teammate for facilities pursuits.",
            "strategic_fit_notes": "Good transition and local ops depth.",
        },
    ).json()["id"]

    source_id = client.post(
        "/api/intelligence/sources",
        json={
            "name": "State Budget Notes",
            "source_type": "BUDGET",
            "region": "Mid-Atlantic",
            "owner_scope": "State",
        },
    ).json()["id"]
    event_id = client.post(
        "/api/intelligence/signals",
        json={
            "source_id": source_id,
            "title": "Budget signals regional facilities expansion",
            "signal_type": "FUNDING",
            "signal_date": "2026-03-05",
            "agency_name": "Metro Facilities Agency",
            "summary": "Budget material points to outsourced facilities support and transition work.",
            "confidence_level": "HIGH",
        },
    ).json()["id"]
    hypothesis = client.post(
        "/api/intelligence/hypotheses",
        json={
            "title": "Metro facilities support procurement likely",
            "sector": "Facilities Services",
            "geography": "New Jersey",
            "buying_organization_id": organization_id,
            "service_line": "Janitorial and Porter",
            "stage": "CAPTURE_READY",
            "confidence_level": "HIGH",
            "expected_release_start": "2026-06-01",
            "expected_release_end": "2026-08-15",
            "summary": "Signals suggest a funded support-services buying event in the next cycle.",
            "recommended_action": "Stand up early qualification and stakeholder mapping.",
            "primary_signal_event_id": event_id,
            "recommended_contractor_id": contractor_id,
        },
    )
    hypothesis_id = hypothesis.json()["id"]
    assert hypothesis.json()["recommended_contractor_name"] == "Upstream Capture Partner"

    converted = client.post(
        f"/api/intelligence/hypotheses/{hypothesis_id}/convert-to-pursuit",
        json={
            "estimated_contract_value": 2400000,
            "lead_time_days": 75,
            "incumbent_status": True,
            "strategic_alignment": 4,
            "estimated_probability_win": 62,
            "pursuit_stage": "PRE_RFP_CAPTURE",
            "actor": "operator",
        },
    )
    assert converted.status_code == 200
    body = converted.json()
    assert body["opportunity"]["name"] == "Metro facilities support procurement likely"
    assert body["opportunity"]["client"] == "Metro Facilities Agency"
    assert body["opportunity"]["buying_organization_id"] == organization_id
    assert body["opportunity"]["buying_organization_name"] == "Metro Facilities Agency"
    assert body["opportunity"]["pursuit_stage"] == "PRE_RFP_CAPTURE"
    assert body["hypothesis"]["stage"] == "CONVERTED"
    assert body["hypothesis"]["converted_opportunity_id"] == body["opportunity"]["id"]
    commercial = client.get(f"/api/opportunities/{body['opportunity']['id']}/commercials")
    assert commercial.status_code == 200
    assert commercial.json()["contractor_id"] == contractor_id
    assert commercial.json()["contractor_name"] == "Upstream Capture Partner"

    hypotheses = client.get("/api/intelligence/hypotheses")
    assert hypotheses.status_code == 200
    converted_hypothesis = next(item for item in hypotheses.json() if item["id"] == hypothesis_id)
    assert converted_hypothesis["converted_opportunity_name"] == "Metro facilities support procurement likely"
    assert converted_hypothesis["recommended_contractor_id"] == contractor_id
    assert converted_hypothesis["recommended_contractor_name"] == "Upstream Capture Partner"

    second_attempt = client.post(
        f"/api/intelligence/hypotheses/{hypothesis_id}/convert-to-pursuit",
        json={
            "estimated_contract_value": 2400000,
            "lead_time_days": 75,
            "strategic_alignment": 4,
            "pursuit_stage": "PRE_RFP_CAPTURE",
            "actor": "operator",
        },
    )
    assert second_attempt.status_code == 422
