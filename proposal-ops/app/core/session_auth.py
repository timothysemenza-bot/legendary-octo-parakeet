from fastapi import Request
from sqlalchemy.orm import Session

from app.modules.identity.models import User
from app.modules.identity.service import IdentityService


def get_session_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = IdentityService(db).get_user(user_id)
    if not user or user.status != "ACTIVE":
        return None
    return user

