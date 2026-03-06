from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.modules.opportunity_intake.models import Opportunity
from app.modules.identity.schemas import (
    EffectiveRolesResponse,
    RoleAssignmentRequest,
    UserCreateRequest,
    UserResponse,
    UserRoleResponse,
)
from app.modules.identity.service import IdentityService


api_router = APIRouter(prefix="/api/users", tags=["identity"])
web_router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/web/templates")


def _require_admin_session(request: Request) -> None:
    if not request.session.get("user_id"):
        raise HTTPException(status_code=403, detail="Login required")
    if not request.session.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin role required")


@api_router.get("", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)) -> list[UserResponse]:
    users = IdentityService(db).list_users()
    return [UserResponse.model_validate(u, from_attributes=True) for u in users]


@api_router.post("", response_model=UserResponse)
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db)) -> UserResponse:
    user = IdentityService(db).create_user(payload.display_name, payload.email)
    return UserResponse.model_validate(user, from_attributes=True)


@api_router.get("/{user_id}/roles", response_model=list[UserRoleResponse])
def list_user_roles(user_id: str, db: Session = Depends(get_db)) -> list[UserRoleResponse]:
    service = IdentityService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    roles = service.list_roles(user_id)
    return [UserRoleResponse.model_validate(r, from_attributes=True) for r in roles]


@api_router.post("/{user_id}/roles", response_model=UserRoleResponse)
def assign_user_role(user_id: str, payload: RoleAssignmentRequest, db: Session = Depends(get_db)) -> UserRoleResponse:
    service = IdentityService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        role = service.assign_role(user_id, payload.role, payload.scope_type, payload.scope_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return UserRoleResponse.model_validate(role, from_attributes=True)


@api_router.get("/{user_id}/effective-roles", response_model=EffectiveRolesResponse)
def effective_roles_for_user(
    user_id: str,
    opportunity_id: str,
    db: Session = Depends(get_db),
) -> EffectiveRolesResponse:
    service = IdentityService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    roles = service.scoped_roles(user_id, opportunity_id)
    return EffectiveRolesResponse(user_id=user_id, opportunity_id=opportunity_id, roles=roles)


@web_router.get("/admin/users", response_class=HTMLResponse)
def users_admin(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    _require_admin_session(request)
    service = IdentityService(db)
    users = service.list_users()
    user_roles = {u.id: service.list_roles(u.id) for u in users}
    opportunities = list(db.scalars(select(Opportunity).order_by(Opportunity.created_at.desc())))
    return templates.TemplateResponse(
        request=request,
        name="users_admin.html",
        context={"users": users, "user_roles": user_roles, "opportunities": opportunities},
    )


@web_router.post("/admin/users")
def create_user_web(
    request: Request,
    display_name: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    _require_admin_session(request)
    IdentityService(db).create_user(display_name, email)
    return RedirectResponse(url="/admin/users", status_code=303)


@web_router.post("/admin/users/{user_id}/roles")
def assign_user_role_web(
    request: Request,
    user_id: str,
    role: str = Form(...),
    scope_type: str = Form(...),
    scope_id: str = Form(""),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    _require_admin_session(request)
    service = IdentityService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        service.assign_role(user_id, role, scope_type, scope_id or None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(url="/admin/users", status_code=303)
