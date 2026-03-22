from __future__ import annotations

import base64
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .models import EmailMessage

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


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


def _decode_b64url(value: str) -> str:
    if not value:
        return ""
    return base64.urlsafe_b64decode(value.encode("utf-8")).decode("utf-8", errors="ignore")


def _extract_part(payload: dict[str, Any], mime_type: str) -> str:
    if payload.get("mimeType") == mime_type:
        body = payload.get("body", {}).get("data", "")
        return _decode_b64url(body)

    for part in payload.get("parts", []) or []:
        nested = _extract_part(part, mime_type)
        if nested:
            return nested
    return ""


def _header_value(headers: list[dict[str, str]], name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _quote_if_needed(term: str) -> str:
    escaped = term.replace('"', '\\"')
    if any(ch.isspace() for ch in escaped) or "/" in escaped:
        return f'"{escaped}"'
    return escaped


def build_gmail_query(start: datetime, end_exclusive: datetime, merchants: dict[str, Any]) -> str:
    query = f"after:{int(start.timestamp())} before:{int(end_exclusive.timestamp())}"

    sender_terms: list[str] = []
    subject_terms: list[str] = []
    for vendor in merchants.get("vendors", []):
        sender_terms.extend(vendor.get("sender_contains", []))
        subject_terms.extend(vendor.get("subject_contains", []))

    sender_clause = " OR ".join(_quote_if_needed(s) for s in sender_terms)
    subject_clause = " OR ".join(_quote_if_needed(s) for s in subject_terms)

    if sender_clause and subject_clause:
        query = f'{query} from:({sender_clause}) subject:({subject_clause})'
    elif sender_clause:
        query = f"{query} from:({sender_clause})"
    elif subject_clause:
        query = f"{query} subject:({subject_clause})"

    return query


class GmailApiEmailClient:
    def __init__(self, client_secret: str, token_path: str, allowed_account_email: str | None = None) -> None:
        creds = _load_credentials(client_secret, token_path)
        self.service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        self.account_email = self.get_authenticated_email()
        if allowed_account_email and self.account_email != allowed_account_email.strip().lower():
            raise ValueError(
                f"Authenticated Gmail account '{self.account_email}' does not match allowed account '{allowed_account_email}'."
            )

    def get_authenticated_email(self) -> str:
        profile = self.service.users().getProfile(userId="me").execute()
        return str(profile.get("emailAddress", "")).strip().lower()

    def fetch_messages(
        self,
        start: datetime,
        end_exclusive: datetime,
        merchants: dict[str, Any],
    ) -> list[EmailMessage]:
        users = self.service.users()
        query = build_gmail_query(start, end_exclusive, merchants)

        results = users.messages().list(userId="me", q=query, maxResults=500).execute()
        messages = results.get("messages", [])
        out: list[EmailMessage] = []

        for m in messages:
            detail = users.messages().get(userId="me", id=m["id"], format="full").execute()
            payload = detail.get("payload", {})
            headers = payload.get("headers", [])
            subject = _header_value(headers, "Subject")
            sender = _header_value(headers, "From")
            date_header = _header_value(headers, "Date")
            parsed_date = parsedate_to_datetime(date_header) if date_header else start

            text_body = _extract_part(payload, "text/plain")
            html_body = _extract_part(payload, "text/html")
            raw_content = f"Subject: {subject}\nFrom: {sender}\nDate: {date_header}\n\n{text_body or html_body}"

            out.append(
                EmailMessage(
                    message_id=detail.get("id", ""),
                    subject=subject,
                    sender=sender,
                    date=parsed_date,
                    text_body=text_body,
                    html_body=html_body,
                    raw_content=raw_content,
                )
            )
        return out
