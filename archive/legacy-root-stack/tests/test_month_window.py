from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from src.date_utils import get_prior_month_window


def test_prior_month_boundary_new_york_march_first() -> None:
    now = datetime(2026, 3, 1, 9, 0, 0, tzinfo=ZoneInfo("America/New_York"))
    window = get_prior_month_window("America/New_York", now=now)
    assert window.month_key == "2026-02"
    assert window.start.isoformat() == "2026-02-01T00:00:00-05:00"
    assert window.end_exclusive.isoformat() == "2026-03-01T00:00:00-05:00"
