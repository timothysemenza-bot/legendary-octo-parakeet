from datetime import date

from app.modules.company_os.service import classify_route, extract_action_items, extract_deadline


def test_classify_route_detects_proposal_capture() -> None:
    route = classify_route("RFP response needed with reverse timeline and pricing sheet by Friday.")
    assert route == "proposal-capture"


def test_extract_deadline_parses_textual_month_deadline() -> None:
    deadline = extract_deadline("Proposal due March 22, 2026 with pricing review beforehand.", date(2026, 3, 17))
    assert deadline == date(2026, 3, 22)


def test_extract_action_items_derives_follow_ups() -> None:
    actions = extract_action_items(
        "We need to review pricing today. Please schedule the stakeholder interview tomorrow. We will draft the proposal narrative next.",
        "proposal-capture",
        date(2026, 3, 17),
        date(2026, 3, 24),
    )

    assert len(actions) >= 3
    assert actions[0]["review_required"] == "yes"
    assert any(item["type"] == "meeting" for item in actions)
    assert any(item["type"] == "artifact-build" for item in actions)
