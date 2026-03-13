import re


REQUIREMENT_PATTERNS = [
    re.compile(r"\bshall\b", re.IGNORECASE),
    re.compile(r"\bmust\b", re.IGNORECASE),
    re.compile(r"\bis required to\b", re.IGNORECASE),
    re.compile(r"\brequired to\b", re.IGNORECASE),
    re.compile(r"\bin order to be considered\b", re.IGNORECASE),
    re.compile(r"\bfailure to\b", re.IGNORECASE),
]

DATE_PATTERN = re.compile(
    r"\b("
    r"\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}/\d{1,2}/\d{2,4}"
    r"|(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
    r"sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2},\s+\d{4}"
    r")\b",
    re.IGNORECASE,
)
TIME_PATTERN = re.compile(
    r"\b\d{1,2}(?::\d{2})?\s*(?:a\.m\.|p\.m\.|am|pm)?(?:\s*(?:et|est|edt|ct|cst|cdt|mt|mst|mdt|pt|pst|pdt|local time))?\b",
    re.IGNORECASE,
)
SOLICITATION_NUMBER_PATTERN = re.compile(
    r"(?:rfp|rfq|ifb|itb|solicitation|bid)(?:\s+(?:number|no\.?))?[\s#:.-]*(?P<value>[A-Za-z0-9][A-Za-z0-9./-]{2,})",
    re.IGNORECASE,
)
PAGE_HEADER_PATTERN = re.compile(r"^page\s+\d+\s+of\s+\d+$", re.IGNORECASE)

ACTION_VERBS = (
    "submit",
    "provide",
    "complete",
    "include",
    "attach",
    "certify",
    "register",
    "perform",
    "bid",
    "comply",
    "receive",
    "received",
)

SHOULD_ACTION_VERBS = (
    "submit",
    "complete",
    "attach",
    "certify",
    "provide proof",
)

SUBJECT_TERMS = (
    "bidder",
    "bidders",
    "offeror",
    "contractor",
    "subcontractor",
    "quote",
    "quotes",
)

EXCLUDE_PATTERNS = [
    re.compile(r"\bare strongly encouraged\b", re.IGNORECASE),
    re.compile(r"\bfor example\b", re.IGNORECASE),
    re.compile(r"^note[:\s]", re.IGNORECASE),
    re.compile(r"\bshall mean\b", re.IGNORECASE),
    re.compile(r"\bmeans\b", re.IGNORECASE),
    re.compile(r"\bstate reserves the right\b", re.IGNORECASE),
    re.compile(r"\bwill be publicly\b", re.IGNORECASE),
    re.compile(r"\bthe state intends to award\b", re.IGNORECASE),
    re.compile(r"\bbidders should note\b", re.IGNORECASE),
    re.compile(r"\bthis list is not exhaustive\b", re.IGNORECASE),
    re.compile(r"\bstate may request a revision\b", re.IGNORECASE),
    re.compile(r"\bpublicly announced\b", re.IGNORECASE),
    re.compile(r"\bdefinitions?\b", re.IGNORECASE),
    re.compile(r"\bquick reference guides?\b", re.IGNORECASE),
]

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

CLIENT_PATTERNS = (
    re.compile(r"^issued by[:\s-]+(?P<value>.+)$", re.IGNORECASE),
    re.compile(r"^issued for[:\s-]+(?P<value>.+)$", re.IGNORECASE),
    re.compile(r"^agency[:\s-]+(?P<value>.+)$", re.IGNORECASE),
    re.compile(r"^client[:\s-]+(?P<value>.+)$", re.IGNORECASE),
)
CLIENT_KEYWORDS = ("city", "county", "state", "university", "authority", "district", "board", "office", "department")
CLIENT_BLOCKLIST = ("request", "proposal", "rfp", "due", "deadline", "evaluation", "submit", "shall", "must")
CLIENT_ENTITY_SUFFIXES = (" city", " county", " state", " university", " authority", " district", " board", " office", " department")

QUESTION_DUE_CUES = ("question due", "questions due", "written questions due", "questions deadline")
PROPOSAL_DUE_CUES = ("proposal due", "proposals due", "submission due", "submissions due", "bid due", "bids due")
ISSUE_DATE_CUES = ("issue date", "release date", "issued date", "rfp release date", "solicitation issued")
CONTRACT_TERM_CUES = ("contract term", "term of the contract", "base year", "option year", "renewal term", "contract period")
GEOGRAPHY_CUES = ("location", "locations", "site", "sites", "facility", "facilities", "county", "city", "region", "campus")
SCOPE_CUES = ("scope of work", "scope summary", "services include", "the work includes", "services to be provided")
SUBMISSION_CUES = ("submit", "submission", "portal", "upload", "electronic", "hard copy", "email")
BONDING_CUES = ("bond", "bonding", "performance bond", "payment bond", "bid bond")
INSURANCE_CUES = ("insurance", "certificate of insurance", "coverage", "general liability", "workers compensation")
FORM_CUES = ("form", "forms", "attachment", "attachments", "appendix", "exhibit", "affidavit", "certification", "resume")
MEETING_CUES = ("walkthrough", "walk-through", "pre-bid", "pre bid", "pre-proposal", "pre proposal", "site visit", "conference")
INCUMBENT_CUES = ("incumbent", "current provider", "current contractor")
OPERATIONAL_CUES = ("staffing", "janitorial", "cleaning", "transition", "supervision", "schedule", "mobilization", "site")

SIMILARITY_STOPWORDS = {
    "the",
    "a",
    "an",
    "of",
    "to",
    "for",
    "and",
    "or",
    "in",
    "on",
    "by",
    "with",
    "as",
    "at",
    "be",
    "is",
    "are",
    "that",
    "this",
    "these",
    "those",
    "it",
    "its",
    "their",
    "all",
    "any",
    "from",
    "within",
    "through",
}


def _deadline_priority(line: str) -> int:
    lowered = line.lower()
    if "proposal due" in lowered or "proposals due" in lowered:
        return 4
    if "submission due" in lowered or "submissions due" in lowered:
        return 3
    if "bid due" in lowered or "bids due" in lowered or "deadline" in lowered:
        return 2
    if "questions due" in lowered or "written questions due" in lowered:
        return 1
    return 0


def _classify_requirement(text: str) -> str:
    lowered = text.lower()
    if "past performance" in lowered:
        return "PAST_PERFORMANCE"
    if "price" in lowered or "pricing" in lowered or "cost" in lowered:
        return "PRICING"
    if "technical" in lowered or "approach" in lowered or "method" in lowered:
        return "TECHNICAL"
    if "management" in lowered or "staff" in lowered or "personnel" in lowered:
        return "MANAGEMENT"
    return "GENERAL"


def _classify_requirement_type(text: str) -> str:
    lowered = text.lower()
    compliance_markers = (
        "must",
        "shall",
        "required to",
        "in order to be considered",
        "non-responsive",
        "failure to",
        "must submit",
        "must be received",
        "must complete",
    )
    evaluation_markers = (
        "evaluation criteria",
        "used to evaluate",
        "will be used to evaluate",
        "demonstrate",
        "approach",
        "plans and approach",
        "ability to complete",
    )
    context_markers = (
        "state may",
        "state reserves",
        "definitions",
        "shall mean",
        "is defined as",
        "publicly announced",
    )

    if any(marker in lowered for marker in context_markers):
        return "CONTEXT_ONLY"
    if any(marker in lowered for marker in compliance_markers):
        return "COMPLIANCE_REQUIRED"
    if any(marker in lowered for marker in evaluation_markers):
        return "EVALUATION_SIGNAL"
    return "CONTEXT_ONLY"


def _suggest_proposal_section(category: str) -> str:
    mapping = {
        "PAST_PERFORMANCE": "Past Performance",
        "PRICING": "Pricing Narrative",
        "TECHNICAL": "Technical Approach",
        "MANAGEMENT": "Management Plan",
        "GENERAL": "Executive Summary",
    }
    return mapping.get(category, "Executive Summary")


def _normalize_text(value: str) -> str:
    lowered = value.strip().lower()
    lowered = re.sub(r"\s+", " ", lowered)
    lowered = re.sub(r"[^a-z0-9\s]", "", lowered)
    return lowered


def _similarity_tokens(value: str) -> set[str]:
    normalized = _normalize_text(value)
    tokens = []
    for token in normalized.split():
        if token.isdigit():
            continue
        if token in SIMILARITY_STOPWORDS:
            continue
        if len(token) > 4 and token.endswith("s"):
            token = token[:-1]
        tokens.append(token)
    return set(tokens)


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


def _split_compound_requirement(line: str) -> list[str]:
    text = line.strip()
    if not text:
        return []

    subject_break = re.compile(
        r"(?:(?:\s+and)?\s*;\s*|\s+and\s+)(?=(?:the\s+)?(?:bidder|bidders|offeror|contractor|subcontractor)\s+(?:shall|must|should)\b)",
        re.IGNORECASE,
    )
    parts = [p.strip(" ;") for p in subject_break.split(text) if p.strip(" ;")]

    expanded: list[str] = []
    repeated_modal = re.compile(r"\s+and\s+(?=(?:must|shall|should)\b)", re.IGNORECASE)
    for part in parts:
        modal_parts = [p.strip(" ;") for p in repeated_modal.split(part) if p.strip(" ;")]
        if len(modal_parts) > 1:
            subject_match = re.match(
                r"^\s*((?:the\s+)?(?:bidder|bidders|offeror|contractor|subcontractor))\s+",
                modal_parts[0],
                re.IGNORECASE,
            )
            subject = subject_match.group(1) if subject_match else None
            for idx, clause in enumerate(modal_parts):
                if idx == 0 or not subject:
                    expanded.append(clause)
                    continue
                if re.match(r"^(?:must|shall|should)\b", clause, re.IGNORECASE):
                    expanded.append(f"{subject} {clause}")
                else:
                    expanded.append(clause)
        else:
            expanded.extend(modal_parts)

    cleaned = [p for p in expanded if len(p) >= 25]
    if len(cleaned) < 2:
        return [text]
    return cleaned


def _is_actionable_requirement(line: str) -> bool:
    lowered = line.lower()

    if len(line.strip()) < 30:
        return False
    if line.strip().endswith(":"):
        return False

    if any(pattern.search(line) for pattern in EXCLUDE_PATTERNS):
        return False

    if re.match(r"^[A-Za-z0-9/\-\s\(\)]+[–-]\s", line) and " means " in f" {lowered} ":
        return False

    if lowered.startswith("the state ") and not any(term in lowered for term in ("bidder", "contractor", "offeror")):
        return False

    has_trigger = any(pattern.search(line) for pattern in REQUIREMENT_PATTERNS)
    has_subject = any(term in lowered for term in SUBJECT_TERMS)
    has_action = any(verb in lowered for verb in ACTION_VERBS)
    has_should = " should " in f" {lowered} "
    has_should_action = any(verb in lowered for verb in SHOULD_ACTION_VERBS)
    has_enforcement = any(
        marker in lowered
        for marker in (
            "non-responsive",
            "must comply",
            "failure to",
            "in order to be considered",
            "required",
        )
    )

    if not has_trigger:
        if not (has_should and has_subject and has_should_action and has_enforcement):
            return False

    if has_subject and has_action:
        return True

    if "contractor shall" in lowered:
        return True

    return False


def _dedupe_requirements(requirements: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen_exact = set()
    seen_semantic: list[tuple[set[str], str]] = []

    for req in requirements:
        text = req["requirement_text"]
        exact_key = _normalize_text(text)
        if exact_key in seen_exact:
            continue

        tokens = _similarity_tokens(text)
        is_duplicate = False
        for prior_tokens, prior_category in seen_semantic:
            similarity = _jaccard_similarity(tokens, prior_tokens)
            if similarity >= 0.85 and req["category"] == prior_category:
                is_duplicate = True
                break
        if is_duplicate:
            continue

        seen_exact.add(exact_key)
        seen_semantic.append((tokens, req["category"]))
        deduped.append(req)

    numbered: list[dict] = []
    for idx, req in enumerate(deduped, start=1):
        numbered.append(
            {
                "requirement_code": f"REQ-{idx:03d}",
                **req,
            }
        )
    return numbered


def _clean_line(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip(" -:;\t"))


def _content_lines(raw_text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in raw_text.splitlines():
        cleaned = raw_line.strip()
        if not cleaned or cleaned.lower().startswith("source file:") or PAGE_HEADER_PATTERN.match(cleaned):
            continue
        lines.append(cleaned)
    return lines


def _is_client_like(value: str) -> bool:
    lowered = value.lower()
    if any(marker in lowered for marker in CLIENT_BLOCKLIST):
        return False
    if any(pattern.search(value) for pattern in CLIENT_PATTERNS):
        return True
    if lowered.endswith(CLIENT_ENTITY_SUFFIXES):
        return True
    return "public schools" in lowered


def _looks_like_title(value: str) -> bool:
    if not value or len(value) > 140:
        return False
    lowered = value.lower()
    normalized = re.sub(r"\([^)]*\)", "", lowered)
    normalized = re.sub(r"[^a-z\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if normalized in GENERIC_TITLE_LINES:
        return False
    if any(marker in lowered for marker in TITLE_BLOCKLIST):
        return False
    if _is_client_like(value):
        return False
    if SOLICITATION_NUMBER_PATTERN.search(value):
        return False
    alpha_words = re.findall(r"[A-Za-z]{2,}", value)
    return len(alpha_words) >= 2


def _candidate_client_value(line: str) -> str | None:
    cleaned = _clean_line(line)
    if not cleaned:
        return None
    for pattern in CLIENT_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            return _clean_line(match.group("value"))
    lowered = cleaned.lower()
    if any(keyword in lowered for keyword in CLIENT_KEYWORDS) and not any(marker in lowered for marker in CLIENT_BLOCKLIST):
        return cleaned
    return None


def _first_date(line: str) -> str | None:
    match = DATE_PATTERN.search(line)
    return match.group(1) if match else None


def _first_time(line: str) -> str | None:
    match = TIME_PATTERN.search(line)
    if not match:
        return None
    value = _clean_line(match.group(0))
    return value if any(token in value.lower() for token in ("am", "pm", ":")) else None


def _record_provenance(field_provenance: dict[str, list[str]], field_name: str, line: str) -> None:
    snippet = _clean_line(line)
    if not snippet:
        return
    existing = field_provenance.setdefault(field_name, [])
    if snippet in existing:
        return
    if len(existing) >= 3:
        return
    existing.append(snippet)


def _set_scalar_field(
    structured_fields: dict[str, object],
    field_provenance: dict[str, list[str]],
    field_name: str,
    value: str | None,
    line: str,
) -> None:
    if not value:
        return
    if structured_fields.get(field_name):
        return
    structured_fields[field_name] = _clean_line(value)
    _record_provenance(field_provenance, field_name, line)


def _append_list_field(
    structured_fields: dict[str, object],
    field_provenance: dict[str, list[str]],
    field_name: str,
    value: str | None,
    line: str,
    *,
    limit: int = 8,
) -> None:
    if not value:
        return
    items = structured_fields.setdefault(field_name, [])
    assert isinstance(items, list)
    cleaned = _clean_line(value)
    normalized = _normalize_text(cleaned)
    if not cleaned or any(_normalize_text(existing) == normalized for existing in items):
        return
    if len(items) >= limit:
        return
    items.append(cleaned)
    _record_provenance(field_provenance, field_name, line)


def _extract_after_delimiter(line: str) -> str | None:
    for delimiter in (":", " - ", " -- "):
        if delimiter in line:
            value = line.split(delimiter, 1)[1].strip()
            return value or None
    return None


def _clip_sentence(value: str, *, max_length: int = 240) -> str:
    cleaned = _clean_line(value)
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 3].rstrip(" ,;:") + "..."


def _empty_structured_fields() -> dict[str, object]:
    return {
        "client_name": None,
        "opportunity_name": None,
        "solicitation_number": None,
        "issue_date": None,
        "questions_due_date": None,
        "proposal_due_date": None,
        "proposal_due_time": None,
        "contract_term": None,
        "geography": [],
        "scope_summary": None,
        "submission_method": None,
        "bonding_requirements": [],
        "insurance_requirements": [],
        "mandatory_forms": [],
        "evaluation_criteria": [],
        "mandatory_meetings": [],
        "incumbent_hints": [],
        "operational_requirements": [],
    }


def _extract_structured_fields(lines: list[str], requirements: list[dict]) -> tuple[dict[str, object], dict[str, list[str]]]:
    structured_fields = _empty_structured_fields()
    field_provenance: dict[str, list[str]] = {}

    for line in lines:
        cleaned = _clean_line(line)
        lowered = cleaned.lower()

        if not structured_fields["client_name"]:
            client_value = _candidate_client_value(cleaned)
            if client_value:
                _set_scalar_field(structured_fields, field_provenance, "client_name", client_value, cleaned)

        if not structured_fields["opportunity_name"] and _looks_like_title(cleaned):
            _set_scalar_field(structured_fields, field_provenance, "opportunity_name", cleaned, cleaned)

        if not structured_fields["solicitation_number"]:
            solicitation_match = SOLICITATION_NUMBER_PATTERN.search(cleaned)
            if solicitation_match:
                _set_scalar_field(
                    structured_fields,
                    field_provenance,
                    "solicitation_number",
                    solicitation_match.group("value"),
                    cleaned,
                )

        first_date = _first_date(cleaned)
        if first_date and any(cue in lowered for cue in ISSUE_DATE_CUES):
            _set_scalar_field(structured_fields, field_provenance, "issue_date", first_date, cleaned)
        if first_date and any(cue in lowered for cue in QUESTION_DUE_CUES):
            _set_scalar_field(structured_fields, field_provenance, "questions_due_date", first_date, cleaned)
        if first_date and any(cue in lowered for cue in PROPOSAL_DUE_CUES):
            _set_scalar_field(structured_fields, field_provenance, "proposal_due_date", first_date, cleaned)
            _set_scalar_field(structured_fields, field_provenance, "proposal_due_time", _first_time(cleaned), cleaned)

        if any(cue in lowered for cue in CONTRACT_TERM_CUES):
            _set_scalar_field(
                structured_fields,
                field_provenance,
                "contract_term",
                _extract_after_delimiter(cleaned) or cleaned,
                cleaned,
            )

        if any(cue in lowered for cue in GEOGRAPHY_CUES):
            _append_list_field(
                structured_fields,
                field_provenance,
                "geography",
                _extract_after_delimiter(cleaned) or cleaned,
                cleaned,
                limit=6,
            )

        if any(cue in lowered for cue in SCOPE_CUES):
            _set_scalar_field(
                structured_fields,
                field_provenance,
                "scope_summary",
                _clip_sentence(_extract_after_delimiter(cleaned) or cleaned),
                cleaned,
            )

        if any(cue in lowered for cue in SUBMISSION_CUES) and any(
            marker in lowered for marker in ("portal", "upload", "electronic", "email", "hard copy", "sealed", "submit")
        ):
            _set_scalar_field(
                structured_fields,
                field_provenance,
                "submission_method",
                _extract_after_delimiter(cleaned) or cleaned,
                cleaned,
            )

        if any(cue in lowered for cue in BONDING_CUES):
            _append_list_field(
                structured_fields,
                field_provenance,
                "bonding_requirements",
                cleaned,
                cleaned,
                limit=6,
            )

        if any(cue in lowered for cue in INSURANCE_CUES):
            _append_list_field(
                structured_fields,
                field_provenance,
                "insurance_requirements",
                cleaned,
                cleaned,
                limit=6,
            )

        if any(cue in lowered for cue in FORM_CUES) and any(marker in lowered for marker in ("must", "shall", "required", "include", "submit", "attach")):
            _append_list_field(
                structured_fields,
                field_provenance,
                "mandatory_forms",
                cleaned,
                cleaned,
                limit=10,
            )

        if "evaluation" in lowered or "criteria" in lowered or "factor" in lowered or "points" in lowered:
            _append_list_field(
                structured_fields,
                field_provenance,
                "evaluation_criteria",
                cleaned,
                cleaned,
                limit=10,
            )

        if any(cue in lowered for cue in MEETING_CUES):
            _append_list_field(
                structured_fields,
                field_provenance,
                "mandatory_meetings",
                cleaned,
                cleaned,
                limit=8,
            )

        if any(cue in lowered for cue in INCUMBENT_CUES):
            _append_list_field(
                structured_fields,
                field_provenance,
                "incumbent_hints",
                cleaned,
                cleaned,
                limit=6,
            )

    for req in requirements:
        requirement_text = req["requirement_text"]
        lowered = requirement_text.lower()
        if any(cue in lowered for cue in OPERATIONAL_CUES) or req["category"] in {"TECHNICAL", "MANAGEMENT"}:
            _append_list_field(
                structured_fields,
                field_provenance,
                "operational_requirements",
                requirement_text,
                requirement_text,
                limit=8,
            )

    if not structured_fields["scope_summary"] and structured_fields["operational_requirements"]:
        first_requirement = structured_fields["operational_requirements"][0]
        assert isinstance(first_requirement, str)
        structured_fields["scope_summary"] = _clip_sentence(first_requirement)
        _record_provenance(field_provenance, "scope_summary", first_requirement)

    return structured_fields, field_provenance


def parse_rfp_text(raw_text: str) -> dict:
    lines = _content_lines(raw_text)

    deadline = None
    deadline_priority = -1
    criteria_hits: list[str] = []
    instructions_hits: list[str] = []
    requirements: list[dict] = []

    for line in lines:
        deadline_match = DATE_PATTERN.search(line)
        if deadline_match and any(x in line.lower() for x in ["due", "deadline", "submit"]):
            line_priority = _deadline_priority(line)
            if line_priority > deadline_priority:
                deadline = deadline_match.group(1)
                deadline_priority = line_priority

        lowered = line.lower()
        if "evaluation" in lowered or "factor" in lowered or "criteria" in lowered:
            criteria_hits.append(_clean_line(line))
        if "submit" in lowered or "instruction" in lowered or "format" in lowered or "portal" in lowered:
            instructions_hits.append(_clean_line(line))

        for atomic in _split_compound_requirement(line):
            if _is_actionable_requirement(atomic):
                category = _classify_requirement(atomic)
                requirement_type = _classify_requirement_type(atomic)
                requirements.append(
                    {
                        "requirement_text": atomic,
                        "category": category,
                        "requirement_type": requirement_type,
                        "mandatory": True,
                        "proposal_section": _suggest_proposal_section(category),
                    }
                )

    deduped = _dedupe_requirements(requirements)
    structured_fields, field_provenance = _extract_structured_fields(lines, deduped)
    proposal_due_date = structured_fields.get("proposal_due_date")
    if isinstance(proposal_due_date, str) and proposal_due_date:
        deadline = proposal_due_date

    evaluation_lines = structured_fields["evaluation_criteria"] if structured_fields["evaluation_criteria"] else criteria_hits[:10]
    submission_lines: list[str] = []
    submission_method = structured_fields.get("submission_method")
    if isinstance(submission_method, str) and submission_method:
        submission_lines.append(submission_method)
    submission_lines.extend([line for line in instructions_hits[:10] if line not in submission_lines])

    return {
        "deadline": deadline,
        "evaluation_criteria": "\n".join(evaluation_lines[:10]) if evaluation_lines else None,
        "submission_instructions": "\n".join(submission_lines[:10]) if submission_lines else None,
        "structured_fields": structured_fields,
        "field_provenance": field_provenance,
        "requirements": deduped,
    }
