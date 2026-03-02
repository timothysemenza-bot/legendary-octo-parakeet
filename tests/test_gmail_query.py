from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.email_client_gmail_api import build_gmail_query


def test_build_gmail_query_quotes_subject_terms_with_spaces() -> None:
    merchants = {
        "vendors": [
            {
                "sender_contains": ["apple.com", "no_reply@email.apple.com"],
                "subject_contains": ["receipt", "app store", "apple.com/bill"],
            }
        ]
    }
    start = datetime(2026, 2, 1, tzinfo=ZoneInfo("America/New_York"))
    end_exclusive = datetime(2026, 3, 1, tzinfo=ZoneInfo("America/New_York"))
    q = build_gmail_query(start, end_exclusive, merchants)

    assert "from:(apple.com OR no_reply@email.apple.com)" in q
    assert 'subject:(receipt OR "app store" OR "apple.com/bill")' in q
