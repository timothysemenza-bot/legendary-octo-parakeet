import time

from fastapi.testclient import TestClient

from app.modules.proposal_builder.package_service import ProposalPackageService
from app.modules.proposal_builder.service import ProposalBuilderService
from tests.integration.test_proposal_package_api import _FakeOpenAIClient, _fake_package_ai, _wait_for_status


def test_proposal_package_dashboard_renders_run_status(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _FakeOpenAIClient())
    monkeypatch.setattr(ProposalPackageService, "_run_ai_structured_stage", _fake_package_ai)

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    initial_page = client.get(f"/opportunities/{opportunity_id}/proposal-builder")
    assert initial_page.status_code == 200
    assert "Allow draft pricing and template assets for testing only" in initial_page.text

    started_run = client.post(
        f"/opportunities/{opportunity_id}/proposal-package/start",
        data={"actor": "operator", "demo_mode": "true"},
        follow_redirects=False,
    )
    assert started_run.status_code == 303

    refreshed = None
    for _ in range(40):
        refreshed = client.get(f"/opportunities/{opportunity_id}/proposal-builder")
        if "Approve Pricing and Continue" in refreshed.text or "AWAITING_PRICING_APPROVAL" in refreshed.text:
            break
        time.sleep(0.1)
    assert refreshed is not None
    assert refreshed.status_code == 200
    assert "Full Proposal Package Engine" in refreshed.text
    assert "Package engine trail" in refreshed.text
    assert "Build final files" in refreshed.text
    assert ("Approve Pricing and Continue" in refreshed.text) or ("AWAITING_PRICING_APPROVAL" in refreshed.text)
    assert "Build Updated Proposal Package" in refreshed.text


def test_proposal_package_dashboard_hides_color_team_review_actions_by_default(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _FakeOpenAIClient())
    monkeypatch.setattr(ProposalPackageService, "_run_ai_structured_stage", _fake_package_ai)

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    opportunity_id = started.headers["location"].split("/")[2]

    started_run = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-package/runs",
        json={"actor": "operator"},
    )
    assert started_run.status_code == 200
    run_id = started_run.json()["id"]

    _wait_for_status(client, opportunity_id, run_id, "AWAITING_PRICING_APPROVAL")

    approved_pricing = client.post(
        f"/api/opportunities/{opportunity_id}/proposal-package/runs/{run_id}/approve-stage",
        json={"actor": "operator", "stage_name": "pricing"},
    )
    assert approved_pricing.status_code == 200

    export_payload = _wait_for_status(client, opportunity_id, run_id, "AWAITING_EXPORT_APPROVAL")
    assert export_payload["status"] == "AWAITING_EXPORT_APPROVAL"

    refreshed_page = None
    for _ in range(40):
        refreshed_page = client.get(f"/opportunities/{opportunity_id}/proposal-builder")
        if "Approve Final Export" in refreshed_page.text:
            break
        time.sleep(0.1)

    assert refreshed_page is not None
    assert refreshed_page.status_code == 200
    assert "Approve Final Export" in refreshed_page.text
    assert "Blocked at Pink Team Review" not in refreshed_page.text
    assert "Acknowledge Findings and Continue" not in refreshed_page.text
