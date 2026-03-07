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
