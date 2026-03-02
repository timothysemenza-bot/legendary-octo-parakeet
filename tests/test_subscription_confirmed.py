from __future__ import annotations

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from src.models import EmailMessage
from src.receipt_extractors.apple_receipt_parser import parse_apple_receipt


def test_subscription_confirmed_with_charge_evidence_is_imported() -> None:
    msg = EmailMessage(
        message_id="msg-sub-confirmed-1",
        subject="Your Subscription Is Confirmed",
        sender="no_reply@email.apple.com",
        date=datetime(2026, 2, 14, tzinfo=ZoneInfo("America/New_York")),
        text_body=(
            "Your Subscription Is Confirmed\n"
            "You have been billed for YouTube Premium\n"
            "Price $13.99\n"
            "Total $13.99\n"
        ),
        html_body="",
        raw_content="",
    )

    items = parse_apple_receipt(msg)
    assert len(items) == 1
    assert str(items[0].amount) == "13.99"


def test_subscription_confirmed_without_charge_evidence_is_skipped() -> None:
    msg = EmailMessage(
        message_id="msg-sub-confirmed-2",
        subject="Your Subscription Is Confirmed",
        sender="no_reply@email.apple.com",
        date=datetime(2026, 2, 14, tzinfo=ZoneInfo("America/New_York")),
        text_body=(
            "Your Subscription Is Confirmed\n"
            "You can manage your subscription in Settings\n"
        ),
        html_body="",
        raw_content="",
    )

    with pytest.raises(ValueError, match="charge evidence"):
        parse_apple_receipt(msg)
