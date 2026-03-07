from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import re

from app.modules.rfp_parser.parser import parse_rfp_text


GENERIC_TITLE_LINES = {
    "request for proposal",
    "request for proposals",
    "request for quotation",
    "request for quotations",
    "request for bid",
    "request for bids",
    "solicitation",
    "solicitation document",
}

TITLE_BLOCKLIST = (
    "issued by",
    "issued for",
    "due date",
    "deadline",
    "evaluation",
    "criteria",
    "submit",
    "submission",
    "instruction",
    "shall",
    "must",
    "contract value",
    "budget",
    "not to exceed",
)

TITLE_STOP_MARKERS = (
    "rfp release date",
    "pre-proposal",
    "walk-through",
    "written questions due",
    "proposals due",
    "electronic submissions only",
    "see section",
)

CLIENT_PATTERNS = (
    re.compile(r"^issued by[:\s-]+(?P<value>.+)$", re.IGNORECASE),
    re.compile(r"^issued for[:\s-]+(?P<value>.+)$", re.IGNORECASE),
    re.compile(r"^(?P<value>(?:city|county|state|university|authority|district|board|office|department)\b.+)$", re.IGNORECASE),
)

CLIENT_KEYWORDS = ("city", "county", "state", "university", "authority", "district", "board", "office", "department")
CLIENT_BLOCKLIST = ("request", "proposal", "rfp", "due", "deadline", "evaluation", "submit", "shall", "must")
CLIENT_ENTITY_SUFFIXES = (" city", " county", " state", " university", " authority", " district", " board", " office", " department")
PAGE_HEADER_PATTERN = re.compile(r"^page\s+\d+\s+of\s+\d+$", re.IGNORECASE)
SOLICITATION_CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{1,8}(?:[-/][A-Za-z0-9]{1,8})+$")

VALUE_CUES = (
    "budget",
    "estimated value",
    "estimated contract value",
    "not to exceed",
    "ceiling",
    "maximum amount",
    "total contract value",
    "contract value",
)

CURRENCY_PATTERN = re.compile(r"(?P<prefix>\$)?\s*(?P<number>\d[\d,]*(?:\.\d+)?)\s*(?P<scale>million|billion|thousand|m|k)?", re.IGNORECASE)

DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y")


@dataclass(frozen=True)
class DraftInferenceResult:
    suggested_fields: dict[str, str | float | int | bool | None]
    field_statuses: dict[str, str]
    extracted_deadline: str | None


@dataclass(frozen=True)
class FieldInference:
    value: str | float | int | bool | None
    status: str
    source: str


def infer_intake_draft_fields(
    combined_text: str,
    parsed_files: list[str],
    *,
    today: date | None = None,
) -> DraftInferenceResult:
    content_lines = _content_lines(combined_text)
    parsed = parse_rfp_text(combined_text)
    extracted_deadline = parsed["deadline"]
    name = infer_name(content_lines, parsed_files)
    client = infer_client(content_lines)
    contract_value = infer_contract_value(content_lines)
    lead_time = infer_lead_time_days(extracted_deadline, today=today)

    suggested_fields = {
        "name": name.value,
        "client": client.value,
        "estimated_contract_value": contract_value.value,
        "lead_time_days": lead_time.value,
        "incumbent_status": False,
        "strategic_alignment": 3,
        "estimated_probability_win": 50,
    }
    field_statuses = {
        "name": name.status,
        "client": client.status,
        "estimated_contract_value": contract_value.status,
        "lead_time_days": lead_time.status,
        "incumbent_status": "DEFAULTED",
        "strategic_alignment": "DEFAULTED",
        "estimated_probability_win": "DEFAULTED",
    }
    return DraftInferenceResult(
        suggested_fields=suggested_fields,
        field_statuses=field_statuses,
        extracted_deadline=extracted_deadline,
    )


def infer_name(lines: list[str], parsed_files: list[str]) -> FieldInference:
    for index, line in enumerate(lines[:15]):
        cleaned = _clean_candidate(line)
        if not _is_title_candidate(cleaned):
            continue

        if _looks_like_solicitation_code(cleaned):
            title_suffix = _next_title_suffix(lines, start_index=index)
            if title_suffix:
                return FieldInference(value=f"{cleaned} {title_suffix}", status="INFERRED", source="SOLICITATION_CODE_TITLE")
            continue

        return FieldInference(value=cleaned, status="INFERRED", source="TITLE_LINE")

    if parsed_files:
        return FieldInference(value=_normalize_filename_stem(parsed_files[0]), status="INFERRED", source="FILENAME_FALLBACK")
    return FieldInference(value=None, status="MISSING", source="MISSING")


def infer_client(lines: list[str]) -> FieldInference:
    for line in lines[:25]:
        cleaned = _clean_candidate(line)
        if not cleaned:
            continue
        for pattern in CLIENT_PATTERNS:
            match = pattern.search(cleaned)
            if match:
                value = _clean_candidate(match.group("value"))
                if value:
                    return FieldInference(value=value, status="INFERRED", source="ISSUER_LINE")
        lowered = cleaned.lower()
        if any(keyword in lowered for keyword in CLIENT_KEYWORDS) and not any(
            marker in lowered for marker in CLIENT_BLOCKLIST
        ):
            return FieldInference(value=cleaned, status="INFERRED", source="ENTITY_KEYWORD_LINE")
    return FieldInference(value=None, status="MISSING", source="MISSING")


def infer_contract_value(lines: list[str]) -> FieldInference:
    for line in lines[:100]:
        lowered = line.lower()
        if not any(cue in lowered for cue in VALUE_CUES):
            continue
        amount = _largest_currency_amount(line)
        if amount is not None:
            return FieldInference(value=amount, status="INFERRED", source="CUED_CURRENCY_LINE")
    return FieldInference(value=None, status="MISSING", source="MISSING")


def infer_lead_time_days(deadline: str | None, *, today: date | None = None) -> FieldInference:
    if not deadline:
        return FieldInference(value=None, status="MISSING", source="NO_DEADLINE")
    parsed_date = _parse_deadline(deadline)
    if not parsed_date:
        return FieldInference(value=None, status="MISSING", source="UNPARSEABLE_DEADLINE")
    reference_date = today or date.today()
    delta_days = (parsed_date - reference_date).days
    if delta_days < 1:
        return FieldInference(value=None, status="MISSING", source="PAST_DEADLINE")
    return FieldInference(value=delta_days, status="INFERRED", source="PARSED_DEADLINE")


def _content_lines(raw_text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in raw_text.splitlines():
        cleaned = raw_line.strip()
        if not cleaned or cleaned.lower().startswith("source file:") or PAGE_HEADER_PATTERN.match(cleaned):
            continue
        lines.append(cleaned)
    return lines


def _clean_candidate(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip(" -:;\t"))


def _normalized_generic_heading(value: str) -> str:
    cleaned = re.sub(r"\([^)]*\)", "", value.lower())
    cleaned = re.sub(r"[^a-z\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _is_client_like(value: str) -> bool:
    lowered = value.lower()
    if any(marker in lowered for marker in CLIENT_BLOCKLIST):
        return False
    if any(pattern.search(value) for pattern in CLIENT_PATTERNS):
        return True
    if lowered.endswith(CLIENT_ENTITY_SUFFIXES):
        return True
    return "public schools" in lowered


def _looks_like_solicitation_code(value: str) -> bool:
    return SOLICITATION_CODE_PATTERN.match(value) is not None


def _is_title_candidate(value: str) -> bool:
    if not value or len(value) > 120:
        return False
    lowered = value.lower()
    if _normalized_generic_heading(value) in GENERIC_TITLE_LINES:
        return False
    if any(marker in lowered for marker in TITLE_BLOCKLIST):
        return False
    if any(marker in lowered for marker in TITLE_STOP_MARKERS):
        return False
    if _is_client_like(value):
        return False
    if _looks_like_solicitation_code(value):
        return True
    alpha_words = re.findall(r"[A-Za-z]{2,}", value)
    return len(alpha_words) >= 2


def _next_title_suffix(lines: list[str], start_index: int) -> str | None:
    for line in lines[start_index + 1 : start_index + 4]:
        cleaned = _clean_candidate(line)
        if not _is_title_candidate(cleaned):
            continue
        if _looks_like_solicitation_code(cleaned):
            continue
        return cleaned
    return None


def _normalize_filename_stem(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"[_\-]+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem.title()


def _largest_currency_amount(line: str) -> float | None:
    matches = list(CURRENCY_PATTERN.finditer(line))
    if not matches:
        return None

    amounts: list[float] = []
    for match in matches:
        raw_number = match.group("number")
        prefix = match.group("prefix")
        scale = (match.group("scale") or "").lower()
        value = float(raw_number.replace(",", ""))
        if scale in {"million", "m"}:
            value *= 1_000_000
        elif scale in {"billion"}:
            value *= 1_000_000_000
        elif scale in {"thousand", "k"}:
            value *= 1_000
        elif not prefix and value < 10_000:
            continue
        amounts.append(value)

    if not amounts:
        return None
    return max(amounts)


def _parse_deadline(raw_value: str) -> date | None:
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(raw_value, date_format).date()
        except ValueError:
            continue
    return None
