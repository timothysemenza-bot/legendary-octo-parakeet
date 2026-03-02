from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from .models import NormalizedLineItem


def build_report_text(month_key: str, friend_name: str, items: list[NormalizedLineItem]) -> str:
    total = sum((item.amount for item in items), Decimal("0.00"))
    lines: list[str] = []
    lines.append(f"MonthKey: {month_key}")
    lines.append(f"Total: ${total:.2f}")
    lines.append("")
    lines.append("Itemized list:")
    if not items:
        lines.append("- (no items)")
    else:
        for item in sorted(items, key=lambda x: (x.purchase_date, x.description.lower())):
            lines.append(
                f"- {item.purchase_date.date().isoformat()} | {item.description} | {item.currency} {item.amount:.2f}"
            )

    lines.append("")
    lines.append(f"Venmo memo: Apple expenses {month_key}")
    lines.append(f"Amount to pay {friend_name}: ${total:.2f}")
    return "\n".join(lines) + "\n"


def write_report(output_dir: Path, month_key: str, friend_name: str, items: list[NormalizedLineItem]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{month_key}.txt"
    path.write_text(build_report_text(month_key, friend_name, items), encoding="utf-8")
    return path


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
