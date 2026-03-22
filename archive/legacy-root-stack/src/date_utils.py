from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .models import MonthWindow


def get_prior_month_window(timezone_name: str, now: datetime | None = None) -> MonthWindow:
    tz = ZoneInfo(timezone_name)
    current = now.astimezone(tz) if now else datetime.now(tz)
    first_this_month = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    prev_month_last_day = first_this_month - timedelta(days=1)
    start_prev = prev_month_last_day.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end_prev_exclusive = first_this_month
    return MonthWindow(
        month_key=start_prev.strftime("%Y-%m"),
        start=start_prev,
        end_exclusive=end_prev_exclusive,
    )


def get_month_window(timezone_name: str, month_key: str) -> MonthWindow:
    tz = ZoneInfo(timezone_name)
    year_str, month_str = month_key.split("-", 1)
    year = int(year_str)
    month = int(month_str)

    start = datetime(year, month, 1, tzinfo=tz)
    if month == 12:
        end_exclusive = datetime(year + 1, 1, 1, tzinfo=tz)
    else:
        end_exclusive = datetime(year, month + 1, 1, tzinfo=tz)

    return MonthWindow(month_key=month_key, start=start, end_exclusive=end_exclusive)


def iter_month_keys(start_month: str, end_month: str) -> list[str]:
    start_year, start_mon = map(int, start_month.split("-", 1))
    end_year, end_mon = map(int, end_month.split("-", 1))
    keys: list[str] = []
    year, month = start_year, start_mon

    while (year, month) <= (end_year, end_mon):
        keys.append(f"{year:04d}-{month:02d}")
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1

    return keys
