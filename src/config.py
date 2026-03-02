from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os

from dotenv import load_dotenv


@dataclass(slots=True)
class AppConfig:
    gmail_mode: str
    timezone: str
    friend_name: str

    imap_host: str
    imap_user: str
    imap_app_password: str

    spreadsheet_id: str
    sheets_range: str

    oauth_client_secret_json: str
    gmail_oauth_token_json: str
    sheets_oauth_token_json: str

    merchants: dict[str, Any]
    sheet_schema: dict[str, Any]

    email_fixtures_dir: str


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_config(base_dir: Path | None = None) -> AppConfig:
    if base_dir is None:
        base_dir = Path.cwd()

    load_dotenv(base_dir / ".env")

    merchants = _read_json(base_dir / "config" / "merchants.json")
    sheet_schema = _read_json(base_dir / "config" / "sheet_schema.json")

    return AppConfig(
        gmail_mode=os.getenv("GMAIL_MODE", "api").strip().lower(),
        timezone=os.getenv("TIMEZONE", "America/New_York").strip(),
        friend_name=os.getenv("FRIEND_NAME", "Matt").strip(),
        imap_host=os.getenv("IMAP_HOST", "imap.gmail.com").strip(),
        imap_user=os.getenv("IMAP_USER", "").strip(),
        imap_app_password=os.getenv("IMAP_APP_PASSWORD", "").strip(),
        spreadsheet_id=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip(),
        sheets_range=os.getenv("GOOGLE_SHEETS_RANGE", "Ledger!A1").strip(),
        oauth_client_secret_json=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_JSON", "").strip(),
        gmail_oauth_token_json=os.getenv(
            "GOOGLE_GMAIL_OAUTH_TOKEN_JSON",
            os.getenv("GOOGLE_OAUTH_TOKEN_JSON", "./credentials/gmail_token.json"),
        ).strip(),
        sheets_oauth_token_json=os.getenv(
            "GOOGLE_SHEETS_OAUTH_TOKEN_JSON",
            os.getenv("GOOGLE_OAUTH_TOKEN_JSON", "./credentials/sheets_token.json"),
        ).strip(),
        merchants=merchants,
        sheet_schema=sheet_schema,
        email_fixtures_dir=os.getenv("EMAIL_FIXTURES_DIR", "").strip(),
    )
