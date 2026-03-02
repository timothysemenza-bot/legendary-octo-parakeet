from __future__ import annotations

import hashlib
from datetime import datetime
from decimal import Decimal


def normalize_amount_text(raw: str) -> Decimal:
    text = raw.strip().replace(",", "")
    neg = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    value = Decimal(text)
    return -value if neg else value


def stable_description_hash(description: str) -> str:
    normalized = " ".join(description.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def month_key_from_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m")
