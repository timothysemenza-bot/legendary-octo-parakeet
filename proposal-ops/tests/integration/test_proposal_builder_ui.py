import io

from fastapi.testclient import TestClient
from docx import Document

from app.modules.proposal_builder.service import ProposalBuilderService


class _UnavailableOpenAIClient:
    available = False
    model = "gpt-5.4"
    timeout_seconds = 300


def test_proposal_builder_start_page_renders(client: TestClient) -> None:
    response = client.get("/proposal-builder")
    assert response.status_code == 200
    assert "Upload an RFP" in response.text
    assert "Start Proposal" in response.text
    assert "Launch Demo Sample" in response.text
    assert "Manage Client Profiles" in response.text
    assert "Client Onboarding" in response.text


def test_proposal_builder_demo_sample_flow_supports_export(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _UnavailableOpenAIClient())

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    workspace_path = started.headers["location"]

    workspace = client.get(workspace_path)
    assert workspace.status_code == 200
    assert "Proposal Package" in workspace.text
    assert "Package engine trail" in workspace.text
    assert "Shape the response" in workspace.text
    assert "Prepare pricing and forms" in workspace.text
    assert "Fastest demo path" in workspace.text
    assert "Create Presentable Word Draft Fast" in workspace.text
    assert "Token safeguards" in workspace.text
    assert "What we found" in workspace.text
    assert "What we still need from you" in workspace.text
    assert "Start Full Package Run" in workspace.text
    assert "Best next step" in workspace.text
    assert "Add Addendum Files" in workspace.text
    assert "Paste Buyer Notes" in workspace.text
    assert "Other things you can add" in workspace.text
    assert "Advanced details" in workspace.text

    skeleton = client.post(f"{workspace_path}/skeleton", data={"actor": "operator"})
    assert skeleton.status_code == 200
    assert "Proposal structure" in skeleton.text
    assert "Win themes and plan" in skeleton.text

    draft = client.post(f"{workspace_path}/draft", data={"actor": "operator"})
    assert draft.status_code == 200
    assert "Draft preview" in draft.text
    assert "Executive Summary" in draft.text
    assert "Technical Approach" in draft.text
    assert "Management and Staffing Plan" in draft.text
    assert "Transition and Mobilization Plan" in draft.text

    exported = client.post(f"{workspace_path}/export", data={"actor": "operator"})
    assert exported.status_code == 200
    assert "Draft Proposal DOCX" in exported.text
    assert "Support Bundle" in exported.text

    opportunity_id = workspace_path.split("/")[2]
    docx = client.get(f"/api/opportunities/{opportunity_id}/proposal-builder/export/docx")
    assert docx.status_code == 200
    bundle = client.get(f"/api/opportunities/{opportunity_id}/proposal-builder/export/bundle")
    assert bundle.status_code == 200


def test_proposal_builder_best_draft_action_runs_full_fast_path(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _UnavailableOpenAIClient())

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    workspace_path = started.headers["location"]

    built = client.post(f"{workspace_path}/best-draft", data={"actor": "operator"})
    assert built.status_code == 200
    assert "Presentable Word draft generated." in built.text
    assert "Your presentable Word draft is ready" in built.text
    assert "Download Presentable Word Draft" in built.text

    opportunity_id = workspace_path.split("/")[2]
    docx = client.get(f"/api/opportunities/{opportunity_id}/proposal-builder/export/docx")
    assert docx.status_code == 200


def test_proposal_builder_preview_edits_can_refresh_word_export(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _UnavailableOpenAIClient())

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    workspace_path = started.headers["location"]
    opportunity_id = workspace_path.split("/")[2]

    built = client.post(f"{workspace_path}/best-draft", data={"actor": "operator"})
    assert built.status_code == 200
    assert "Open HTML Preview" in built.text

    preview = client.get(f"{workspace_path}/preview")
    assert preview.status_code == 200
    assert "HTML Proposal Preview" in preview.text
    assert "Edit this section" in preview.text

    edited = client.post(
        f"{workspace_path}/preview/sections/0",
        data={
            "actor": "operator",
            "body_markdown": "Updated executive summary for Eric.\n\n- Stronger opening\n- Clearer differentiators",
        },
    )
    assert edited.status_code == 200
    assert "Section changes saved. Refresh the Word draft when you are ready." in edited.text
    assert "Create Word Draft" in edited.text
    assert "Updated executive summary for Eric." in edited.text

    exported = client.post(f"{workspace_path}/export", data={"actor": "operator"})
    assert exported.status_code == 200
    assert "Download Presentable Word Draft" in exported.text

    docx = client.get(f"/api/opportunities/{opportunity_id}/proposal-builder/export/docx")
    assert docx.status_code == 200
    document = Document(io.BytesIO(docx.content))
    combined_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    assert "Updated executive summary for Eric." in combined_text
    assert "Stronger opening" in combined_text


def test_proposal_builder_workspace_accepts_additional_materials(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(ProposalBuilderService, "_openai_client", lambda self, **_kwargs: _UnavailableOpenAIClient())

    started = client.post(
        "/proposal-builder/start",
        data={"use_demo_sample": "true", "actor": "operator"},
        follow_redirects=False,
    )
    assert started.status_code == 303
    workspace_path = started.headers["location"]

    updated = client.post(
        f"{workspace_path}/materials",
        data={
            "actor": "operator",
            "material_kind": "buyer discovery notes",
            "raw_text_filename": "buyer-discovery-notes.txt",
            "raw_text": "Buyer discovery notes: emphasize reporting visibility, local supervision, and a strong response-time story.",
        },
    )
    assert updated.status_code == 200
    assert "New material added. The RFP summary and checklist were refreshed." in updated.text
    assert "Keep shaping the response" in updated.text
    assert "v2" in updated.text
    assert "buyer-discovery-notes.txt" in updated.text
    assert "Suggested next inputs" in updated.text
    assert "Build Updated Package" in updated.text
