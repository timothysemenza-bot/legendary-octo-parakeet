from __future__ import annotations


FORM_EXAMPLE_PRESETS: dict[str, list[dict[str, object]]] = {
    "organization_create": [
        {
            "key": "municipal_buyer",
            "title": "Municipal Buyer",
            "description": "Example of a city buying organization with procurement and notes fields filled in.",
            "values": {
                "name": "City of Sacramento",
                "organization_type": "MUNICIPALITY",
                "city": "Sacramento",
                "state": "CA",
                "website_url": "https://www.cityofsacramento.gov",
                "procurement_url": "https://www.cityofsacramento.gov/Finance/Procurement",
                "notes": "Tracks civic facilities, airport support, and municipal operations buying activity.",
            },
        },
        {
            "key": "airport_authority",
            "title": "Airport System",
            "description": "Example of a public airport buyer that could feed facilities and contractor opportunity tracking.",
            "values": {
                "name": "Sacramento County Airport System",
                "organization_type": "AIRPORT",
                "city": "Sacramento",
                "state": "CA",
                "website_url": "https://sacramento.aero",
                "procurement_url": "https://sacramento.aero/scas/business",
                "notes": "Use for terminal support, passenger services, and airport facilities procurements.",
            },
        },
    ],
    "facility_create": [
        {
            "key": "airport_terminal",
            "title": "Airport Terminal",
            "description": "Example of a complex facility record. If no organization exists yet, create one first or select the first available option after loading.",
            "values": {
                "organization_id": "__first__",
                "parent_facility_id": "",
                "name": "Terminal B Passenger Complex",
                "facility_kind": "FACILITY",
                "facility_type": "TERMINAL",
                "city": "Sacramento",
                "state": "CA",
                "service_complexity": "HIGH",
                "square_footage": "740000",
                "notes": "High-visibility passenger space with day porter, restrooms, circulation areas, and overnight custodial scope.",
            },
        }
    ],
    "contract_create": [
        {
            "key": "airport_support_contract",
            "title": "Airport Support Contract",
            "description": "Example of a contract radar record showing value, timing, incumbent, and rebid window.",
            "values": {
                "organization_id": "__first__",
                "title": "Terminal Janitorial and Day Porter Services",
                "incumbent_vendor": "SBM Management Services",
                "estimated_annual_value": "4200000",
                "estimated_total_value": "12600000",
                "start_date": "2024-10-01",
                "expiration_date": "2027-09-30",
                "rebid_window_start": "2027-02-01",
                "rebid_window_end": "2027-05-15",
                "procurement_source_url": "https://example.org/airport-board-packet",
                "source_type": "PUBLIC",
                "source_notes": "Board materials and operating updates suggest scrutiny on service responsiveness and transition readiness.",
            },
        }
    ],
    "contractor_create": [
        {
            "key": "national_facilities_partner",
            "title": "National Facilities Partner",
            "description": "Example of a fully populated contractor prospect for airport and municipal work.",
            "values": {
                "name": "SBM Management Services",
                "service_geographies": "California, Arizona, Washington, Oregon, New Jersey, Massachusetts",
                "headquarters_city": "Sacramento",
                "headquarters_state": "CA",
                "vertical_experience": "Airports, life sciences, data centers, distribution, commercial real estate, financial services",
                "labor_profile": "W2 self-perform",
                "union_profile": "Mixed",
                "diversity_certs": "Minority Business Enterprise",
                "airport_experience": True,
                "healthcare_experience": False,
                "education_experience": False,
                "municipal_experience": True,
                "scale_band": "NATIONAL",
                "relationship_strength": "4",
                "prospect_stage": "OUTREACH",
                "next_follow_up_date": "2026-03-17",
                "relationship_notes": "Existing alumni relationship with current leaders and proposal support credibility.",
                "strategic_fit_notes": "Strong candidate for airport and municipal expansion with pre-RFP support needs.",
            },
        }
    ],
    "contractor_touchpoint_create": [
        {
            "key": "growth_call",
            "title": "Growth Lead Call",
            "description": "Example of a relationship touchpoint that leaves a clear next step and follow-up date.",
            "values": {
                "contact_name": "Melissa Hampton",
                "touchpoint_type": "CALL",
                "touchpoint_at": "2026-03-09T11:20",
                "summary": "Discussed proposal support coverage, airport expansion goals, and likely municipal timing in California.",
                "next_step": "Send airport support positioning note and schedule a follow-up strategy call.",
                "next_follow_up_date": "2026-03-17",
            },
        }
    ],
    "contractor_pursuit_handoff": [
        {
            "key": "airport_handoff",
            "title": "Airport Handoff",
            "description": "Example of a contractor-to-pursuit handoff using a likely airport support target.",
            "values": {
                "contract_id": "__first__",
                "title": "Sacramento Airport Terminal Support Pursuit",
                "primary_facility_id": "__first__",
                "pursuit_stage": "PRE_RFP_CAPTURE",
                "confidence_level": "HIGH",
                "expected_rfp_date": "2026-08-15",
                "provenance_summary": "Contractor handoff from an airport-capable operator with active relationship access and transition credibility.",
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
        }
    ],
    "signal_source_create": [
        {
            "key": "board_packet_watch",
            "title": "Board Packet Watch",
            "description": "Example of a governance-oriented signal source for airport or authority monitoring.",
            "values": {
                "name": "California Airport Board Packet Watch",
                "source_type": "BOARD_PACKET",
                "region": "California",
                "owner_scope": "Airport Authority",
                "source_url": "https://example.org/airport-board-packets",
                "notes": "Tracks board packets, operating updates, and action items tied to airport support services.",
            },
        },
        {
            "key": "budget_tracker",
            "title": "Budget Tracker",
            "description": "Example of a funding-oriented source for state and local program movement.",
            "values": {
                "name": "State and Local Budget Hearing Tracker",
                "source_type": "BUDGET",
                "region": "Mid-Atlantic",
                "owner_scope": "State and Local Government",
                "source_url": "https://example.org/budget-hearings",
                "notes": "Tracks budget workshops, adopted budgets, and pass-through funding shifts tied to outsourced services.",
            },
        },
    ],
    "signal_event_create": [
        {
            "key": "airport_governance_signal",
            "title": "Airport Governance Signal",
            "description": "Example of a signal event derived from board materials. Works best after you have at least one source created.",
            "values": {
                "source_id": "__first__",
                "title": "Board packet signals terminal support expansion and custodial performance pressure",
                "signal_type": "GOVERNANCE",
                "signal_date": "2026-03-10",
                "jurisdiction": "California",
                "agency_name": "Sacramento County Airport System",
                "program_name": "Terminal Operations and Passenger Experience",
                "confidence_level": "HIGH",
                "summary": "Board materials indicate rising passenger-volume pressure, expanded terminal support needs, and dissatisfaction with custodial responsiveness.",
                "recommended_action": "Qualify the likely buying office, map current incumbent position, and start pre-RFP outreach around terminal support and transition readiness.",
                "source_url": "https://example.org/airport-board-packets/march",
                "source_reference": "March board packet, terminal readiness section",
            },
        }
    ],
    "opportunity_hypothesis_create": [
        {
            "key": "airport_hypothesis",
            "title": "Airport Hypothesis",
            "description": "Example of a capture-ready hypothesis tied to an existing signal, organization, and optional contractor recommendation.",
            "values": {
                "title": "Sacramento airport terminal support procurement likely in FY27 planning window",
                "sector": "Facilities Services",
                "geography": "Sacramento, California",
                "buying_organization_id": "__first__",
                "buying_organization": "Sacramento County Airport System",
                "service_line": "Janitorial, day porter, and terminal support services",
                "stage": "CAPTURE_READY",
                "confidence_level": "HIGH",
                "expected_release_start": "2026-07-15",
                "expected_release_end": "2026-10-15",
                "primary_signal_event_id": "__first__",
                "recommended_contractor_id": "__first__",
                "summary": "Upstream governance and operating signals suggest the airport will need stronger terminal-support coverage, service-level responsiveness, and public-facing facilities performance.",
                "recommended_action": "Validate procurement timing, incumbent vulnerability, and the transition story for an airport-capable operator before formal release.",
            },
        }
    ],
    "opportunity_manual_intake": [
        {
            "key": "manual_capture_entry",
            "title": "Manual Intake Example",
            "description": "Example of a manually qualified pursuit when you already know the buyer and contract value.",
            "values": {
                "name": "Sacramento Airport Terminal Support Pursuit",
                "buying_organization_id": "__first__",
                "client": "Sacramento County Airport System",
                "estimated_contract_value": "4200000",
                "lead_time_days": "120",
                "incumbent_status": True,
                "strategic_alignment": "5",
                "estimated_probability_win": "62",
                "actor": "operator",
            },
        }
    ],
    "capture_workbench_contact_create": [
        {
            "key": "buyer_contact",
            "title": "Buyer Contact",
                "description": "Example of a buying-side contact entry with role and source quality.",
                "values": {
                    "organization_id": "",
                    "contractor_id": "",
                "full_name": "Jordan Buyer",
                "role_title": "Procurement Director",
                "email": "jordan.buyer@example.org",
                "phone": "555-0102",
                "contact_side": "BUYER",
                "source_type": "PUBLIC",
                "confidence_level": "MEDIUM",
                "notes": "Named in board materials and likely tied to sourcing workflow.",
            },
        },
        {
            "key": "contractor_contact",
            "title": "Contractor Contact",
                "description": "Example of a contractor-side relationship entry tied to direct outreach.",
                "values": {
                    "organization_id": "",
                    "contractor_id": "__first__",
                "full_name": "Riley Partner",
                "role_title": "Regional Growth Lead",
                "email": "riley.partner@example.com",
                "phone": "555-0198",
                "contact_side": "CONTRACTOR",
                "source_type": "DIRECT_CONVERSATION",
                "confidence_level": "HIGH",
                "notes": "Aligned on pre-RFP timing and next capture meeting.",
            },
        },
    ],
    "capture_workbench_intelligence_create": [
        {
            "key": "positioning_note",
            "title": "Positioning Note",
            "description": "Example of a capture note that records one useful interpretation and where it came from.",
            "values": {
                "title": "Evaluator hypothesis",
                "note_type": "POSITIONING",
                "source_class": "INFERRED",
                "confidence_level": "MEDIUM",
                "provenance": "Public board commentary, current contract complaints, and terminal service-level discussion.",
                "note_text": "Likely emphasis on visible cleanliness, transition readiness, and rapid response during peak passenger windows.",
            },
        }
    ],
    "capture_workbench_evidence_create": [
        {
            "key": "board_packet_evidence",
            "title": "Board Packet Evidence",
            "description": "Example of an evidence record tied to a public source and a concise summary.",
                "values": {
                    "intelligence_note_id": "",
                    "contract_id": "",
                "source_class": "PUBLIC",
                "confidence_level": "HIGH",
                "source_url": "https://example.org/airport-board-packet",
                "provenance": "March board packet and contract record review.",
                "summary": "Board packet reinforces transition-speed concerns and service-level pressure in passenger areas.",
            },
        }
    ],
    "capture_workbench_action_create": [
        {
            "key": "follow_up_action",
            "title": "Follow-Up Action",
            "description": "Example of a concrete next step with an owner and due date.",
            "values": {
                "title": "Follow up with advised contractor",
                "action_type": "FOLLOW_UP",
                "status": "IN_PROGRESS",
                "owner": "operator",
                "due_date": "2026-03-18",
                "notes": "Confirm transition story, staffing assumptions, and pre-RFP meeting goals.",
            },
        }
    ],
    "capture_workbench_commercials": [
        {
            "key": "managed_pursuit_model",
            "title": "Managed Pursuit Model",
            "description": "Example of a basic commercial structure with retainer and fixed success fee.",
            "values": {
                "contractor_id": "__first__",
                "retainer_amount": "6000",
                "success_fee_type": "FIXED",
                "success_fee_value": "12000",
                "projected_payout_date": "2026-10-01",
                "projected_payout_amount": "18000",
                "realized_revenue": "",
                "notes": "Managed pursuit advisory model with fixed fee success component.",
            },
        }
    ],
}


def select_example_presets(*form_keys: str) -> dict[str, list[dict[str, object]]]:
    return {
        form_key: FORM_EXAMPLE_PRESETS[form_key]
        for form_key in form_keys
        if form_key in FORM_EXAMPLE_PRESETS
    }
