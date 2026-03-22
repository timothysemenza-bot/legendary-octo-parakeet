from __future__ import annotations

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from src.models import EmailMessage
from src.receipt_extractors.apple_receipt_parser import parse_apple_receipt


def test_fallback_extracts_subscription_name_when_subject_is_generic() -> None:
    msg = EmailMessage(
        message_id="msg-generic-subject-sub-1",
        subject="Your receipt from Apple.",
        sender="no_reply@email.apple.com",
        date=datetime(2026, 2, 20, tzinfo=ZoneInfo("America/New_York")),
        text_body=(
            "Apple.com/bill\n"
            "Subscription: YouTube Premium\n"
            "Order ID: MXA-SUB-1001\n"
            "Total $13.99\n"
        ),
        html_body="",
        raw_content="",
    )

    items = parse_apple_receipt(msg)
    assert len(items) == 1
    assert items[0].description == "Subscription: YouTube Premium"
    assert str(items[0].amount) == "13.99"


def test_generic_subject_without_service_name_is_rejected() -> None:
    msg = EmailMessage(
        message_id="msg-generic-subject-no-service-1",
        subject="Your receipt from Apple.",
        sender="no_reply@email.apple.com",
        date=datetime(2026, 2, 20, tzinfo=ZoneInfo("America/New_York")),
        text_body=(
            "Apple.com/bill\n"
            "Order ID: MXA-UNKNOWN-1002\n"
            "Total $19.99\n"
        ),
        html_body="",
        raw_content="",
    )

    with pytest.raises(ValueError, match="description"):
        parse_apple_receipt(msg)
