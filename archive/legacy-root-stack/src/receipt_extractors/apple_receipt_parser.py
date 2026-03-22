from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import re
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from ..models import EmailMessage, NormalizedLineItem

CURRENCY_MAP = {
    "$": "USD",
    "USD": "USD",
    "EUR": "EUR",
    "GBP": "GBP",
    "€": "EUR",
    "£": "GBP",
}

MONEY_RE = re.compile(r"(?P<cur>USD|EUR|GBP|[$€£])\s*(?P<amt>\(?-?\d[\d,]*\.\d{2}\)?)", re.IGNORECASE)
TOTAL_RE = re.compile(
    r"(?im)^.*\b(total|amount due|charged|refund total|order total)\b.*?(USD|EUR|GBP|[$€£])?\s*(\(?-?\d[\d,]*\.\d{2}\)?)"
)
LINE_ITEM_RE = re.compile(
    r"(?im)^(?P<desc>[A-Za-z0-9][^\n]{2,120}?)\s+(?P<cur>USD|EUR|GBP|[$€£])\s*(?P<amt>\(?-?\d[\d,]*\.\d{2}\)?)\s*$"
)
INVOICE_RE = re.compile(
    r"(?im)\b(?:order\s*id|invoice|document\s*no\.?|receipt\s*number)\s*[:#-]?\s*([A-Z0-9\-]{5,})"
)
REFUND_RE = re.compile(r"(?i)\b(refund|credited|credit)\b")
APPLE_RECEIPT_CONTEXT_RE = re.compile(
    r"(?i)\b(apple\.com/bill|app\s*store|itunes|apple\s*store|apple\s*services|order\s*id|invoice|document\s*no\.?|refund|purchase|subscription\s+is\s+confirmed)\b"
)
APPLE_PAY_CONTEXT_RE = re.compile(
    r"(?i)\b(apple\s*pay|tip|surcharge|loyalty earned|on account|to pay)\b"
)
SUBSCRIPTION_CONFIRMED_SUBJECT_RE = re.compile(r"(?i)\byour\s+subscription\s+is\s+confirmed\b")
CHARGE_SIGNAL_RE = re.compile(
    r"(?i)\b(total|charged|billed|amount due|price|payment|you were billed|you have been billed)\b"
)
NON_BILLABLE_DESC_RE = re.compile(
    r"(?i)^(?:1\s*item|to\s*pay|on\s*account|loyalty\s*earned|tax|subtotal|total)$"
)
DEVICE_ONLY_DESC_RE = re.compile(
    r"(?i)^(?:[a-z][a-z .-]*[’']s\s+)?(?:iphone|ipad|ipod|mac|macbook|apple\s*watch|airpods)(?:\s+[a-z0-9.-]+){0,3}$"
)
GENERIC_SUBJECT_RE = re.compile(r"(?i)^your\s+receipt\s+from\s+apple\.?$")
SERVICE_HINT_RE = re.compile(
    r"(?i)\b(subscription|premium|plus|\bmax\b|icloud|tv\+|music|arcade|storage|plan|youtube|hbo|disney|netflix|app)\b"
)
NOISE_LINE_RE = re.compile(
    r"(?i)\b(apple support|privacy policy|all rights reserved|copyright|one apple park|account|help|terms|authorized)\b"
)


def _is_billable_description(desc: str) -> bool:
    normalized = " ".join(desc.split()).strip()
    if not normalized:
        return False
    if NON_BILLABLE_DESC_RE.fullmatch(normalized):
        return False
    if DEVICE_ONLY_DESC_RE.fullmatch(normalized):
        return False
    return True


def _to_text(message: EmailMessage) -> str:
    if message.text_body.strip():
        return message.text_body
    if message.html_body.strip():
        soup = BeautifulSoup(message.html_body, "html.parser")
        return soup.get_text("\n", strip=True)
    return ""


def _extract_invoice_id(text: str) -> str:
    match = INVOICE_RE.search(text)
    return (match.group(1).strip() if match else "")


def _extract_total(text: str) -> tuple[Decimal, str] | None:
    match = TOTAL_RE.search(text)
    if not match:
        return None

    currency = CURRENCY_MAP.get((match.group(2) or "$" ).upper(), "USD")
    amount_text = match.group(3).replace(",", "")
    neg = amount_text.startswith("(") and amount_text.endswith(")")
    amount_text = amount_text.strip("()")
    amount = Decimal(amount_text)
    if neg:
        amount = -amount
    return amount, currency


def _extract_line_items(text: str) -> list[tuple[str, Decimal, str]]:
    out: list[tuple[str, Decimal, str]] = []
    for match in LINE_ITEM_RE.finditer(text):
        desc = " ".join(match.group("desc").split())
        if re.search(r"(?i)\b(total|subtotal|tax)\b", desc):
            continue
        if re.fullmatch(r"\d+\s*[x×]", desc, flags=re.IGNORECASE):
            continue
        if re.fullmatch(r"[A-Z0-9]{8,}", desc):
            continue
        if not _is_billable_description(desc):
            continue
        amt_text = match.group("amt").replace(",", "")
        neg = amt_text.startswith("(") and amt_text.endswith(")")
        amt_text = amt_text.strip("()")
        amount = Decimal(amt_text)
        if neg:
            amount = -amount
        cur = CURRENCY_MAP.get(match.group("cur").upper(), "USD")
        out.append((desc, amount, cur))
    return out


def _extract_service_name_fallback(text: str) -> str:
    best_line = ""
    best_score = 0
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split()).strip(" -:\t")
        if len(line) < 3:
            continue
        if NOISE_LINE_RE.search(line):
            continue
        if NON_BILLABLE_DESC_RE.fullmatch(line):
            continue
        if DEVICE_ONLY_DESC_RE.fullmatch(line):
            continue
        if re.search(r"(?i)\b(total|subtotal|tax|amount due|order total|invoice|order id)\b", line):
            continue
        if re.fullmatch(r"[A-Z0-9]{8,}", line):
            continue
        if re.fullmatch(r"\d+\s*[x×]", line, flags=re.IGNORECASE):
            continue

        score = 0
        if SERVICE_HINT_RE.search(line):
            score += 5
        if re.search(r"[A-Za-z].*[A-Za-z]", line):
            score += 2
        if 4 <= len(line) <= 80:
            score += 1
        if re.match(r"(?i)^(dear|from|date|subject)\b", line):
            score -= 3

        if score > best_score:
            best_score = score
            best_line = line

    return best_line if best_score >= 5 else ""


def parse_apple_receipt(
    message: EmailMessage,
    timezone: str = "America/New_York",
) -> list[NormalizedLineItem]:
    text = _to_text(message)
    if not text.strip():
        raise ValueError("No receipt body found")

    combined_context = f"{message.subject}\n{text}"
    if not APPLE_RECEIPT_CONTEXT_RE.search(combined_context):
        raise ValueError("Message does not look like an Apple billing receipt")
    if APPLE_PAY_CONTEXT_RE.search(combined_context) and not re.search(
        r"(?i)\b(app\s*store|itunes|apple\.com/bill)\b", combined_context
    ):
        raise ValueError("Likely Apple Pay merchant receipt; skipping")

    invoice_id = _extract_invoice_id(text)
    line_items = _extract_line_items(text)
    total_tuple = _extract_total(text)
    money_match = MONEY_RE.search(text)

    if SUBSCRIPTION_CONFIRMED_SUBJECT_RE.search(message.subject):
        has_charge_signal = bool(CHARGE_SIGNAL_RE.search(combined_context))
        if not (has_charge_signal and (total_tuple is not None or money_match is not None)):
            raise ValueError("Subscription confirmation without charge evidence")

    is_refund = bool(REFUND_RE.search(message.subject) or REFUND_RE.search(text))

    purchase_date = message.date.astimezone(ZoneInfo(timezone)) if message.date.tzinfo else message.date.replace(tzinfo=ZoneInfo(timezone))

    results: list[NormalizedLineItem] = []
    if line_items:
        for desc, amount, currency in line_items:
            if is_refund and amount > 0:
                amount = -amount
            results.append(
                NormalizedLineItem(
                    purchase_date=purchase_date,
                    vendor="Apple",
                    description=desc,
                    amount=amount,
                    currency=currency,
                    invoice_id=invoice_id,
                    raw_message_id=message.message_id,
                    source="gmail",
                )
            )
        return results

    if not total_tuple:
        # Final fallback: use first recognized money token from body.
        if not money_match:
            raise ValueError("Could not parse receipt total")
        currency = CURRENCY_MAP.get(money_match.group("cur").upper(), "USD")
        amount = Decimal(money_match.group("amt").replace(",", "").strip("()"))
    else:
        amount, currency = total_tuple

    if is_refund and amount > 0:
        amount = -amount

    description = _extract_service_name_fallback(text) or message.subject.strip()
    if GENERIC_SUBJECT_RE.fullmatch(description):
        raise ValueError("Receipt total found but app/subscription description was not identifiable")
    if not _is_billable_description(description):
        raise ValueError("Receipt description is not billable")
    results.append(
        NormalizedLineItem(
            purchase_date=purchase_date,
            vendor="Apple",
            description=description,
            amount=amount,
            currency=currency,
            invoice_id=invoice_id,
            raw_message_id=message.message_id,
            source="gmail",
        )
    )
    return results
