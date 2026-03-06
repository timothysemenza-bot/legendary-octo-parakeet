from enum import StrEnum


class OpportunityStage(StrEnum):
    INTAKE = "INTAKE"
    QUALIFICATION = "QUALIFICATION"
    STRATEGY = "STRATEGY"
    COMPLIANCE = "COMPLIANCE"
    CONTENT_PLANNING = "CONTENT_PLANNING"
    DRAFTING = "DRAFTING"
    REVIEW = "REVIEW"
    SUBMISSION = "SUBMISSION"
    ARCHIVE = "ARCHIVE"


class GateDecision(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REWORK_REQUIRED = "REWORK_REQUIRED"


class GateCode(StrEnum):
    GATE_A = "GATE_A"  # Intake validation + bid/no-bid
    GATE_B = "GATE_B"  # Strategy approval
    GATE_C = "GATE_C"  # Compliance/response architecture approval
    GATE_D = "GATE_D"  # Content QC + factual validation
    GATE_E = "GATE_E"  # Narrative/persuasion integrity
    GATE_F = "GATE_F"  # Final compliance cert + submission auth
    GATE_G = "GATE_G"  # Lessons learned approval


LEGACY_GATE_ALIASES = {
    "BID_NO_BID": GateCode.GATE_A.value,
}

STAGE_SEQUENCE = [
    OpportunityStage.INTAKE,
    OpportunityStage.QUALIFICATION,
    OpportunityStage.STRATEGY,
    OpportunityStage.COMPLIANCE,
    OpportunityStage.CONTENT_PLANNING,
    OpportunityStage.DRAFTING,
    OpportunityStage.REVIEW,
    OpportunityStage.SUBMISSION,
    OpportunityStage.ARCHIVE,
]

ALLOWED_STAGE_TRANSITIONS = {
    OpportunityStage.INTAKE: {OpportunityStage.QUALIFICATION},
    OpportunityStage.QUALIFICATION: {OpportunityStage.INTAKE, OpportunityStage.STRATEGY},
    OpportunityStage.STRATEGY: {OpportunityStage.QUALIFICATION, OpportunityStage.COMPLIANCE},
    OpportunityStage.COMPLIANCE: {OpportunityStage.STRATEGY, OpportunityStage.CONTENT_PLANNING},
    OpportunityStage.CONTENT_PLANNING: {OpportunityStage.COMPLIANCE, OpportunityStage.DRAFTING},
    OpportunityStage.DRAFTING: {OpportunityStage.CONTENT_PLANNING, OpportunityStage.REVIEW},
    OpportunityStage.REVIEW: {OpportunityStage.DRAFTING, OpportunityStage.SUBMISSION},
    OpportunityStage.SUBMISSION: {OpportunityStage.REVIEW, OpportunityStage.ARCHIVE},
    OpportunityStage.ARCHIVE: {OpportunityStage.SUBMISSION},
}

STAGE_ENTRY_REQUIRED_GATES = {
    OpportunityStage.STRATEGY: [GateCode.GATE_A],
    OpportunityStage.COMPLIANCE: [GateCode.GATE_B],
    OpportunityStage.CONTENT_PLANNING: [GateCode.GATE_C],
    OpportunityStage.DRAFTING: [GateCode.GATE_C],
    OpportunityStage.SUBMISSION: [GateCode.GATE_D, GateCode.GATE_E],
    OpportunityStage.ARCHIVE: [GateCode.GATE_F],
}

STAGE_ACTIVE_GATE = {
    OpportunityStage.INTAKE: GateCode.GATE_A,
    OpportunityStage.QUALIFICATION: GateCode.GATE_A,
    OpportunityStage.STRATEGY: GateCode.GATE_B,
    OpportunityStage.COMPLIANCE: GateCode.GATE_C,
    OpportunityStage.CONTENT_PLANNING: GateCode.GATE_C,
    OpportunityStage.DRAFTING: GateCode.GATE_D,
    OpportunityStage.REVIEW: GateCode.GATE_E,
    OpportunityStage.SUBMISSION: GateCode.GATE_F,
    OpportunityStage.ARCHIVE: GateCode.GATE_G,
}

GATE_APPROVAL_STAGE_ADVANCE = {
    GateCode.GATE_A: OpportunityStage.STRATEGY,
    GateCode.GATE_B: OpportunityStage.COMPLIANCE,
    GateCode.GATE_C: OpportunityStage.CONTENT_PLANNING,
    GateCode.GATE_D: OpportunityStage.REVIEW,
    GateCode.GATE_E: OpportunityStage.SUBMISSION,
    GateCode.GATE_F: OpportunityStage.ARCHIVE,
    GateCode.GATE_G: OpportunityStage.ARCHIVE,
}

GATE_REWORK_STAGE_TARGET = {
    GateCode.GATE_A: OpportunityStage.QUALIFICATION,
    GateCode.GATE_B: OpportunityStage.STRATEGY,
    GateCode.GATE_C: OpportunityStage.COMPLIANCE,
    GateCode.GATE_D: OpportunityStage.DRAFTING,
    GateCode.GATE_E: OpportunityStage.REVIEW,
    GateCode.GATE_F: OpportunityStage.SUBMISSION,
    GateCode.GATE_G: OpportunityStage.ARCHIVE,
}

GATE_REJECT_STAGE_TARGET = {
    GateCode.GATE_A: OpportunityStage.INTAKE,
    GateCode.GATE_B: OpportunityStage.QUALIFICATION,
    GateCode.GATE_C: OpportunityStage.STRATEGY,
    GateCode.GATE_D: OpportunityStage.CONTENT_PLANNING,
    GateCode.GATE_E: OpportunityStage.DRAFTING,
    GateCode.GATE_F: OpportunityStage.REVIEW,
    GateCode.GATE_G: OpportunityStage.SUBMISSION,
}


def normalize_gate_code(gate_code: str) -> str:
    normalized = LEGACY_GATE_ALIASES.get(gate_code, gate_code)
    return normalized


def evaluate_gate_transition(current_stage: str, gate_code: str, decision: str) -> tuple[str, str]:
    gate = GateCode(normalize_gate_code(gate_code))
    if decision == GateDecision.APPROVED.value:
        return (current_stage, GATE_APPROVAL_STAGE_ADVANCE[gate].value)
    if decision == GateDecision.REWORK_REQUIRED.value:
        return (current_stage, GATE_REWORK_STAGE_TARGET[gate].value)
    if decision == GateDecision.REJECTED.value:
        return (current_stage, GATE_REJECT_STAGE_TARGET[gate].value)
    return (current_stage, current_stage)


def can_enter_stage(current_stage: str, next_stage: str, approved_gates: set[str]) -> tuple[bool, list[str]]:
    current = OpportunityStage(current_stage)
    target = OpportunityStage(next_stage)
    blockers: list[str] = []

    if current == target:
        blockers.append("Already in target stage.")
    allowed_targets = ALLOWED_STAGE_TRANSITIONS[current]
    if target not in allowed_targets:
        blockers.append(f"Transition {current.value} -> {target.value} is not allowed by state machine.")

    current_idx = STAGE_SEQUENCE.index(current)
    target_idx = STAGE_SEQUENCE.index(target)
    if target_idx > current_idx + 1:
        blockers.append("Cannot skip stages.")
    if target_idx < current_idx - 1:
        blockers.append("Cannot jump back multiple stages without gate rework/rejection.")

    required = STAGE_ENTRY_REQUIRED_GATES.get(target, [])
    for gate in required:
        if gate.value not in approved_gates:
            blockers.append(f"{gate.value} must be APPROVED before entering {target.value}.")

    return (len(blockers) == 0, blockers)


def active_gate_for_stage(stage: str) -> str:
    return STAGE_ACTIVE_GATE[OpportunityStage(stage)].value
