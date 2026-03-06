from dataclasses import dataclass

from app.modules.opportunity_intake.schemas import PursuitRecommendation, Tier


@dataclass(frozen=True)
class ScoreWeights:
    strategic_alignment: float = 0.30
    probability: float = 0.25
    lead_time: float = 0.20
    contract_value: float = 0.15
    incumbent: float = 0.10


def normalize_strategic_alignment(value: int) -> float:
    return ((value - 1) / 4) * 100


def normalize_probability(value: int) -> float:
    return float(value)


def normalize_lead_time(days: int) -> float:
    if days >= 45:
        return 100.0
    if days >= 21:
        return 65.0
    return 35.0


def normalize_contract_value(amount: float) -> float:
    if amount >= 1_000_000:
        return 100.0
    if amount >= 250_000:
        return 70.0
    return 45.0


def normalize_incumbent_status(incumbent_status: bool) -> float:
    return 40.0 if incumbent_status else 85.0


def compute_intake_score(
    strategic_alignment: int,
    probability_win: int,
    lead_time_days: int,
    contract_value: float,
    incumbent_status: bool,
    weights: ScoreWeights | None = None,
) -> tuple[float, dict[str, float]]:
    w = weights or ScoreWeights()

    strategic = normalize_strategic_alignment(strategic_alignment) * w.strategic_alignment
    probability = normalize_probability(probability_win) * w.probability
    lead_time = normalize_lead_time(lead_time_days) * w.lead_time
    contract_value_component = normalize_contract_value(contract_value) * w.contract_value
    incumbent = normalize_incumbent_status(incumbent_status) * w.incumbent

    score = round(strategic + probability + lead_time + contract_value_component + incumbent, 2)
    breakdown = {
        "strategic_alignment_component": round(strategic, 2),
        "probability_component": round(probability, 2),
        "lead_time_component": round(lead_time, 2),
        "contract_value_component": round(contract_value_component, 2),
        "incumbent_component": round(incumbent, 2),
    }
    return score, breakdown


def classify_recommendation(score: float) -> PursuitRecommendation:
    if score >= 75:
        return PursuitRecommendation.BID
    if score >= 60:
        return PursuitRecommendation.CONDITIONAL
    return PursuitRecommendation.NO_BID


def classify_tier(score: float, contract_value: float) -> Tier:
    if score >= 80 and contract_value >= 1_000_000:
        return Tier.TIER_1
    if score >= 60:
        return Tier.TIER_2
    return Tier.TIER_3

