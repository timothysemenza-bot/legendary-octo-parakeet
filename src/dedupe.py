from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .models import ExistingLedgerKeys, NormalizedLineItem
from .utils import stable_description_hash


@dataclass(slots=True)
class DedupeResult:
    unique_items: list[NormalizedLineItem]
    dropped_count: int


def fingerprint(item: NormalizedLineItem) -> str:
    desc_hash = stable_description_hash(item.description)
    return f"{item.purchase_date.date().isoformat()}|{item.amount:.2f}|{desc_hash}"


def filter_new_items(
    items: list[NormalizedLineItem],
    existing: ExistingLedgerKeys,
) -> DedupeResult:
    seen_invoice_item_keys: set[str] = set()
    seen_fingerprints = set(existing.fingerprints)
    seen_message_item_keys: set[str] = set()
    unique: list[NormalizedLineItem] = []
    dropped = 0

    for item in items:
        fp = fingerprint(item)
        msg_item_key = f"{item.raw_message_id}|{fp}"
        invoice_item_key = f"{item.invoice_id}|{fp}" if item.invoice_id else ""

        # Existing invoice IDs are treated as strong hints, but final dedupe stays row-level.
        if item.invoice_id and item.invoice_id in existing.invoice_ids and fp in seen_fingerprints:
            dropped += 1
            continue
        if invoice_item_key and invoice_item_key in seen_invoice_item_keys:
            dropped += 1
            continue
        if fp in seen_fingerprints:
            dropped += 1
            continue
        if item.raw_message_id and msg_item_key in seen_message_item_keys:
            dropped += 1
            continue

        unique.append(item)
        seen_fingerprints.add(fp)
        if invoice_item_key:
            seen_invoice_item_keys.add(invoice_item_key)
        if item.raw_message_id:
            seen_message_item_keys.add(msg_item_key)

    return DedupeResult(unique_items=unique, dropped_count=dropped)
