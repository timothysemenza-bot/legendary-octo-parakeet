from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.models import EmailMessage
from src.receipt_extractors.apple_receipt_parser import parse_apple_receipt


def test_parser_filters_device_only_lines_but_keeps_subscription_line() -> None:
    msg = EmailMessage(
        message_id="msg-subscription-mix-1",
        subject="Your receipt from Apple",
        sender="no_reply@email.apple.com",
        date=datetime(2026, 2, 12, tzinfo=ZoneInfo("America/New_York")),
        text_body=(
            "Apple.com/bill\n"
            "Order ID: MXA12345SUB\n"
            "Timmy Semenza's iPhone $19.99\n"
            "YouTube Premium $13.99\n"
            "Total $33.98\n"
        ),
        html_body="",
        raw_content="",
    )

    items = parse_apple_receipt(msg)
    assert len(items) == 1
    assert items[0].description == "YouTube Premium"
    assert str(items[0].amount) == "13.99"
