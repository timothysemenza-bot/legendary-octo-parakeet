from datetime import date, datetime, time, timedelta

from fastapi.testclient import TestClient


def test_market_data_crud_and_contract_import_api(client: TestClient) -> None:
    org = client.post(
        "/api/organizations",
        json={
            "name": "Metro Airport Authority",
            "organization_type": "AIRPORT",
            "city": "Atlantic City",
            "state": "NJ",
        },
    )
    assert org.status_code == 200
    organization_id = org.json()["id"]

    facility = client.post(
        "/api/facilities",
        json={
            "organization_id": organization_id,
            "name": "Terminal Portfolio",
            "facility_kind": "PORTFOLIO",
            "facility_type": "AIRPORT_TERMINAL",
            "city": "Atlantic City",
            "state": "NJ",
            "service_complexity": "HIGH",
            "square_footage": 900000,
        },
    )
    assert facility.status_code == 200
    facility_id = facility.json()["id"]

    contract = client.post(
        "/api/contracts",
        json={
            "organization_id": organization_id,
            "title": "Airport Janitorial Services",
            "incumbent_vendor": "CleanCo",
            "estimated_annual_value": 2500000,
            "estimated_total_value": 12500000,
            "start_date": "2026-01-01",
            "expiration_date": "2026-12-31",
            "rebid_window_start": "2026-08-01",
            "rebid_window_end": "2026-10-01",
            "procurement_source_url": "https://example.org/rfp",
            "source_type": "PUBLIC",
            "source_notes": "Board minutes",
            "facility_ids": [facility_id],
        },
    )
    assert contract.status_code == 200
    contract_id = contract.json()["id"]
    assert contract.json()["facility_ids"] == [facility_id]

    listing = client.get("/api/contracts?state=NJ&facility_kind=PORTFOLIO&rebid_within_days=365")
    assert listing.status_code == 200
    assert listing.json()[0]["id"] == contract_id

    imported = client.post(
        "/api/contracts/import",
        files={
            "file": (
                "radar.csv",
                (
                    "organization_name,organization_type,organization_city,state,facility_name,facility_kind,facility_type,contract_title,incumbent_vendor,annual_value,total_value,start_date,expiration_date,rebid_window_start,rebid_window_end,procurement_source_url,source_type,source_notes\n"
                    "Mercer Health Network,HOSPITAL,Trenton,NJ,Central Hospital Campus,FACILITY,HOSPITAL,Healthcare EVS,Sterling Support,1450000,7250000,2026-01-01,2026-09-15,2026-06-01,2026-08-01,https://example.org/health,PUBLIC,Public archive\n"
                ).encode("utf-8"),
                "text/csv",
            )
        },
    )
    assert imported.status_code == 200
    assert imported.json()["imported_count"] == 1


def test_contractor_prospect_pipeline_api(client: TestClient) -> None:
    today = date.today()
    initial_follow_up = today + timedelta(days=33)
    next_follow_up = today + timedelta(days=10)
    overdue_follow_up = today - timedelta(days=7)
    touchpoint_at = datetime.combine(today, time(hour=9, minute=30))

    contractor = client.post(
        "/api/contractors",
        json={
            "name": "Tri-State Janitorial Partners",
            "service_geographies": "NJ PA",
            "headquarters_city": "Newark",
            "headquarters_state": "NJ",
            "vertical_experience": "airport education",
            "labor_profile": "W2 self-perform",
            "union_profile": "mixed",
            "diversity_certs": "MWBE",
            "airport_experience": True,
            "healthcare_experience": False,
            "education_experience": True,
            "municipal_experience": False,
            "scale_band": "REGIONAL",
            "relationship_strength": 3,
            "prospect_stage": "OUTREACH",
            "next_follow_up_date": initial_follow_up.isoformat(),
            "relationship_notes": "Warm intro through local operator.",
            "strategic_fit_notes": "Good airport crossover potential.",
        },
    )
    assert contractor.status_code == 200
    contractor_id = contractor.json()["id"]
    assert contractor.json()["prospect_stage"] == "OUTREACH"
    assert contractor.json()["labor_profile"] == "W2 self-perform"
    assert contractor.json()["union_profile"] == "Mixed"

    touchpoint = client.post(
        f"/api/contractors/{contractor_id}/touchpoints",
        json={
            "contact_name": "Alex Rivera",
            "touchpoint_type": "CALL",
            "touchpoint_at": touchpoint_at.isoformat(),
            "summary": "Intro call completed with regional growth lead.",
            "next_step": "Send airport case-study summary.",
            "next_follow_up_date": next_follow_up.isoformat(),
        },
    )
    assert touchpoint.status_code == 200
    assert touchpoint.json()["touchpoint_type"] == "CALL"

    detail = client.get(f"/api/contractors/{contractor_id}")
    assert detail.status_code == 200
    assert detail.json()["last_touch_at"].startswith(touchpoint_at.isoformat())
    assert detail.json()["next_follow_up_date"] == next_follow_up.isoformat()

    updated = client.put(
        f"/api/contractors/{contractor_id}",
        json={
            "name": "Tri-State Janitorial Partners",
            "service_geographies": "NJ PA",
            "headquarters_city": "Newark",
            "headquarters_state": "NJ",
            "vertical_experience": "airport education",
            "labor_profile": "W2 self-perform",
            "union_profile": "mixed",
            "diversity_certs": "MWBE",
            "airport_experience": True,
            "healthcare_experience": False,
            "education_experience": True,
            "municipal_experience": False,
            "scale_band": "REGIONAL",
            "relationship_strength": 4,
            "prospect_stage": "DISCOVERY",
            "next_follow_up_date": next_follow_up.isoformat(),
            "relationship_notes": "Warm intro through local operator.",
            "strategic_fit_notes": "Good airport crossover potential.",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["prospect_stage"] == "DISCOVERY"

    filtered = client.get(
        "/api/contractors",
        params={"prospect_stage": "DISCOVERY", "follow_up_before": (today + timedelta(days=20)).isoformat()},
    )
    assert filtered.status_code == 200
    assert any(item["id"] == contractor_id for item in filtered.json())

    touchpoints = client.get(f"/api/contractors/{contractor_id}/touchpoints")
    assert touchpoints.status_code == 200
    assert len(touchpoints.json()) == 1
    assert touchpoints.json()[0]["summary"].startswith("Intro call completed")

    overdue = client.post(
        "/api/contractors",
        json={
            "name": "Dormant Prospect Services",
            "service_geographies": "NJ",
            "headquarters_city": "Vineland",
            "headquarters_state": "NJ",
            "vertical_experience": "municipal",
            "labor_profile": "W2 self-perform",
            "union_profile": "non-union",
            "diversity_certs": "",
            "airport_experience": False,
            "healthcare_experience": False,
            "education_experience": False,
            "municipal_experience": True,
            "scale_band": "LOCAL",
            "relationship_strength": 2,
            "prospect_stage": "OUTREACH",
            "next_follow_up_date": overdue_follow_up.isoformat(),
            "relationship_notes": "Initial outreach stalled.",
            "strategic_fit_notes": "Keep warm for municipal small-balance work.",
        },
    )
    assert overdue.status_code == 200

    dashboard = client.get("/api/dashboard/summary")
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert any(item["contractor_id"] == contractor_id for item in body["upcoming_contractor_follow_ups"])
    upcoming_item = next(item for item in body["upcoming_contractor_follow_ups"] if item["contractor_id"] == contractor_id)
    assert upcoming_item["next_step"] == "Send airport case-study summary."
    assert any(item["contractor_id"] == overdue.json()["id"] for item in body["overdue_contractor_follow_ups"])


def test_contractor_handoff_and_opportunity_link_api(client: TestClient) -> None:
    client.post("/api/dashboard/seed-demo")
    today = date.today()
    contractor = client.post(
        "/api/contractors",
        json={
            "name": "Handoff Ready Services",
            "service_geographies": "NJ PA",
            "headquarters_city": "Trenton",
            "headquarters_state": "NJ",
            "vertical_experience": "airport municipal",
            "labor_profile": "W2 self-perform",
            "union_profile": "mixed",
            "diversity_certs": "MWBE",
            "airport_experience": True,
            "healthcare_experience": False,
            "education_experience": False,
            "municipal_experience": True,
            "scale_band": "REGIONAL",
            "relationship_strength": 4,
            "prospect_stage": "ENGAGED",
            "next_follow_up_date": (today + timedelta(days=7)).isoformat(),
            "relationship_notes": "Ready for active capture work.",
            "strategic_fit_notes": "Strong transition operator.",
        },
    )
    assert contractor.status_code == 200
    contractor_id = contractor.json()["id"]

    contract = client.get("/api/contracts").json()[0]
    handoff = client.post(
        f"/api/contractors/{contractor_id}/pursuits",
        json={
            "contract_id": contract["id"],
            "title": "Contractor Handoff Pursuit",
            "primary_facility_id": contract["facility_ids"][0],
            "pursuit_stage": "PRE_RFP_CAPTURE",
            "confidence_level": "HIGH",
            "expected_rfp_date": (today + timedelta(days=45)).isoformat(),
            "provenance_summary": "Created from contractor handoff workflow.",
            "strategic_fit": 4,
            "incumbent_vulnerability": 3,
            "rebid_probability": 4,
            "relationship_access": 4,
            "contractor_fit": 5,
            "operational_complexity": 3,
            "margin_potential": 4,
            "pre_rfp_influence": 4,
            "timeline_urgency": 3,
            "actor": "operator",
        },
    )
    assert handoff.status_code == 200
    opportunity_id = handoff.json()["id"]
    assert handoff.json()["primary_contract_id"] == contract["id"]

    seeded_commercial = client.get(f"/api/opportunities/{opportunity_id}/commercials")
    assert seeded_commercial.status_code == 200
    assert seeded_commercial.json()["contractor_id"] == contractor_id

    existing = client.post(
        f"/api/contracts/{contract['id']}/pursuits",
        json={
            "title": "Existing Linked Pursuit",
            "primary_facility_id": contract["facility_ids"][0],
            "pursuit_stage": "INTELLIGENCE",
            "confidence_level": "MEDIUM",
            "expected_rfp_date": (today + timedelta(days=60)).isoformat(),
            "provenance_summary": "Created for contractor linking validation.",
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
    )
    assert existing.status_code == 200
    existing_opp_id = existing.json()["id"]

    commercial = client.post(
        f"/api/opportunities/{existing_opp_id}/commercials",
        json={
            "retainer_amount": 7500,
            "success_fee_type": "FIXED",
            "success_fee_value": 11000,
            "projected_payout_date": (today + timedelta(days=120)).isoformat(),
            "notes": "Existing commercial values should survive link.",
        },
    )
    assert commercial.status_code == 200
    commercial_id = commercial.json()["id"]

    linked = client.post(
        f"/api/contractors/{contractor_id}/opportunity-links",
        json={"opportunity_id": existing_opp_id, "actor": "operator"},
    )
    assert linked.status_code == 200
    assert linked.json()["opportunity_id"] == existing_opp_id
    assert linked.json()["commercial_id"] == commercial_id

    linked_again = client.post(
        f"/api/contractors/{contractor_id}/opportunity-links",
        json={"opportunity_id": existing_opp_id, "actor": "operator"},
    )
    assert linked_again.status_code == 200
    assert linked_again.json()["commercial_id"] == commercial_id

    preserved = client.get(f"/api/opportunities/{existing_opp_id}/commercials")
    assert preserved.status_code == 200
    assert preserved.json()["id"] == commercial_id
    assert preserved.json()["contractor_id"] == contractor_id
    assert preserved.json()["retainer_amount"] == 7500.0
    assert preserved.json()["success_fee_value"] == 11000.0

    links = client.get(f"/api/contractors/{contractor_id}/opportunity-links")
    assert links.status_code == 200
    linked_ids = {item["opportunity_id"] for item in links.json()}
    assert opportunity_id in linked_ids
    assert existing_opp_id in linked_ids


def test_pursuit_creation_matching_capture_workbench_and_dashboard_api(client: TestClient) -> None:
    seed = client.post("/api/dashboard/seed-demo")
    assert seed.status_code == 200

    contracts = client.get("/api/contracts")
    assert contracts.status_code == 200
    contract = contracts.json()[0]

    pursuit = client.post(
        f"/api/contracts/{contract['id']}/pursuits",
        json={
            "title": "Airport Rebid Pursuit",
            "primary_facility_id": contract["facility_ids"][0],
            "pursuit_stage": "INTELLIGENCE",
            "confidence_level": "HIGH",
            "expected_rfp_date": "2026-08-15",
            "provenance_summary": "Public contract radar entry and board-calendar review.",
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
    )
    assert pursuit.status_code == 200
    opportunity_id = pursuit.json()["id"]
    assert pursuit.json()["buying_organization_name"]
    assert pursuit.json()["primary_contract_id"] == contract["id"]

    matches = client.post(f"/api/opportunities/{opportunity_id}/matches")
    assert matches.status_code == 200
    assert len(matches.json()) >= 1
    assert matches.json()[0]["contractor_name"]

    contact = client.post(
        f"/api/opportunities/{opportunity_id}/contacts",
        json={
            "organization_id": pursuit.json()["buying_organization_id"],
            "full_name": "Dana Procurement",
            "role_title": "Procurement Director",
            "contact_side": "BUYER",
            "source_type": "PUBLIC",
            "confidence_level": "HIGH",
            "notes": "Named in public board packet.",
        },
    )
    assert contact.status_code == 200

    note = client.post(
        f"/api/opportunities/{opportunity_id}/intelligence",
        json={
            "title": "Likely transition concern",
            "note_type": "POSITIONING",
            "note_text": "Airport operator appears focused on daytime terminal presentation and fast mobilization.",
            "source_class": "INFERRED",
            "provenance": "Inferred from public board discussion and current incumbent service complaints.",
            "confidence_level": "MEDIUM",
        },
    )
    assert note.status_code == 200

    evidence = client.post(
        f"/api/opportunities/{opportunity_id}/evidence",
        json={
            "intelligence_note_id": note.json()["id"],
            "contract_id": contract["id"],
            "source_class": "PUBLIC",
            "provenance": "Public airport board agenda packet dated 2026-02-15.",
            "source_url": "https://example.org/board-packet",
            "summary": "Board packet references cleanliness complaints and contract timing.",
            "confidence_level": "HIGH",
        },
    )
    assert evidence.status_code == 200

    action = client.post(
        f"/api/opportunities/{opportunity_id}/capture-actions",
        json={
            "title": "Review board packet history",
            "action_type": "RESEARCH",
            "status": "OPEN",
            "owner": "operator",
            "due_date": "2026-04-01",
            "notes": "Trace incumbent vulnerabilities and likely evaluation themes.",
        },
    )
    assert action.status_code == 200

    contractors = client.get("/api/contractors").json()
    commercial = client.post(
        f"/api/opportunities/{opportunity_id}/commercials",
        json={
            "contractor_id": contractors[0]["id"],
            "retainer_amount": 6000,
            "success_fee_type": "FIXED",
            "success_fee_value": 12000,
            "projected_payout_date": "2026-12-31",
            "notes": "Internal managed-retainer model.",
        },
    )
    assert commercial.status_code == 200
    assert commercial.json()["weighted_expected_value"] >= 6000

    dashboard = client.get("/api/dashboard/summary")
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["contracts_total"] >= 2
    assert body["pursuits_total"] >= 1
    assert body["expected_consulting_revenue"] >= 6000
    assert len(body["top_matches"]) >= 1
    assert "overdue_contractor_follow_ups" in body
    assert "upcoming_contractor_follow_ups" in body


def test_scoring_profile_update_api(client: TestClient) -> None:
    profiles = client.get("/api/scoring/profiles", params={"profile_type": "OPPORTUNITY"})
    assert profiles.status_code == 200
    profile = profiles.json()[0]
    original = {item["code"]: item["weight"] for item in profile["criteria"]}

    updated = client.put(
        f"/api/scoring/profiles/{profile['id']}",
        json={
            "criteria": [
                {"code": code, "weight": (weight + 1 if code == "contract_value" else weight)}
                for code, weight in original.items()
            ]
        },
    )
    assert updated.status_code == 200
    refreshed = {item["code"]: item["weight"] for item in updated.json()["criteria"]}
    assert refreshed["contract_value"] == original["contract_value"] + 1
