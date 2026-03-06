from fastapi.testclient import TestClient


def _create_opportunity(client: TestClient) -> str:
    response = client.post(
        "/api/opportunities/intake",
        json={
            "name": "Review Workflow Pursuit",
            "client": "State Agency",
            "estimated_contract_value": 800000,
            "lead_time_days": 40,
            "incumbent_status": False,
            "strategic_alignment": 4,
            "estimated_probability_win": 65,
            "actor": "operator",
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def _prepare_gate_c_ready(client: TestClient, opportunity_id: str) -> None:
    client.post(
        f"/api/opportunities/{opportunity_id}/rfp/parse",
        data={
            "raw_text": "The Contractor shall provide staffing plan. The Bidder must submit pricing sheet.",
            "source_filename": "rfp.txt",
            "actor": "operator",
        },
    )
    rows = client.get(f"/api/opportunities/{opportunity_id}/compliance-matrix").json()
    for row in rows:
        client.patch(
            f"/api/compliance-matrix/{row['id']}",
            json={
                "proposal_section": row["proposal_section"],
                "owner": "Compliance Lead",
                "status": "COMPLETE",
                "actor": "operator",
            },
        )


def test_review_cycle_comment_and_readiness_flow(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    cycle = client.post(
        f"/api/opportunities/{opportunity_id}/reviews",
        json={"review_type": "PINK", "round_number": 1, "actor": "review-lead"},
    )
    assert cycle.status_code == 200
    cycle_id = cycle.json()["id"]

    comment = client.post(
        f"/api/opportunities/reviews/{cycle_id}/comments",
        json={
            "section_code": "Technical Approach",
            "severity": "HIGH",
            "comment_text": "Claim lacks evidence.",
            "owner": "section-owner",
            "created_by": "reviewer-a",
        },
    )
    assert comment.status_code == 200
    comment_id = comment.json()["id"]

    close = client.post(
        f"/api/opportunities/{opportunity_id}/reviews/{cycle_id}/close",
        json={"actor": "review-lead"},
    )
    assert close.status_code == 200

    readiness = client.get(f"/api/opportunities/{opportunity_id}/reviews/readiness")
    assert readiness.status_code == 200
    assert readiness.json()["gate_d_ready"] is False

    resolve = client.post(
        f"/api/opportunities/reviews/comments/{comment_id}/resolve",
        json={"actor": "reviewer-a"},
    )
    assert resolve.status_code == 200

    readiness_after = client.get(f"/api/opportunities/{opportunity_id}/reviews/readiness")
    assert readiness_after.status_code == 200
    assert readiness_after.json()["gate_d_ready"] is True


def test_gate_d_and_e_enforced_by_review_readiness(client: TestClient) -> None:
    opportunity_id = _create_opportunity(client)
    _prepare_gate_c_ready(client, opportunity_id)
    client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_A",
            "decision": "APPROVED",
            "decider": "pm-1",
            "decider_role": "proposal_manager",
            "rationale": "Proceed to strategy.",
        },
    )
    client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_B",
            "decision": "APPROVED",
            "decider": "strategy-1",
            "decider_role": "capture_strategy_lead",
            "rationale": "Strategy approved.",
        },
    )
    client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_C",
            "decision": "APPROVED",
            "decider": "compliance-1",
            "decider_role": "compliance_lead",
            "rationale": "Compliance architecture approved.",
        },
    )
    client.post(
        f"/api/opportunities/{opportunity_id}/stage-transition",
        json={
            "next_stage": "DRAFTING",
            "actor": "pm-1",
            "actor_role": "proposal_manager",
            "reason": "Start drafting after planning.",
        },
    )

    blocked_d = client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_D",
            "decision": "APPROVED",
            "decider": "review-lead-1",
            "decider_role": "review_lead",
            "rationale": "Attempting gate D without review.",
        },
    )
    assert blocked_d.status_code == 409

    pink = client.post(
        f"/api/opportunities/{opportunity_id}/reviews",
        json={"review_type": "PINK", "round_number": 1, "actor": "review-lead"},
    ).json()
    client.post(
        f"/api/opportunities/{opportunity_id}/reviews/{pink['id']}/close",
        json={"actor": "review-lead"},
    )

    approved_d = client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_D",
            "decision": "APPROVED",
            "decider": "review-lead-1",
            "decider_role": "review_lead",
            "rationale": "Pink review complete and clear.",
        },
    )
    assert approved_d.status_code == 200

    blocked_e = client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_E",
            "decision": "APPROVED",
            "decider": "pm-1",
            "decider_role": "proposal_manager",
            "rationale": "Attempting gate E without red/gold review.",
        },
    )
    assert blocked_e.status_code == 409

    red = client.post(
        f"/api/opportunities/{opportunity_id}/reviews",
        json={"review_type": "RED", "round_number": 1, "actor": "review-lead"},
    ).json()
    client.post(
        f"/api/opportunities/{opportunity_id}/reviews/{red['id']}/close",
        json={"actor": "review-lead"},
    )

    approved_e = client.post(
        f"/api/opportunities/{opportunity_id}/gate-decisions",
        json={
            "gate_code": "GATE_E",
            "decision": "APPROVED",
            "decider": "pm-1",
            "decider_role": "proposal_manager",
            "rationale": "Narrative review complete.",
        },
    )
    assert approved_e.status_code == 200
