import re


REQUIREMENT_PATTERNS = [
    re.compile(r"\bshall\b", re.IGNORECASE),
    re.compile(r"\bmust\b", re.IGNORECASE),
    re.compile(r"\bis required to\b", re.IGNORECASE),
    re.compile(r"\brequired to\b", re.IGNORECASE),
    re.compile(r"\bin order to be considered\b", re.IGNORECASE),
    re.compile(r"\bfailure to\b", re.IGNORECASE),
]

DEADLINE_PATTERN = re.compile(
    r"\b("
    r"\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}/\d{1,2}/\d{2,4}"
    r"|(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
    r"sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2},\s+\d{4}"
    r")\b",
    re.IGNORECASE,
)

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
    re.compile(r"\bstate reserves the right\b", re.IGNORECASE),
    re.compile(r"\bstate may request a revision\b", re.IGNORECASE),
    re.compile(r"\bpublicly announced\b", re.IGNORECASE),
    re.compile(r"\bdefinitions?\b", re.IGNORECASE),
    re.compile(r"\bshall mean\b", re.IGNORECASE),
    re.compile(r"\bfor example\b", re.IGNORECASE),
    re.compile(r"\bquick reference guides?\b", re.IGNORECASE),
]

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
        # Tiny singularization step helps collapse "line/lines", "bidder/bidders".
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

    # Split subject-repeated clauses:
    # "... and the Bidder shall ...", "...; The Contractor shall ...".
    subject_break = re.compile(
        r"(?:(?:\s+and)?\s*;\s*|\s+and\s+)(?=(?:the\s+)?(?:bidder|bidders|offeror|contractor|subcontractor)\s+(?:shall|must|should)\b)",
        re.IGNORECASE,
    )
    parts = [p.strip(" ;") for p in subject_break.split(text) if p.strip(" ;")]

    # Split simple "must/shall ... and must/shall ..." constructions.
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

    # Avoid over-splitting very short fragments; keep original when split is noisy.
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

    # Drop obvious term-definition headings ("Dealer/Distributor – ...")
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

    # Keep "should" lines only when tied to compliance-enforcement language.
    if not has_trigger:
        if not (has_should and has_subject and has_should_action and has_enforcement):
            return False

    # Keep lines that define direct bidder/contractor obligations or scope execution tasks.
    if has_subject and has_action:
        return True

    # Some scope lines use "Contractor shall ..." without explicit action keyword from ACTION_VERBS list.
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
            # Keep similarity strict to avoid dropping legitimately distinct obligations.
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


def parse_rfp_text(raw_text: str) -> dict:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    deadline = None
    deadline_priority = -1
    criteria_hits: list[str] = []
    instructions_hits: list[str] = []
    requirements: list[dict] = []

    for line in lines:
        deadline_match = DEADLINE_PATTERN.search(line)
        if deadline_match and any(x in line.lower() for x in ["due", "deadline", "submit"]):
            line_priority = _deadline_priority(line)
            if line_priority > deadline_priority:
                deadline = deadline_match.group(1)
                deadline_priority = line_priority

        lowered = line.lower()
        if "evaluation" in lowered or "factor" in lowered or "criteria" in lowered:
            criteria_hits.append(line)
        if "submit" in lowered or "instruction" in lowered or "format" in lowered:
            instructions_hits.append(line)

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

    return {
        "deadline": deadline,
        "evaluation_criteria": "\n".join(criteria_hits[:10]) if criteria_hits else None,
        "submission_instructions": "\n".join(instructions_hits[:10]) if instructions_hits else None,
        "requirements": deduped,
    }
