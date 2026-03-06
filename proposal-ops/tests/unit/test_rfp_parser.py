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
