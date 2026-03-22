from __future__ import annotations

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from src.models import EmailMessage
from src.receipt_extractors.apple_receipt_parser import parse_apple_receipt


def test_parser_rejects_apple_pay_merchant_style_receipt() -> None:
    msg = EmailMessage(
        message_id="msg-bad-1",
        subject="Receipt for your purchase",
        sender="no_reply@email.apple.com",
        date=datetime(2026, 2, 7, tzinfo=ZoneInfo("America/New_York")),
        text_body=(
            "Apple Pay\n"
            "1 Large Plain Cheese $15.99\n"
            "Tip $2.00\n"
            "To pay $17.99\n"
        ),
        html_body="",
        raw_content="",
    )

    with pytest.raises(ValueError, match="Apple billing receipt|Apple Pay merchant receipt"):
        parse_apple_receipt(msg)
