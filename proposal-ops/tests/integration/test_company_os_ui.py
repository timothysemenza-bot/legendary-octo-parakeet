from pathlib import Path


def _seed_company_os(client, tmp_path: Path) -> None:
    source_dir = tmp_path / "sources"
    source_dir.mkdir(parents=True)
    (source_dir / "signal-2026-03-16.txt").write_text(
        "Client: Northstar. We need to review pricing and schedule the proposal meeting. Proposal due March 28, 2026.",
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
    response = client.post(
        "/api/company-os/ingest",
        json={"source_config_path": str(config_path), "marketing_agents_root": str(marketing_root)},
    )
    assert response.status_code == 200


def test_company_os_pages_render(client, tmp_path: Path) -> None:
    _seed_company_os(client, tmp_path)

    inbox = client.get("/company-os/inbox")
    assert inbox.status_code == 200
    assert "Engagement Inbox" in inbox.text

    engagements = client.get("/company-os/engagements")
    assert engagements.status_code == 200
    assert "Engagement Register" in engagements.text

    approvals = client.get("/company-os/approvals")
    assert approvals.status_code == 200
    assert "Approval Queue" in approvals.text

    founder = client.get("/company-os/founder-brief")
    assert founder.status_code == 200
    assert "Founder Brief" in founder.text

    scoreboard = client.get("/company-os/scoreboard")
    assert scoreboard.status_code == 200
    assert "Executive Scoreboard" in scoreboard.text
