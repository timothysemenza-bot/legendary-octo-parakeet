from app.core.config import GATE_POLICY_PACK
from app.core.workflow import GateCode


POLICY_PACKS: dict[str, dict[str, dict[str, list[str]]]] = {
    "default": {
        GateCode.GATE_A.value: {
            "approvers": ["proposal_manager", "executive_approver"],
            "delegates": ["capture_lead_delegate"],
        },
        GateCode.GATE_B.value: {
            "approvers": ["capture_strategy_lead", "proposal_manager"],
            "delegates": ["strategy_delegate"],
        },
        GateCode.GATE_C.value: {
            "approvers": ["compliance_lead", "proposal_manager"],
            "delegates": ["compliance_delegate"],
        },
        GateCode.GATE_D.value: {
            "approvers": ["review_lead", "compliance_lead"],
            "delegates": ["review_delegate"],
        },
        GateCode.GATE_E.value: {
            "approvers": ["proposal_manager", "executive_approver"],
            "delegates": ["narrative_delegate"],
        },
        GateCode.GATE_F.value: {
            "approvers": ["executive_approver", "compliance_lead"],
            "delegates": ["executive_delegate"],
        },
        GateCode.GATE_G.value: {
            "approvers": ["knowledge_manager", "proposal_manager"],
            "delegates": ["knowledge_delegate"],
        },
    },
    "lean": {
        GateCode.GATE_A.value: {"approvers": ["proposal_manager"], "delegates": ["operations_delegate"]},
        GateCode.GATE_B.value: {"approvers": ["proposal_manager"], "delegates": ["operations_delegate"]},
        GateCode.GATE_C.value: {"approvers": ["proposal_manager"], "delegates": ["operations_delegate"]},
        GateCode.GATE_D.value: {"approvers": ["proposal_manager"], "delegates": ["operations_delegate"]},
        GateCode.GATE_E.value: {"approvers": ["proposal_manager"], "delegates": ["operations_delegate"]},
        GateCode.GATE_F.value: {"approvers": ["proposal_manager"], "delegates": ["operations_delegate"]},
        GateCode.GATE_G.value: {"approvers": ["proposal_manager"], "delegates": ["operations_delegate"]},
    },
}


def active_policy_pack_name() -> str:
    if GATE_POLICY_PACK in POLICY_PACKS:
        return GATE_POLICY_PACK
    return "default"


def gate_policy(gate_code: str) -> dict[str, list[str]]:
    pack = POLICY_PACKS[active_policy_pack_name()]
    return pack[gate_code]


def is_role_authorized_for_gate(gate_code: str, role: str) -> bool:
    normalized = role.strip().lower()
    policy = gate_policy(gate_code)
    allowed = {r.lower() for r in policy["approvers"] + policy["delegates"]}
    return normalized in allowed

