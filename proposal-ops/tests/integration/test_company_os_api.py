from pathlib import Path

from fastapi.testclient import TestClient


def test_company_os_ingest_and_projection_cycle(client: TestClient, tmp_path: Path) -> None:
    source_dir = tmp_path / "sources"
    source_dir.mkdir(parents=True)
    (source_dir / "acme-intro-call-2026-03-16.txt").write_text(
        "Client: Acme Facility Services. We need to review pricing, build a reverse timeline, and schedule a stakeholder meeting. Proposal due March 25, 2026.",
        encoding="utf-8",
    )

    config_path = tmp_path / "approved_sources.csv"
    config_path.write_text(
        "source_id,source_type,source_path,file_pattern,enabled\n"
        f"tmp_transcripts,document_dir,{source_dir.as_posix()},*.txt,yes\n",
        encoding="utf-8",
    )

    marketing_root = tmp_path / "marketing-agents"
    (marketing_root / "data").mkdir(parents=True)
    (marketing_root / "briefs").mkdir(parents=True)

    response = client.post(
        "/api/company-os/ingest",
        json={
            "source_config_path": str(config_path),
            "marketing_agents_root": str(marketing_root),
            "owner": "Timmy Semenza",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["signals_created"] == 1
    assert payload["engagements_created"] == 1
    assert payload["approvals_created"] == 1

    engagements = client.get("/api/company-os/engagements")
    assert engagements.status_code == 200
    assert len(engagements.json()) == 1
    assert engagements.json()[0]["workflow_stage"] == "APPROVAL_WAIT"

    scoreboard = client.get("/api/company-os/scoreboard/latest")
    assert scoreboard.status_code == 200
    assert "weighted_pipeline" in scoreboard.json()

    founder_brief = client.get("/api/company-os/founder-brief/latest")
    assert founder_brief.status_code == 200
    assert "executive_control_summary" in founder_brief.json()

    assert (marketing_root / "data" / "communication_signal_log.csv").exists()
    assert (marketing_root / "data" / "engagement_register.csv").exists()
    assert (marketing_root / "data" / "executive_scoreboard.csv").exists()
    assert (marketing_root / "briefs" / "founder-brief-latest.md").exists()


def test_company_os_status_update_endpoints(client: TestClient, tmp_path: Path) -> None:
    source_dir = tmp_path / "sources"
    source_dir.mkdir(parents=True)
    (source_dir / "client-thread-2026-03-16.txt").write_text(
        "Client: BrightPath. We need to review the intake and send follow up notes.",
        encoding="utf-8",
    )
    config_path = tmp_path / "approved_sources.csv"
    config_path.write_text(
        "source_id,source_type,source_path,file_pattern,enabled\n"
        f"tmp_docs,document_dir,{source_dir.as_posix()},*.txt,yes\n",
        encoding="utf-8",
    )
    marketing_root = tmp_path / "marketing-agents"
    (marketing_root / "data").mkdir(parents=True)
    (marketing_root / "briefs").mkdir(parents=True)

    ingest = client.post(
        "/api/company-os/ingest",
        json={"source_config_path": str(config_path), "marketing_agents_root": str(marketing_root)},
    )
    assert ingest.status_code == 200

    approvals = client.get("/api/company-os/approvals").json()
    approval_id = approvals[0]["id"]
    approval_update = client.post(f"/api/company-os/approvals/{approval_id}/status", json={"status": "approved"})
    assert approval_update.status_code == 200
    assert approval_update.json()["status"] == "approved"

    commitments = client.get("/api/company-os/commitments").json()
    commitment_id = commitments[0]["id"]
    commitment_update = client.post(f"/api/company-os/commitments/{commitment_id}/status", json={"status": "done"})
    assert commitment_update.status_code == 200
    assert commitment_update.json()["status"] == "done"
