from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.main import _message_matches_merchants
from src.models import EmailMessage

MERCHANTS = {
    "vendors": [
        {
            "name": "Apple",
            "sender_contains": ["apple.com", "no_reply@email.apple.com"],
            "subject_contains": ["receipt", "invoice", "apple.com/bill", "app store", "itunes"],
        }
    ]
}


def _msg(sender: str, subject: str) -> EmailMessage:
    return EmailMessage(
        message_id="m1",
        subject=subject,
        sender=sender,
        date=datetime(2026, 2, 10, tzinfo=ZoneInfo("America/New_York")),
        text_body="",
        html_body="",
        raw_content="",
    )


def test_message_match_requires_sender_and_subject() -> None:
    assert _message_matches_merchants(_msg("no_reply@email.apple.com", "Your App Store receipt"), MERCHANTS)
    assert not _message_matches_merchants(_msg("merchant@example.com", "Your receipt"), MERCHANTS)
    assert not _message_matches_merchants(_msg("no_reply@email.apple.com", "Hello there"), MERCHANTS)
