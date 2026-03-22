from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(slots=True)
class EmailMessage:
    message_id: str
    subject: str
    sender: str
    date: datetime
    text_body: str
    html_body: str
    raw_content: str


@dataclass(slots=True)
class NormalizedLineItem:
    purchase_date: datetime
    vendor: str
    description: str
    amount: Decimal
    currency: str
    invoice_id: str
    raw_message_id: str
    source: str

    @property
    def month_key(self) -> str:
        return self.purchase_date.strftime("%Y-%m")


@dataclass(slots=True)
class ExistingLedgerKeys:
    invoice_ids: set[str]
    source_message_ids: set[str]
    fingerprints: set[str]


@dataclass(slots=True)
class MonthWindow:
    month_key: str
    start: datetime
    end_exclusive: datetime


@dataclass(slots=True)
class ProcessResult:
    month_key: str
    fetched_messages: int
    parsed_items: int
    new_items: int
    appended_rows: int
    report_path: str
