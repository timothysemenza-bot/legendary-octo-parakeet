from __future__ import annotations

import imaplib
from datetime import datetime
from email import message_from_bytes
from email.message import Message
from email.utils import parsedate_to_datetime
from typing import Any

from .models import EmailMessage


def _extract_text_parts(msg: Message) -> tuple[str, str]:
    text_body = ""
    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type not in {"text/plain", "text/html"}:
                continue
            payload = part.get_payload(decode=True) or b""
            decoded = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
            if content_type == "text/plain" and not text_body:
                text_body = decoded
            elif content_type == "text/html" and not html_body:
                html_body = decoded
    else:
        payload = msg.get_payload(decode=True) or b""
        decoded = payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")
        if msg.get_content_type() == "text/html":
            html_body = decoded
        else:
            text_body = decoded

    return text_body, html_body


class ImapEmailClient:
    def __init__(self, host: str, user: str, app_password: str) -> None:
        self.host = host
        self.user = user
        self.app_password = app_password

    def fetch_messages(
        self,
        start: datetime,
        end_exclusive: datetime,
        merchants: dict[str, Any],
    ) -> list[EmailMessage]:
        sender_terms: list[str] = []
        subject_terms: list[str] = []
        for vendor in merchants.get("vendors", []):
            sender_terms.extend(vendor.get("sender_contains", []))
            subject_terms.extend(vendor.get("subject_contains", []))

        criteria = [
            "SINCE",
            start.strftime("%d-%b-%Y"),
            "BEFORE",
            end_exclusive.strftime("%d-%b-%Y"),
        ]

        out: list[EmailMessage] = []
        with imaplib.IMAP4_SSL(self.host) as imap:
            imap.login(self.user, self.app_password)
            imap.select("INBOX")
            status, data = imap.search(None, *criteria)
            if status != "OK":
                return out

            for num in (data[0] or b"").split():
                status, msg_data = imap.fetch(num, "(RFC822)")
                if status != "OK" or not msg_data:
                    continue

                raw_bytes = msg_data[0][1]
                msg = message_from_bytes(raw_bytes)
                subject = msg.get("Subject", "")
                sender = msg.get("From", "")

                sender_ok = any(s.lower() in sender.lower() for s in sender_terms) if sender_terms else True
                subject_ok = any(s.lower() in subject.lower() for s in subject_terms) if subject_terms else True
                if not (sender_ok and subject_ok):
                    continue

                date_hdr = msg.get("Date", "")
                parsed_date = parsedate_to_datetime(date_hdr) if date_hdr else start
                text_body, html_body = _extract_text_parts(msg)

                out.append(
                    EmailMessage(
                        message_id=msg.get("Message-ID", str(num.decode("utf-8", errors="ignore"))),
                        subject=subject,
                        sender=sender,
                        date=parsed_date,
                        text_body=text_body,
                        html_body=html_body,
                        raw_content=raw_bytes.decode("utf-8", errors="ignore"),
                    )
                )

        return out
