from __future__ import annotations

import csv
import fnmatch
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import BASE_DIR
from app.modules.company_os.models import (
    ActionItem,
    ApprovalRequest,
    Engagement,
    FounderBriefRun,
    KnowledgePromotionCandidate,
    MeetingCommitment,
    ScoreboardSnapshot,
    SourceSignal,
    Stakeholder,
    TimelineMilestone,
)
from app.modules.company_os.schemas import CashflowForecastRow, FounderDecision, RevenueForecastRow
from app.modules.janitorial_os.models import CommercialEngagement, GrowthRelationshipProfile
from app.modules.opportunity_intake.models import Opportunity


REPO_ROOT = BASE_DIR.parent
DEFAULT_SOURCE_CONFIG = REPO_ROOT / "marketing-agents" / "data" / "approved_communication_sources.csv"
DEFAULT_MARKETING_ROOT = REPO_ROOT / "marketing-agents"
SUPPORTED_FILE_EXTENSIONS = {".txt", ".md", ".json", ".eml", ".srt"}
OWNER_NAME = "Timmy Semenza"
PROJECTION_HEADERS: dict[str, list[str]] = {
    "communication_signal_log.csv": [
        "signal_id",
        "source_type",
        "source_system",
        "client_name",
        "engagement_id",
        "thread_or_meeting_id",
        "signal_date",
        "signal_kind",
        "summary",
        "owner",
        "status",
        "provenance_ref",
    ],
    "engagement_register.csv": [
        "engagement_id",
        "client_name",
        "engagement_name",
        "engagement_type",
        "status",
        "intake_date",
        "owner",
        "complexity_level",
        "next_action",
        "deadline",
        "source_signal_id",
        "notes",
    ],
    "engagement_timeline.csv": [
        "engagement_id",
        "milestone_code",
        "milestone_label",
        "target_date",
        "owner",
        "status",
        "source",
        "notes",
    ],
    "stakeholder_map.csv": [
        "engagement_id",
        "stakeholder_name",
        "role_code",
        "role_label",
        "organization",
        "email",
        "status",
        "interview_required",
        "approval_scope",
        "notes",
    ],
    "action_workbench.csv": [
        "action_id",
        "engagement_id",
        "client_name",
        "source_signal_id",
        "action_type",
        "task_or_artifact",
        "owner",
        "due_date",
        "status",
        "review_required",
        "notes",
    ],
    "approval_router_queue.csv": [
        "routing_id",
        "engagement_id",
        "client_name",
        "approval_type",
        "requested_role",
        "requested_person",
        "status",
        "due_date",
        "channel",
        "policy_key",
        "notes",
    ],
    "meeting_follow_through.csv": [
        "meeting_id",
        "meeting_date",
        "account_or_client",
        "meeting_title",
        "owner",
        "commitment",
        "commitment_owner",
        "due_date",
        "status",
        "system_to_update",
        "notes",
    ],
    "executive_scoreboard.csv": [
        "snapshot_date",
        "pipeline_value",
        "weighted_pipeline",
        "meetings_booked",
        "proposal_count",
        "proposal_win_rate",
        "active_delivery_count",
        "overdue_invoices",
        "total_ar_over_30",
        "open_hiring_roles",
        "urgent_risks",
        "notes",
    ],
    "revenue_forecast.csv": [
        "snapshot_date",
        "forecast_window",
        "forecast_type",
        "account_name",
        "stage",
        "amount",
        "expected_close_date",
        "probability_percent",
        "weighted_amount",
        "owner",
        "next_action",
        "notes",
    ],
    "cashflow_forecast.csv": [
        "snapshot_date",
        "week_start",
        "projected_cash_in",
        "projected_cash_out",
        "net_cash_change",
        "ending_cash_balance",
        "confidence",
        "notes",
    ],
}
OPERATING_GUARDRAILS = [
    "Manual-first ingress only. Approved exports and file-drop inboxes are the only v1 sources.",
    "AI assists with extraction, routing, summaries, and projections. Humans retain external judgment and approvals.",
    "The system stays narrowly focused on engagement operations, founder control, and internal review loops.",
    "No autonomous outbound email, calls, LinkedIn actions, or live mailbox surveillance in Wave 1.",
    "Every generated record carries provenance, agent ownership, run id, and workflow state for auditability.",
]


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _today() -> date:
    return _utcnow().date()


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "item"


def _humanize_slug(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("_", " ").replace("-", " ")).strip().title()


def _truncate(value: str | None, limit: int) -> str:
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[: max(0, limit - 3)].rstrip()}..."


def _split_sentences(text: str) -> list[str]:
    collapsed = re.sub(r"\s+", " ", text).strip()
    if not collapsed:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", collapsed) if part.strip()]


def _stringify(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _normalize_status_token(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def classify_route(text: str) -> str:
    lower = text.lower()
    if any(token in lower for token in ["rfp", "proposal", "bid", "submission", "solicitation", "scope of work", "reverse timeline", "pricing sheet"]):
        return "proposal-capture"
    if any(token in lower for token in ["invoice", "billing", "collections", "payment", "retainer", "budget", "estimate", "pricing"]):
        return "finance-commercial"
    if any(token in lower for token in ["kickoff", "implementation", "deliverable", "client success", "onboarding", "support", "maintenance", "change order"]):
        return "delivery-client-success"
    if any(token in lower for token in ["follow up", "follow-up", "pipeline", "lead", "opportunity", "demo", "intro call", "discovery", "sales process", "meeting booked"]):
        return "revenue-follow-up"
    return "general-engagement"


def infer_complexity_level(text: str) -> str:
    lower = text.lower()
    score = 0
    if len(text) > 1800:
        score += 2
    if any(token in lower for token in ["stakeholder", "timeline", "deliverable", "interview", "approval", "pricing", "proposal", "compliance"]):
        score += 2
    if any(token in lower for token in ["demo", "follow-up", "meeting", "budget", "workflow"]):
        score += 1
    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def infer_signal_kind(item: dict[str, Any], text: str) -> str:
    lower = text.lower()
    source_type = str(item.get("source_type") or "")
    provenance_ref = str(item.get("provenance_ref") or "")
    if source_type == "csv_interactions":
        return "interaction-log"
    if source_type == "csv_events":
        return "website-contact"
    if provenance_ref.endswith(".eml"):
        return "email-export"
    if any(token in lower for token in ["call", "intro call", "meeting", "zoom"]):
        return "call-transcript"
    if any(token in lower for token in ["proposal", "rfp", "solicitation"]):
        return "opportunity-brief"
    return "communication-capture"


def summarize_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= 220:
        return cleaned
    sentences = _split_sentences(cleaned)
    first = next((sentence for sentence in sentences if len(sentence) > 20), cleaned[:220])
    return _truncate(first, 220)


@dataclass
class IngestSummary:
    run_id: str
    sources_scanned: int = 0
    items_discovered: int = 0
    skipped_items: int = 0
    signals_created: int = 0
    engagements_created: int = 0
    engagements_updated: int = 0
    actions_created: int = 0
    approvals_created: int = 0
    commitments_created: int = 0
    knowledge_candidates_created: int = 0
    projections_written: list[str] | None = None
    founder_brief_id: str | None = None
    scoreboard_snapshot_id: str | None = None
    created_at: datetime | None = None


class CompanyOsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_signals(self, limit: int = 200) -> list[SourceSignal]:
        stmt = select(SourceSignal).order_by(SourceSignal.signal_date.desc(), SourceSignal.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt))

    def list_engagements(self) -> list[Engagement]:
        stmt = select(Engagement).order_by(Engagement.updated_at.desc(), Engagement.client_name.asc())
        return list(self.db.scalars(stmt))

    def get_engagement(self, engagement_id: str) -> Engagement | None:
        return self.db.get(Engagement, engagement_id)

    def list_actions(self) -> list[ActionItem]:
        stmt = select(ActionItem).order_by(ActionItem.due_date.asc().nulls_last(), ActionItem.created_at.desc())
        return list(self.db.scalars(stmt))

    def list_approvals(self) -> list[ApprovalRequest]:
        stmt = select(ApprovalRequest).order_by(ApprovalRequest.status.asc(), ApprovalRequest.due_date.asc().nulls_last())
        return list(self.db.scalars(stmt))

    def list_commitments(self) -> list[MeetingCommitment]:
        stmt = select(MeetingCommitment).order_by(MeetingCommitment.status.asc(), MeetingCommitment.due_date.asc().nulls_last())
        return list(self.db.scalars(stmt))

    def list_knowledge_candidates(self) -> list[KnowledgePromotionCandidate]:
        stmt = select(KnowledgePromotionCandidate).order_by(KnowledgePromotionCandidate.updated_at.desc())
        return list(self.db.scalars(stmt))

    def latest_scoreboard_snapshot(self) -> ScoreboardSnapshot | None:
        stmt = select(ScoreboardSnapshot).order_by(ScoreboardSnapshot.snapshot_date.desc(), ScoreboardSnapshot.created_at.desc())
        return self.db.scalars(stmt).first()

    def latest_founder_brief(self) -> FounderBriefRun | None:
        stmt = select(FounderBriefRun).order_by(FounderBriefRun.brief_date.desc(), FounderBriefRun.created_at.desc())
        return self.db.scalars(stmt).first()

    def update_engagement_status(self, engagement_id: str, *, status: str, owner: str | None = None, note: str | None = None) -> Engagement:
        engagement = self.db.get(Engagement, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found.")
        engagement.status = status
        if owner:
            engagement.owner = owner
        if note:
            engagement.notes = _append_note(engagement.notes, note)
        if _normalize_status_token(status) == "closed":
            engagement.workflow_stage = "CLOSED"
        elif engagement.workflow_stage == "CLOSED":
            engagement.workflow_stage = "ENGAGEMENT_TRIAGE"
        self.db.commit()
        self.db.refresh(engagement)
        return engagement

    def update_action_status(self, action_id: str, *, status: str, owner: str | None = None, note: str | None = None) -> ActionItem:
        action = self.db.get(ActionItem, action_id)
        if not action:
            raise ValueError("Action item not found.")
        action.status = status
        if owner:
            action.owner = owner
        if note:
            action.notes = _append_note(action.notes, note)
        self.db.commit()
        self.db.refresh(action)
        return action

    def update_approval_status(self, approval_id: str, *, status: str, owner: str | None = None, note: str | None = None) -> ApprovalRequest:
        approval = self.db.get(ApprovalRequest, approval_id)
        if not approval:
            raise ValueError("Approval request not found.")
        approval.status = status
        if owner:
            approval.owner = owner
        if note:
            approval.notes = _append_note(approval.notes, note)
        engagement = approval.engagement
        normalized = _normalize_status_token(status)
        if engagement and normalized == "approved":
            engagement.workflow_stage = "FOUNDER_BRIEF"
        elif engagement and normalized in {"rejected", "reopen"}:
            engagement.workflow_stage = "ENGAGEMENT_TRIAGE"
        elif engagement and normalized in {"rework-required", "needs-rework"}:
            engagement.workflow_stage = "APPROVAL_WAIT"
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def update_commitment_status(self, commitment_id: str, *, status: str, owner: str | None = None, note: str | None = None) -> MeetingCommitment:
        commitment = self.db.get(MeetingCommitment, commitment_id)
        if not commitment:
            raise ValueError("Meeting commitment not found.")
        commitment.status = status
        if owner:
            commitment.commitment_owner = owner
        if note:
            commitment.notes = _append_note(commitment.notes, note)
        engagement = commitment.engagement
        if engagement and _normalize_status_token(status) == "done":
            open_commitments = self.db.scalar(
                select(func.count()).select_from(MeetingCommitment).where(
                    MeetingCommitment.engagement_id == engagement.id,
                    MeetingCommitment.status != "done",
                    MeetingCommitment.id != commitment.id,
                )
            ) or 0
            if open_commitments == 0 and engagement.workflow_stage in {"FOUNDER_BRIEF", "FOLLOW_THROUGH"}:
                engagement.workflow_stage = "KNOWLEDGE_PROMOTION"
        self.db.commit()
        self.db.refresh(commitment)
        return commitment


def extract_deadline(text: str, signal_date: date) -> date | None:
    for pattern in (
        r"\b(\d{4}-\d{2}-\d{2})\b",
        r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b",
    ):
        match = re.search(pattern, text)
        if not match:
            continue
        token = match.group(1)
        if "-" in token:
            try:
                return date.fromisoformat(token)
            except ValueError:
                continue
        month, day, year = token.split("/")
        if len(year) == 2:
            year = f"20{year}"
        try:
            return date(int(year), int(month), int(day))
        except ValueError:
            continue

    month_match = re.search(
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,\s*(\d{4}))?\b",
        text,
        flags=re.IGNORECASE,
    )
    if month_match:
        month_name, day_text, year_text = month_match.groups()
        month_index = [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ].index(month_name.lower()) + 1
        year = int(year_text or signal_date.year)
        try:
            return date(year, month_index, int(day_text))
        except ValueError:
            return None

    relative = re.search(r"\b(?:due|deadline|proposal due(?: on)?)\s+the\s+(\d{1,2})(?:st|nd|rd|th)\b", text, flags=re.IGNORECASE)
    if relative:
        target_day = int(relative.group(1))
        guess_month = signal_date.month
        guess_year = signal_date.year
        if target_day < signal_date.day:
            guess_month += 1
            if guess_month == 13:
                guess_month = 1
                guess_year += 1
        try:
            return date(guess_year, guess_month, target_day)
        except ValueError:
            return None
    return None


def infer_risk_level(*, deadline: date | None, route: str, text: str) -> str:
    lower = text.lower()
    if deadline and deadline <= _today() + timedelta(days=2):
        return "high"
    if route == "proposal-capture":
        return "high"
    if any(token in lower for token in ["urgent", "asap", "deadline", "escalate", "risk"]):
        return "high"
    if any(token in lower for token in ["review", "pricing", "approval", "follow-up"]):
        return "medium"
    return "low"


def extract_action_items(text: str, route: str, signal_date: date, deadline: date | None) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for sentence in _split_sentences(text):
        trimmed = sentence.strip("- ").strip()
        if len(trimmed) < 24 or len(trimmed) > 220:
            continue
        lower = trimmed.lower()
        if not any(token in lower for token in ["need to", "will ", "follow up", "follow-up", "send", "review", "build", "prepare", "schedule", "draft", "deliver", "approve", "upload", "book", "set up", "rewrite"]):
            continue
        if any(existing["task"].lower() == trimmed.lower() for existing in tasks):
            continue
        task_type = "follow-up"
        if any(token in lower for token in ["schedule", "book", "meeting", "interview"]):
            task_type = "meeting"
        elif any(token in lower for token in ["review", "approve", "signoff"]):
            task_type = "review"
        elif any(token in lower for token in ["build", "draft", "rewrite", "prepare", "deliverable", "template", "content", "proposal"]):
            task_type = "artifact-build"
        due = extract_deadline(trimmed, signal_date) or deadline or (signal_date + timedelta(days=min(len(tasks) + 1, 5)))
        tasks.append(
            {
                "type": task_type,
                "task": trimmed,
                "due_date": due,
                "review_required": "yes" if any(token in lower for token in ["review", "approve", "proposal", "strategy"]) else "no",
                "notes": f"Derived from intake signal sentence: {_truncate(sentence, 180)}",
            }
        )
        if len(tasks) >= 4:
            break

    if tasks:
        return tasks

    fallback_task = ROUTE_CONFIG[route]["default_action"]
    return [
        {
            "type": "follow-up",
            "task": fallback_task,
            "due_date": deadline or (signal_date + timedelta(days=1)),
            "review_required": "yes" if route == "proposal-capture" else "no",
            "notes": "Fallback action seeded from route defaults.",
        }
    ]


ROUTE_CONFIG: dict[str, dict[str, Any]] = {
    "proposal-capture": {
        "label": "Proposal Capture",
        "milestones": [
            {"code": "signal-captured", "label": "Signal Captured", "offset_days": 0},
            {"code": "qualification-review", "label": "Qualification Review", "offset_days": 1, "reverse_offset_days": -14},
            {"code": "stakeholder-inputs", "label": "Stakeholder Inputs", "offset_days": 3, "reverse_offset_days": -10},
            {"code": "draft-assembly", "label": "Draft Assembly", "offset_days": 5, "reverse_offset_days": -7},
            {"code": "internal-review", "label": "Internal Review", "offset_days": 7, "reverse_offset_days": -4},
            {"code": "final-package", "label": "Final Package", "offset_days": 9, "reverse_offset_days": -2},
            {"code": "submission", "label": "Submission", "offset_days": 11, "reverse_offset_days": 0},
        ],
        "stakeholders": [
            {"name": OWNER_NAME, "role_code": "internal_owner", "role_label": "Internal Owner", "organization": "Boss Key", "interview_required": "no", "approval_scope": "workflow-owner"},
            {"name": "Client Sponsor", "role_code": "client_sponsor", "role_label": "Client Sponsor", "organization_from_client": True, "interview_required": "yes", "approval_scope": "requirements"},
            {"name": "Sales Lead", "role_code": "sales_lead", "role_label": "Sales Lead", "organization_from_client": True, "interview_required": "yes", "approval_scope": "commercial"},
            {"name": "Operations Lead", "role_code": "operations_lead", "role_label": "Operations Lead", "organization_from_client": True, "interview_required": "yes", "approval_scope": "delivery"},
            {"name": "Executive Approver", "role_code": "executive_approver", "role_label": "Executive Approver", "organization_from_client": True, "interview_required": "no", "approval_scope": "signoff"},
        ],
        "default_action": "Review intake, confirm qualification, and build reverse timeline.",
    },
    "delivery-client-success": {
        "label": "Delivery / Client Success",
        "milestones": [
            {"code": "intake", "label": "Delivery Intake", "offset_days": 0},
            {"code": "scope-align", "label": "Scope Alignment", "offset_days": 2},
            {"code": "work-plan", "label": "Work Plan Published", "offset_days": 4},
            {"code": "client-checkpoint", "label": "Client Checkpoint", "offset_days": 7},
        ],
        "stakeholders": [
            {"name": OWNER_NAME, "role_code": "internal_owner", "role_label": "Internal Owner", "organization": "Boss Key", "interview_required": "no", "approval_scope": "workflow-owner"},
            {"name": "Client Sponsor", "role_code": "client_sponsor", "role_label": "Client Sponsor", "organization_from_client": True, "interview_required": "yes", "approval_scope": "service-direction"},
            {"name": "Delivery Lead", "role_code": "delivery_lead", "role_label": "Delivery Lead", "organization_from_client": True, "interview_required": "yes", "approval_scope": "execution"},
            {"name": "Success Lead", "role_code": "success_lead", "role_label": "Success Lead", "organization": "Boss Key", "interview_required": "no", "approval_scope": "retention"},
        ],
        "default_action": "Translate the client discussion into a scoped delivery work plan.",
    },
    "finance-commercial": {
        "label": "Finance / Commercial",
        "milestones": [
            {"code": "intake", "label": "Commercial Intake", "offset_days": 0},
            {"code": "estimate-review", "label": "Estimate Review", "offset_days": 2},
            {"code": "terms-confirmed", "label": "Terms Confirmed", "offset_days": 4},
            {"code": "billing-ready", "label": "Billing Ready", "offset_days": 6},
        ],
        "stakeholders": [
            {"name": OWNER_NAME, "role_code": "internal_owner", "role_label": "Internal Owner", "organization": "Boss Key", "interview_required": "no", "approval_scope": "workflow-owner"},
            {"name": "Client Sponsor", "role_code": "client_sponsor", "role_label": "Client Sponsor", "organization_from_client": True, "interview_required": "yes", "approval_scope": "commercial-input"},
            {"name": "Commercial Owner", "role_code": "commercial_owner", "role_label": "Commercial Owner", "organization": "Boss Key", "interview_required": "no", "approval_scope": "pricing"},
            {"name": "Billing Owner", "role_code": "billing_owner", "role_label": "Billing Owner", "organization": "Boss Key", "interview_required": "no", "approval_scope": "collections"},
        ],
        "default_action": "Turn the commercial discussion into a budget, billing, or collections action.",
    },
    "revenue-follow-up": {
        "label": "Revenue Follow-Up",
        "milestones": [
            {"code": "signal-captured", "label": "Signal Captured", "offset_days": 0},
            {"code": "qualification", "label": "Qualification", "offset_days": 1},
            {"code": "follow-up", "label": "Follow-Up Sent", "offset_days": 2},
            {"code": "next-meeting", "label": "Next Meeting Booked", "offset_days": 5},
        ],
        "stakeholders": [
            {"name": OWNER_NAME, "role_code": "internal_owner", "role_label": "Internal Owner", "organization": "Boss Key", "interview_required": "no", "approval_scope": "workflow-owner"},
            {"name": "Primary Contact", "role_code": "primary_contact", "role_label": "Primary Contact", "organization_from_client": True, "interview_required": "yes", "approval_scope": "discovery"},
            {"name": "Revenue Owner", "role_code": "revenue_owner", "role_label": "Revenue Owner", "organization": "Boss Key", "interview_required": "no", "approval_scope": "pipeline"},
        ],
        "default_action": "Capture the next follow-up and move the engagement toward a scheduled decision step.",
    },
    "general-engagement": {
        "label": "General Engagement",
        "milestones": [
            {"code": "intake", "label": "Intake Logged", "offset_days": 0},
            {"code": "triage", "label": "Triage Review", "offset_days": 1},
            {"code": "execution", "label": "Execution Path Chosen", "offset_days": 3},
        ],
        "stakeholders": [
            {"name": OWNER_NAME, "role_code": "internal_owner", "role_label": "Internal Owner", "organization": "Boss Key", "interview_required": "no", "approval_scope": "workflow-owner"},
            {"name": "Primary Contact", "role_code": "primary_contact", "role_label": "Primary Contact", "organization_from_client": True, "interview_required": "yes", "approval_scope": "context"},
        ],
        "default_action": "Review the communication and route it into a concrete workstream.",
    },
}


def find_engagement_id(client_name: str, route: str) -> str:
    return f"eng-{_slugify(client_name)}-{_slugify(route)}"


def build_engagement_name(client_name: str, route: str, title: str) -> str:
    route_label = ROUTE_CONFIG[route]["label"]
    title_text = _truncate(title or route_label, 80)
    if client_name.lower() in title_text.lower():
        return title_text
    return f"{client_name} - {route_label}"


def infer_client_name(title: str, text: str, payload: dict[str, Any]) -> str:
    by_payload = str(payload.get("company_name") or payload.get("company") or "").strip()
    if by_payload:
        return _humanize_slug(by_payload)
    match = re.search(r"(?:company|account|client)\s*[:=-]\s*([^,;\n]+)", text, flags=re.IGNORECASE)
    if match:
        return _humanize_slug(match.group(1))
    match = re.search(r"with\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})", text)
    if match:
        return match.group(1).strip()
    cleaned_title = re.sub(r"\b\d{4}[-_ ]\d{2}[-_ ]\d{2}\b", " ", title)
    cleaned_title = re.sub(r"\b(?:intro|call|meeting|notes|transcript|email|thread|capture|processed|export|follow|followup|follow-up|proposal|rfp)\b", " ", cleaned_title, flags=re.IGNORECASE)
    cleaned_title = re.sub(r"\s+", " ", cleaned_title).strip()
    return _humanize_slug(cleaned_title) if cleaned_title else ""


def _append_note(existing: str | None, addition: str | None) -> str:
    base = (existing or "").strip()
    extra = (addition or "").strip()
    if not extra:
        return base
    if not base:
        return extra
    if extra in base:
        return base
    return f"{base}\n{extra}"


def _highest_complexity(left: str, right: str) -> str:
    order = ["low", "medium", "high"]
    return order[max(order.index(left or "low"), order.index(right or "low"))]


def _resolve_repo_path(raw: str) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return REPO_ROOT / path


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _write_text(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _write_json(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=_stringify), encoding="utf-8")
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _list_files_recursive(path: Path) -> list[Path]:
    files: list[Path] = []
    for child in path.iterdir():
        if child.is_dir():
            files.extend(_list_files_recursive(child))
        else:
            files.append(child)
    return files


def _dedupe_directory_files(files: list[Path], pattern: str) -> list[Path]:
    matched = [
        file_path
        for file_path in files
        if file_path.suffix.lower() in SUPPORTED_FILE_EXTENSIONS
        and not file_path.name.startswith(".")
        and file_path.name.lower() != "readme.md"
        and fnmatch.fnmatch(file_path.name, pattern or "*")
    ]
    preferred: dict[str, Path] = {}
    for file_path in matched:
        key = str(file_path.with_suffix("")).lower()
        current = preferred.get(key)
        if current is None:
            preferred[key] = file_path
            continue
        if current.suffix.lower() == ".srt" and file_path.suffix.lower() == ".txt":
            preferred[key] = file_path
            continue
        if file_path.stat().st_mtime > current.stat().st_mtime:
            preferred[key] = file_path
    return sorted(preferred.values())


def _read_source_file(path: Path) -> str:
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return json.dumps(payload, indent=2, sort_keys=True)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return path.read_text(encoding="utf-8", errors="ignore")
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() == ".srt":
        lines = []
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped or stripped.isdigit() or "-->" in stripped:
                continue
            lines.append(stripped)
        return " ".join(lines)
    return raw


def _extract_date_from_string(value: str) -> date | None:
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", value)
    if not match:
        return None
    try:
        return date.fromisoformat(match.group(1))
    except ValueError:
        return None


def _extract_datetime_date(value: str) -> date | None:
    text = (value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return _extract_date_from_string(text)


class CompanyOsService(CompanyOsService):
    def _collect_source_items(self, source: dict[str, str]) -> Iterable[dict[str, Any]]:
        source_type = str(source.get("source_type") or "").strip()
        source_path = _resolve_repo_path(source.get("source_path") or "")
        if source_type in {"transcript_dir", "document_dir"}:
            if not source_path.exists() or not source_path.is_dir():
                return []
            files = _dedupe_directory_files(_list_files_recursive(source_path), source.get("file_pattern") or "*.*")
            items: list[dict[str, Any]] = []
            for file_path in files:
                item = self._build_file_item(source, file_path)
                if item:
                    items.append(item)
            return items
        if source_type == "csv_interactions":
            items = []
            for index, row in enumerate(_read_csv(source_path)):
                item = self._build_interaction_item(source, row, index)
                if item:
                    items.append(item)
            return items
        if source_type == "csv_events":
            items = []
            for index, row in enumerate(_read_csv(source_path)):
                item = self._build_event_item(source, row, index)
                if item:
                    items.append(item)
            return items
        return []

    def _build_file_item(self, source: dict[str, str], file_path: Path) -> dict[str, Any] | None:
        content = _read_source_file(file_path)
        if not content.strip():
            return None
        signal_date = _extract_date_from_string(file_path.name) or date.fromtimestamp(file_path.stat().st_mtime)
        try:
            rel = str(file_path.relative_to(REPO_ROOT)).replace("\\", "/")
        except ValueError:
            rel = str(file_path)
        return {
            "source_id": source.get("source_id") or file_path.stem,
            "source_type": source.get("source_type") or "document_dir",
            "source_system": source.get("source_id") or file_path.parent.name,
            "thread_or_meeting_id": file_path.stem,
            "signal_date": signal_date,
            "title": _humanize_slug(file_path.stem),
            "text": content,
            "provenance_ref": rel,
            "source_payload": {"path": rel},
        }

    def _build_interaction_item(self, source: dict[str, str], row: dict[str, str], index: int) -> dict[str, Any] | None:
        company_name = (row.get("company_name") or "").strip()
        summary = (row.get("summary") or "").strip()
        if not company_name and not summary:
            return None
        text = " ".join(
            part
            for part in [
                company_name,
                row.get("contact_name") or "",
                row.get("channel") or "",
                row.get("direction") or "",
                summary,
                row.get("outcome") or "",
                row.get("next_action") or "",
            ]
            if str(part).strip()
        )
        signal_date = _extract_date_from_string(row.get("date") or "") or _extract_datetime_date(row.get("created_at") or "") or _today()
        interaction_id = (row.get("interaction_id") or f"interaction-{index + 1}").strip()
        return {
            "source_id": source.get("source_id") or "interaction_log",
            "source_type": "csv_interactions",
            "source_system": "interaction_log",
            "thread_or_meeting_id": interaction_id,
            "signal_date": signal_date,
            "title": f"{company_name or 'Interaction'} {signal_date.isoformat()}",
            "text": text,
            "provenance_ref": f"{source.get('source_path')}#{interaction_id}",
            "source_payload": row,
        }

    def _build_event_item(self, source: dict[str, str], row: dict[str, str], index: int) -> dict[str, Any] | None:
        event_date = _extract_date_from_string(row.get("event_date") or "") or _extract_datetime_date(row.get("event_at") or "") or _today()
        context = (row.get("context") or "").strip()
        if not context and not row.get("source_page"):
            return None
        title = _humanize_slug((row.get("source_page") or "website_contact").replace("/", " "))
        text = " ".join(
            part for part in [title, row.get("channel") or "", context, row.get("referrer") or ""] if str(part).strip()
        )
        return {
            "source_id": source.get("source_id") or "website_contact_events",
            "source_type": "csv_events",
            "source_system": "website_contact_events",
            "thread_or_meeting_id": f"event-{index + 1}",
            "signal_date": event_date,
            "title": title,
            "text": text,
            "provenance_ref": f"{source.get('source_path')}#event-{index + 1}",
            "source_payload": row,
        }

    def _normalize_item(self, item: dict[str, Any], *, owner: str, run_id: str) -> dict[str, Any] | None:
        text = re.sub(r"\s+", " ", str(item.get("text") or "")).strip()
        if not text:
            return None
        signal_date = item["signal_date"]
        title = str(item.get("title") or "").strip() or "Captured Signal"
        route = classify_route(text)
        client_name = infer_client_name(title, text, item.get("source_payload") or {}) or "Unknown Account"
        deadline = extract_deadline(text, signal_date)
        summary = summarize_text(text)
        actions = extract_action_items(text, route, signal_date, deadline)
        fingerprint = hashlib.sha1(f"{item['provenance_ref']}|{summary}".encode("utf-8")).hexdigest()
        return {
            "signal_id": f"signal-{_slugify(client_name)}-{signal_date.isoformat()}-{fingerprint[:8]}",
            "fingerprint": fingerprint,
            "source_id": item["source_id"],
            "source_type": item["source_type"],
            "source_system": item["source_system"],
            "thread_or_meeting_id": item.get("thread_or_meeting_id"),
            "signal_date": signal_date,
            "title": title,
            "route": route,
            "client_name": client_name,
            "summary": summary,
            "content_excerpt": _truncate(text, 600),
            "content_text": text,
            "signal_kind": infer_signal_kind(item, text),
            "provenance_ref": item["provenance_ref"],
            "source_payload_json": json.dumps(item.get("source_payload") or {}),
            "deadline": deadline,
            "actions": actions,
            "engagement_id": find_engagement_id(client_name, route),
            "engagement_name": build_engagement_name(client_name, route, title),
            "complexity_level": infer_complexity_level(text),
            "risk_level": infer_risk_level(deadline=deadline, route=route, text=text),
            "owner": owner,
            "run_id": run_id,
        }

    def _upsert_signal(self, normalized: dict[str, Any]) -> SourceSignal | None:
        existing = self.db.scalars(select(SourceSignal).where(SourceSignal.fingerprint == normalized["fingerprint"])).first()
        if existing:
            return None
        signal = SourceSignal(
            id=normalized["signal_id"],
            fingerprint=normalized["fingerprint"],
            source_id=normalized["source_id"],
            source_type=normalized["source_type"],
            source_system=normalized["source_system"],
            thread_or_meeting_id=normalized["thread_or_meeting_id"],
            signal_date=normalized["signal_date"],
            signal_kind=normalized["signal_kind"],
            client_name=normalized["client_name"],
            title=normalized["title"],
            route=normalized["route"],
            summary=normalized["summary"],
            content_excerpt=normalized["content_excerpt"],
            content_text=normalized["content_text"],
            provenance_ref=normalized["provenance_ref"],
            source_payload_json=normalized["source_payload_json"],
            agent_id="26",
            run_id=normalized["run_id"],
            owner=normalized["owner"],
            status="captured",
        )
        self.db.add(signal)
        self.db.flush()
        return signal

    def _upsert_engagement(self, signal: SourceSignal, normalized: dict[str, Any]) -> tuple[Engagement, bool]:
        engagement = self.db.get(Engagement, normalized["engagement_id"])
        if engagement is None:
            engagement = Engagement(
                id=normalized["engagement_id"],
                client_name=normalized["client_name"],
                engagement_name=normalized["engagement_name"],
                engagement_type=normalized["route"],
                workflow_stage="SIGNAL_CAPTURE",
                status="active",
                intake_date=normalized["signal_date"],
                owner=normalized["owner"],
                complexity_level=normalized["complexity_level"],
                next_action=normalized["actions"][0]["task"],
                deadline=normalized["deadline"],
                risk_level=normalized["risk_level"],
                last_signal_id=signal.id,
                provenance_ref=normalized["provenance_ref"],
                agent_id="27",
                run_id=normalized["run_id"],
                notes=f"Created from {normalized['provenance_ref']}. {normalized['summary']}",
            )
            self.db.add(engagement)
            self.db.flush()
            return engagement, True

        engagement.client_name = normalized["client_name"]
        engagement.engagement_name = engagement.engagement_name or normalized["engagement_name"]
        engagement.engagement_type = engagement.engagement_type or normalized["route"]
        engagement.workflow_stage = "ENGAGEMENT_TRIAGE"
        engagement.owner = normalized["owner"]
        engagement.complexity_level = _highest_complexity(engagement.complexity_level, normalized["complexity_level"])
        engagement.next_action = normalized["actions"][0]["task"]
        engagement.deadline = normalized["deadline"] or engagement.deadline
        engagement.risk_level = normalized["risk_level"]
        engagement.last_signal_id = signal.id
        engagement.provenance_ref = normalized["provenance_ref"]
        engagement.run_id = normalized["run_id"]
        engagement.notes = _append_note(engagement.notes, f"{normalized['signal_date'].isoformat()}: {normalized['summary']}")
        self.db.flush()
        return engagement, False

    def _seed_timeline(self, engagement: Engagement, signal: SourceSignal, normalized: dict[str, Any]) -> None:
        engagement.workflow_stage = "TIMELINE_SEED"
        existing_codes = {
            row[0]
            for row in self.db.execute(
                select(TimelineMilestone.milestone_code).where(TimelineMilestone.engagement_id == engagement.id)
            ).all()
        }
        for milestone in ROUTE_CONFIG[normalized["route"]]["milestones"]:
            if milestone["code"] in existing_codes:
                continue
            target_date = None
            if normalized["deadline"] and "reverse_offset_days" in milestone:
                target_date = normalized["deadline"] + timedelta(days=milestone["reverse_offset_days"])
            elif milestone.get("offset_days") is not None:
                target_date = normalized["signal_date"] + timedelta(days=milestone["offset_days"])
            self.db.add(
                TimelineMilestone(
                    engagement_id=engagement.id,
                    milestone_code=milestone["code"],
                    milestone_label=milestone["label"],
                    target_date=target_date,
                    owner=normalized["owner"],
                    status="done" if milestone["code"] in {"signal-captured", "intake"} else "pending",
                    source_signal_id=signal.id,
                    provenance_ref=normalized["provenance_ref"],
                    agent_id="28",
                    run_id=normalized["run_id"],
                    notes="Reverse-timed from detected deadline." if normalized["deadline"] and "reverse_offset_days" in milestone else "Auto-seeded from intake signal.",
                )
            )
        self.db.flush()

    def _seed_stakeholders(self, engagement: Engagement, signal: SourceSignal, normalized: dict[str, Any]) -> None:
        existing_keys = {
            (role_code, stakeholder_name)
            for role_code, stakeholder_name in self.db.execute(
                select(Stakeholder.role_code, Stakeholder.stakeholder_name).where(Stakeholder.engagement_id == engagement.id)
            ).all()
        }
        for stakeholder in ROUTE_CONFIG[normalized["route"]]["stakeholders"]:
            stakeholder_name = normalized["client_name"] if stakeholder["name"] == "Primary Contact" else stakeholder["name"]
            key = (stakeholder["role_code"], stakeholder_name)
            if key in existing_keys:
                continue
            organization = normalized["client_name"] if stakeholder.get("organization_from_client") else stakeholder.get("organization")
            self.db.add(
                Stakeholder(
                    engagement_id=engagement.id,
                    stakeholder_name=stakeholder_name,
                    role_code=stakeholder["role_code"],
                    role_label=stakeholder["role_label"],
                    organization=organization,
                    email="",
                    status="active",
                    interview_required=stakeholder["interview_required"],
                    approval_scope=stakeholder.get("approval_scope"),
                    source_signal_id=signal.id,
                    provenance_ref=normalized["provenance_ref"],
                    agent_id="28",
                    run_id=normalized["run_id"],
                    owner=normalized["owner"],
                    notes=f"Auto-seeded from {normalized['route']} intake.",
                )
            )
        self.db.flush()

    def _seed_actions(self, engagement: Engagement, signal: SourceSignal, normalized: dict[str, Any]) -> int:
        engagement.workflow_stage = "ACTION_SEED"
        count = 0
        existing_ids = {row.id for row in engagement.action_items}
        for index, action in enumerate(normalized["actions"], start=1):
            action_id = f"action-{signal.id}-{index:02d}"
            if action_id in existing_ids:
                continue
            self.db.add(
                ActionItem(
                    id=action_id,
                    engagement_id=engagement.id,
                    source_signal_id=signal.id,
                    item_type=action["type"],
                    task_or_artifact=action["task"],
                    owner=normalized["owner"],
                    due_date=action["due_date"],
                    status="open",
                    review_required=action["review_required"],
                    provenance_ref=normalized["provenance_ref"],
                    agent_id="29",
                    run_id=normalized["run_id"],
                    notes=action["notes"],
                )
            )
            count += 1
        self.db.flush()
        return count

    def _seed_approval(self, engagement: Engagement, signal: SourceSignal, normalized: dict[str, Any]) -> int:
        engagement.workflow_stage = "APPROVAL_WAIT"
        approval_id = f"approval-{engagement.id}-intake-review"
        if self.db.get(ApprovalRequest, approval_id):
            return 0
        self.db.add(
            ApprovalRequest(
                id=approval_id,
                engagement_id=engagement.id,
                source_signal_id=signal.id,
                approval_type="intake-review",
                requested_role="Executive Approver" if normalized["route"] == "proposal-capture" else "Internal Owner",
                requested_person=normalized["owner"],
                status="pending",
                due_date=normalized["signal_date"] + timedelta(days=1),
                channel="company-os",
                policy_key=f"{normalized['route']}-intake-review",
                provenance_ref=normalized["provenance_ref"],
                agent_id="30",
                run_id=normalized["run_id"],
                owner=normalized["owner"],
                notes=f"Review the newly captured signal from {normalized['provenance_ref']}.",
            )
        )
        self.db.flush()
        return 1

    def _seed_commitments(self, engagement: Engagement, signal: SourceSignal, normalized: dict[str, Any]) -> int:
        if normalized["signal_kind"] not in {"call-transcript", "interaction-log", "communication-capture"}:
            return 0
        count = 0
        for index, action in enumerate(normalized["actions"][:3], start=1):
            commitment_id = f"follow-{signal.id}-{index:02d}"
            if self.db.get(MeetingCommitment, commitment_id):
                continue
            self.db.add(
                MeetingCommitment(
                    id=commitment_id,
                    engagement_id=engagement.id,
                    source_signal_id=signal.id,
                    meeting_date=normalized["signal_date"],
                    account_or_client=normalized["client_name"],
                    meeting_title=normalized["title"],
                    owner=normalized["owner"],
                    commitment=action["task"],
                    commitment_owner=normalized["owner"],
                    due_date=action["due_date"],
                    status="open",
                    system_to_update="company-os",
                    provenance_ref=normalized["provenance_ref"],
                    agent_id="25",
                    run_id=normalized["run_id"],
                    notes=f"Captured from {normalized['signal_kind']}.",
                )
            )
            count += 1
        self.db.flush()
        return count

    def _seed_knowledge_candidates(self, engagement: Engagement, signal: SourceSignal, normalized: dict[str, Any]) -> int:
        candidate_id = f"lesson-{signal.id}"
        if self.db.get(KnowledgePromotionCandidate, candidate_id):
            return 0
        self.db.add(
            KnowledgePromotionCandidate(
                id=candidate_id,
                engagement_id=engagement.id,
                source_signal_id=signal.id,
                candidate_type="lesson",
                title=f"Lessons from {normalized['engagement_name']}",
                status="candidate",
                owner=normalized["owner"],
                provenance_ref=normalized["provenance_ref"],
                agent_id="31",
                run_id=normalized["run_id"],
                notes=normalized["summary"],
            )
        )
        self.db.flush()
        return 1

    def _count_urgent_risks(self, *, today: date) -> int:
        approvals_due = self.db.scalar(
            select(func.count()).select_from(ApprovalRequest).where(
                ApprovalRequest.status == "pending",
                ApprovalRequest.due_date.is_not(None),
                ApprovalRequest.due_date <= today,
            )
        ) or 0
        commitments_due = self.db.scalar(
            select(func.count()).select_from(MeetingCommitment).where(
                MeetingCommitment.status != "done",
                MeetingCommitment.due_date.is_not(None),
                MeetingCommitment.due_date <= today,
            )
        ) or 0
        engagements_due = self.db.scalar(
            select(func.count()).select_from(Engagement).where(
                Engagement.status == "active",
                Engagement.deadline.is_not(None),
                Engagement.deadline <= today + timedelta(days=2),
            )
        ) or 0
        return int(approvals_due + commitments_due + engagements_due)

    def _build_revenue_forecast_rows(self, *, today: date) -> list[RevenueForecastRow]:
        opportunities = list(
            self.db.scalars(
                select(Opportunity).order_by(Opportunity.weighted_pipeline_value.desc().nulls_last(), Opportunity.updated_at.desc())
            )
        )
        rows: list[RevenueForecastRow] = []
        for opportunity in opportunities[:25]:
            probability = int(round(float(opportunity.qualification_score or 0.0)))
            rows.append(
                RevenueForecastRow(
                    snapshot_date=today,
                    forecast_window="90-day",
                    forecast_type="pipeline",
                    account_name=opportunity.client,
                    stage=opportunity.pursuit_stage,
                    amount=float(opportunity.estimated_contract_value or 0.0),
                    expected_close_date=opportunity.expected_rfp_date,
                    probability_percent=probability,
                    weighted_amount=float(opportunity.weighted_pipeline_value or 0.0),
                    owner="proposal-ops",
                    next_action=opportunity.name,
                    notes=opportunity.provenance_summary or "",
                )
            )
        return rows

    def _build_cashflow_forecast_rows(self, *, today: date, revenue_rows: list[RevenueForecastRow]) -> list[CashflowForecastRow]:
        commercials = list(
            self.db.scalars(
                select(CommercialEngagement).order_by(CommercialEngagement.projected_payout_date.asc().nulls_last(), CommercialEngagement.updated_at.desc())
            )
        )
        buckets: dict[date, float] = defaultdict(float)
        for row in commercials:
            payout_date = row.projected_payout_date or (today + timedelta(days=14))
            week_start = payout_date - timedelta(days=payout_date.weekday())
            buckets[week_start] += float(row.projected_payout_amount or row.retainer_amount or 0.0)
        if not buckets:
            for forecast in revenue_rows[:4]:
                expected_date = forecast.expected_close_date or (today + timedelta(days=21))
                week_start = expected_date - timedelta(days=expected_date.weekday())
                buckets[week_start] += forecast.weighted_amount
        rows: list[CashflowForecastRow] = []
        running = 0.0
        for week_start in sorted(buckets.keys())[:8]:
            cash_in = round(buckets[week_start], 2)
            cash_out = 0.0
            running += cash_in - cash_out
            rows.append(
                CashflowForecastRow(
                    snapshot_date=today,
                    week_start=week_start,
                    projected_cash_in=cash_in,
                    projected_cash_out=cash_out,
                    net_cash_change=round(cash_in - cash_out, 2),
                    ending_cash_balance=round(running, 2),
                    confidence="medium",
                    notes="Projected from commercial engagements and weighted pipeline.",
                )
            )
        return rows

    def build_scoreboard_snapshot(self, *, owner: str, run_id: str) -> ScoreboardSnapshot:
        today = _today()
        pipeline_value = float(self.db.scalar(select(func.coalesce(func.sum(Opportunity.estimated_contract_value), 0.0))) or 0.0)
        weighted_pipeline = float(self.db.scalar(select(func.coalesce(func.sum(Opportunity.weighted_pipeline_value), 0.0))) or 0.0)
        meetings_booked = int(
            self.db.scalar(
                select(func.count()).select_from(GrowthRelationshipProfile).where(GrowthRelationshipProfile.meeting_status.ilike("%booked%"))
            )
            or 0
        )
        proposal_count = int(
            self.db.scalar(select(func.count()).select_from(Opportunity).where(Opportunity.proposal_stage.in_(["DRAFTING", "REVIEW", "SUBMISSION"])))
            or 0
        )
        wins = int(self.db.scalar(select(func.count()).select_from(Opportunity).where(Opportunity.pursuit_stage == "AWARD")) or 0)
        losses = int(self.db.scalar(select(func.count()).select_from(Opportunity).where(Opportunity.pursuit_stage == "LOST")) or 0)
        proposal_win_rate = round((wins / (wins + losses) * 100.0), 2) if (wins + losses) else 0.0
        active_delivery_count = int(
            self.db.scalar(
                select(func.count()).select_from(Engagement).where(Engagement.engagement_type == "delivery-client-success", Engagement.status == "active")
            )
            or 0
        )
        overdue_invoice_rows = list(
            self.db.scalars(
                select(CommercialEngagement).where(
                    CommercialEngagement.projected_payout_date.is_not(None),
                    CommercialEngagement.projected_payout_date < today - timedelta(days=30),
                )
            )
        )
        overdue_invoices = len(overdue_invoice_rows)
        total_ar_over_30 = round(
            sum(float(row.projected_payout_amount or row.retainer_amount or 0.0) - float(row.realized_revenue or 0.0) for row in overdue_invoice_rows),
            2,
        )
        urgent_risks = self._count_urgent_risks(today=today)
        revenue_rows = self._build_revenue_forecast_rows(today=today)
        cashflow_rows = self._build_cashflow_forecast_rows(today=today, revenue_rows=revenue_rows)
        snapshot = ScoreboardSnapshot(
            snapshot_date=today,
            pipeline_value=pipeline_value,
            weighted_pipeline=weighted_pipeline,
            meetings_booked=meetings_booked,
            proposal_count=proposal_count,
            proposal_win_rate=proposal_win_rate,
            active_delivery_count=active_delivery_count,
            overdue_invoices=overdue_invoices,
            total_ar_over_30=total_ar_over_30,
            open_hiring_roles=0,
            urgent_risks=urgent_risks,
            notes=f"Pipeline {pipeline_value:,.0f}; weighted {weighted_pipeline:,.0f}; {len(self.list_approvals())} approval items tracked.",
            revenue_rows_json=json.dumps([row.model_dump(mode='json') for row in revenue_rows]),
            cashflow_rows_json=json.dumps([row.model_dump(mode='json') for row in cashflow_rows]),
            agent_id="24",
            run_id=run_id,
            owner=owner,
            status="generated",
        )
        self.db.add(snapshot)
        self.db.flush()
        return snapshot

    def build_founder_brief(self, *, owner: str, run_id: str, scoreboard_snapshot: ScoreboardSnapshot | None = None) -> FounderBriefRun:
        today = _today()
        snapshot = scoreboard_snapshot or self.latest_scoreboard_snapshot() or self.build_scoreboard_snapshot(owner=owner, run_id=run_id)
        pending_approvals = [row for row in self.list_approvals() if row.status == "pending"]
        overdue_commitments = [row for row in self.list_commitments() if row.status != "done" and row.due_date and row.due_date < today]
        at_risk_engagements = [row for row in self.list_engagements() if row.status == "active" and row.deadline and row.deadline <= today + timedelta(days=2)]
        decisions = [
            FounderDecision(
                title=f"{item.engagement.client_name}: {item.approval_type}",
                owner=item.requested_person or item.owner,
                due_date=item.due_date,
                cost_of_delay="Blocks the engagement from moving past internal review.",
            )
            for item in pending_approvals[:5]
        ]
        if not decisions:
            decisions.append(FounderDecision(title="No immediate decision gate", owner=owner, due_date=None, cost_of_delay="No immediate action required."))
        top_moves = [
            f"Clear the oldest pending approval: {pending_approvals[0].id}" if pending_approvals else "Keep approvals queue empty by same-day review.",
            f"Rescue overdue commitment: {overdue_commitments[0].commitment}" if overdue_commitments else "Keep meeting follow-through current before close of day.",
            f"Advance nearest deadline: {at_risk_engagements[0].client_name}" if at_risk_engagements else "Protect top weighted pipeline opportunities.",
        ]
        delegation_queue = [item.next_action for item in at_risk_engagements[:3]] or ["No immediate delegation required."]
        brief = FounderBriefRun(
            brief_date=today,
            executive_control_summary=f"{snapshot.urgent_risks} urgent risk signals are open across approvals, deadlines, and collections. Weighted pipeline sits at ${snapshot.weighted_pipeline:,.0f}. {len(pending_approvals)} approvals and {len(overdue_commitments)} follow-through items need attention.",
            decisions_needed_json=json.dumps([item.model_dump(mode='json') for item in decisions]),
            revenue_watch=f"Weighted pipeline is ${snapshot.weighted_pipeline:,.0f} across {len(snapshot_revenue_rows(snapshot))} forecast rows. {snapshot.meetings_booked} meetings are booked and {snapshot.proposal_count} proposal-stage pursuits are active.",
            delivery_risk_watch="No immediate action required." if not at_risk_engagements else " | ".join(f"{item.client_name} due {item.deadline.isoformat()} with next action: {item.next_action}" for item in at_risk_engagements[:4]),
            cash_collections_watch=f"{snapshot.overdue_invoices} overdue invoice signals total ${snapshot.total_ar_over_30:,.0f} over 30 days. {len(snapshot_cash_rows(snapshot))} weekly cashflow rows are projected.",
            people_capacity_watch="No immediate action required.",
            top_moves_json=json.dumps(top_moves),
            delegation_queue_json=json.dumps(delegation_queue),
            scoreboard_snapshot_id=snapshot.id,
            agent_id="16",
            run_id=run_id,
            owner=owner,
            status="generated",
        )
        self.db.add(brief)
        for engagement in self.list_engagements():
            if engagement.workflow_stage == "FOUNDER_BRIEF":
                engagement.workflow_stage = "FOLLOW_THROUGH"
        self.db.flush()
        return brief


def snapshot_revenue_rows(snapshot: ScoreboardSnapshot | None) -> list[RevenueForecastRow]:
    if snapshot is None:
        return []
    payload = json.loads(snapshot.revenue_rows_json or "[]")
    return [RevenueForecastRow.model_validate(row) for row in payload]


def snapshot_cash_rows(snapshot: ScoreboardSnapshot | None) -> list[CashflowForecastRow]:
    if snapshot is None:
        return []
    payload = json.loads(snapshot.cashflow_rows_json or "[]")
    return [CashflowForecastRow.model_validate(row) for row in payload]


def founder_decisions(brief: FounderBriefRun | None) -> list[FounderDecision]:
    if brief is None:
        return []
    payload = json.loads(brief.decisions_needed_json or "[]")
    return [FounderDecision.model_validate(row) for row in payload]


def founder_top_moves(brief: FounderBriefRun | None) -> list[str]:
    if brief is None:
        return []
    payload = json.loads(brief.top_moves_json or "[]")
    return [str(item) for item in payload]


def founder_delegation_queue(brief: FounderBriefRun | None) -> list[str]:
    if brief is None:
        return []
    payload = json.loads(brief.delegation_queue_json or "[]")
    return [str(item) for item in payload]


def render_founder_brief_markdown(brief: FounderBriefRun, snapshot: ScoreboardSnapshot | None = None) -> str:
    decisions = founder_decisions(brief)
    top_moves = founder_top_moves(brief)
    delegation_queue = founder_delegation_queue(brief)
    revenue_rows = snapshot_revenue_rows(snapshot)
    cash_rows = snapshot_cash_rows(snapshot)

    lines = [
        f"# Founder Brief - {brief.brief_date.isoformat()}",
        "",
        "_AI-assisted internal operating brief. Final external judgment stays human-owned._",
        "",
        "## Executive Control Summary",
        brief.executive_control_summary,
        "",
        "## Decisions Needed",
    ]
    if decisions:
        for item in decisions:
            due_text = item.due_date.isoformat() if item.due_date else "No due date"
            lines.append(f"- {item.title} | Owner: {item.owner} | Due: {due_text} | Cost of delay: {item.cost_of_delay}")
    else:
        lines.append("- No immediate decision gates.")

    lines.extend(
        [
            "",
            "## Revenue Watch",
            brief.revenue_watch,
            "",
            "## Delivery Risk Watch",
            brief.delivery_risk_watch,
            "",
            "## Cash And Collections Watch",
            brief.cash_collections_watch,
            "",
            "## People And Capacity Watch",
            brief.people_capacity_watch,
            "",
            "## Top Moves",
        ]
    )
    if top_moves:
        lines.extend([f"- {item}" for item in top_moves])
    else:
        lines.append("- No top moves queued.")

    lines.extend(["", "## Delegation Queue"])
    if delegation_queue:
        lines.extend([f"- {item}" for item in delegation_queue])
    else:
        lines.append("- No delegation queue entries.")

    if snapshot is not None:
        lines.extend(
            [
                "",
                "## Scoreboard Snapshot",
                f"- Pipeline value: ${snapshot.pipeline_value:,.0f}",
                f"- Weighted pipeline: ${snapshot.weighted_pipeline:,.0f}",
                f"- Meetings booked: {snapshot.meetings_booked}",
                f"- Proposal count: {snapshot.proposal_count}",
                f"- Overdue invoices: {snapshot.overdue_invoices}",
                f"- Urgent risks: {snapshot.urgent_risks}",
            ]
        )

    if revenue_rows:
        lines.extend(["", "## Revenue Forecast Rows"])
        for row in revenue_rows[:8]:
            lines.append(
                f"- {row.account_name} | {row.stage} | Weighted ${row.weighted_amount:,.0f} | Close: {row.expected_close_date or 'TBD'}"
            )

    if cash_rows:
        lines.extend(["", "## Cashflow Forecast Rows"])
        for row in cash_rows[:8]:
            lines.append(
                f"- Week of {row.week_start.isoformat()} | Cash in ${row.projected_cash_in:,.0f} | Ending balance ${row.ending_cash_balance or 0:,.0f}"
            )

    lines.extend(["", "## Guardrails"])
    lines.extend([f"- {guardrail}" for guardrail in OPERATING_GUARDRAILS])
    return "\n".join(lines).strip() + "\n"


def render_ingest_summary_markdown(summary: IngestSummary, recent_engagements: list[Engagement]) -> str:
    lines = [
        "# Engagement Intake Snapshot",
        "",
        "_Proposal-ops is the system of record. This file is a generated compatibility brief._",
        "",
        "## Run Summary",
        f"- Run id: {summary.run_id}",
        f"- Created at: {_stringify(summary.created_at)}",
        f"- Sources scanned: {summary.sources_scanned}",
        f"- Items discovered: {summary.items_discovered}",
        f"- Signals created: {summary.signals_created}",
        f"- Engagements created: {summary.engagements_created}",
        f"- Engagements updated: {summary.engagements_updated}",
        f"- Actions created: {summary.actions_created}",
        f"- Approvals created: {summary.approvals_created}",
        f"- Commitments created: {summary.commitments_created}",
        "",
        "## Recent Engagements",
    ]
    if recent_engagements:
        for engagement in recent_engagements[:8]:
            deadline_text = engagement.deadline.isoformat() if engagement.deadline else "No deadline"
            lines.append(
                f"- {engagement.client_name} | {engagement.engagement_type} | {engagement.workflow_stage} | Deadline: {deadline_text} | Next: {engagement.next_action}"
            )
    else:
        lines.append("- No engagements have been captured yet.")

    lines.extend(["", "## Guardrails"])
    lines.extend([f"- {guardrail}" for guardrail in OPERATING_GUARDRAILS])
    return "\n".join(lines).strip() + "\n"


class CompanyOsService(CompanyOsService):
    def list_timeline_milestones(self) -> list[TimelineMilestone]:
        stmt = select(TimelineMilestone).order_by(TimelineMilestone.target_date.asc().nulls_last(), TimelineMilestone.created_at.asc())
        return list(self.db.scalars(stmt))

    def list_stakeholders(self) -> list[Stakeholder]:
        stmt = select(Stakeholder).order_by(Stakeholder.organization.asc().nulls_last(), Stakeholder.role_label.asc())
        return list(self.db.scalars(stmt))

    def generate_scoreboard_snapshot(self, *, owner: str = OWNER_NAME, run_id: str | None = None) -> ScoreboardSnapshot:
        effective_run_id = run_id or f"scoreboard-{_utcnow().strftime('%Y%m%d%H%M%S')}"
        snapshot = self.build_scoreboard_snapshot(owner=owner, run_id=effective_run_id)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def generate_founder_brief(self, *, owner: str = OWNER_NAME, run_id: str | None = None) -> FounderBriefRun:
        effective_run_id = run_id or f"brief-{_utcnow().strftime('%Y%m%d%H%M%S')}"
        snapshot = self.build_scoreboard_snapshot(owner=owner, run_id=effective_run_id)
        brief = self.build_founder_brief(owner=owner, run_id=effective_run_id, scoreboard_snapshot=snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        self.db.refresh(brief)
        return brief

    def run_projection_cycle(self, *, marketing_agents_root: str | Path | None = None, owner: str = OWNER_NAME, run_id: str | None = None) -> list[str]:
        effective_run_id = run_id or f"projection-{_utcnow().strftime('%Y%m%d%H%M%S')}"
        snapshot = self.build_scoreboard_snapshot(owner=owner, run_id=effective_run_id)
        brief = self.build_founder_brief(owner=owner, run_id=effective_run_id, scoreboard_snapshot=snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        self.db.refresh(brief)
        return self.export_projection_bundle(marketing_agents_root=marketing_agents_root)

    def run_manual_cycle(
        self,
        *,
        source_config_path: str | Path | None = None,
        marketing_agents_root: str | Path | None = None,
        owner: str = OWNER_NAME,
    ) -> IngestSummary:
        run_id = f"company-os-{_utcnow().strftime('%Y%m%d%H%M%S')}"
        summary = IngestSummary(run_id=run_id, created_at=_utcnow())
        source_config = _resolve_repo_path(source_config_path or DEFAULT_SOURCE_CONFIG)

        try:
            enabled_sources = [
                row
                for row in _read_csv(source_config)
                if str(row.get("enabled") or "").strip().lower() == "yes"
            ]
            summary.sources_scanned = len(enabled_sources)

            for source in enabled_sources:
                items = list(self._collect_source_items(source))
                summary.items_discovered += len(items)
                for item in items:
                    normalized = self._normalize_item(item, owner=owner, run_id=run_id)
                    if normalized is None:
                        summary.skipped_items += 1
                        continue

                    signal = self._upsert_signal(normalized)
                    if signal is None:
                        continue

                    summary.signals_created += 1
                    engagement, created = self._upsert_engagement(signal, normalized)
                    if created:
                        summary.engagements_created += 1
                    else:
                        summary.engagements_updated += 1

                    self._seed_timeline(engagement, signal, normalized)
                    self._seed_stakeholders(engagement, signal, normalized)
                    summary.actions_created += self._seed_actions(engagement, signal, normalized)
                    summary.approvals_created += self._seed_approval(engagement, signal, normalized)
                    summary.commitments_created += self._seed_commitments(engagement, signal, normalized)
                    summary.knowledge_candidates_created += self._seed_knowledge_candidates(engagement, signal, normalized)

            snapshot = self.build_scoreboard_snapshot(owner=owner, run_id=run_id)
            brief = self.build_founder_brief(owner=owner, run_id=run_id, scoreboard_snapshot=snapshot)
            self.db.commit()
            self.db.refresh(snapshot)
            self.db.refresh(brief)

            summary.scoreboard_snapshot_id = snapshot.id
            summary.founder_brief_id = brief.id
            summary.projections_written = self.export_projection_bundle(marketing_agents_root=marketing_agents_root, summary=summary)
            return summary
        except Exception:
            self.db.rollback()
            raise

    def export_projection_bundle(self, *, marketing_agents_root: str | Path | None = None, summary: IngestSummary | None = None) -> list[str]:
        marketing_root = _resolve_repo_path(marketing_agents_root or DEFAULT_MARKETING_ROOT)
        data_dir = marketing_root / "data"
        briefs_dir = marketing_root / "briefs"

        engagements = self.list_engagements()
        engagement_map = {row.id: row for row in engagements}
        signals = self.list_signals(limit=5000)
        actions = self.list_actions()
        approvals = self.list_approvals()
        commitments = self.list_commitments()
        milestones = self.list_timeline_milestones()
        stakeholders = self.list_stakeholders()
        snapshot = self.latest_scoreboard_snapshot()
        brief = self.latest_founder_brief()

        paths = [
            _write_csv(data_dir / "communication_signal_log.csv", PROJECTION_HEADERS["communication_signal_log.csv"], self._signal_projection_rows(signals)),
            _write_csv(data_dir / "engagement_register.csv", PROJECTION_HEADERS["engagement_register.csv"], self._engagement_projection_rows(engagements)),
            _write_csv(data_dir / "engagement_timeline.csv", PROJECTION_HEADERS["engagement_timeline.csv"], self._timeline_projection_rows(milestones)),
            _write_csv(data_dir / "stakeholder_map.csv", PROJECTION_HEADERS["stakeholder_map.csv"], self._stakeholder_projection_rows(stakeholders)),
            _write_csv(data_dir / "action_workbench.csv", PROJECTION_HEADERS["action_workbench.csv"], self._action_projection_rows(actions, engagement_map)),
            _write_csv(data_dir / "approval_router_queue.csv", PROJECTION_HEADERS["approval_router_queue.csv"], self._approval_projection_rows(approvals, engagement_map)),
            _write_csv(data_dir / "meeting_follow_through.csv", PROJECTION_HEADERS["meeting_follow_through.csv"], self._commitment_projection_rows(commitments)),
            _write_csv(data_dir / "executive_scoreboard.csv", PROJECTION_HEADERS["executive_scoreboard.csv"], self._scoreboard_projection_rows(snapshot)),
            _write_csv(data_dir / "revenue_forecast.csv", PROJECTION_HEADERS["revenue_forecast.csv"], self._revenue_projection_rows(snapshot)),
            _write_csv(data_dir / "cashflow_forecast.csv", PROJECTION_HEADERS["cashflow_forecast.csv"], self._cashflow_projection_rows(snapshot)),
        ]

        if summary is not None:
            summary_payload = {
                "run_id": summary.run_id,
                "sources_scanned": summary.sources_scanned,
                "items_discovered": summary.items_discovered,
                "skipped_items": summary.skipped_items,
                "signals_created": summary.signals_created,
                "engagements_created": summary.engagements_created,
                "engagements_updated": summary.engagements_updated,
                "actions_created": summary.actions_created,
                "approvals_created": summary.approvals_created,
                "commitments_created": summary.commitments_created,
                "knowledge_candidates_created": summary.knowledge_candidates_created,
                "founder_brief_id": summary.founder_brief_id,
                "scoreboard_snapshot_id": summary.scoreboard_snapshot_id,
                "created_at": summary.created_at,
                "proposal_ops_source_of_truth": True,
                "guardrails": OPERATING_GUARDRAILS,
            }
            paths.append(_write_json(data_dir / "engagement_intake_summary.json", summary_payload))
            paths.append(_write_text(briefs_dir / "engagement-intake-latest.md", render_ingest_summary_markdown(summary, engagements)))

        if brief is not None:
            paths.append(_write_text(briefs_dir / "founder-brief-latest.md", render_founder_brief_markdown(brief, snapshot)))

        return paths

    def _signal_projection_rows(self, rows: list[SourceSignal]) -> list[dict[str, Any]]:
        return [
            {
                "signal_id": row.id,
                "source_type": row.source_type,
                "source_system": row.source_system,
                "client_name": row.client_name,
                "engagement_id": find_engagement_id(row.client_name, row.route),
                "thread_or_meeting_id": row.thread_or_meeting_id or "",
                "signal_date": _stringify(row.signal_date),
                "signal_kind": row.signal_kind,
                "summary": row.summary,
                "owner": row.owner,
                "status": row.status,
                "provenance_ref": row.provenance_ref,
            }
            for row in rows
        ]

    def _engagement_projection_rows(self, rows: list[Engagement]) -> list[dict[str, Any]]:
        return [
            {
                "engagement_id": row.id,
                "client_name": row.client_name,
                "engagement_name": row.engagement_name,
                "engagement_type": row.engagement_type,
                "status": row.status,
                "intake_date": _stringify(row.intake_date),
                "owner": row.owner,
                "complexity_level": row.complexity_level,
                "next_action": row.next_action,
                "deadline": _stringify(row.deadline),
                "source_signal_id": row.last_signal_id or "",
                "notes": row.notes or "",
            }
            for row in rows
        ]

    def _timeline_projection_rows(self, rows: list[TimelineMilestone]) -> list[dict[str, Any]]:
        return [
            {
                "engagement_id": row.engagement_id,
                "milestone_code": row.milestone_code,
                "milestone_label": row.milestone_label,
                "target_date": _stringify(row.target_date),
                "owner": row.owner,
                "status": row.status,
                "source": row.source_signal_id or row.provenance_ref,
                "notes": row.notes or "",
            }
            for row in rows
        ]

    def _stakeholder_projection_rows(self, rows: list[Stakeholder]) -> list[dict[str, Any]]:
        return [
            {
                "engagement_id": row.engagement_id,
                "stakeholder_name": row.stakeholder_name,
                "role_code": row.role_code,
                "role_label": row.role_label,
                "organization": row.organization or "",
                "email": row.email or "",
                "status": row.status,
                "interview_required": row.interview_required,
                "approval_scope": row.approval_scope or "",
                "notes": row.notes or "",
            }
            for row in rows
        ]

    def _action_projection_rows(self, rows: list[ActionItem], engagement_map: dict[str, Engagement]) -> list[dict[str, Any]]:
        return [
            {
                "action_id": row.id,
                "engagement_id": row.engagement_id,
                "client_name": engagement_map.get(row.engagement_id).client_name if engagement_map.get(row.engagement_id) else "",
                "source_signal_id": row.source_signal_id or "",
                "action_type": row.item_type,
                "task_or_artifact": row.task_or_artifact,
                "owner": row.owner,
                "due_date": _stringify(row.due_date),
                "status": row.status,
                "review_required": row.review_required,
                "notes": row.notes or "",
            }
            for row in rows
        ]

    def _approval_projection_rows(self, rows: list[ApprovalRequest], engagement_map: dict[str, Engagement]) -> list[dict[str, Any]]:
        return [
            {
                "routing_id": row.id,
                "engagement_id": row.engagement_id,
                "client_name": engagement_map.get(row.engagement_id).client_name if engagement_map.get(row.engagement_id) else "",
                "approval_type": row.approval_type,
                "requested_role": row.requested_role,
                "requested_person": row.requested_person or "",
                "status": row.status,
                "due_date": _stringify(row.due_date),
                "channel": row.channel,
                "policy_key": row.policy_key,
                "notes": row.notes or "",
            }
            for row in rows
        ]

    def _commitment_projection_rows(self, rows: list[MeetingCommitment]) -> list[dict[str, Any]]:
        return [
            {
                "meeting_id": row.id,
                "meeting_date": _stringify(row.meeting_date),
                "account_or_client": row.account_or_client,
                "meeting_title": row.meeting_title,
                "owner": row.owner,
                "commitment": row.commitment,
                "commitment_owner": row.commitment_owner,
                "due_date": _stringify(row.due_date),
                "status": row.status,
                "system_to_update": row.system_to_update,
                "notes": row.notes or "",
            }
            for row in rows
        ]

    def _scoreboard_projection_rows(self, snapshot: ScoreboardSnapshot | None) -> list[dict[str, Any]]:
        if snapshot is None:
            return []
        return [
            {
                "snapshot_date": _stringify(snapshot.snapshot_date),
                "pipeline_value": snapshot.pipeline_value,
                "weighted_pipeline": snapshot.weighted_pipeline,
                "meetings_booked": snapshot.meetings_booked,
                "proposal_count": snapshot.proposal_count,
                "proposal_win_rate": snapshot.proposal_win_rate,
                "active_delivery_count": snapshot.active_delivery_count,
                "overdue_invoices": snapshot.overdue_invoices,
                "total_ar_over_30": snapshot.total_ar_over_30,
                "open_hiring_roles": snapshot.open_hiring_roles,
                "urgent_risks": snapshot.urgent_risks,
                "notes": snapshot.notes or "",
            }
        ]

    def _revenue_projection_rows(self, snapshot: ScoreboardSnapshot | None) -> list[dict[str, Any]]:
        return [
            {
                "snapshot_date": _stringify(row.snapshot_date),
                "forecast_window": row.forecast_window,
                "forecast_type": row.forecast_type,
                "account_name": row.account_name,
                "stage": row.stage,
                "amount": row.amount,
                "expected_close_date": _stringify(row.expected_close_date),
                "probability_percent": row.probability_percent,
                "weighted_amount": row.weighted_amount,
                "owner": row.owner,
                "next_action": row.next_action or "",
                "notes": row.notes or "",
            }
            for row in snapshot_revenue_rows(snapshot)
        ]

    def _cashflow_projection_rows(self, snapshot: ScoreboardSnapshot | None) -> list[dict[str, Any]]:
        return [
            {
                "snapshot_date": _stringify(row.snapshot_date),
                "week_start": _stringify(row.week_start),
                "projected_cash_in": row.projected_cash_in,
                "projected_cash_out": row.projected_cash_out,
                "net_cash_change": row.net_cash_change,
                "ending_cash_balance": row.ending_cash_balance if row.ending_cash_balance is not None else "",
                "confidence": row.confidence,
                "notes": row.notes or "",
            }
            for row in snapshot_cash_rows(snapshot)
        ]
