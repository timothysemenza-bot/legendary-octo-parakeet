from datetime import date
from types import SimpleNamespace

from app.modules.capture_plan.service import (
    DEFAULT_CAPTURE_TIMELINE,
    build_capture_timeline,
    build_bootstrap_capture_plan_content,
    build_enriched_capture_plan_content,
    evaluate_capture_plan_readiness,
)


def test_build_capture_timeline_backplans_from_deadline() -> None:
    timeline = build_capture_timeline(date(2026, 5, 30))
    assert (
        timeline
        == "Kickoff by 2026-04-15; Strategy lock by 2026-04-30; Content complete by 2026-05-09; "
        "Pink/Red review window by 2026-05-16; Final packaging by 2026-05-23; "
        "Executive authorization by 2026-05-28; Submission on 2026-05-30."
    )


def test_build_capture_timeline_uses_default_without_deadline() -> None:
    assert build_capture_timeline(None) == DEFAULT_CAPTURE_TIMELINE


def test_build_enriched_capture_plan_content_is_deterministic() -> None:
    opportunity = SimpleNamespace(
        name="Deterministic Capture Pursuit",
        client="Transit Authority",
        estimated_contract_value=1250000.0,
        lead_time_days=28,
        incumbent_status=False,
        qualification_score=74.6,
        tier="TIER_1",
        pursuit_recommendation="BID",
    )
    solicitation = SimpleNamespace(
        extracted_deadline="2026-05-30",
        extracted_evaluation_criteria="Evaluation criteria include technical approach, management, and pricing.",
        extracted_submission_instructions="Submissions must be uploaded electronically by 5:00 PM.",
    )
    matrix_rows = [
        {"category": "TECHNICAL", "proposal_section": "Technical Approach", "status": "UNMAPPED", "owner": "UNASSIGNED"},
        {"category": "MANAGEMENT", "proposal_section": "Management Plan", "status": "UNMAPPED", "owner": "UNASSIGNED"},
        {"category": "PAST_PERFORMANCE", "proposal_section": "Past Performance", "status": "UNMAPPED", "owner": "UNASSIGNED"},
        {"category": "PRICING", "proposal_section": "Pricing Narrative", "status": "UNMAPPED", "owner": "UNASSIGNED"},
    ]
    matrix_quality = {
        "gate_c_ready": False,
        "gate_c_blockers": ["4 rows remain UNMAPPED.", "4 rows have no assigned owner."],
    }

    content = build_enriched_capture_plan_content(
        opportunity,
        solicitation,
        matrix_rows,
        matrix_quality,
        today=date(2026, 4, 1),
    )

    assert "Deterministic Capture Pursuit for Transit Authority" in content["summary"]
    assert "BID recommendation" in content["summary"]
    assert "2026-05-30" in content["summary"]
    assert "Evaluation focus:" in content["client_priorities"]
    assert "Submission discipline:" in content["client_priorities"]
    assert "Submission is due in 59 days" in content["client_priorities"]
    assert "No incumbent advantage is recorded" in content["competitive_landscape"]
    assert "Current compliance blockers: 4 rows remain UNMAPPED.; 4 rows have no assigned owner." in content["competitive_landscape"]
    assert "Win Theme: Prove a technical approach" in content["win_themes_draft"]
    assert "Win Theme: Show disciplined staffing" in content["win_themes_draft"]
    assert "technical response" in content["solution_positioning"].lower()
    assert "pricing as disciplined" in content["solution_positioning"].lower()
    assert content["timeline"].endswith("Submission on 2026-05-30.")


def test_capture_plan_readiness_blocks_bootstrap_and_missing_rfp_artifacts() -> None:
    opportunity = SimpleNamespace(
        id="opp-1",
        name="Bootstrap Pursuit",
        client="Transit Authority",
    )
    bootstrap = build_bootstrap_capture_plan_content(opportunity)
    capture_plan = SimpleNamespace(id="cp-1", version=1, **bootstrap)

    readiness = evaluate_capture_plan_readiness(
        opportunity=opportunity,
        capture_plan=capture_plan,
        solicitation=None,
        matrix_rows=[],
    )

    assert readiness.ready_for_gate_b is False
    assert readiness.uses_bootstrap_template is True
    assert "Capture plan is still the intake bootstrap template." in readiness.blockers
    assert "No solicitation has been parsed for this opportunity." in readiness.blockers
    assert "No compliance matrix rows exist for the latest solicitation." in readiness.blockers


def test_capture_plan_readiness_passes_for_enriched_plan_with_multiple_win_themes() -> None:
    opportunity = SimpleNamespace(
        id="opp-2",
        name="Enriched Pursuit",
        client="Transit Authority",
    )
    capture_plan = SimpleNamespace(
        id="cp-2",
        version=2,
        summary="Enriched Pursuit for Transit Authority: BID recommendation, TIER 1, estimated value $1,250,000, due 2026-05-30.",
        client_priorities="Evaluation focus: technical approach and pricing. Submission discipline: electronic upload.",
        competitive_landscape="No incumbent advantage is recorded. Qualification score supports a bid posture.",
        win_themes_draft="Win Theme: Prove the technical approach.\nWin Theme: Show disciplined staffing.",
        solution_positioning="Lead with evaluator priorities and measurable outcomes.",
        timeline="Kickoff by 2026-04-15; Strategy lock by 2026-04-30; Submission on 2026-05-30.",
    )
    solicitation = SimpleNamespace(id="sol-1")

    readiness = evaluate_capture_plan_readiness(
        opportunity=opportunity,
        capture_plan=capture_plan,
        solicitation=solicitation,
        matrix_rows=[{"proposal_section": "Technical Approach"}],
    )

    assert readiness.ready_for_gate_b is True
    assert readiness.uses_bootstrap_template is False
    assert readiness.win_theme_count == 2
    assert readiness.blockers == []
