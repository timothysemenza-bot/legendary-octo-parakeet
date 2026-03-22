from __future__ import annotations

import argparse
import base64
import os
import re
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _parse_csv_emails(value: str) -> list[str]:
    return [_normalize_email(item) for item in value.split(",") if item.strip()]


def _safe_email_for_filename(email: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", _normalize_email(email)).strip("_")


def _resolve_token_path(from_email: str) -> str:
    mapping_raw = os.getenv("GOOGLE_GMAIL_SEND_TOKEN_MAP", "").strip()
    if mapping_raw:
        for pair in mapping_raw.split(";"):
            if "=" not in pair:
                continue
            key, path_value = pair.split("=", 1)
            if _normalize_email(key) == from_email:
                return path_value.strip()

    template = os.getenv(
        "GOOGLE_GMAIL_SEND_TOKEN_TEMPLATE",
        "./credentials/gmail_send_{email_safe}.json",
    ).strip()
    return template.format(email=from_email, email_safe=_safe_email_for_filename(from_email))


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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send Gmail API message from an allowed sender")
    parser.add_argument("--from", dest="from_email", required=True, help="Sender email address")
    parser.add_argument("--to", required=True, help="Comma-separated recipient emails")
    parser.add_argument("--subject", required=True, help="Message subject")
    parser.add_argument("--body", help="Plain text body")
    parser.add_argument("--body-file", help="Path to UTF-8 text file for body")
    parser.add_argument("--reply-to", help="Optional Reply-To address")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    load_dotenv(Path.cwd() / ".env")

    from_email = _normalize_email(args.from_email)
    allowed = _parse_csv_emails(os.getenv("GOOGLE_ALLOWED_SEND_FROM", from_email))
    if from_email not in allowed:
        raise ValueError(
            f"Sender '{from_email}' is not in GOOGLE_ALLOWED_SEND_FROM. Allowed: {', '.join(allowed)}"
        )

    client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_JSON", "").strip()
    if not client_secret:
        raise ValueError("GOOGLE_OAUTH_CLIENT_SECRET_JSON is required")

    token_path = _resolve_token_path(from_email)
    creds = _load_credentials(client_secret, token_path)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    body_text = args.body
    if args.body_file:
        body_text = Path(args.body_file).read_text(encoding="utf-8")
    if not body_text:
        raise ValueError("Provide either --body or --body-file")

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = ", ".join(_parse_csv_emails(args.to))
    msg["Subject"] = args.subject
    if args.reply_to:
        msg["Reply-To"] = args.reply_to
    msg.set_content(body_text)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"SENT_MESSAGE_ID={result.get('id', '')}")
    print(f"SENDER={from_email}")
    print(f"TOKEN_PATH={token_path}")


if __name__ == "__main__":
    main()
