from app.modules.opportunity_intake.scoring import (
    classify_recommendation,
    classify_tier,
    compute_intake_score,
)


def test_scoring_formula_fixed_fixture() -> None:
    score, breakdown = compute_intake_score(
        strategic_alignment=5,
        probability_win=80,
        lead_time_days=50,
        contract_value=1_200_000,
        incumbent_status=False,
    )
    assert round(score, 2) == 93.5
    assert breakdown["strategic_alignment_component"] == 30.0


def test_tier_boundaries() -> None:
    assert classify_tier(59, 2_000_000).value == "TIER_3"
    assert classify_tier(60, 500_000).value == "TIER_2"
    assert classify_tier(74, 500_000).value == "TIER_2"
    assert classify_tier(75, 500_000).value == "TIER_2"
    assert classify_tier(80, 1_500_000).value == "TIER_1"


def test_recommendation_mapping() -> None:
    assert classify_recommendation(59).value == "NO_BID"
    assert classify_recommendation(60).value == "CONDITIONAL"
    assert classify_recommendation(74).value == "CONDITIONAL"
    assert classify_recommendation(75).value == "BID"
