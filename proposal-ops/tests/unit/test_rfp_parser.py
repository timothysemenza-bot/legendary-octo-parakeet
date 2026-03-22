from app.modules.rfp_parser.parser import parse_rfp_text


def test_parse_rfp_text_extracts_requirements_and_metadata() -> None:
    sample = """
    Proposal due date is 2026-05-30 and submissions must be uploaded electronically.
    Evaluation criteria include technical approach, management, and pricing.
    The contractor shall provide a staffing plan and must submit past performance references.
    Offeror must provide a detailed pricing narrative.
    """
    parsed = parse_rfp_text(sample)
    assert parsed["deadline"] == "2026-05-30"
    assert parsed["evaluation_criteria"] is not None
    assert parsed["submission_instructions"] is not None
    assert len(parsed["requirements"]) >= 2
    assert any(r["category"] == "PRICING" for r in parsed["requirements"])


def test_parse_rfp_text_extracts_month_name_deadline() -> None:
    sample = """
    Proposals Due: January 5, 2026.
    Evaluation criteria include technical approach and pricing.
    The contractor shall provide a staffing plan.
    """
    parsed = parse_rfp_text(sample)
    assert parsed["deadline"] == "January 5, 2026"


def test_parse_rfp_text_prefers_proposal_due_over_question_due_dates() -> None:
    sample = """
    Written Questions Due: December 8, 2025.
    Proposals Due: January 5, 2026.
    The contractor shall provide a staffing plan.
    """
    parsed = parse_rfp_text(sample)
    assert parsed["deadline"] == "January 5, 2026"


def test_parse_rfp_text_filters_boilerplate_but_keeps_actionable_obligations() -> None:
    sample = """
    Bidders are strongly encouraged to visit the NJSTART Vendor Support Page.
    The State intends to award one (1) Contract per Group in this Bid Solicitation.
    The Bidder should complete and submit the Offer and Acceptance Page with the Quote. If a Bidder does not submit the form with the Quote, the State may deem the Quote non-responsive.
    In order to be considered for award, the Quote must be received electronically by the required date and time.
    The Contractor shall provide its own equipment to perform the services required by this Bid Solicitation.
    """
    parsed = parse_rfp_text(sample)
    texts = [r["requirement_text"] for r in parsed["requirements"]]

    # Excluded as informational/non-actionable boilerplate.
    assert all("strongly encouraged" not in t.lower() for t in texts)
    assert all("state intends to award" not in t.lower() for t in texts)

    # Included as actionable compliance/scope obligations.
    assert any("submit the offer and acceptance page" in t.lower() for t in texts)
    assert any("must be received electronically" in t.lower() for t in texts)
    assert any("shall provide its own equipment" in t.lower() for t in texts)


def test_parse_rfp_text_excludes_definitions_and_state_discretion_lines() -> None:
    sample = """
    Dealer/Distributor – A Company authorized by a Bidder or Contractor ... means an authorized dealer relationship.
    The State may request a revision of the Bidder’s Quote within NJSTART.
    Bidders should note that this list is not exhaustive.
    The Bidder must submit its pricing using the State-Supplied Price Sheet.
    """
    parsed = parse_rfp_text(sample)
    texts = [r["requirement_text"].lower() for r in parsed["requirements"]]
    assert any("must submit its pricing" in t for t in texts)
    assert all("dealer/distributor" not in t for t in texts)
    assert all("state may request a revision" not in t for t in texts)
    assert all("list is not exhaustive" not in t for t in texts)


def test_parse_rfp_text_splits_compound_obligations_into_atomic_rows() -> None:
    sample = """
    The Bidder must submit the Offer and Acceptance Page and must submit the Ownership Disclosure Form.
    """
    parsed = parse_rfp_text(sample)
    texts = [r["requirement_text"].lower() for r in parsed["requirements"]]
    assert len(texts) == 2
    assert any("offer and acceptance page" in t for t in texts)
    assert any("ownership disclosure form" in t for t in texts)


def test_parse_rfp_text_collapses_near_duplicate_requirements() -> None:
    sample = """
    Price Lines 34, 68, and 102 are net line for agency use only, Bidders are not required to provide pricing for Price Lines 34, 68, and 102.
    Price Lines 34, 68, and 102 are net lines reserved for agency use only, Bidders are not required to provide pricing for Price Lines 34, 68, and 102.
    """
    parsed = parse_rfp_text(sample)
    texts = [r["requirement_text"] for r in parsed["requirements"]]
    assert len(texts) == 1


def test_parse_rfp_text_keeps_demo_structured_fields_clean() -> None:
    sample = """
    REQUEST FOR PROPOSALS
    Airport Terminal Janitorial and Day Porter Services
    Issued by: Metro Regional Airport Authority
    Solicitation Number: MR-AA-2026-041
    Issue Date: March 18, 2026

    Questions due: March 26, 2026
    Proposal due date: April 10, 2026 at 2:00 PM ET
    Contract term: Three-year base term with two one-year renewal options
    Locations: Main terminal, concourse connector, baggage claim, airport administration building

    Mandatory pre-proposal walkthrough: April 1, 2026 at 9:00 AM local time at the Metro Regional Airport Authority administration lobby.
    Evaluation criteria include technical approach, management and staffing plan, relevant airport or transportation past performance, transition and mobilization plan, and pricing.
    The offeror shall include resumes for the contract manager and day-shift supervisor.
    The offeror must complete Attachment A Pricing Workbook and Attachment B Certification Forms.
    The offeror shall provide evidence of general liability, workers compensation, and umbrella insurance coverage.
    """
    parsed = parse_rfp_text(sample)
    fields = parsed["structured_fields"]

    assert fields["solicitation_number"] == "MR-AA-2026-041"
    assert fields["questions_due_date"] == "March 26, 2026"
    assert fields["proposal_due_date"] == "April 10, 2026"
    assert fields["proposal_due_time"] == "2:00 PM ET"
    assert fields["geography"] == [
        "Main terminal",
        "concourse connector",
        "baggage claim",
        "airport administration building",
    ]
    assert fields["insurance_requirements"] == [
        "The offeror shall provide evidence of general liability, workers compensation, and umbrella insurance coverage."
    ]
    assert fields["mandatory_forms"] == [
        "The offeror must complete Attachment A Pricing Workbook and Attachment B Certification Forms."
    ]


def test_parse_rfp_text_extracts_response_due_phrasing() -> None:
    sample = """
    RFP responses must be received by March 4, 2026 at 3:00 PM ET through the procurement portal.
    Questions must be received by February 20, 2026.
    The contractor shall provide a staffing plan.
    """
    parsed = parse_rfp_text(sample)
    fields = parsed["structured_fields"]

    assert parsed["deadline"] == "March 4, 2026"
    assert fields["proposal_due_date"] == "March 4, 2026"
    assert fields["proposal_due_time"] == "3:00 PM ET"
    assert fields["questions_due_date"] == "February 20, 2026"


def test_parse_rfp_text_extracts_ordinal_month_name_deadline() -> None:
    sample = """
    ALL BIDS MUST BE SUBMITTED VIA THE PRISM PLATFORM.
    Bid proposals must be submitted by close of business on Tuesday, March 10th, 2026, to be considered.
    A walk-through of the properties is scheduled to take place on Monday, March 2nd, 2026, at 10:00 AM.
    """
    parsed = parse_rfp_text(sample)
    fields = parsed["structured_fields"]

    assert parsed["deadline"] == "March 10, 2026"
    assert fields["proposal_due_date"] == "March 10, 2026"
