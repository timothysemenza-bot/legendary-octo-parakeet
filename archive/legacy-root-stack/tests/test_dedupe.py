from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from src.dedupe import filter_new_items, fingerprint
from src.models import ExistingLedgerKeys, NormalizedLineItem


def _item(invoice_id: str, message_id: str, description: str, amount: str) -> NormalizedLineItem:
    return NormalizedLineItem(
        purchase_date=datetime(2026, 2, 5, tzinfo=ZoneInfo("America/New_York")),
        vendor="Apple",
        description=description,
        amount=Decimal(amount),
        currency="USD",
        invoice_id=invoice_id,
        raw_message_id=message_id,
        source="test",
    )


def test_dedupe_invoice_id_priority() -> None:
    existing_row = _item("INV-1", "m0", "Item A", "2.99")
    existing = ExistingLedgerKeys(
        invoice_ids={"INV-1"},
        source_message_ids=set(),
        fingerprints={fingerprint(existing_row)},
    )
    incoming = [existing_row, _item("INV-2", "m2", "Item B", "3.99")]
    result = filter_new_items(incoming, existing)
    assert len(result.unique_items) == 1
    assert result.unique_items[0].invoice_id == "INV-2"


def test_dedupe_fingerprint_fallback() -> None:
    a = _item("", "", "Same Desc", "5.00")
    b = _item("", "", "Same Desc", "5.00")
    existing = ExistingLedgerKeys(invoice_ids=set(), source_message_ids=set(), fingerprints=set())
    result = filter_new_items([a, b], existing)
    assert len(result.unique_items) == 1
    assert result.dropped_count == 1
