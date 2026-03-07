import json
import re
from collections import Counter
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import log_audit_event
from app.modules.capture_plan.schemas import (
    CapturePlanGenerateRequest,
    CapturePlanReadinessResponse,
    CapturePlanUpdateRequest,
)
from app.modules.compliance_matrix.service import ComplianceMatrixService
from app.modules.opportunity_intake.models import CapturePlan, Opportunity
from app.modules.rfp_parser.models import ComplianceMatrixRow, Requirement, Solicitation


DEFAULT_CAPTURE_TIMELINE = (
    "T-45 kickoff, T-30 content lock, T-14 red review, T-7 gold review, T-1 final packaging."
)
DEFAULT_CLIENT_PRIORITIES = "Identify buyer priorities, constraints, and decision criteria."
DEFAULT_COMPETITIVE_LANDSCAPE = "Map incumbent position, likely competitors, and differentiation gaps."
DEFAULT_WIN_THEMES = "Theme 1: reduced risk; Theme 2: proven performance; Theme 3: rapid mobilization."
DEFAULT_SOLUTION_POSITIONING = "Position solution benefits before features with evidence-backed claims."

_DEADLINE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y")
_CATEGORY_ORDER = ("TECHNICAL", "MANAGEMENT", "PAST_PERFORMANCE", "PRICING", "GENERAL")
_CATEGORY_THEME_MAP = {
    "TECHNICAL": "Win Theme: Prove a technical approach that reduces delivery risk and accelerates mobilization.",
    "MANAGEMENT": "Win Theme: Show disciplined staffing, governance, and accountability from day one.",
    "PAST_PERFORMANCE": "Win Theme: Back claims with relevant past performance and measurable outcomes.",
    "PRICING": "Win Theme: Present pricing as transparent, compliant, and easy for evaluators to score.",
    "GENERAL": "Win Theme: Lead with executive clarity on buyer priorities and mission impact.",
}
_CATEGORY_POSITIONING_MAP = {
    "TECHNICAL": "Lead the technical response with a clear method, transition control, and requirement traceability.",
    "MANAGEMENT": "Position management content around staffing continuity, governance rhythm, and escalation ownership.",
    "PAST_PERFORMANCE": "Use past performance proof to substantiate execution credibility and lower evaluator risk.",
    "PRICING": "Frame pricing as disciplined, easy to evaluate, and explicitly tied to required outcomes.",
    "GENERAL": "Open with executive framing that connects buyer priorities to measurable impact.",
}


class CapturePlanGenerationError(RuntimeError):
    pass


def build_bootstrap_capture_plan_content(opportunity: Opportunity) -> dict[str, str]:
    return {
        "summary": f"{opportunity.name} pursuit for {opportunity.client}.",
        "client_priorities": DEFAULT_CLIENT_PRIORITIES,
        "competitive_landscape": DEFAULT_COMPETITIVE_LANDSCAPE,
        "win_themes_draft": DEFAULT_WIN_THEMES,
        "solution_positioning": DEFAULT_SOLUTION_POSITIONING,
        "timeline": DEFAULT_CAPTURE_TIMELINE,
    }


def parse_capture_deadline(raw: str | None) -> date | None:
    if not raw:
        return None
    for fmt in _DEADLINE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _as_sentence(value: str | None, *, max_length: int = 180) -> str:
    normalized = _normalize_text(value)
    if not normalized:
        return ""
    clipped = normalized if len(normalized) <= max_length else normalized[: max_length - 3].rstrip(" ,;:") + "..."
    if clipped.endswith(("...", ".", "!", "?")):
        return clipped
    return clipped + "."


def _deadline_priority_note(deadline: date | None, *, today: date) -> str:
    if not deadline:
        return "No parsed submission deadline is available; confirm due date and packaging constraints before Gate B."

    days_to_deadline = (deadline - today).days
    if days_to_deadline < 0:
        return "The parsed submission deadline has already passed; validate amendment history and due-date changes immediately."
    if days_to_deadline <= 14:
        return (
            f"Submission is due in {days_to_deadline} days; prioritize compliance closure, final approvals, and packaging discipline."
        )
    if days_to_deadline <= 30:
        return f"Submission is due in {days_to_deadline} days; lock evaluator priorities, owners, and review dates early."
    return f"Submission is due in {days_to_deadline} days; use the runway to sharpen differentiation and proof."


def build_capture_timeline(deadline: date | None, *, today: date | None = None) -> str:
    _ = today
    if not deadline:
        return DEFAULT_CAPTURE_TIMELINE

    milestones = [
        ("Kickoff", deadline - timedelta(days=45)),
        ("Strategy lock", deadline - timedelta(days=30)),
        ("Content complete", deadline - timedelta(days=21)),
        ("Pink/Red review window", deadline - timedelta(days=14)),
        ("Final packaging", deadline - timedelta(days=7)),
        ("Executive authorization", deadline - timedelta(days=2)),
    ]
    parts = [f"{label} by {milestone.isoformat()}" for label, milestone in milestones]
    parts.append(f"Submission on {deadline.isoformat()}.")
    return "; ".join(parts)


def _ordered_categories(matrix_rows: list[dict[str, str]]) -> list[str]:
    counts = Counter(row["category"] for row in matrix_rows if row.get("category"))

    def _sort_key(category: str) -> tuple[int, int, str]:
        try:
            order_idx = _CATEGORY_ORDER.index(category)
        except ValueError:
            order_idx = len(_CATEGORY_ORDER)
        return (-counts[category], order_idx, category)

    return sorted(counts, key=_sort_key)


def _ordered_sections(matrix_rows: list[dict[str, str]]) -> list[str]:
    counts = Counter(row["proposal_section"] for row in matrix_rows if row.get("proposal_section"))
    return [section for section, _count in counts.most_common()]


def count_win_themes(raw: str) -> int:
    normalized = _normalize_text(raw)
    if not normalized:
        return 0
    marker_count = len(re.findall(r"(?:win theme:|theme\s+\d+\s*:)", raw, re.IGNORECASE))
    if marker_count:
        return marker_count

    newline_parts = [part.strip(" -;\t") for part in raw.splitlines() if part.strip(" -;\t")]
    if len(newline_parts) > 1:
        return len(newline_parts)

    semicolon_parts = [part.strip(" -;\t") for part in raw.split(";") if part.strip(" -;\t")]
    if len(semicolon_parts) > 1:
        return len(semicolon_parts)
    return 1


def evaluate_capture_plan_readiness(
    *,
    opportunity: Opportunity,
    capture_plan: CapturePlan | None,
    solicitation: Solicitation | None,
    matrix_rows: list[dict[str, str]],
) -> CapturePlanReadinessResponse:
    blockers: list[str] = []
    bootstrap_fields = {
        "summary": "Summary",
        "client_priorities": "Client priorities",
        "competitive_landscape": "Competitive landscape",
        "win_themes_draft": "Win themes",
        "solution_positioning": "Solution positioning",
        "timeline": "Timeline",
    }
    capture_plan_id = capture_plan.id if capture_plan else None
    capture_plan_version = capture_plan.version if capture_plan else None
    solicitation_id = solicitation.id if solicitation else None
    win_theme_count = count_win_themes(capture_plan.win_themes_draft) if capture_plan else 0
    uses_bootstrap_template = False

    if not capture_plan:
        blockers.append("No capture plan exists for this opportunity.")
    else:
        bootstrap_content = build_bootstrap_capture_plan_content(opportunity)
        matching_bootstrap_fields = [
            field_name
            for field_name in bootstrap_fields
            if _normalize_text(getattr(capture_plan, field_name, "")) == _normalize_text(bootstrap_content[field_name])
        ]
        uses_bootstrap_template = len(matching_bootstrap_fields) == len(bootstrap_fields)
        if uses_bootstrap_template:
            blockers.append("Capture plan is still the intake bootstrap template.")
        else:
            for field_name in matching_bootstrap_fields:
                blockers.append(f"{bootstrap_fields[field_name]} is still using the intake bootstrap template.")

        if win_theme_count < 2:
            blockers.append("Capture plan must define at least 2 win themes before Gate B approval.")

    if not solicitation:
        blockers.append("No solicitation has been parsed for this opportunity.")
    if not matrix_rows:
        blockers.append("No compliance matrix rows exist for the latest solicitation.")

    return CapturePlanReadinessResponse(
        opportunity_id=opportunity.id,
        capture_plan_id=capture_plan_id,
        capture_plan_version=capture_plan_version,
        solicitation_id=solicitation_id,
        matrix_row_count=len(matrix_rows),
        win_theme_count=win_theme_count,
        uses_bootstrap_template=uses_bootstrap_template,
        ready_for_gate_b=len(blockers) == 0,
        blockers=blockers,
    )


def build_enriched_capture_plan_content(
    opportunity: Opportunity,
    solicitation: Solicitation,
    matrix_rows: list[dict[str, str]],
    matrix_quality: dict,
    *,
    today: date | None = None,
) -> dict[str, str]:
    resolved_today = today or date.today()
    deadline = parse_capture_deadline(solicitation.extracted_deadline)
    recommendation = str(opportunity.pursuit_recommendation).replace("_", " ")
    tier = str(opportunity.tier).replace("_", " ")
    est_value = f"${opportunity.estimated_contract_value:,.0f}"
    summary = (
        f"{opportunity.name} for {opportunity.client}: {recommendation} recommendation, "
        f"{tier}, estimated value {est_value}"
    )
    summary = summary + (f", due {deadline.isoformat()}." if deadline else ".")

    criteria_sentence = _as_sentence(solicitation.extracted_evaluation_criteria)
    instructions_sentence = _as_sentence(solicitation.extracted_submission_instructions)
    client_priorities_parts: list[str] = []
    if criteria_sentence:
        client_priorities_parts.append(f"Evaluation focus: {criteria_sentence}")
    if instructions_sentence:
        client_priorities_parts.append(f"Submission discipline: {instructions_sentence}")
    client_priorities_parts.append(_deadline_priority_note(deadline, today=resolved_today))
    client_priorities = " ".join(client_priorities_parts)

    if opportunity.incumbent_status:
        incumbent_note = "Incumbent advantage is in play; the response must visibly de-risk transition and execution."
    else:
        incumbent_note = "No incumbent advantage is recorded; speed, clarity, and evaluator confidence can set the pace."
    if opportunity.lead_time_days <= 30:
        lead_time_note = "Lead time is compressed, so the team should favor fast decision cycles and early review discipline."
    elif opportunity.lead_time_days <= 60:
        lead_time_note = "Lead time is moderate, allowing disciplined planning without slowing section ownership."
    else:
        lead_time_note = "Lead time is ample enough to sharpen positioning and assemble stronger proof."
    blockers = matrix_quality.get("gate_c_blockers", [])
    if blockers:
        blocker_note = f"Current compliance blockers: {'; '.join(blockers[:2])}."
    else:
        blocker_note = "Current compliance mapping shows no Gate C blockers."
    competitive_landscape = " ".join(
        [
            incumbent_note,
            f"Qualification score {opportunity.qualification_score:.1f} supports a {recommendation.lower()} posture within {tier.lower()}.",
            lead_time_note,
            blocker_note,
        ]
    )

    win_theme_lines: list[str] = []
    used_themes: set[str] = set()
    ordered_categories = _ordered_categories(matrix_rows)
    for category in ordered_categories:
        theme = _CATEGORY_THEME_MAP.get(category)
        if theme and theme not in used_themes:
            win_theme_lines.append(theme)
            used_themes.add(theme)
        if len(win_theme_lines) == 3:
            break
    if len(win_theme_lines) < 2:
        for section in _ordered_sections(matrix_rows):
            theme = f"Win Theme: Make {section} explicit, compliant, and easy for evaluators to score."
            if theme not in used_themes:
                win_theme_lines.append(theme)
                used_themes.add(theme)
            if len(win_theme_lines) == 3:
                break
    if not win_theme_lines:
        win_theme_lines.extend(
            [
                "Win Theme: Reduce evaluator effort with clear requirement traceability and disciplined packaging.",
                "Win Theme: Present a low-risk delivery model with visible ownership and compliance control.",
            ]
        )
    elif len(win_theme_lines) == 1:
        win_theme_lines.append(
            "Win Theme: Reduce evaluator effort with clear requirement traceability and disciplined packaging."
        )
    win_themes_draft = "\n".join(win_theme_lines[:3])

    solution_positioning_parts: list[str] = []
    if criteria_sentence:
        solution_positioning_parts.append(
            f"Shape the response around the stated evaluation priorities: {criteria_sentence}"
        )
    seen_positioning: set[str] = set()
    for category in ordered_categories:
        sentence = _CATEGORY_POSITIONING_MAP.get(category)
        if sentence and sentence not in seen_positioning:
            solution_positioning_parts.append(sentence)
            seen_positioning.add(sentence)
        if len(solution_positioning_parts) >= 5:
            break
    if not solution_positioning_parts:
        solution_positioning_parts.append(
            "Open with executive framing that ties buyer priorities to measurable outcomes and compliance discipline."
        )
    solution_positioning = " ".join(solution_positioning_parts)

    timeline = build_capture_timeline(deadline, today=resolved_today)
    return {
        "summary": summary,
        "client_priorities": client_priorities,
        "competitive_landscape": competitive_landscape,
        "win_themes_draft": win_themes_draft,
        "solution_positioning": solution_positioning,
        "timeline": timeline,
    }


class CapturePlanService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_opportunity(self, opportunity_id: str) -> Opportunity | None:
        return self.db.get(Opportunity, opportunity_id)

    def _latest_solicitation(self, opportunity_id: str) -> Solicitation | None:
        stmt = (
            select(Solicitation)
            .where(Solicitation.opportunity_id == opportunity_id)
            .order_by(Solicitation.version.desc(), Solicitation.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def _strategy_rows(self, opportunity_id: str, solicitation_id: str) -> list[dict[str, str]]:
        stmt = (
            select(ComplianceMatrixRow, Requirement)
            .join(Requirement, ComplianceMatrixRow.requirement_id == Requirement.id)
            .where(ComplianceMatrixRow.opportunity_id == opportunity_id)
            .where(Requirement.solicitation_id == solicitation_id)
            .order_by(Requirement.requirement_code.asc())
        )
        rows: list[dict[str, str]] = []
        for matrix_row, requirement in self.db.execute(stmt).all():
            rows.append(
                {
                    "proposal_section": matrix_row.proposal_section,
                    "status": matrix_row.status,
                    "owner": matrix_row.owner,
                    "category": requirement.category,
                    "requirement_type": requirement.requirement_type,
                }
            )
        return rows

    def get_latest(self, opportunity_id: str) -> CapturePlan | None:
        stmt = (
            select(CapturePlan)
            .where(CapturePlan.opportunity_id == opportunity_id)
            .order_by(CapturePlan.version.desc(), CapturePlan.created_at.desc())
        )
        return self.db.scalars(stmt).first()

    def list_versions(self, opportunity_id: str) -> list[CapturePlan]:
        stmt = (
            select(CapturePlan)
            .where(CapturePlan.opportunity_id == opportunity_id)
            .order_by(CapturePlan.version.desc(), CapturePlan.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def _persist_version(
        self,
        opportunity_id: str,
        *,
        actor: str,
        content: dict[str, str],
        audit_action: str,
        audit_after_state: dict | None = None,
    ) -> CapturePlan:
        latest = self.get_latest(opportunity_id)
        next_version = 1 if latest is None else latest.version + 1
        created = CapturePlan(
            opportunity_id=opportunity_id,
            version=next_version,
            summary=content["summary"],
            client_priorities=content["client_priorities"],
            competitive_landscape=content["competitive_landscape"],
            win_themes_draft=content["win_themes_draft"],
            solution_positioning=content["solution_positioning"],
            timeline=content["timeline"],
        )
        self.db.add(created)
        self.db.flush()
        after_state = {"capture_plan_id": created.id, "version": created.version}
        if audit_after_state:
            after_state.update(audit_after_state)
        log_audit_event(
            self.db,
            opportunity_id=opportunity_id,
            actor=actor,
            action=audit_action,
            before_state_json=json.dumps(
                {
                    "previous_capture_plan_id": latest.id if latest else None,
                    "previous_version": latest.version if latest else None,
                }
            ),
            after_state_json=json.dumps(after_state),
        )
        self.db.commit()
        self.db.refresh(created)
        return created

    def create_version(self, opportunity_id: str, payload: CapturePlanUpdateRequest) -> CapturePlan:
        opportunity = self._get_opportunity(opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found")

        content = {
            "summary": payload.summary,
            "client_priorities": payload.client_priorities,
            "competitive_landscape": payload.competitive_landscape,
            "win_themes_draft": payload.win_themes_draft,
            "solution_positioning": payload.solution_positioning,
            "timeline": payload.timeline,
        }
        return self._persist_version(
            opportunity_id,
            actor=payload.actor,
            content=content,
            audit_action="capture_plan_version_created",
        )

    def readiness(self, opportunity_id: str) -> CapturePlanReadinessResponse:
        opportunity = self._get_opportunity(opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found")

        latest_plan = self.get_latest(opportunity_id)
        latest_solicitation = self._latest_solicitation(opportunity_id)
        strategy_rows = self._strategy_rows(opportunity_id, latest_solicitation.id) if latest_solicitation else []
        return evaluate_capture_plan_readiness(
            opportunity=opportunity,
            capture_plan=latest_plan,
            solicitation=latest_solicitation,
            matrix_rows=strategy_rows,
        )

    def generate_enriched_version(self, opportunity_id: str, payload: CapturePlanGenerateRequest) -> CapturePlan:
        opportunity = self._get_opportunity(opportunity_id)
        if not opportunity:
            raise ValueError("Opportunity not found")

        solicitation = self._latest_solicitation(opportunity_id)
        if not solicitation:
            raise CapturePlanGenerationError("No solicitation has been parsed for this opportunity.")

        matrix_rows = self._strategy_rows(opportunity_id, solicitation.id)
        matrix_quality = ComplianceMatrixService(self.db).matrix_quality(opportunity_id)
        content = build_enriched_capture_plan_content(
            opportunity,
            solicitation,
            matrix_rows,
            matrix_quality,
        )
        return self._persist_version(
            opportunity_id,
            actor=payload.actor,
            content=content,
            audit_action="capture_plan_enriched_generated",
            audit_after_state={
                "solicitation_id": solicitation.id,
                "matrix_row_count": len(matrix_rows),
                "gate_c_ready": matrix_quality["gate_c_ready"],
            },
        )
