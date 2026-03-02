from __future__ import annotations

from pathlib import Path
from typing import Iterable

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .dedupe import fingerprint
from .models import ExistingLedgerKeys, NormalizedLineItem

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _load_credentials(client_secret: str, token_path: str) -> Credentials:
    token_file = Path(token_path)
    creds: Credentials | None = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
        creds = flow.run_local_server(port=0)

    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(creds.to_json(), encoding="utf-8")
    return creds


class GoogleSheetsClient:
    def __init__(self, spreadsheet_id: str, range_name: str, client_secret: str, token_path: str) -> None:
        self.spreadsheet_id = spreadsheet_id
        self.range_name = range_name
        creds = _load_credentials(client_secret, token_path)
        self.service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    def read_existing_keys(self) -> ExistingLedgerKeys:
        # `append` commonly uses `Ledger!A1` for table detection; for reads we need full rows.
        read_range = _to_full_read_range(self.range_name)
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range=read_range)
            .execute()
        )
        values = result.get("values", [])

        invoice_ids: set[str] = set()
        source_message_ids: set[str] = set()
        fingerprints: set[str] = set()

        if not values:
            return ExistingLedgerKeys(invoice_ids=invoice_ids, source_message_ids=source_message_ids, fingerprints=fingerprints)

        header = values[0]
        col_map = {name: idx for idx, name in enumerate(header)}

        for row in values[1:]:
            invoice_id = row[col_map.get("InvoiceId", -1)] if col_map.get("InvoiceId", -1) < len(row) and col_map.get("InvoiceId", -1) >= 0 else ""
            source_message_id = row[col_map.get("SourceMessageId", -1)] if col_map.get("SourceMessageId", -1) < len(row) and col_map.get("SourceMessageId", -1) >= 0 else ""
            date = row[col_map.get("Date", -1)] if col_map.get("Date", -1) < len(row) and col_map.get("Date", -1) >= 0 else ""
            amount = row[col_map.get("Amount", -1)] if col_map.get("Amount", -1) < len(row) and col_map.get("Amount", -1) >= 0 else ""
            description = row[col_map.get("Description", -1)] if col_map.get("Description", -1) < len(row) and col_map.get("Description", -1) >= 0 else ""

            if invoice_id:
                invoice_ids.add(invoice_id)
            if source_message_id:
                source_message_ids.add(source_message_id)
            if date and amount and description:
                pseudo_item = NormalizedLineItem(
                    purchase_date=_parse_sheet_date(date),
                    vendor="Apple",
                    description=description,
                    amount=_parse_decimal(amount),
                    currency="USD",
                    invoice_id=invoice_id,
                    raw_message_id=source_message_id,
                    source="sheets",
                )
                fingerprints.add(fingerprint(pseudo_item))

        return ExistingLedgerKeys(invoice_ids=invoice_ids, source_message_ids=source_message_ids, fingerprints=fingerprints)

    def append_ledger_rows(self, rows: Iterable[list[str]]) -> int:
        rows_list = list(rows)
        if not rows_list:
            return 0

        response = (
            self.service.spreadsheets()
            .values()
            .append(
                spreadsheetId=self.spreadsheet_id,
                range=self.range_name,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": rows_list},
            )
            .execute()
        )
        updates = response.get("updates", {})
        return int(updates.get("updatedRows", 0))


def _parse_decimal(raw: str):
    from decimal import Decimal

    cleaned = str(raw).replace(",", "").strip()
    return Decimal(cleaned)


def _parse_sheet_date(raw: str):
    from datetime import datetime
    from zoneinfo import ZoneInfo

    text = str(raw).strip()
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        dt = datetime.strptime(text, "%Y-%m-%d")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("America/New_York"))
    return dt


def _to_full_read_range(range_name: str) -> str:
    if "!" not in range_name:
        return range_name
    sheet, _ = range_name.split("!", 1)
    return f"{sheet}!A:J"
