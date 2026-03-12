from __future__ import annotations

from decimal import Decimal, InvalidOperation

from fastapi.templating import Jinja2Templates


def format_currency(value: object) -> str:
    if value in (None, ""):
        return "-"
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return str(value)
    normalized = amount.quantize(Decimal("0.01"))
    if normalized == normalized.to_integral():
        return f"${normalized:,.0f}"
    return f"${normalized:,.2f}"


def build_templates(directory: str = "app/web/templates") -> Jinja2Templates:
    templates = Jinja2Templates(directory=directory)
    templates.env.filters["currency"] = format_currency
    return templates
