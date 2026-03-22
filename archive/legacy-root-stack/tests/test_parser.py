from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.models import EmailMessage
from src.receipt_extractors.apple_receipt_parser import parse_apple_receipt


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "messages"


def _load_message(name: str) -> EmailMessage:
    data = json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
    return EmailMessage(
        message_id=data["message_id"],
        subject=data["subject"],
        sender=data["sender"],
        date=datetime.fromisoformat(data["date"]),
        text_body=data.get("text_body", ""),
        html_body=data.get("html_body", ""),
        raw_content=data.get("raw_content", ""),
    )


def test_parse_subscription_receipt() -> None:
    msg = _load_message("apple_bill_subscription.json")
    items = parse_apple_receipt(msg)
    assert len(items) == 1
    assert items[0].invoice_id == "MXA12345ABC"
    assert str(items[0].amount) == "2.99"


def test_parse_multi_item_html_receipt() -> None:
    msg = _load_message("app_store_multi_item.json")
    items = parse_apple_receipt(msg)
    assert len(items) == 2
    assert {str(i.amount) for i in items} == {"4.99", "1.99"}
    assert items[0].invoice_id == "INV-998877"


def test_parse_hardware_invoice() -> None:
    msg = _load_message("apple_store_hardware.json")
    items = parse_apple_receipt(msg)
    assert len(items) == 1
    assert items[0].invoice_id == "DOC-445566"


def test_parse_refund_negative_amount() -> None:
    msg = _load_message("refund_receipt.json")
    items = parse_apple_receipt(msg)
    assert len(items) == 1
    assert str(items[0].amount) == "-3.99"
