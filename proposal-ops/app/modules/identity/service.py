import hashlib
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import APPROVAL_SIGNING_SECRET
from app.core.policy import gate_policy
from app.core.workflow import GateCode
from app.modules.identity.models import User, UserRoleAssignment
from app.modules.opportunity_intake.models import Opportunity


class IdentityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_user(self, display_name: str, email: str) -> User:
        user = User(display_name=display_name, email=email, status="ACTIVE")
        self.db.add(user)
        self.db.flush()
        self.db.commit()
        return user

    def list_users(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.created_at.desc())))

    def get_user(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.scalars(stmt).first()

    def assign_role(self, user_id: str, role: str, scope_type: str, scope_id: str | None) -> UserRoleAssignment:
        normalized_scope = scope_type.upper()
        if normalized_scope not in {"GLOBAL", "OPPORTUNITY"}:
            raise ValueError("scope_type must be GLOBAL or OPPORTUNITY")
        if normalized_scope == "GLOBAL":
            scope_id = None
        if normalized_scope == "OPPORTUNITY":
            if not scope_id:
                raise ValueError("scope_id is required for OPPORTUNITY scope")
            opportunity = self.db.get(Opportunity, scope_id)
            if not opportunity:
                raise ValueError("scope_id does not reference a valid opportunity")
        assignment = UserRoleAssignment(
            user_id=user_id,
            role=role,
            scope_type=normalized_scope,
            scope_id=scope_id,
        )
        self.db.add(assignment)
        self.db.flush()
        self.db.commit()
        return assignment

    def list_roles(self, user_id: str) -> list[UserRoleAssignment]:
        stmt = select(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id).order_by(UserRoleAssignment.created_at.desc())
        return list(self.db.scalars(stmt))

    def global_roles(self, user_id: str) -> list[str]:
        stmt = select(UserRoleAssignment).where(
            UserRoleAssignment.user_id == user_id,
            UserRoleAssignment.scope_type == "GLOBAL",
        )
        return [r.role for r in self.db.scalars(stmt)]

    def scoped_roles(self, user_id: str, opportunity_id: str) -> list[str]:
        stmt = select(UserRoleAssignment).where(UserRoleAssignment.user_id == user_id)
        assignments = list(self.db.scalars(stmt))
        roles: list[str] = []
        for a in assignments:
            if a.scope_type == "GLOBAL":
                roles.append(a.role)
            elif a.scope_type == "OPPORTUNITY" and a.scope_id == opportunity_id:
                roles.append(a.role)
        return roles

    def resolve_authorized_role_for_gate(self, user_id: str, gate_code: str, opportunity_id: str) -> str | None:
        policy = gate_policy(gate_code)
        allowed = {r.lower() for r in policy["approvers"] + policy["delegates"]}
        roles = self.scoped_roles(user_id, opportunity_id)
        for role in roles:
            if role.lower() in allowed:
                return role
        return None

    def gate_permission_report(self, user_id: str, opportunity_id: str, gate_code: str) -> dict:
        policy = gate_policy(gate_code)
        required_roles = policy["approvers"] + policy["delegates"]
        scoped_roles = self.scoped_roles(user_id, opportunity_id)
        allowed = {r.lower() for r in required_roles}
        matched_roles = [r for r in scoped_roles if r.lower() in allowed]
        is_allowed = len(matched_roles) > 0
        if is_allowed:
            reason = "Authorized by matched role assignment."
        elif not scoped_roles:
            reason = "No role assignments found for this opportunity."
        else:
            reason = "Assigned roles do not satisfy gate policy."
        return {
            "gate_code": gate_code,
            "allowed": is_allowed,
            "required_roles": required_roles,
            "user_roles": scoped_roles,
            "matched_roles": matched_roles,
            "reason": reason,
        }

    def gate_permission_reports(self, user_id: str, opportunity_id: str) -> list[dict]:
        reports: list[dict] = []
        for gate in GateCode:
            reports.append(self.gate_permission_report(user_id, opportunity_id, gate.value))
        return reports

    def sign_gate_approval(
        self,
        *,
        user_id: str,
        opportunity_id: str,
        gate_code: str,
        decision: str,
        rationale: str,
        timestamp: datetime,
    ) -> str:
        blob = "|".join(
            [
                user_id,
                opportunity_id,
                gate_code,
                decision,
                rationale.strip(),
                timestamp.isoformat(),
                APPROVAL_SIGNING_SECRET,
            ]
        )
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()
