from unittest.mock import MagicMock

from sqlalchemy.exc import OperationalError

from app.modules.janitorial_os.schemas import UxEventCreate, UxEventType, UxFeedbackCreate, UxFeedbackType
from app.modules.janitorial_os.service import JanitorialOsService


def test_log_ux_event_returns_fallback_response_when_database_is_locked() -> None:
    db = MagicMock()
    db.commit.side_effect = OperationalError("INSERT INTO ux_events ...", {}, Exception("database is locked"))
    service = JanitorialOsService(db)

    response = service.log_ux_event(
        UxEventCreate(
            session_id="session-12345",
            event_type=UxEventType.PAGE_VIEW,
            page_key="/opportunities/:id/proposal-builder",
            path="/opportunities/123/proposal-builder",
            metadata_json={"page_title": "Boss Key Pursuit OS"},
        ),
        actor="demo-user",
    )

    assert response.event_type == UxEventType.PAGE_VIEW.value
    assert response.page_key == "/opportunities/:id/proposal-builder"
    assert response.metadata_json["page_title"] == "Boss Key Pursuit OS"
    db.rollback.assert_called_once()


def test_submit_ux_feedback_returns_fallback_response_when_database_is_locked() -> None:
    db = MagicMock()
    db.flush.side_effect = OperationalError("INSERT INTO ux_feedback ...", {}, Exception("database is locked"))
    service = JanitorialOsService(db)

    response = service.submit_ux_feedback(
        UxFeedbackCreate(
            session_id="session-12345",
            feedback_type=UxFeedbackType.CONFUSING,
            page_key="/contractors",
            path="/contractors",
            form_name="contractor_create",
            note_text="This page was hard to follow.",
            context_json={"step": "create"},
        ),
        actor="demo-user",
    )

    assert response.feedback_type == UxFeedbackType.CONFUSING.value
    assert response.page_key == "/contractors"
    assert response.context_json["step"] == "create"
    db.rollback.assert_called_once()
