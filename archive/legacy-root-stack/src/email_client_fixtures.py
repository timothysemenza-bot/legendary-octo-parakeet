from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
from zoneinfo import ZoneInfo

from .models import EmailMessage


class FixturesEmailClient:
    def __init__(self, fixtures_dir: str) -> None:
        self.fixtures_dir = Path(fixtures_dir)

    def fetch_messages(self, start: datetime, end_exclusive: datetime, merchants: dict) -> list[EmailMessage]:
        tz = start.tzinfo or ZoneInfo("UTC")
        out: list[EmailMessage] = []
        for path in sorted(self.fixtures_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            date = datetime.fromisoformat(data["date"])
            if date.tzinfo is None:
                date = date.replace(tzinfo=tz)

            if not (start <= date < end_exclusive):
                continue

            out.append(
                EmailMessage(
                    message_id=data["message_id"],
                    subject=data.get("subject", ""),
                    sender=data.get("sender", ""),
                    date=date,
                    text_body=data.get("text_body", ""),
                    html_body=data.get("html_body", ""),
                    raw_content=data.get("raw_content", data.get("text_body", "") or data.get("html_body", "")),
                )
            )

        return out
