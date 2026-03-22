from io import BytesIO
import zipfile

from docx import Document
from fastapi.testclient import TestClient


def _template_bytes() -> bytes:
    document = Document()
    for anchor in (
        "{{ transmittal_letter }}",
        "{{ executive_summary }}",
        "{{ technical_approach }}",
        "{{ management_staffing_plan }}",
        "{{ transition_mobilization_plan }}",
        "{{ past_performance }}",
        "{{ pricing_and_commercials }}",
        "{{ compliance_attachments }}",
    ):
        document.add_paragraph(anchor)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _zip_bytes() -> bytes:
    payload = BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("pricing-model.csv", "labor category,hourly rate,burden factor,markup factor,default hours per week\nJanitor,20.5,1.27,1.18,160\n")
        archive.writestr("proposal-template.docx", _template_bytes())
        archive.writestr("client-playbook.txt", "Use buyer-focused language.")
        archive.writestr("resume-lead.txt", "Resume content")
        archive.writestr("reference-one.txt", "Reference content")
    return payload.getvalue()


def test_client_onboarding_pages_render_and_support_pack_flow(client: TestClient) -> None:
    page = client.get("/client-onboarding")
    assert page.status_code == 200
    assert "Client Onboarding" in page.text
    assert "Upload Client Pack" in page.text
    assert "Approve Playbook and Defaults" in page.text
    assert "Activate Client Environment" in page.text

    created = client.post(
        "/client-onboarding/packs",
        data={"actor": "admin", "client_display_name": "Demo Client", "pack_name": "Demo Pack"},
        files={"archive": ("demo-pack.zip", _zip_bytes(), "application/zip")},
        follow_redirects=False,
    )
    assert created.status_code == 303

    detail = client.get(created.headers["location"])
    assert detail.status_code == 200
    assert "Parsed Assets" in detail.text
    assert "Generated Playbook" in detail.text
    assert "Approve Playbook and Defaults" in detail.text
    assert "Save Playbook Draft" in detail.text
    assert "Update" in detail.text
